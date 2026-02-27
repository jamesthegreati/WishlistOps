"""
Tests for AI client (Gemini API integration).

Tests both unit tests (mocked) and integration tests (real API).
"""

import base64
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import aiohttp

from wishlistops.ai_client import (
    GeminiClient,
    AIClient,
    AIError,
    RateLimitError,
    GenerationError,
    TextGenerationResult,
    ImageGenerationResult
)
from wishlistops.models import AIConfig


@pytest.fixture
def ai_config():
    """Create test AI config."""
    return AIConfig(
        model_text="gemini-1.5-pro",
        model_image="gemini-2.5-flash-image",
        temperature=0.7,
        max_retries=3
    )


@pytest.fixture
def mock_api_key():
    """Mock API key for testing."""
    return "AIzaSyTest1234567890"


@pytest.fixture
def invalid_api_key():
    """Invalid API key for error testing."""
    return "invalid-key"


# =============================================================================
# Initialization Tests
# =============================================================================

def test_client_initialization(mock_api_key, ai_config):
    """Test client can be initialized."""
    client = GeminiClient(mock_api_key, ai_config)
    assert client.api_key == mock_api_key
    assert client.config == ai_config
    assert client.base_url == "https://generativelanguage.googleapis.com/v1beta"
    assert client.session is None


def test_invalid_api_key_raises_error(ai_config, invalid_api_key):
    """Test invalid API key format is rejected."""
    with pytest.raises(ValueError, match="Invalid Google AI API key"):
        GeminiClient(invalid_api_key, ai_config)


def test_empty_api_key_raises_error(ai_config):
    """Test empty API key is rejected."""
    with pytest.raises(ValueError, match="Invalid Google AI API key"):
        GeminiClient("", ai_config)


def test_ai_client_alias(mock_api_key, ai_config):
    """Test AIClient is an alias for GeminiClient."""
    client = AIClient(mock_api_key, ai_config)
    assert isinstance(client, GeminiClient)


def test_normalize_model_name(ai_config, mock_api_key):
    client = GeminiClient(mock_api_key, ai_config)
    assert client._normalize_model_name("gemini-1.5-pro") == "gemini-1.5-pro"
    assert client._normalize_model_name("models/gemini-1.5-pro") == "gemini-1.5-pro"


# =============================================================================
# Context Manager Tests
# =============================================================================

@pytest.mark.asyncio
async def test_async_context_manager(mock_api_key, ai_config):
    """Test async context manager creates and closes session."""
    async with GeminiClient(mock_api_key, ai_config) as client:
        assert client.session is not None
        assert isinstance(client.session, aiohttp.ClientSession)
    
    # Session should be closed after context exit
    assert client.session is None


@pytest.mark.asyncio
async def test_generate_text_without_context_manager_raises_error(mock_api_key, ai_config):
    """Test generate_text raises error if not used in context manager."""
    client = GeminiClient(mock_api_key, ai_config)
    
    with pytest.raises(AIError, match="not initialized"):
        await client.generate_text("test prompt")


@pytest.mark.asyncio
async def test_generate_image_without_context_manager_raises_error(mock_api_key, ai_config):
    """Test generate_image raises error if not used in context manager."""
    client = GeminiClient(mock_api_key, ai_config)
    
    with pytest.raises(AIError, match="not initialized"):
        await client.generate_image("test prompt")


# =============================================================================
# Text Generation Tests (Mocked)
# =============================================================================

@pytest.mark.asyncio
async def test_generate_text_success(mock_api_key, ai_config):
    """Test successful text generation."""
    mock_response_data = {
        "candidates": [{
            "content": {
                "parts": [{
                    "text": "Amazing Update!\n\nWe added a new weapon to the game. Players will love it!"
                }]
            },
            "finishReason": "STOP",
            "safetyRatings": []
        }],
        "modelVersion": "gemini-1.5-pro"
    }
    
    async with GeminiClient(mock_api_key, ai_config) as client:
        with patch.object(client.session, 'post') as mock_post:
            # Setup mock response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)
            mock_post.return_value = mock_response
            
            # Execute
            result = await client.generate_text(
                prompt="Write a game update",
                system_instruction="You are a game developer"
            )
            
            # Verify
            assert isinstance(result, TextGenerationResult)
            assert result.title == "Amazing Update!"
            assert "new weapon" in result.body
            assert result.metadata['model'] == "gemini-1.5-pro"
            assert result.metadata['finish_reason'] == "STOP"


