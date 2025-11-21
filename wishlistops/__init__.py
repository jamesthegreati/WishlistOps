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
- discord_notifier.py: Discord webhook notifications
- state_manager.py: State persistence
- models.py: Pydantic data models

Architecture: See 04_WishlistOps_System_Architecture_Diagrams.md
"""

__version__ = "0.1.0"
__author__ = "WishlistOps Team"
