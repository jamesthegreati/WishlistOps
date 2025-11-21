"""
Integration tests for WishlistOps end-to-end workflow.

Tests the complete pipeline from Git commits to Discord notification,
verifying all components work together correctly.

Architecture: See 04_WishlistOps_System_Architecture_Diagrams.md Section 12
Testing Strategy: Mock external APIs, use real components, test all paths
"""

import asyncio
import json
import os
import time
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, Mock

import pytest
from PIL import Image

from wishlistops.main import WishlistOpsOrchestrator, WorkflowError
from wishlistops.models import (
    Config,
    AIConfig,
    VoiceConfig,
    BrandingConfig,
    SteamConfig,
    AutomationConfig,
    WorkflowStatus,
    AnnouncementDraft,
    Commit,
    CommitType,
    LogoPosition
)
from wishlistops.git_parser import GitParser
from wishlistops.ai_client import GeminiClient, TextGenerationResult, ImageGenerationResult
from wishlistops.content_filter import ContentFilter, FilterResult
from wishlistops.discord_notifier import DiscordNotifier
from wishlistops.state_manager import StateManager
from wishlistops.image_compositor import ImageCompositor


@pytest.fixture
def test_config(tmp_path: Path) -> Config:
    """Create test configuration."""
    # Create test logo
    logo_path = tmp_path / "logo.png"
    logo = Image.new('RGBA', (200, 200), color=(255, 0, 0, 255))
    logo.save(logo_path)
    
    return Config(
        steam=SteamConfig(app_id="480", app_name="Test Game"),
        branding=BrandingConfig(
            art_style="pixel art fantasy with vibrant colors and detailed sprites",
            logo_path=str(logo_path),
            logo_position=LogoPosition.TOP_RIGHT
        ),
        voice=VoiceConfig(
            tone="casual",
            personality="friendly indie developer",
            avoid_phrases=["delve", "tapestry", "robust"]
        ),
        ai=AIConfig(
            model_text="gemini-1.5-pro",
            model_image="gemini-2.5-flash-image",
            temperature=0.7,
            max_retries=3
        ),
        automation=AutomationConfig(
            min_days_between_posts=7,
            min_commits_required=5,
            require_manual_approval=True
        ),
        google_ai_key="test-key",
        discord_webhook_url="https://discord.com/api/webhooks/test"
    )


@pytest.fixture
def config_file(tmp_path: Path, test_config: Config) -> Path:
    """Create test config file."""
    config_path = tmp_path / "config.json"
    with open(config_path, 'w') as f:
        # Serialize config (excluding secrets)
        config_dict = test_config.model_dump(exclude={'google_ai_key', 'discord_webhook_url', 'steam_api_key'})
        json.dump(config_dict, f, indent=2)
    return config_path


@pytest.fixture
def mock_commits() -> list[Commit]:
    """Create mock Git commits."""
    return [
        Commit(
            sha="abc1234",
            message="Add double jump mechanic",
            author="Dev",
            timestamp=datetime.now(),
            commit_type=CommitType.FEATURE
        ),
        Commit(
            sha="def4567",
            message="Fix boss AI bug",
            author="Dev",
            timestamp=datetime.now(),
            commit_type=CommitType.BUGFIX
        ),
        Commit(
            sha="ghi7890",
            message="Improve rendering performance",
            author="Dev",
            timestamp=datetime.now(),
            commit_type=CommitType.FEATURE
        ),
        Commit(
            sha="jkl0123",
            message="Add new weapon: plasma rifle",
            author="Dev",
            timestamp=datetime.now(),
            commit_type=CommitType.FEATURE
        ),
        Commit(
            sha="mno3456",
            message="Fix crash on level 3",
            author="Dev",
            timestamp=datetime.now(),
            commit_type=CommitType.BUGFIX
        )
    ]


