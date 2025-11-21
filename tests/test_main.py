"""
Tests for WishlistOps main orchestrator.
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from wishlistops.main import WishlistOpsOrchestrator, WorkflowError
from wishlistops.models import (
    Config,
    SteamConfig,
    VoiceConfig,
    AutomationConfig,
    AIConfig,
    BrandingConfig,
    WorkflowStatus,
    AnnouncementDraft,
    Commit,
    CommitType
)


@pytest.fixture
def mock_config(tmp_path: Path) -> Config:
    """Create a mock configuration for testing."""
    return Config(
        version="1.0",
        steam=SteamConfig(
            app_id="123456",
            app_name="Test Game"
        ),
        branding=BrandingConfig(
            art_style="pixel art fantasy with vibrant colors",
            color_palette=["#FF6B6B", "#4ECDC4"],
            logo_position="top-right"
        ),
        google_ai_key="test_key_1234567890",
        discord_webhook_url="https://discord.com/api/webhooks/123/abc",
        voice=VoiceConfig(
            personality="friendly",
            avoid_phrases=["delve", "leverage"],
            tone="casual"
        ),
        automation=AutomationConfig(
            min_days_between_posts=7,
            min_commits_required=5,
            require_tag=True
        ),
        ai=AIConfig(
            model_text="gemini-1.5-pro",
            model_image="gemini-2.5-flash-image"
        )
    )


@pytest.fixture
def mock_config_file(tmp_path: Path, mock_config: Config) -> Path:
    """Create a mock config file."""
    import json
    
    config_path = tmp_path / "config.json"
    with open(config_path, 'w') as f:
        json.dump(mock_config.model_dump(), f)
    
    return config_path


def test_orchestrator_initializes(mock_config_file: Path) -> None:
    """Test orchestrator can be created."""
    orch = WishlistOpsOrchestrator(mock_config_file, dry_run=True)
    assert orch.config is not None
    assert orch.dry_run is True


def test_orchestrator_requires_valid_config(tmp_path: Path) -> None:
    """Test orchestrator fails with invalid config."""
    invalid_config = tmp_path / "invalid.json"
    invalid_config.write_text("{}")
    
    with pytest.raises(Exception):  # Should raise ValidationError
        WishlistOpsOrchestrator(invalid_config)


def test_orchestrator_requires_existing_config() -> None:
    """Test orchestrator fails with missing config."""
    with pytest.raises(FileNotFoundError):
        WishlistOpsOrchestrator(Path("/nonexistent/config.json"))


@pytest.mark.asyncio
async def test_workflow_skips_on_no_commits(mock_config_file: Path) -> None:
    """Test workflow skips when no commits."""
    orch = WishlistOpsOrchestrator(mock_config_file, dry_run=True)
    
    # Mock git parser to return empty list
    with patch.object(orch.git, 'get_commits_since', return_value=[]):
        result = await orch.run()
        
        assert result.status == WorkflowStatus.SKIPPED
        assert result.reason == "no_commits"


@pytest.mark.asyncio
async def test_workflow_skips_on_rate_limit(mock_config_file: Path) -> None:
    """Test workflow skips when rate limited."""
    from datetime import datetime
    
    orch = WishlistOpsOrchestrator(mock_config_file, dry_run=True)
    
    # Mock state to show recent post
    with patch.object(
        orch.state, 
        'get_last_post_date', 
        return_value=datetime.now().isoformat()
    ):
        result = await orch.run()
        
        assert result.status == WorkflowStatus.SKIPPED
        assert result.reason == "rate_limit"


@pytest.mark.asyncio
async def test_workflow_success_flow(mock_config_file: Path) -> None:
    """Test successful workflow execution."""
    orch = WishlistOpsOrchestrator(mock_config_file, dry_run=True)
    
    # Create mock commits
    mock_commits = [
        Commit(
            sha="abc123",
            message="Add new feature",
            author="Test User",
            timestamp=pytest.importorskip("datetime").datetime.now(),
            commit_type=CommitType.FEATURE
        )
        for _ in range(5)
    ]
    
    # Mock all the components
    with patch.object(orch.state, 'get_last_post_date', return_value=None), \
         patch.object(orch.git, 'get_commits_since', return_value=mock_commits), \
         patch.object(orch.git, 'is_player_facing', return_value=True), \
         patch.object(
             orch.ai, 
             'generate_text', 
             new_callable=AsyncMock,
             return_value={'title': 'Test Title', 'body': 'Test body content'}
         ), \
         patch.object(orch.filter, 'check', return_value=[]), \
         patch.object(
             orch.notifier, 
             'send_approval_request', 
             new_callable=AsyncMock
         ), \
         patch.object(orch.state, 'update_last_run'):
        
        result = await orch.run()
        
        assert result.status == WorkflowStatus.SUCCESS
        assert result.draft is not None
        assert result.draft.title == 'Test Title'


@pytest.mark.asyncio
async def test_workflow_handles_ai_failure(mock_config_file: Path) -> None:
    """Test workflow handles AI generation failure."""
    orch = WishlistOpsOrchestrator(mock_config_file, dry_run=True)
    
    mock_commits = [
        Commit(
            sha="abc123",
            message="Test",
            author="Test",
            timestamp=pytest.importorskip("datetime").datetime.now(),
            commit_type=CommitType.FEATURE
        )
    ] * 5
    
    # Mock AI to raise an exception
    with patch.object(orch.state, 'get_last_post_date', return_value=None), \
         patch.object(orch.git, 'get_commits_since', return_value=mock_commits), \
         patch.object(orch.git, 'is_player_facing', return_value=True), \
         patch.object(
             orch.ai, 
             'generate_text', 
             new_callable=AsyncMock,
             side_effect=Exception("AI API error")
         ), \
         patch.object(
             orch.notifier,
             'send_error',
             new_callable=AsyncMock
         ):
        
        with pytest.raises(WorkflowError):
            await orch.run()


@pytest.mark.asyncio
async def test_workflow_regenerates_on_filter_issues(mock_config_file: Path) -> None:
    """Test workflow regenerates content when filter finds issues."""
    orch = WishlistOpsOrchestrator(mock_config_file, dry_run=True)
    
    mock_commits = [
        Commit(
            sha="abc123",
            message="Test",
            author="Test",
            timestamp=pytest.importorskip("datetime").datetime.now(),
            commit_type=CommitType.FEATURE
        )
    ] * 5
    
    # First call returns content with issues, second call returns clean content
    generate_calls = 0
    async def mock_generate(*args, **kwargs):
        nonlocal generate_calls
        generate_calls += 1
        if generate_calls == 1:
            return {'title': 'First attempt', 'body': 'Let us delve into this'}
        else:
            return {'title': 'Second attempt', 'body': 'Clean content here'}
    
    with patch.object(orch.state, 'get_last_post_date', return_value=None), \
         patch.object(orch.git, 'get_commits_since', return_value=mock_commits), \
         patch.object(orch.git, 'is_player_facing', return_value=True), \
         patch.object(
             orch.ai,
             'generate_text',
             new_callable=AsyncMock,
             side_effect=mock_generate
         ), \
         patch.object(
             orch.notifier,
             'send_approval_request',
             new_callable=AsyncMock
         ), \
         patch.object(orch.state, 'update_last_run'):
        
        # Filter will find "delve" in first attempt
        result = await orch.run()
        
        # Should have regenerated
        assert generate_calls == 2
        assert result.status == WorkflowStatus.SUCCESS


def test_build_ai_context(mock_config_file: Path) -> None:
    """Test AI context building."""
    orch = WishlistOpsOrchestrator(mock_config_file, dry_run=True)
    
    mock_commits = [
        Commit(
            sha="abc123",
            message="Add feature X",
            author="Dev User",
            timestamp=pytest.importorskip("datetime").datetime.now(),
            commit_type=CommitType.FEATURE
        )
    ]
    
    context = orch._build_ai_context(mock_commits)
    
    assert "Test Game" in context
    assert "Add feature X" in context
    assert "friendly" in context.lower() or "casual" in context.lower()


def test_build_image_prompt(mock_config_file: Path) -> None:
    """Test image prompt building."""
    orch = WishlistOpsOrchestrator(mock_config_file, dry_run=True)
    
    draft = AnnouncementDraft(
        title="New Update!",
        body="Great new features",
        created_at="2025-11-20T10:00:00"
    )
    
    prompt = orch._build_image_prompt(draft)
    
    assert "New Update!" in prompt
    assert "16:9" in prompt


def test_should_run_with_no_previous_posts(mock_config_file: Path) -> None:
    """Test should_run returns True with no previous posts."""
    orch = WishlistOpsOrchestrator(mock_config_file, dry_run=True)
    
    with patch.object(orch.state, 'get_last_post_date', return_value=None):
        assert orch._should_run() is True


def test_should_run_with_old_post(mock_config_file: Path) -> None:
    """Test should_run returns True when enough time has passed."""
    from datetime import datetime, timedelta
    
    orch = WishlistOpsOrchestrator(mock_config_file, dry_run=True)
    
    old_date = (datetime.now() - timedelta(days=10)).isoformat()
    
    with patch.object(orch.state, 'get_last_post_date', return_value=old_date):
        assert orch._should_run() is True


def test_should_run_with_recent_post(mock_config_file: Path) -> None:
    """Test should_run returns False when post is too recent."""
    from datetime import datetime, timedelta
    
    orch = WishlistOpsOrchestrator(mock_config_file, dry_run=True)
    
    recent_date = (datetime.now() - timedelta(days=1)).isoformat()
    
    with patch.object(orch.state, 'get_last_post_date', return_value=recent_date):
        assert orch._should_run() is False
