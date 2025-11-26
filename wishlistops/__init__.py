"""
WishlistOps - Automated Steam marketing for indie game developers.

This package provides automation for generating Steam announcements from Git commits,
using AI for content generation and human approval via Discord.

Main components:
- main.py: Orchestrator coordinating the workflow
- config_manager.py: Configuration loading and validation
- git_parser.py: Git commit parsing and classification
- ai_client.py: Google Gemini API wrapper
- content_filter.py: Anti-slop quality filtering
- image_compositor.py: Banner image composition
- image_processor.py: Advanced image cropping and upscaling
- discord_notifier.py: Discord webhook notifications
- state_manager.py: State persistence
- models.py: Pydantic data models
- cli_v2.py: Enhanced interactive CLI
- template_banner.py: Template-based banner generation

Architecture: See 04_WishlistOps_System_Architecture_Diagrams.md
"""

__version__ = "0.2.0"
__author__ = "WishlistOps Team"

# Convenience imports
from .image_processor import ImageProcessor, QualityPreset, CropMode, process_screenshot
from .template_banner import TemplateBannerGenerator, BannerStyle, generate_template_banner

__all__ = [
    "ImageProcessor",
    "QualityPreset", 
    "CropMode",
    "process_screenshot",
    "TemplateBannerGenerator",
    "BannerStyle",
    "generate_template_banner",
]