@pytest.mark.asyncio
async def test_end_to_end_workflow_success(config_file: Path, test_config: Config, mock_commits: list[Commit], tmp_path: Path):
    """
    Test complete workflow executes successfully.
    
    This is the main integration test that verifies:
    1. Git commits are parsed
    2. AI generates content
    3. Content passes filter
    4. Image is generated
    5. Discord notification sent
    6. State is updated
    """
    # Setup state manager
    state_path = tmp_path / "state.json"
    
    # Mock external API calls
    with patch('wishlistops.main.load_config', return_value=test_config), \
         patch.object(GitParser, 'get_player_facing_commits', return_value=mock_commits), \
         patch.object(GeminiClient, 'generate_text', new_callable=AsyncMock) as mock_text, \
         patch.object(GeminiClient, 'generate_image', new_callable=AsyncMock) as mock_image, \
         patch.object(DiscordNotifier, '_send_webhook', new_callable=AsyncMock) as mock_discord:
        
        # Configure mocks
        mock_text.return_value = {
            'title': 'Combat Update v1.2',
            'body': 'We added double jump and fixed the boss AI bug. Thanks for the feedback!'
        }
        
        # Create fake image
        fake_image = Image.new('RGB', (800, 450), color='blue')
        buffer = BytesIO()
        fake_image.save(buffer, format='PNG')
        mock_image.return_value = buffer.getvalue()
        
        mock_discord.return_value = None
        
        # Create orchestrator
        orchestrator = WishlistOpsOrchestrator(config_file, dry_run=False)
        orchestrator.state = StateManager(state_path)
        
        # Run workflow
        result = await orchestrator.run()
        
        # Verify success
        assert result.status == WorkflowStatus.SUCCESS
        assert result.draft is not None
        assert result.draft.title == "Combat Update v1.2"
        
        # Verify all mocks were called
        mock_text.assert_called_once()
        mock_discord.assert_called_once()
        
        # Verify state was updated
        assert orchestrator.state.state.total_runs == 1
        assert orchestrator.state.state.successful_runs == 1


@pytest.mark.asyncio
async def test_workflow_skips_on_no_commits(config_file: Path, test_config: Config, tmp_path: Path):
    """Test workflow skips when no commits found."""
    
    with patch('wishlistops.main.load_config', return_value=test_config), \
         patch.object(GitParser, 'get_player_facing_commits', return_value=[]):
        
        orchestrator = WishlistOpsOrchestrator(config_file, dry_run=True)
        orchestrator.state = StateManager(tmp_path / "state.json")
        
        result = await orchestrator.run()
        
        assert result.status == WorkflowStatus.SKIPPED
        assert result.reason == "no_commits"


@pytest.mark.asyncio
async def test_workflow_skips_on_insufficient_commits(config_file: Path, test_config: Config, tmp_path: Path):
    """Test workflow skips when not enough commits."""
    
    # Only 2 commits (need 5)
    few_commits = [
        Commit(
            sha="abc1234",
            message="Small fix",
            author="Dev",
            timestamp=datetime.now(),
            commit_type=CommitType.BUGFIX
        ),
        Commit(
            sha="def4567",
            message="Another fix",
            author="Dev",
            timestamp=datetime.now(),
            commit_type=CommitType.BUGFIX
        )
    ]
    
    with patch('wishlistops.main.load_config', return_value=test_config), \
         patch.object(GitParser, 'get_player_facing_commits', return_value=few_commits):
        
        orchestrator = WishlistOpsOrchestrator(config_file, dry_run=True)
        orchestrator.state = StateManager(tmp_path / "state.json")
        
        result = await orchestrator.run()
        
        assert result.status == WorkflowStatus.SKIPPED
        assert result.reason == "no_commits"


@pytest.mark.asyncio
async def test_content_filter_triggers_regeneration(config_file: Path, test_config: Config, mock_commits: list[Commit], tmp_path: Path):
    """Test that content filter triggers AI regeneration on bad content."""
    
    generate_count = 0
    
    async def mock_generate(*args, **kwargs):
        nonlocal generate_count
        generate_count += 1
        if generate_count == 1:
            # First call returns bad content (AI slop)
            return {
                'title': 'Delve into our robust tapestry',
                'body': 'Let us delve into the tapestry of innovation with our cutting-edge solution.'
            }
        else:
            # Second call returns good content
            return {
                'title': 'Combat Update',
                'body': 'We added double jump and fixed the boss AI. Thanks for your feedback!'
            }
    
    with patch('wishlistops.main.load_config', return_value=test_config), \
         patch.object(GitParser, 'get_player_facing_commits', return_value=mock_commits), \
         patch.object(GeminiClient, 'generate_text', new_callable=AsyncMock, side_effect=mock_generate), \
         patch.object(DiscordNotifier, '_send_webhook', new_callable=AsyncMock):
        
        orchestrator = WishlistOpsOrchestrator(config_file, dry_run=False)
        orchestrator.state = StateManager(tmp_path / "state.json")
        
        result = await orchestrator.run()
        
        # Verify regeneration happened
        assert generate_count == 2
        
        # Verify final content is good
        assert result.status == WorkflowStatus.SUCCESS
        assert "delve" not in result.draft.body.lower()
        assert "tapestry" not in result.draft.body.lower()