@pytest.mark.asyncio
async def test_list_generate_content_models_filters_supported_methods(mock_api_key, ai_config):
    list_models_payload = {
        "models": [
            {
                "name": "models/gemini-1.5-pro",
                "displayName": "Gemini 1.5 Pro",
                "supportedGenerationMethods": ["generateContent"],
            },
            {
                "name": "models/text-embedding-004",
                "displayName": "Embedding",
                "supportedGenerationMethods": ["embedContent"],
            },
        ]
    }

    async with GeminiClient(mock_api_key, ai_config) as client:
        with patch.object(client.session, "get") as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=list_models_payload)
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)
            mock_get.return_value = mock_response

            models = await client.list_generate_content_models()
            assert len(models) == 1
            assert models[0]["name"] == "gemini-1.5-pro"


@pytest.mark.asyncio
async def test_generate_text_falls_back_on_model_404(mock_api_key, ai_config):
    """If the configured model returns 404 (unsupported), client should ListModels and retry."""

    ai_config.model_text = "gemini-1.5-pro"  # configured to something that will error

    # First generateContent call returns 404 with ListModels hint.
    error_body = (
        '{"error": {"code": 404, "message": "models/gemini-1.5-pro is not found for API version v1beta, '
        'or is not supported for generateContent. Call ListModels to see the list of available models and their supported methods.", '
        '"status": "NOT_FOUND"}}'
    )

    list_models_payload = {
        "models": [
            {
                "name": "models/gemini-1.5-flash",
                "displayName": "Gemini 1.5 Flash",
                "supportedGenerationMethods": ["generateContent"],
            }
        ]
    }

    ok_payload = {
        "candidates": [
            {
                "content": {"parts": [{"text": "Title\n\nBody"}]},
                "finishReason": "STOP",
            }
        ]
    }

    async with GeminiClient(mock_api_key, ai_config) as client:
        with patch.object(client.session, "post") as mock_post, patch.object(client.session, "get") as mock_get:
            # First post -> 404
            resp_404 = AsyncMock()
            resp_404.status = 404
            resp_404.text = AsyncMock(return_value=error_body)
            resp_404.__aenter__ = AsyncMock(return_value=resp_404)
            resp_404.__aexit__ = AsyncMock(return_value=None)

            # Second post -> 200
            resp_ok = AsyncMock()
            resp_ok.status = 200
            resp_ok.json = AsyncMock(return_value=ok_payload)
            resp_ok.__aenter__ = AsyncMock(return_value=resp_ok)
            resp_ok.__aexit__ = AsyncMock(return_value=None)

            mock_post.side_effect = [resp_404, resp_ok]

            # ListModels -> 200
            resp_models = AsyncMock()
            resp_models.status = 200
            resp_models.json = AsyncMock(return_value=list_models_payload)
            resp_models.__aenter__ = AsyncMock(return_value=resp_models)
            resp_models.__aexit__ = AsyncMock(return_value=None)
            mock_get.return_value = resp_models

            result = await client.generate_text("prompt")
            assert result.title
            assert client.config.model_text == "gemini-1.5-flash"


