"""
Gemini AI client for content generation.

Handles both text generation (announcements) and image generation (banners)
using Google's Gemini API.

Architecture: See 04_WishlistOps_System_Architecture_Diagrams.md Section 2
API Specs: See Section 11 for detailed API integration
"""

import asyncio
import base64
import logging
import json
from dataclasses import dataclass
from typing import Optional, Any
from pathlib import Path

import aiohttp
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from .models import AIConfig


logger = logging.getLogger(__name__)


class AIError(Exception):
    """Base exception for AI client errors."""
    pass


class RateLimitError(AIError):
    """Raised when API rate limit is exceeded."""
    pass


class GenerationError(AIError):
    """Raised when content generation fails."""
    pass


@dataclass
class TextGenerationResult:
    """Result of text generation."""
    title: str
    body: str
    metadata: dict[str, Any]


@dataclass
class ImageGenerationResult:
    """Result of image generation."""
    image_data: bytes  # PNG bytes
    width: int
    height: int
    metadata: dict[str, Any]


class GeminiClient:
    """
    Client for Google Gemini API (text and image generation).
    
    This client handles:
    - Announcement text generation (Gemini 1.5 Pro)
    - Banner image generation (Gemini 2.5 Flash Image)
    - Retry logic with exponential backoff
    - Context window management
    - Rate limiting
    
    Attributes:
        api_key: Google AI API key
        config: AI configuration
        base_url: Gemini API base URL
        session: Async HTTP session
    """
    
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

    @staticmethod
    def _normalize_model_name(model_name: str) -> str:
        """Accept either 'gemini-...' or 'models/gemini-...'; return bare id."""
        name = (model_name or "").strip()
        if name.startswith("models/"):
            return name[len("models/"):]
        return name

    @staticmethod
    def _prefer_text_model(model_names: list[str]) -> Optional[str]:
        """Pick a reasonable default text model from a list of bare model ids."""
        if not model_names:
            return None

        # Prefer fast/cheap general-purpose text models if present.
        preferred_prefixes = [
            "gemini-2.0-flash",
            "gemini-2.0-pro",
            "gemini-1.5-flash",
            "gemini-1.5-pro",
        ]
        for pref in preferred_prefixes:
            for name in model_names:
                if name == pref or name.startswith(pref + "-"):
                    return name

        # Fall back to first sorted to keep deterministic.
        return sorted(model_names)[0]
    
    def __init__(self, api_key: str, config: AIConfig) -> None:
        """
        Initialize Gemini AI client.
        
        Args:
            api_key: Google AI API key (from AI Studio or Cloud Console)
            config: AI configuration (models, temperature, etc.)
            
        Raises:
            ValueError: If API key is invalid format
        """
        if not api_key or not api_key.startswith('AIza'):
            raise ValueError(
                "Invalid Google AI API key format.\n"
                "Expected: AIzaSy...\n"
                "Get key at: https://ai.google.dev/"
            )
        
        self.api_key = api_key
        self.config = config
        self.base_url = self.BASE_URL
        self.session: Optional[aiohttp.ClientSession] = None
        
        logger.info("Gemini client initialized", extra={
            "model_text": config.model_text,
            "model_image": config.model_image
        })
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
            self.session = None
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
        reraise=True
    )
    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> TextGenerationResult:
        """
        Generate announcement text using Gemini 1.5 Pro.
        
        Args:
            prompt: The prompt containing commits and context
            system_instruction: System instruction for persona/tone
            temperature: Creativity level (0-1), uses config default if None
            
        Returns:
            TextGenerationResult with title and body
            
        Raises:
            RateLimitError: If rate limit exceeded
            GenerationError: If generation fails
            AIError: For other API errors
        """
        if not self.session:
            raise AIError("Client not initialized. Use 'async with' context manager.")
        
        temp = temperature if temperature is not None else self.config.temperature
        
        logger.info("Generating text with Gemini", extra={
            "model": self.config.model_text,
            "temperature": temp,
            "prompt_length": len(prompt)
        })
        
        # Build request payload
        payload = {
            "contents": [{
                "role": "user",
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": temp,
                "maxOutputTokens": 2048,
                "topP": 0.95,
                "topK": 40
            }
        }
        
        # Add system instruction if provided
        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }
        
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key,
        }

        async def _post_with_model(model_text: str) -> TextGenerationResult:
            model_id = self._normalize_model_name(model_text)
            url = f"{self.base_url}/models/{model_id}:generateContent"
            async with self.session.post(
                url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                # Handle rate limiting
                if response.status == 429:
                    retry_after = response.headers.get("Retry-After", "60")
                    raise RateLimitError(
                        f"Rate limit exceeded. Retry after {retry_after}s.\n"
                        f"Tip: Reduce frequency or upgrade to paid tier."
                    )

                if response.status != 200:
                    error_text = await response.text()
                    raise GenerationError(
                        f"API error (status {response.status}): {error_text}"
                    )

                data = await response.json()
                result = self._parse_text_response(data)
                logger.info(
                    "Text generation successful",
                    extra={"title_length": len(result.title), "body_length": len(result.body)},
                )
                return result

        try:
            try:
                return await _post_with_model(self.config.model_text)
            except GenerationError as first_error:
                # If the configured model is unavailable, try to auto-pick a supported model.
                msg = str(first_error)
                if "status 404" not in msg:
                    raise
                if "Call ListModels" not in msg and "ListModels" not in msg:
                    raise

                try:
                    models = await self.list_generate_content_models()
                except Exception:
                    raise first_error

                choices = [m.get("name") for m in models if isinstance(m, dict) and m.get("name")]
                picked = self._prefer_text_model([self._normalize_model_name(c) for c in choices if isinstance(c, str)])
                if not picked:
                    raise GenerationError(
                        "No generateContent-capable models are available for this API key. "
                        "Call ListModels and choose a supported model."
                    )

                logger.warning(
                    "Configured text model not available; falling back",
                    extra={"from": self.config.model_text, "to": picked},
                )
                self.config.model_text = picked
                return await _post_with_model(picked)
        
        except asyncio.TimeoutError as e:
            raise AIError("API request timed out after 30s") from e
        except aiohttp.ClientError as e:
            raise AIError(f"Network error: {e}") from e

    async def list_models(self) -> list[dict[str, Any]]:
        """List models available to the current API key (Gemini v1beta ListModels)."""
        if not self.session:
            raise AIError("Client not initialized. Use 'async with' context manager.")

        url = f"{self.base_url}/models"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key,
        }

        models: list[dict[str, Any]] = []
        page_token: Optional[str] = None

        while True:
            params = {}
            if page_token:
                params["pageToken"] = page_token

            async with self.session.get(
                url,
                headers=headers,
                params=params,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise GenerationError(f"API error (status {response.status}): {error_text}")

                data = await response.json()
                page_models = data.get("models", [])
                if isinstance(page_models, list):
                    for m in page_models:
                        if isinstance(m, dict):
                            models.append(m)

                page_token = data.get("nextPageToken")
                if not page_token:
                    break

        return models

    async def list_generate_content_models(self) -> list[dict[str, Any]]:
        """Return models that support generateContent, with normalized bare ids in 'name'."""
        raw = await self.list_models()
        supported: list[dict[str, Any]] = []
        for model in raw:
            methods = model.get("supportedGenerationMethods") or model.get("supported_methods") or []
            if not isinstance(methods, list):
                methods = []
            if "generateContent" not in methods:
                continue

            name = model.get("name") or ""
            supported.append(
                {
                    "name": self._normalize_model_name(str(name)),
                    "display_name": model.get("displayName") or model.get("display_name"),
                    "description": model.get("description"),
                    "supported_methods": methods,
                }
            )

        supported.sort(key=lambda m: str(m.get("name") or ""))
        return supported
    
    def _parse_text_response(self, data: dict) -> TextGenerationResult:
        """
        Parse Gemini API response for text generation.
        
        Args:
            data: JSON response from API
            
        Returns:
            Parsed TextGenerationResult
            
        Raises:
            GenerationError: If response format is invalid
        """
        try:
            # Extract generated text
            candidates = data.get('candidates', [])
            if not candidates:
                raise GenerationError("No candidates in response")
            
            content = candidates[0].get('content', {})
            parts = content.get('parts', [])
            if not parts:
                raise GenerationError("No parts in response")
            
            text = parts[0].get('text', '')
            if not text:
                raise GenerationError("Empty text in response")

            def _strip_code_fences(raw: str) -> str:
                s = raw.strip()
                if not s.startswith("```"):
                    return s
                lines_local = s.splitlines()
                if not lines_local:
                    return s
                if not lines_local[0].startswith("```"):
                    return s
                # Drop opening fence (``` or ```json)
                body_lines = lines_local[1:]
                # Drop trailing fence if present
                if body_lines and body_lines[-1].strip() == "```":
                    body_lines = body_lines[:-1]
                return "\n".join(body_lines).strip()

            def _try_parse_json_payload(raw: str) -> Optional[dict[str, Any]]:
                s = _strip_code_fences(raw)
                s2 = s.strip()
                if not (s2.startswith("{") and s2.endswith("}")):
                    return None
                try:
                    parsed = json.loads(s2)
                except Exception:
                    return None
                if isinstance(parsed, dict):
                    return parsed
                return None

            parsed_json = _try_parse_json_payload(text)
            if parsed_json:
                title_json = parsed_json.get("title")
                body_json = parsed_json.get("body")
                if isinstance(title_json, str) and isinstance(body_json, str) and title_json.strip() and body_json.strip():
                    metadata = {
                        'model': data.get('modelVersion', self.config.model_text),
                        'finish_reason': (data.get('candidates', [{}])[0].get('finishReason', 'unknown') if isinstance(data.get('candidates', []), list) else 'unknown'),
                        'safety_ratings': (data.get('candidates', [{}])[0].get('safetyRatings', []) if isinstance(data.get('candidates', []), list) else []),
                        'parsed_as': 'json',
                    }
                    return TextGenerationResult(
                        title=title_json.strip()[:255],
                        body=body_json.strip(),
                        metadata=metadata,
                    )
            
            # Parse into title and body
            # Expected format: "Title: ...\n\nBody: ..."
            text_clean = _strip_code_fences(text)
            lines = text_clean.strip().split('\n', 1)
            
            if len(lines) < 2:
                # Fallback: use first line as title, rest as body
                title = lines[0][:255]  # Max Steam title length
                body = text_clean
            else:
                # Extract title (remove "Title:" prefix if present)
                title = lines[0].replace('Title:', '').strip()[:255]
                body = lines[1].replace('Body:', '').strip()
            
            # Extract metadata
            metadata = {
                'model': data.get('modelVersion', self.config.model_text),
                'finish_reason': candidates[0].get('finishReason', 'unknown'),
                'safety_ratings': candidates[0].get('safetyRatings', [])
            }
            
            return TextGenerationResult(
                title=title,
                body=body,
                metadata=metadata
            )
            
        except (KeyError, IndexError, AttributeError) as e:
            raise GenerationError(f"Failed to parse response: {e}") from e
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
        reraise=True
    )
    async def generate_image(
        self,
        prompt: str,
        reference_image_path: Optional[Path] = None,
        aspect_ratio: str = "16:9"
    ) -> ImageGenerationResult:
        """
        Generate banner image using Gemini 2.5 Flash Image.
        
        Args:
            prompt: Image generation prompt (art style, content description)
            reference_image_path: Path to reference screenshot for style matching
            aspect_ratio: Image aspect ratio ("16:9", "1:1", "4:3")
            
        Returns:
            ImageGenerationResult with PNG bytes
            
        Raises:
            RateLimitError: If rate limit exceeded
            GenerationError: If generation fails
            AIError: For other API errors
        """
        if not self.session:
            raise AIError("Client not initialized. Use 'async with' context manager.")
        
        logger.info("Generating image with Gemini", extra={
            "model": self.config.model_image,
            "aspect_ratio": aspect_ratio,
            "has_reference": reference_image_path is not None
        })
        
        # Build request parts
        parts = [{"text": prompt}]
        
        # Add reference image if provided
        if reference_image_path and reference_image_path.exists():
            with open(reference_image_path, 'rb') as f:
                image_bytes = f.read()
                image_b64 = base64.b64encode(image_bytes).decode('utf-8')
            
            parts.append({
                "inline_data": {
                    "mime_type": "image/png",
                    "data": image_b64
                }
            })
        
        # Build payload
        payload = {
            "contents": [{
                "role": "user",
                "parts": parts
            }],
            "generationConfig": {
                "responseModalities": ["image"],
                "aspectRatio": aspect_ratio
            }
        }
        
        # Make API call
        model_id = self._normalize_model_name(self.config.model_image)
        url = f"{self.base_url}/models/{model_id}:generateContent"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key
        }
        
        try:
            async with self.session.post(
                url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=60)  # Image gen takes longer
            ) as response:
                
                if response.status == 429:
                    retry_after = response.headers.get('Retry-After', '60')
                    raise RateLimitError(
                        f"Rate limit exceeded. Retry after {retry_after}s"
                    )
                
                if response.status != 200:
                    error_text = await response.text()
                    raise GenerationError(
                        f"Image generation failed (status {response.status}): {error_text}"
                    )
                
                # Parse response
                data = await response.json()
                result = self._parse_image_response(data)
                
                logger.info("Image generation successful", extra={
                    "size_bytes": len(result.image_data),
                    "dimensions": f"{result.width}x{result.height}"
                })
                
                return result
        
        except asyncio.TimeoutError as e:
            raise AIError("Image generation timed out after 60s") from e
        except aiohttp.ClientError as e:
            raise AIError(f"Network error: {e}") from e
    
    def _parse_image_response(self, data: dict) -> ImageGenerationResult:
        """
        Parse Gemini API response for image generation.
        
        Args:
            data: JSON response from API
            
        Returns:
            Parsed ImageGenerationResult
            
        Raises:
            GenerationError: If response format is invalid
        """
        try:
            candidates = data.get('candidates', [])
            if not candidates:
                raise GenerationError("No candidates in response")
            
            content = candidates[0].get('content', {})
            parts = content.get('parts', [])
            if not parts:
                raise GenerationError("No parts in response")
            
            # Extract base64 image data
            inline_data = parts[0].get('inline_data', {})
            if not inline_data:
                inline_data = parts[0].get('inlineData', {})
            image_b64 = inline_data.get('data', '')
            
            if not image_b64:
                raise GenerationError("No image data in response")
            
            # Decode base64
            image_bytes = base64.b64decode(image_b64)
            
            # Get dimensions from metadata or assume standard
            # Note: Gemini doesn't always return dimensions, so we may need to parse PNG header
            width = 1024  # Default
            height = 576   # Default for 16:9
            
            metadata = {
                'model': data.get('modelVersion', self.config.model_image),
                'finish_reason': candidates[0].get('finishReason', 'unknown')
            }
            
            return ImageGenerationResult(
                image_data=image_bytes,
                width=width,
                height=height,
                metadata=metadata
            )
            
        except (KeyError, IndexError, base64.binascii.Error) as e:
            raise GenerationError(f"Failed to parse image response: {e}") from e
    
    async def close(self) -> None:
        """Close the HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None


# Convenience wrapper class for backwards compatibility
class AIClient(GeminiClient):
    """Alias for GeminiClient (backwards compatibility)."""
    pass