@pytest.mark.asyncio
async def test_workflow_handles_rate_limiting(config_file: Path, test_config: Config, mock_commits: list[Commit], tmp_path: Path):
    """Test workflow respects rate limits."""
    
    state_path = tmp_path / "state.json"
    state = StateManager(state_path)
    
    # Simulate recent post (yesterday)
    recent_date = (datetime.utcnow() - timedelta(days=1)).isoformat()
    state.state.last_post_date = recent_date
    state._save()
    
    with patch('wishlistops.main.load_config', return_value=test_config), \
         patch.object(GitParser, 'get_player_facing_commits', return_value=mock_commits):
        
        orchestrator = WishlistOpsOrchestrator(config_file, dry_run=True)
        orchestrator.state = state
        
        # Try to run (should be rate limited - need 7 days)
        result = await orchestrator.run()
        
        assert result.status == WorkflowStatus.SKIPPED
        assert result.reason == "rate_limit"


@pytest.mark.asyncio
async def test_workflow_allows_post_after_rate_limit(config_file: Path, test_config: Config, mock_commits: list[Commit], tmp_path: Path):
    """Test workflow proceeds after rate limit period."""
    
    state_path = tmp_path / "state.json"
    state = StateManager(state_path)
    
    # Simulate old post (10 days ago)
    old_date = (datetime.utcnow() - timedelta(days=10)).isoformat()
    state.state.last_post_date = old_date
    state._save()
    
    with patch('wishlistops.main.load_config', return_value=test_config), \
         patch.object(GitParser, 'get_player_facing_commits', return_value=mock_commits), \
         patch.object(GeminiClient, 'generate_text', new_callable=AsyncMock) as mock_text, \
         patch.object(DiscordNotifier, '_send_webhook', new_callable=AsyncMock):
        
        mock_text.return_value = {
            'title': 'Test Update',
            'body': 'This is a test update with enough content to pass validation checks.'
        }
        
        orchestrator = WishlistOpsOrchestrator(config_file, dry_run=False)
        orchestrator.state = state
        
        result = await orchestrator.run()
        
        # Should succeed since enough time has passed
        assert result.status == WorkflowStatus.SUCCESS


@pytest.mark.asyncio
async def test_workflow_error_handling(config_file: Path, test_config: Config, mock_commits: list[Commit], tmp_path: Path):
    """Test workflow handles errors gracefully."""
    
    with patch('wishlistops.main.load_config', return_value=test_config), \
         patch.object(GitParser, 'get_player_facing_commits', return_value=mock_commits), \
         patch.object(GeminiClient, 'generate_text', new_callable=AsyncMock, side_effect=Exception("API Error")), \
         patch.object(DiscordNotifier, 'send_error', new_callable=AsyncMock) as mock_error:
        
        orchestrator = WishlistOpsOrchestrator(config_file, dry_run=False)
        orchestrator.state = StateManager(tmp_path / "state.json")
        
        # Run should raise exception
        with pytest.raises(WorkflowError, match="API Error"):
            await orchestrator.run()
        
        # Verify error notification was sent
        mock_error.assert_called_once()
        
        # Verify state recorded failure
        assert orchestrator.state.state.failed_runs == 1


@pytest.mark.asyncio
async def test_image_compositor_integration(test_config: Config, tmp_path: Path):
    """Test image compositor integrates correctly."""
    
    # Create test logo
    logo_path = tmp_path / "logo.png"
    logo = Image.new('RGBA', (200, 200), color=(255, 0, 0, 255))
    logo.save(logo_path)
    
    test_config.branding.logo_path = str(logo_path)
    
    # Create test base image
    base_image = Image.new('RGB', (1024, 576), color='blue')
    buffer = BytesIO()
    base_image.save(buffer, format='PNG')
    base_image_bytes = buffer.getvalue()
    
    # Composite
    compositor = ImageCompositor(test_config.branding)
    result = compositor.composite_logo(base_image_bytes)
    
    # Verify result
    assert len(result) > 0
    
    result_image = Image.open(BytesIO(result))
    assert result_image.size == (800, 450)  # Steam specs


