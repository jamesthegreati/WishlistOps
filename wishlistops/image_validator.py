"""
Image-Commit Validation for WishlistOps.

Multi-tier validation system to ensure screenshots match commit messages:
1. Deterministic keyword matching (fast, reliable, no API)
2. Screenshot file validation (format, size, dimensions)
3. AI Vision enhancement (optional, for uncertain cases)

This ensures announcements use relevant, high-quality screenshots.
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, List, Set, Dict, Any

from PIL import Image

logger = logging.getLogger(__name__)


class ValidationResult(str, Enum):
    """Result of image-commit validation."""
    MATCH = "match"
    NO_MATCH = "no_match"
    UNCERTAIN = "uncertain"
    INVALID_FILE = "invalid_file"


class MatchCategory(str, Enum):
    """Categories for commit-image matching."""
    GAMEPLAY = "gameplay"
    UI = "ui"
    CHARACTER = "character"
    ENVIRONMENT = "environment"
    COMBAT = "combat"
    MENU = "menu"
    CUTSCENE = "cutscene"
    UNKNOWN = "unknown"


@dataclass
class ValidationReport:
    """Report from image validation."""
    result: ValidationResult
    confidence: float  # 0.0 to 1.0
    category: MatchCategory
    keywords_found: List[str]
    warnings: List[str]
    ai_analysis: Optional[str] = None
    
    @property
    def is_valid(self) -> bool:
        """Check if validation passed."""
        return self.result in (ValidationResult.MATCH, ValidationResult.UNCERTAIN)


class ImageValidator:
    """
    Validates that screenshots match commit messages.
    
    Uses a three-tier approach:
    1. Deterministic keyword extraction and matching
    2. Screenshot file validation (technical checks)
    3. AI vision enhancement (optional fallback)
    """
    
    # Keyword mappings for different categories
    CATEGORY_KEYWORDS: Dict[MatchCategory, Set[str]] = {
        MatchCategory.GAMEPLAY: {
            "gameplay", "play", "mechanic", "game", "action", "movement",
            "jump", "dash", "run", "walk", "shoot", "attack", "defend"
        },
        MatchCategory.UI: {
            "ui", "menu", "button", "interface", "hud", "overlay", "widget",
            "panel", "dialog", "popup", "notification", "inventory", "settings"
        },
        MatchCategory.CHARACTER: {
            "character", "player", "hero", "protagonist", "npc", "enemy",
            "boss", "companion", "sprite", "model", "avatar"
        },
        MatchCategory.ENVIRONMENT: {
            "environment", "level", "map", "world", "area", "zone", "biome",
            "terrain", "background", "scenery", "landscape", "room"
        },
        MatchCategory.COMBAT: {
            "combat", "fight", "battle", "weapon", "skill", "ability", "spell",
            "damage", "health", "attack", "defense", "boss fight"
        },
        MatchCategory.MENU: {
            "menu", "screen", "title", "pause", "options", "main menu",
            "settings", "controls", "audio", "graphics"
        },
        MatchCategory.CUTSCENE: {
            "cutscene", "cinematic", "dialogue", "dialog", "story", "narrative",
            "conversation", "event", "scene"
        }
    }
    
    # Steam recommended dimensions
    MIN_WIDTH = 1280
    MIN_HEIGHT = 720
    RECOMMENDED_WIDTH = 1920
    RECOMMENDED_HEIGHT = 1080
    MAX_FILE_SIZE_MB = 5
    
    def __init__(self, use_ai: bool = True, ai_client: Optional[Any] = None):
        """
        Initialize validator.
        
        Args:
            use_ai: Whether to use AI vision for uncertain cases
            ai_client: Optional AIClient instance for vision analysis
        """
        self.use_ai = use_ai
        self.ai_client = ai_client
        
    def validate(
        self,
        screenshot_path: Path,
        commit_message: str,
        commit_files: Optional[List[str]] = None
    ) -> ValidationReport:
        """
        Validate screenshot matches commit.
        
        Args:
            screenshot_path: Path to screenshot image
            commit_message: Git commit message
            commit_files: Optional list of files changed in commit
            
        Returns:
            ValidationReport with results and recommendations
        """
        logger.info(f"Validating screenshot: {screenshot_path}")
        
        warnings: List[str] = []
        
        # Tier 1: File validation
        if not screenshot_path.exists():
            return ValidationReport(
                result=ValidationResult.INVALID_FILE,
                confidence=0.0,
                category=MatchCategory.UNKNOWN,
                keywords_found=[],
                warnings=[f"Screenshot not found: {screenshot_path}"]
            )
        
        # Validate file format and dimensions
        file_warnings = self._validate_file(screenshot_path)
        warnings.extend(file_warnings)
        
        # Tier 2: Deterministic keyword matching
        commit_keywords = self._extract_keywords(commit_message)
        filename_keywords = self._extract_filename_keywords(screenshot_path)
        file_path_keywords = self._extract_filepath_keywords(commit_files or [])
        
        all_keywords = commit_keywords | filename_keywords | file_path_keywords
        
        logger.debug(f"Extracted keywords: {all_keywords}")
        
        # Classify based on keywords
        category = self._classify_keywords(all_keywords)
        
        # Check for matches
        keyword_matches = self._find_keyword_matches(all_keywords)
        
        if len(keyword_matches) >= 2:
            # Strong match: multiple keyword categories align
            return ValidationReport(
                result=ValidationResult.MATCH,
                confidence=0.85,
                category=category,
                keywords_found=list(keyword_matches),
                warnings=warnings
            )
        elif len(keyword_matches) == 1:
            # Weak match: single keyword found
            result = ValidationResult.MATCH if category != MatchCategory.UNKNOWN else ValidationResult.UNCERTAIN
            return ValidationReport(
                result=result,
                confidence=0.6,
                category=category,
                keywords_found=list(keyword_matches),
                warnings=warnings
            )
        
        # Tier 3: AI Vision (if enabled and uncertain)
        if self.use_ai and self.ai_client:
            return self._ai_enhance_validation(
                screenshot_path,
                commit_message,
                category,
                all_keywords,
                warnings
            )
        
        # No matches found
        return ValidationReport(
            result=ValidationResult.NO_MATCH,
            confidence=0.3,
            category=MatchCategory.UNKNOWN,
            keywords_found=[],
            warnings=warnings + ["No keyword matches found between commit and screenshot"]
        )
    
    def _validate_file(self, screenshot_path: Path) -> List[str]:
        """Validate screenshot file (format, size, dimensions)."""
        warnings: List[str] = []
        
        try:
            # Check file size
            file_size_mb = screenshot_path.stat().st_size / (1024 * 1024)
            if file_size_mb > self.MAX_FILE_SIZE_MB:
                warnings.append(
                    f"Screenshot is large ({file_size_mb:.1f}MB). "
                    f"Consider optimizing to <{self.MAX_FILE_SIZE_MB}MB for faster uploads."
                )
            
            # Check image format and dimensions
            with Image.open(screenshot_path) as img:
                width, height = img.size
                
                if width < self.MIN_WIDTH or height < self.MIN_HEIGHT:
                    warnings.append(
                        f"Screenshot resolution ({width}x{height}) is below Steam minimum "
                        f"({self.MIN_WIDTH}x{self.MIN_HEIGHT}). Consider using higher resolution."
                    )
                elif width < self.RECOMMENDED_WIDTH or height < self.RECOMMENDED_HEIGHT:
                    warnings.append(
                        f"Screenshot resolution ({width}x{height}) is below recommended "
                        f"({self.RECOMMENDED_WIDTH}x{self.RECOMMENDED_HEIGHT}) for best quality."
                    )
                
                # Check format
                if img.format not in ("PNG", "JPEG", "WEBP"):
                    warnings.append(
                        f"Screenshot format ({img.format}) is not optimal. "
                        f"PNG or JPEG recommended for Steam."
                    )
        
        except Exception as e:
            logger.warning(f"Failed to validate screenshot file: {e}")
            warnings.append(f"Could not validate screenshot: {e}")
        
        return warnings
    
    def _extract_keywords(self, text: str) -> Set[str]:
        """Extract relevant keywords from commit message."""
        # Convert to lowercase and split
        text_lower = text.lower()
        
        # Extract words (alphanumeric with underscores/hyphens)
        words = re.findall(r'\b[\w-]+\b', text_lower)
        
        # Filter out common words
        stopwords = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
        keywords = {word for word in words if word not in stopwords and len(word) > 2}
        
        # Also extract commonly used multi-word phrases
        phrases = re.findall(r'\b(boss fight|main menu|title screen|pause menu|skill tree|inventory system)\b', text_lower)
        keywords.update(phrases)
        
        return keywords
    
    def _extract_filename_keywords(self, screenshot_path: Path) -> Set[str]:
        """Extract keywords from screenshot filename."""
        # Get filename without extension
        filename = screenshot_path.stem.lower()
        
        # Split on common separators
        parts = re.split(r'[_\-\s]+', filename)
        
        # Filter numeric-only parts and short parts
        keywords = {part for part in parts if not part.isdigit() and len(part) > 2}
        
        return keywords
    
    def _extract_filepath_keywords(self, file_paths: List[str]) -> Set[str]:
        """Extract keywords from file paths changed in commit."""
        keywords: Set[str] = set()
        
        for path_str in file_paths:
            path = Path(path_str)
            
            # Extract directory names and filename
            parts = list(path.parts) + [path.stem]
            
            for part in parts:
                part_lower = part.lower()
                # Skip common directory names
                if part_lower not in ("src", "assets", "content", "game"):
                    keywords.add(part_lower)
        
        return keywords
    
    def _classify_keywords(self, keywords: Set[str]) -> MatchCategory:
        """Classify keywords into a category."""
        category_scores: Dict[MatchCategory, int] = {}
        
        for category, category_keywords in self.CATEGORY_KEYWORDS.items():
            score = len(keywords & category_keywords)
            if score > 0:
                category_scores[category] = score
        
        if not category_scores:
            return MatchCategory.UNKNOWN
        
        # Return category with highest score
        return max(category_scores.items(), key=lambda x: x[1])[0]
    
    def _find_keyword_matches(self, keywords: Set[str]) -> Set[str]:
        """Find keywords that match known categories."""
        matches: Set[str] = set()
        
        for category_keywords in self.CATEGORY_KEYWORDS.values():
            matches.update(keywords & category_keywords)
        
        return matches
    
    def _ai_enhance_validation(
        self,
        screenshot_path: Path,
        commit_message: str,
        category: MatchCategory,
        keywords: Set[str],
        warnings: List[str]
    ) -> ValidationReport:
        """
        Use AI vision to enhance validation (Tier 3).
        
        Only called when deterministic matching is uncertain.
        """
        logger.info("Using AI vision to analyze screenshot")
        
        try:
            # TODO: Implement AI vision analysis using Google Gemini Vision
            # This would send the screenshot to the AI and ask it to describe
            # what's shown, then compare with the commit message
            
            # For now, return uncertain result
            logger.warning("AI vision not yet implemented")
            return ValidationReport(
                result=ValidationResult.UNCERTAIN,
                confidence=0.5,
                category=category,
                keywords_found=list(keywords),
                warnings=warnings + ["AI vision analysis not available"],
                ai_analysis="AI vision analysis not yet implemented"
            )
            
        except Exception as e:
            logger.error(f"AI vision analysis failed: {e}")
            return ValidationReport(
                result=ValidationResult.UNCERTAIN,
                confidence=0.4,
                category=category,
                keywords_found=list(keywords),
                warnings=warnings + [f"AI vision failed: {e}"]
            )