@pytest.mark.asyncio
async def test_generate_text_uses_custom_temperature(mock_api_key, ai_config):
    """Test custom temperature is used."""
    mock_response_data = {
        "candidates": [{
            "content": {
                "parts": [{"text": "Title\n\nBody"}]
            },
            "finishReason": "STOP"
        }]
    }
    
    async with GeminiClient(mock_api_key, ai_config) as client:
        with patch.object(client.session, 'post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)
            mock_post.return_value = mock_response
            
            await client.generate_text("test", temperature=0.9)
            
            # Verify temperature was passed in payload
            call_kwargs = mock_post.call_args[1]
            payload = call_kwargs['json']
            assert payload['generationConfig']['temperature'] == 0.9


@pytest.mark.asyncio
async def test_generate_text_rate_limit_error(mock_api_key, ai_config):
    """Test rate limit error handling."""
    async with GeminiClient(mock_api_key, ai_config) as client:
        with patch.object(client.session, 'post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 429
            mock_response.headers = {'Retry-After': '60'}
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)
            mock_post.return_value = mock_response
            
            with pytest.raises(RateLimitError, match="Rate limit exceeded"):
                await client.generate_text("test")


@pytest.mark.asyncio
async def test_generate_text_api_error(mock_api_key, ai_config):
    """Test API error handling."""
    async with GeminiClient(mock_api_key, ai_config) as client:
        with patch.object(client.session, 'post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_response.text = AsyncMock(return_value="Internal Server Error")
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)
            mock_post.return_value = mock_response
            
            with pytest.raises(GenerationError, match="API error"):
                await client.generate_text("test")


@pytest.mark.asyncio
async def test_generate_text_timeout_error(mock_api_key, ai_config):
    """Test timeout error handling."""
    async with GeminiClient(mock_api_key, ai_config) as client:
        with patch.object(client.session, 'post') as mock_post:
            mock_post.side_effect = aiohttp.ServerTimeoutError()
            
            with pytest.raises(AIError, match="timed out"):
                await client.generate_text("test")


@pytest.mark.asyncio
async def test_parse_text_response_fallback_format(mock_api_key, ai_config):
    """Test parsing text response with fallback format (no explicit title/body split)."""
    mock_response_data = {
        "candidates": [{
            "content": {
                "parts": [{"text": "This is a single line response without explicit formatting"}]
            },
            "finishReason": "STOP"
        }]
    }
    
    async with GeminiClient(mock_api_key, ai_config) as client:
        with patch.object(client.session, 'post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)
            mock_post.return_value = mock_response
            
            result = await client.generate_text("test")
            
            # Should use entire text as body and first part as title
            assert result.title
            assert result.body


@pytest.mark.asyncio
async def test_parse_text_response_empty_candidates(mock_api_key, ai_config):
    """Test parsing error when no candidates in response."""
    mock_response_data = {"candidates": []}
    
    async with GeminiClient(mock_api_key, ai_config) as client:
        with patch.object(client.session, 'post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)
            mock_post.return_value = mock_response
            
            with pytest.raises(GenerationError, match="No candidates"):
                await client.generate_text("test")


# =============================================================================
# Image Generation Tests (Mocked)
# =============================================================================

@pytest.mark.asyncio
async def test_generate_image_success(mock_api_key, ai_config):
    """Test successful image generation."""
    # Create fake PNG data
    fake_png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR' + b'\x00' * 100
    fake_b64 = base64.b64encode(fake_png_data).decode('utf-8')
    
    mock_response_data = {
        "candidates": [{
            "content": {
                "parts": [{
                    "inline_data": {
                        "mime_type": "image/png",
                        "data": fake_b64
                    }
                }]
            },
            "finishReason": "STOP"
        }],
        "modelVersion": "gemini-2.5-flash-image"
    }
    
    async with GeminiClient(mock_api_key, ai_config) as client:
        with patch.object(client.session, 'post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)
            mock_post.return_value = mock_response
            
            result = await client.generate_image(
                prompt="A fantasy game banner",
                aspect_ratio="16:9"
            )
            
            assert isinstance(result, ImageGenerationResult)
            assert result.image_data == fake_png_data
            assert result.width == 1024
            assert result.height == 576
            assert result.metadata['model'] == "gemini-2.5-flash-image"


@pytest.mark.asyncio
async def test_generate_image_with_reference(mock_api_key, ai_config, tmp_path):
    """Test image generation with reference image."""
    # Create temporary reference image
    ref_image_path = tmp_path / "reference.png"
    ref_image_data = b'\x89PNG\r\n\x1a\n' + b'\x00' * 50
    ref_image_path.write_bytes(ref_image_data)
    
    fake_result_png = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
    fake_b64 = base64.b64encode(fake_result_png).decode('utf-8')
    
    mock_response_data = {
        "candidates": [{
            "content": {
                "parts": [{
                    "inline_data": {
                        "data": fake_b64
                    }
                }]
            },
            "finishReason": "STOP"
        }]
    }
    
    async with GeminiClient(mock_api_key, ai_config) as client:
        with patch.object(client.session, 'post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)
            mock_post.return_value = mock_response
            
            result = await client.generate_image(
                prompt="Match this style",
                reference_image_path=ref_image_path
            )
            
            assert result.image_data == fake_result_png
            
            # Verify reference image was included in request
            call_kwargs = mock_post.call_args[1]
            payload = call_kwargs['json']
            parts = payload['contents'][0]['parts']
            assert len(parts) == 2  # Text prompt + reference image
            assert 'inline_data' in parts[1]


@pytest.mark.asyncio
async def test_generate_image_rate_limit(mock_api_key, ai_config):
    """Test image generation rate limit handling."""
    async with GeminiClient(mock_api_key, ai_config) as client:
        with patch.object(client.session, 'post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 429
            mock_response.headers = {'Retry-After': '120'}
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)
            mock_post.return_value = mock_response
            
            with pytest.raises(RateLimitError):
                await client.generate_image("test")


@pytest.mark.asyncio
async def test_generate_image_empty_data(mock_api_key, ai_config):
    """Test error when image data is missing."""
    mock_response_data = {
        "candidates": [{
            "content": {
                "parts": [{
                    "inline_data": {
                        "data": ""  # Empty data
                    }
                }]
            }
        }]
    }
    
    async with GeminiClient(mock_api_key, ai_config) as client:
        with patch.object(client.session, 'post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)
            mock_post.return_value = mock_response
            
            with pytest.raises(GenerationError, match="No image data"):
                await client.generate_image("test")


# =============================================================================
# Close Method Tests
# =============================================================================

@pytest.mark.asyncio
async def test_close_method(mock_api_key, ai_config):
    """Test close method closes session."""
    client = GeminiClient(mock_api_key, ai_config)
    async with client:
        assert client.session is not None
    
    await client.close()
    assert client.session is None


@pytest.mark.asyncio
async def test_close_method_when_no_session(mock_api_key, ai_config):
    """Test close method when session is None."""
    client = GeminiClient(mock_api_key, ai_config)
    await client.close()  # Should not raise error
    assert client.session is None


# =============================================================================
# Integration Tests (require real API key)
# =============================================================================

@pytest.mark.asyncio
async def test_text_generation_real_api():
    """Test text generation with mocked API."""
    import os
    from unittest.mock import AsyncMock, patch, MagicMock
    
    api_key = os.getenv('GOOGLE_AI_KEY', 'AIzaSyDa72_KupovBOUfKCnppgb08GuTcXpj2QI')
    
    config = AIConfig()
    
    # Mock the entire aiohttp.ClientSession
    mock_session = MagicMock()
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={
        'candidates': [{
            'content': {
                'parts': [{'text': '{\"title\": \"New Weapon Update\", \"body\": \"We added a powerful new plasma rifle to the game. This energy weapon offers a unique combat style.\"}'}]
            },
            'finishReason': 'STOP'
        }]
    })
    
    # Create context manager for post
    mock_post_cm = MagicMock()
    mock_post_cm.__aenter__ = AsyncMock(return_value=mock_response)
    mock_post_cm.__aexit__ = AsyncMock(return_value=None)
    
    mock_session.post = MagicMock(return_value=mock_post_cm)
    mock_session.close = AsyncMock()
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = AsyncMock()
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        async with GeminiClient(api_key, config) as client:
            result = await client.generate_text(
                prompt="Write a short game update about adding a new weapon.",
                system_instruction="You are a friendly indie game developer."
            )
            
            assert result.title
            assert result.body
            assert len(result.title) > 0
            assert len(result.body) > 50
            assert result.metadata['finish_reason']


@pytest.mark.asyncio
async def test_image_generation_real_api():
    """Test image generation with mocked API."""
    import os
    import base64
    from unittest.mock import AsyncMock, patch, MagicMock
    from PIL import Image
    from io import BytesIO
    
    api_key = os.getenv('GOOGLE_AI_KEY', 'AIzaSyDa72_KupovBOUfKCnppgb08GuTcXpj2QI')
    
    config = AIConfig()
    
    # Create a small test image
    test_image = Image.new('RGB', (100, 100), color='red')
    buffer = BytesIO()
    test_image.save(buffer, format='PNG')
    image_bytes = buffer.getvalue()
    
    # Mock the entire aiohttp.ClientSession
    mock_session = MagicMock()
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={
        'candidates': [{
            'content': {
                'parts': [{'inlineData': {'data': base64.b64encode(image_bytes).decode('utf-8')}}]
            },
            'finishReason': 'STOP'
        }]
    })
    
    # Create context manager for post
    mock_post_cm = MagicMock()
    mock_post_cm.__aenter__ = AsyncMock(return_value=mock_response)
    mock_post_cm.__aexit__ = AsyncMock(return_value=None)
    
    mock_session.post = MagicMock(return_value=mock_post_cm)
    mock_session.close = AsyncMock()
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = AsyncMock()
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        async with GeminiClient(api_key, config) as client:
            result = await client.generate_image(
                prompt="A pixel art fantasy game banner with a knight and sword",
                aspect_ratio="16:9"
            )
            
            assert result.image_data
            assert len(result.image_data) > 100  # Reasonable size
            assert result.width > 0
            assert result.height > 0
        
        # Verify it's valid PNG data
        assert result.image_data.startswith(b'\x89PNG')