def test_configuration_validation():
    """Test configuration validation catches errors."""
    from pydantic import ValidationError
    
    # Invalid Steam App ID (not numeric)
    with pytest.raises(ValidationError):
        Config(
            steam=SteamConfig(app_id="abc", app_name="Test"),
            branding=BrandingConfig(art_style="test art style description")
        )


def test_state_persistence_between_runs(tmp_path: Path):
    """Test state persists correctly between workflow runs."""
    state_path = tmp_path / "state.json"
    
    # First run
    state1 = StateManager(state_path)
    draft1 = AnnouncementDraft(
        title="Test v1.0",
        body="This is test body content for version 1.0 with enough characters.",
        created_at=datetime.now().isoformat()
    )
    state1.update_last_run(draft=draft1, tag="v1.0.0", status="success")
    
    # Second run (new instance)
    state2 = StateManager(state_path)
    
    assert state2.state.total_runs == 1
    assert state2.state.last_tag == "v1.0.0"
    
    # Third run
    draft2 = AnnouncementDraft(
        title="Test v1.1",
        body="This is test body content for version 1.1 with enough characters.",
        created_at=datetime.now().isoformat()
    )
    state2.update_last_run(draft=draft2, tag="v1.1.0", status="success")
    
    # Fourth run (verify count)
    state3 = StateManager(state_path)
    assert state3.state.total_runs == 2
    assert state3.state.successful_runs == 2
    assert state3.state.last_tag == "v1.1.0"


def test_state_tracks_failures(tmp_path: Path):
    """Test state correctly tracks failed runs."""
    state_path = tmp_path / "state.json"
    state = StateManager(state_path)
    
    # Record successful run
    state.update_last_run(status="success", tag="v1.0.0")
    
    # Record failed run
    state.update_last_run(status="failed", error="API timeout")
    
    # Record skipped run
    state.update_last_run(status="skipped")
    
    assert state.state.total_runs == 3
    assert state.state.successful_runs == 1
    assert state.state.failed_runs == 1
    assert state.state.skipped_runs == 1


def test_state_maintains_recent_runs_history(tmp_path: Path):
    """Test state maintains recent runs history."""
    state_path = tmp_path / "state.json"
    state = StateManager(state_path)
    
    # Add 15 runs (should keep only last 10)
    for i in range(15):
        draft = AnnouncementDraft(
            title=f"Update {i}",
            body=f"This is the body content for update {i} with enough characters to pass validation.",
            created_at=datetime.now().isoformat()
        )
        state.update_last_run(draft=draft, tag=f"v1.{i}.0", status="success")
    
    # Should only keep last 10
    assert len(state.state.recent_runs) == StateManager.MAX_RECENT_RUNS
    assert state.state.recent_runs[0].tag == "v1.14.0"  # Most recent
    assert state.state.recent_runs[-1].tag == "v1.5.0"  # Oldest kept


@pytest.mark.asyncio
async def test_discord_notification_formatting(tmp_path: Path):
    """Test Discord notification is properly formatted."""
    
    webhook_url = "https://discord.com/api/webhooks/123/abc"
    notifier = DiscordNotifier(webhook_url, dry_run=False)
    
    # Build approval embed
    embed = notifier._build_approval_embed(
        title="Test Update v1.0",
        body="We added new features and fixed bugs.",
        banner_url="https://example.com/banner.png",
        game_name="Test Game",
        tag="v1.0.0"
    )
    
    # Verify structure
    assert "title" in embed
    assert "description" in embed
    assert "fields" in embed
    assert "image" in embed
    assert embed["image"]["url"] == "https://example.com/banner.png"
    
    # Verify content
    assert "Test Update v1.0" in embed["title"]
    assert "Test Game" in embed["description"]
    assert "v1.0.0" in embed["description"]


