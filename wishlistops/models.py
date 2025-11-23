"""
Data models for WishlistOps configuration and runtime state.

All models use Pydantic for validation and type safety.
See: 04_WishlistOps_System_Architecture_Diagrams.md Section 10
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, field_validator, ConfigDict


class CommitType(str, Enum):
    """Classification of commit types."""
    PLAYER_FACING = "player_facing"
    INTERNAL = "internal"
    BUGFIX = "bugfix"
    FEATURE = "feature"


class WorkflowStatus(str, Enum):
    """Status of workflow execution."""
    SUCCESS = "success"
    SKIPPED = "skipped"
    FAILED = "failed"


class LogoPosition(str, Enum):
    """Valid logo positions on generated banners."""
    TOP_LEFT = "top-left"
    TOP_RIGHT = "top-right"
    CENTER = "center"
    BOTTOM_LEFT = "bottom-left"
    BOTTOM_RIGHT = "bottom-right"


class LogoPosition(str, Enum):
    """Valid logo positions on generated banners."""
    TOP_LEFT = "top-left"
    TOP_RIGHT = "top-right"
    CENTER = "center"
    BOTTOM_LEFT = "bottom-left"
    BOTTOM_RIGHT = "bottom-right"


class SteamConfig(BaseModel):
    """Steam platform configuration."""
    model_config = ConfigDict(extra='forbid')
    
    app_id: str = Field(
        ...,
        description="Steam Application ID (3-7 digits)",
        pattern=r"^\d{3,7}$"
    )
    app_name: str = Field(
        ...,
        description="Game name as displayed on Steam",
        min_length=1,
        max_length=255
    )
    
    @field_validator('app_id')
    @classmethod
    def validate_app_id(cls, v: str) -> str:
        """Validate Steam App ID format and reasonableness."""
        if not v.isdigit():
            raise ValueError(
                f"Steam app_id must be numeric, got: '{v}'\n"
                f"Find your App ID at: https://partner.steamgames.com/"
            )
        if len(v) < 3:
            raise ValueError(
                f"Steam app_id seems too short: '{v}'\n"
                f"Most Steam games have 6-7 digit IDs"
            )
        return v


class BrandingConfig(BaseModel):
    """
    Branding configuration for image generation.
    
    Attributes:
        art_style: Artistic style description (e.g., "pixel art", "hand-drawn")
        color_palette: List of hex color codes for brand consistency
        logo_position: Logo position on generated banners
        logo_size_percent: Logo size as percentage of banner width
        logo_path: Path to game logo file for compositing
        logo_opacity: Logo opacity (0.0 to 1.0)
    """
    model_config = ConfigDict(extra='forbid')
    
    art_style: str = Field(
        ...,
        description="Art style keywords for AI image generation",
        min_length=10,
        max_length=500
    )
    color_palette: list[str] = Field(
        default_factory=list,
        description="Hex color codes for brand consistency"
    )
    logo_position: LogoPosition = Field(
        default=LogoPosition.TOP_RIGHT,
        description="Where to place logo on generated banners"
    )
    logo_size_percent: int = Field(
        default=25,
        ge=10,
        le=50,
        description="Logo size as percentage of banner width"
    )
    logo_path: Optional[str] = Field(
        default="wishlistops/assets/logo.png",
        description="Path to game logo (transparent PNG recommended)"
    )
    logo_opacity: float = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description="Logo opacity"
    )
    
    @field_validator('color_palette')
    @classmethod
    def validate_hex_colors(cls, v: list[str]) -> list[str]:
        """Validate all colors are proper hex codes."""
        if not v:
            return v
        
        for color in v:
            if not color.startswith('#'):
                raise ValueError(
                    f"Color must start with #, got: '{color}'\n"
                    f"Example: #FF6B6B"
                )
            if len(color) != 7:
                raise ValueError(
                    f"Color must be 7 characters (#RRGGBB), got: '{color}'"
                )
            try:
                int(color[1:], 16)
            except ValueError:
                raise ValueError(
                    f"Invalid hex color: '{color}'\n"
                    f"Use format: #RRGGBB (e.g., #FF6B6B)"
                )
        return v


class VoiceConfig(BaseModel):
    """
    Voice and tone configuration for AI-generated content.
    
    Attributes:
        tone: Overall tone of announcements
        personality: Writer persona for AI to adopt
        avoid_phrases: List of phrases to avoid (anti-slop filter)
        max_title_length: Maximum characters in title
        max_body_length: Maximum characters in body
    """
    model_config = ConfigDict(extra='forbid')
    
    tone: str = Field(
        default="casual and excited",
        description="Overall tone of announcements"
    )
    personality: str = Field(
        default="friendly indie developer",
        description="Writer persona for AI to adopt"
    )
    avoid_phrases: list[str] = Field(
        default_factory=lambda: ["monetization", "grind", "lootbox"],
        description="Words/phrases to avoid in announcements"
    )
    max_title_length: int = Field(100, gt=0, le=200, description="Max title length")
    max_body_length: int = Field(3000, gt=0, le=10000, description="Max body length")
    
    @field_validator('avoid_phrases')
    @classmethod
    def lowercase_phrases(cls, v: list[str]) -> list[str]:
        """Convert all avoid phrases to lowercase for matching."""
        return [phrase.lower() for phrase in v]


class AutomationConfig(BaseModel):
    """
    Automation rules and triggers.
    
    Attributes:
        enabled: Master switch for automation
        trigger_on_tags: Trigger on Git tag pushes
        schedule: Cron schedule for automatic runs
        min_days_between_posts: Minimum days between auto-posts
        min_commits_required: Minimum commits to trigger automation
        require_tag: Whether to require Git tag to trigger
        require_manual_approval: Require Discord approval before posting
    """
    model_config = ConfigDict(extra='forbid')
    
    enabled: bool = Field(
        default=True,
        description="Master switch for automation"
    )
    trigger_on_tags: bool = Field(
        default=True,
        description="Trigger on Git tag pushes"
    )
    schedule: Optional[str] = Field(
        default=None,
        description="Cron schedule for automatic runs"
    )
    min_days_between_posts: int = Field(7, ge=1, le=365, description="Min days between posts")
    min_commits_required: int = Field(5, ge=1, description="Min commits to trigger")
    require_tag: bool = Field(True, description="Require Git tag to trigger")
    require_manual_approval: bool = Field(
        default=True,
        description="Require Discord approval before posting"
    )


class AIConfig(BaseModel):
    """
    AI model configuration.
    
    Attributes:
        model_text: Model for text generation (e.g., "gemini-1.5-pro")
        model_image: Model for image generation (e.g., "gemini-2.5-flash-image")
        temperature: Temperature for generation (0.0 to 2.0)
        max_retries: Maximum API retry attempts
        timeout_seconds: API call timeout in seconds
    """
    model_config = ConfigDict(extra='forbid')
    
    model_text: str = Field("gemini-1.5-pro", description="Text generation model")
    model_image: str = Field("gemini-2.5-flash-image", description="Image generation model")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Generation temperature")
    max_retries: int = Field(3, ge=1, le=10, description="Max API retries")
    timeout_seconds: int = Field(30, ge=5, le=120, description="API timeout")


class Config(BaseModel):
    """
    Main configuration model for WishlistOps.
    
    This combines all configuration sections and validates the complete config.
    Secrets (API keys) are loaded from environment variables.
    
    Attributes:
        version: Configuration version
        steam: Steam platform configuration
        branding: Branding configuration
        voice: Voice and tone configuration
        automation: Automation rules
        ai: AI model configuration
        steam_api_key: Steam API key (from environment)
        google_ai_key: Google AI API key (from environment)
        discord_webhook_url: Discord webhook URL (from environment)
    """
    model_config = ConfigDict(
        extra='forbid',
        json_schema_extra={
            "example": {
                "version": "1.0",
                "steam": {
                    "app_id": "480",
                    "app_name": "Spacewar"
                },
                "branding": {
                    "art_style": "retro arcade space shooter",
                    "color_palette": ["#000000", "#FFFFFF"],
                    "logo_position": "top-right"
                }
            }
        }
    )
    
    version: str = Field(default="1.0")
    steam: SteamConfig
    branding: BrandingConfig
    voice: VoiceConfig = Field(default_factory=VoiceConfig)
    automation: AutomationConfig = Field(default_factory=AutomationConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    
    # Runtime secrets (not in config.json, from environment)
    steam_api_key: Optional[str] = Field(default=None, exclude=True)
    google_ai_key: Optional[str] = Field(default=None, exclude=True)
    discord_webhook_url: Optional[str] = Field(default=None, exclude=True)


class Commit(BaseModel):
    """Represents a Git commit used for AI context building."""

    model_config = ConfigDict(extra='forbid')

    sha: str = Field(..., min_length=7, max_length=40, description="Commit SHA")
    message: str = Field(..., min_length=1, description="Commit message")
    author: str = Field(..., min_length=1, description="Commit author")
    timestamp: datetime = Field(..., description="Commit timestamp")
    commit_type: CommitType = Field(CommitType.INTERNAL, description="Commit classification")
    files_changed: list[str] = Field(default_factory=list, description="Files touched by the commit")
    screenshot_path: Optional[str] = Field(
        default=None,
        description="Path to a deterministic screenshot artifact discovered in the commit",
    )


class AnnouncementDraft(BaseModel):
    """
    Draft announcement generated by AI.
    
    Attributes:
        title: Announcement title
        body: Announcement body text
        banner_url: Optional URL to banner image
        created_at: When draft was created
        approved: Whether draft has been approved
        approved_at: When draft was approved (if applicable)
    """
    model_config = ConfigDict(extra='allow')
    
    title: str = Field(..., min_length=1, max_length=200, description="Announcement title")
    body: str = Field(..., min_length=10, max_length=10000, description="Announcement body")
    banner_url: Optional[str] = Field(None, description="Banner image URL or local path")
    banner_path: Optional[str] = Field(None, description="Local filesystem path to banner for uploads")
    created_at: str = Field(..., description="Creation timestamp (ISO format)")
    approved: bool = Field(False, description="Approval status")
    approved_at: Optional[str] = Field(None, description="Approval timestamp")


class WorkflowState(BaseModel):
    """
    State of a workflow execution.
    
    Attributes:
        status: Execution status
        reason: Optional reason for status (e.g., why skipped)
        draft: Generated announcement draft (if any)
        error: Error message (if failed)
        started_at: When workflow started
        completed_at: When workflow completed
    """
    model_config = ConfigDict(extra='allow')
    
    status: WorkflowStatus = Field(..., description="Workflow status")
    reason: Optional[str] = Field(None, description="Status reason")
    draft: Optional[AnnouncementDraft] = Field(None, description="Generated draft")
    error: Optional[str] = Field(None, description="Error message")
    started_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = Field(None, description="Completion timestamp")


class StateData(BaseModel):
    """
    Persisted state data for tracking workflow history.
    
    Attributes:
        last_tag: Last processed Git tag
        last_post_date: Date of last successful post
        last_run_status: Status of last run
        total_runs: Total number of runs
        total_posts: Total number of successful posts
        last_run_timestamp: Timestamp of last run
        successful_runs: Count of successful runs
        failed_runs: Count of failed runs
    """
    model_config = ConfigDict(extra='allow')
    
    last_tag: Optional[str] = Field(None, description="Last processed Git tag")
    last_post_date: Optional[str] = Field(None, description="Last post date (ISO format)")
    last_run_status: Optional[WorkflowStatus] = Field(None, description="Last run status")
    total_runs: int = Field(0, ge=0, description="Total runs")
    total_posts: int = Field(0, ge=0, description="Total successful posts")
    last_run_timestamp: Optional[str] = Field(None, description="Last run timestamp")
    successful_runs: int = Field(0, ge=0, description="Successful runs count")
    failed_runs: int = Field(0, ge=0, description="Failed runs count")


# Alias for compatibility with build plan naming
StateSnapshot = StateData