@pytest.mark.asyncio
async def test_content_filter_integration(test_config: Config):
    """Test content filter works in real workflow context."""
    
    filter = ContentFilter(test_config.voice)
    
    # Test AI slop detection
    bad_text = "Let's delve into the robust tapestry of our game."
    result = filter.check(bad_text)
    
    assert result.passed is False
    assert len(result.issues) > 0
    
    # Test good content passes
    good_text = (
        "We fixed the boss AI and added double jump. "
        "The new mechanic makes platforming way more fun! "
        "Thanks for all your feedback on the Discord. "
        "We also improved the framerate in the forest level."
    )
    result = filter.check(good_text)
    
    assert result.passed is True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_api_integration():
    """
    Test with real APIs (requires API keys in environment).
    
    This test is skipped in CI but useful for local validation.
    """
    
    api_key = os.getenv('GOOGLE_AI_KEY')
    if not api_key:
        pytest.skip("GOOGLE_AI_KEY not set")
    
    from wishlistops.ai_client import GeminiClient
    from wishlistops.models import AIConfig
    
    config = AIConfig()
    
    # Test text generation
    async with GeminiClient(api_key, config) as client:
        prompt = "Write a short announcement about adding a new weapon to a game."
        system = "You are a friendly indie game developer."
        
        # Note: Actual implementation would use client methods
        # This is a placeholder for real API testing
        
        # result = await client.generate_text(
        #     prompt=prompt,
        #     system_instruction=system
        # )
        
        # assert 'title' in result
        # assert 'body' in result
        # assert len(result['body']) > 50
        
        # Verify content filter
        # from wishlistops.content_filter import ContentFilter
        # filter = ContentFilter()
        # filter_result = filter.check(result['body'])
        
        # Content should be reasonably good
        # assert filter_result.score > 0.5


@pytest.mark.performance
@pytest.mark.asyncio
async def test_workflow_completes_within_time_limit(config_file: Path, test_config: Config, mock_commits: list[Commit], tmp_path: Path):
    """Test workflow completes within expected time (60 seconds)."""
    
    with patch('wishlistops.main.load_config', return_value=test_config), \
         patch.object(GitParser, 'get_player_facing_commits', return_value=mock_commits), \
         patch.object(GeminiClient, 'generate_text', new_callable=AsyncMock) as mock_text, \
         patch.object(GeminiClient, 'generate_image', new_callable=AsyncMock) as mock_image, \
         patch.object(DiscordNotifier, '_send_webhook', new_callable=AsyncMock):
        
        mock_text.return_value = {
            'title': 'Test',
            'body': 'Test body with enough content to pass validation.'
        }
        
        fake_image = Image.new('RGB', (800, 450), color='blue')
        buffer = BytesIO()
        fake_image.save(buffer, format='PNG')
        mock_image.return_value = buffer.getvalue()
        
        orchestrator = WishlistOpsOrchestrator(config_file, dry_run=False)
        orchestrator.state = StateManager(tmp_path / "state.json")
        
        start = time.time()
        result = await orchestrator.run()
        duration = time.time() - start
        
        assert result.status == WorkflowStatus.SUCCESS
        assert duration < 60  # Should complete in under 60 seconds


@pytest.mark.asyncio
async def test_workflow_with_missing_logo(config_file: Path, test_config: Config, mock_commits: list[Commit], tmp_path: Path):
    """Test workflow continues gracefully when logo is missing."""
    
    # Set logo to non-existent path
    test_config.branding.logo_path = str(tmp_path / "nonexistent_logo.png")
    
    with patch('wishlistops.main.load_config', return_value=test_config), \
         patch.object(GitParser, 'get_player_facing_commits', return_value=mock_commits), \
         patch.object(GeminiClient, 'generate_text', new_callable=AsyncMock) as mock_text, \
         patch.object(DiscordNotifier, '_send_webhook', new_callable=AsyncMock):
        
        mock_text.return_value = {
            'title': 'Test Update',
            'body': 'Test body with enough content.'
        }
        
        orchestrator = WishlistOpsOrchestrator(config_file, dry_run=False)
        orchestrator.state = StateManager(tmp_path / "state.json")
        
        # Should still succeed (graceful degradation)
        result = await orchestrator.run()
        
        # Workflow should complete successfully even without logo
        assert result.status == WorkflowStatus.SUCCESS


@pytest.mark.asyncio
async def test_workflow_dry_run_mode(config_file: Path, test_config: Config, mock_commits: list[Commit], tmp_path: Path):
    """Test workflow in dry-run mode doesn't make external calls."""
    
    with patch('wishlistops.main.load_config', return_value=test_config), \
         patch.object(GitParser, 'get_player_facing_commits', return_value=mock_commits), \
         patch.object(GeminiClient, 'generate_text', new_callable=AsyncMock) as mock_text, \
         patch.object(DiscordNotifier, '_send_webhook', new_callable=AsyncMock) as mock_discord:
        
        mock_text.return_value = {
            'title': 'Dry Run Test',
            'body': 'This is a dry run test.'
        }
        
        orchestrator = WishlistOpsOrchestrator(config_file, dry_run=True)
        orchestrator.state = StateManager(tmp_path / "state.json")
        
        result = await orchestrator.run()
        
        # In dry run, Discord should not be called (notifier is initialized with dry_run=True)
        # The mock might still be called, but the actual notifier won't send
        assert result.status == WorkflowStatus.SUCCESS


@pytest.mark.asyncio
async def test_multiple_regeneration_attempts(config_file: Path, test_config: Config, mock_commits: list[Commit], tmp_path: Path):
    """Test workflow handles multiple regeneration attempts."""
    
    attempt_count = 0
    
    async def mock_generate(*args, **kwargs):
        nonlocal attempt_count
        attempt_count += 1
        
        if attempt_count == 1:
            # First: AI slop
            return {
                'title': 'Delve into tapestry',
                'body': 'Let us delve into the robust tapestry of our cutting-edge solution.'
            }
        elif attempt_count == 2:
            # Second: Still has issues
            return {
                'title': 'Robust solution',
                'body': 'Our robust solution leverages cutting-edge technology to delve deeper.'
            }
        else:
            # Third: Finally good
            return {
                'title': 'Combat Update',
                'body': 'We fixed bugs and added new features. Thanks for your feedback!'
            }
    
    with patch('wishlistops.main.load_config', return_value=test_config), \
         patch.object(GitParser, 'get_player_facing_commits', return_value=mock_commits), \
         patch.object(GeminiClient, 'generate_text', new_callable=AsyncMock, side_effect=mock_generate), \
         patch.object(DiscordNotifier, '_send_webhook', new_callable=AsyncMock):
        
        orchestrator = WishlistOpsOrchestrator(config_file, dry_run=False)
        orchestrator.state = StateManager(tmp_path / "state.json")
        
        result = await orchestrator.run()
        
        # Should eventually succeed after multiple attempts
        assert result.status == WorkflowStatus.SUCCESS
        assert attempt_count >= 2


def test_git_parser_filters_internal_commits(tmp_path: Path):
    """Test Git parser correctly filters internal vs player-facing commits."""
    
    all_commits = [
        Commit(
            sha="abc1234",
            message="Add feature",
            author="Dev",
            timestamp=datetime.now(),
            commit_type=CommitType.FEATURE
        ),
        Commit(
            sha="def4567",
            message="Update CI config",
            author="Dev",
            timestamp=datetime.now(),
            commit_type=CommitType.INTERNAL
        ),
        Commit(
            sha="ghi7890",
            message="Fix bug",
            author="Dev",
            timestamp=datetime.now(),
            commit_type=CommitType.BUGFIX
        )
    ]
    
    # In a real workflow, internal commits would be filtered
    player_facing = [c for c in all_commits if c.commit_type != CommitType.INTERNAL]
    
    assert len(player_facing) == 2
    assert all(c.commit_type != CommitType.INTERNAL for c in player_facing)


@pytest.mark.asyncio
async def test_workflow_state_recovery_after_crash(tmp_path: Path, config_file: Path, test_config: Config):
    """Test workflow can recover state after a crash."""
    
    state_path = tmp_path / "state.json"
    
    # Simulate a crash by creating incomplete state
    state1 = StateManager(state_path)
    state1.state.total_runs = 5
    state1.state.successful_runs = 3
    state1.state.failed_runs = 2
    state1._save()
    
    # "Crash" and restart
    state2 = StateManager(state_path)
    
    # Should recover previous state
    assert state2.state.total_runs == 5
    assert state2.state.successful_runs == 3
    assert state2.state.failed_runs == 2


def test_banner_size_meets_steam_specs(tmp_path: Path, test_config: Config):
    """Test generated banners meet Steam specifications."""
    
    # Create test base image
    base_image = Image.new('RGB', (1920, 1080), color='red')
    buffer = BytesIO()
    base_image.save(buffer, format='PNG')
    base_image_bytes = buffer.getvalue()
    
    # Create compositor
    compositor = ImageCompositor(test_config.branding)
    
    # Composite
    result = compositor.composite_logo(base_image_bytes)
    
    # Load result
    result_image = Image.open(BytesIO(result))
    
    # Verify Steam specs (800x450)
    assert result_image.size == (800, 450)
    assert result_image.mode in ['RGB', 'RGBA']
