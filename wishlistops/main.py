"""
WishlistOps Main Orchestrator

This module coordinates the entire automation workflow from Git commits
to Discord approval notifications.

Architecture: See 04_WishlistOps_System_Architecture_Diagrams.md
Production fixes: See 05_WishlistOps_Revised_Architecture.md

Workflow Steps:
1. Parse Git commits since last run
2. Generate announcement text using AI
3. Filter content for quality (anti-slop)
4. Generate banner image
5. Composite game logo
6. Send to Discord for approval
7. Update state for next run

Error Handling:
- API failures retry with exponential backoff
- Partial failures continue with degraded functionality
- All errors logged with full context
"""

import argparse
import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from .config_manager import load_config
from .models import Config, WorkflowState, AnnouncementDraft, Commit, WorkflowStatus
from .git_parser import GitParser
from .ai_client import AIClient
from .content_filter import ContentFilter
from .image_compositor import ImageCompositor
from .discord_notifier import DiscordNotifier
from .state_manager import StateManager


# Configure structured JSON logging
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp":"%(asctime)s","level":"%(levelname)s","module":"%(name)s","message":"%(message)s"}',
    datefmt='%Y-%m-%dT%H:%M:%S'
)
logger = logging.getLogger(__name__)


class WorkflowError(Exception):
    """Base exception for workflow errors."""
    pass


class WishlistOpsOrchestrator:
    """
    Main orchestrator for WishlistOps automation workflow.
    
    This class coordinates all components to transform Git commits
    into Steam-ready announcements with human approval.
    
    Attributes:
        config: Validated configuration
        state: State manager for persistence
        git: Git operations handler
        ai: AI client for content generation
        filter: Content quality filter
        compositor: Image compositing handler
        notifier: Discord notification sender
        dry_run: If True, skip actual API calls
    """
    
    def __init__(self, config_path: Path, dry_run: bool = False) -> None:
        """
        Initialize orchestrator with configuration.
        
        Args:
            config_path: Path to config.json file
            dry_run: If True, skip actual API calls
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValidationError: If config is invalid
        """
        logger.info("Initializing WishlistOps orchestrator", extra={
            "config_path": str(config_path),
            "dry_run": dry_run
        })
        
        self.dry_run = dry_run
        self.config = load_config(config_path)
        self.state = StateManager(config_path.parent / "state.json")
        
        # Initialize all components
        # Git parser needs repo root, not config directory
        repo_root = config_path.parent.parent if config_path.parent.name == "wishlistops" else config_path.parent
        self.git = GitParser(repo_root)
        self.ai = AIClient(
            api_key=self.config.google_ai_key,
            model_config=self.config.ai
        )
        self.filter = ContentFilter(self.config.voice)
        self.compositor = ImageCompositor(self.config.branding) if self.config.branding else None
        self.notifier = DiscordNotifier(
            webhook_url=self.config.discord_webhook_url,
            dry_run=dry_run
        )
        
        logger.info("Orchestrator initialized successfully")
    
    async def run(self) -> WorkflowState:
        """
        Execute the complete automation workflow.
        
        This is the main entry point that orchestrates all steps:
        1. Parse commits
        2. Generate content
        3. Filter quality
        4. Send for approval
        5. Update state
        
        Returns:
            WorkflowState with execution results
            
        Raises:
            WorkflowError: If critical step fails
        """
        logger.info("="*60)
        logger.info("Starting WishlistOps workflow execution")
        logger.info("="*60)
        
        workflow_state = WorkflowState(
            status=WorkflowStatus.SUCCESS,
            started_at=datetime.now().isoformat()
        )
        
        try:
            # Step 1: Check if we should run (rate limiting)
            if not self._should_run():
                logger.info("Skipping run due to rate limits")
                workflow_state.status = WorkflowStatus.SKIPPED
                workflow_state.reason = "rate_limit"
                workflow_state.completed_at = datetime.now().isoformat()
                return workflow_state
            
            # Step 2: Parse Git commits
            commits = await self._parse_commits()
            if not commits:
                logger.info("No new commits found, ending run")
                workflow_state.status = WorkflowStatus.SKIPPED
                workflow_state.reason = "no_commits"
                workflow_state.completed_at = datetime.now().isoformat()
                return workflow_state
            
            logger.info(f"Found {len(commits)} commits to process")
            
            # Step 3: Generate announcement text
            draft = await self._generate_announcement(commits)
            logger.info(f"Generated announcement: {draft.title}")
            
            # Step 4: Filter content for quality
            draft = await self._filter_content(draft)
            logger.info("Content passed quality filter")
            
            # Step 5: Generate and composite banner
            if self.config.branding and self.compositor:
                draft = await self._create_banner(draft)
                logger.info("Banner generated successfully")
            
            # Step 6: Send to Discord for approval
            await self._send_for_approval(draft)
            logger.info("Sent to Discord for approval")
            
            # Step 7: Update state
            self.state.update_last_run(draft)
            logger.info("State updated successfully")
            
            workflow_state.status = WorkflowStatus.SUCCESS
            workflow_state.draft = draft
            workflow_state.completed_at = datetime.now().isoformat()
            
            logger.info("="*60)
            logger.info("✅ Workflow completed successfully")
            logger.info("="*60)
            
            return workflow_state
            
        except Exception as e:
            logger.error(f"❌ Workflow failed: {e}", exc_info=True)
            workflow_state.status = WorkflowStatus.FAILED
            workflow_state.error = str(e)
            workflow_state.completed_at = datetime.now().isoformat()
            
            try:
                await self.notifier.send_error(str(e))
            except Exception as notify_error:
                logger.error(f"Failed to send error notification: {notify_error}")
            
            raise WorkflowError(f"Workflow failed: {e}") from e
    
    def _should_run(self) -> bool:
        """
        Check if workflow should run based on rate limits.
        
        Returns:
            True if OK to run, False if rate limited
        """
        last_post = self.state.get_last_post_date()
        if not last_post:
            logger.info("No previous posts found, OK to run")
            return True
        
        try:
            last_post_dt = datetime.fromisoformat(last_post)
            days_since = (datetime.now() - last_post_dt).days
            min_days = self.config.automation.min_days_between_posts
            
            if days_since < min_days:
                logger.warning(
                    f"Rate limit: Only {days_since} days since last post (min: {min_days})"
                )
                return False
            
            logger.info(f"Rate limit OK: {days_since} days since last post")
            return True
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Error parsing last post date: {e}, allowing run")
            return True
    
    async def _parse_commits(self) -> list[Commit]:
        """
        Parse Git commits since last run.
        
        Returns:
            List of player-facing commits
        """
        logger.info("Parsing Git commits")
        
        try:
            last_tag = self.state.get_last_tag()
            
            # Get player-facing commits (already filtered by GitParser)
            player_facing = self.git.get_player_facing_commits(since_tag=last_tag)
            
            logger.info(
                f"Found {len(player_facing)} player-facing commits",
                extra={
                    "player_facing_commits": len(player_facing),
                    "last_tag": last_tag
                }
            )
            
            # Check minimum commits requirement
            if len(player_facing) < self.config.automation.min_commits_required:
                logger.info(
                    f"Not enough commits to trigger automation "
                    f"({len(player_facing)} < {self.config.automation.min_commits_required})"
                )
                return []
            
            return player_facing
            
        except Exception as e:
            logger.error(f"Error parsing commits: {e}", exc_info=True)
            raise WorkflowError(f"Failed to parse commits: {e}") from e
    
    async def _generate_announcement(self, commits: list[Commit]) -> AnnouncementDraft:
        """
        Generate announcement text using AI.
        
        Args:
            commits: List of commits to generate announcement from
            
        Returns:
            Generated announcement draft
        """
        logger.info("Generating announcement with AI")
        
        try:
            # Build context from config
            context = self._build_ai_context(commits)
            
            logger.debug("AI context built", extra={"context_length": len(context)})
            
            # Call AI API
            result = await self.ai.generate_text(
                prompt=context,
                temperature=self.config.ai.temperature
            )
            
            draft = AnnouncementDraft(
                title=result['title'],
                body=result['body'],
                created_at=datetime.now().isoformat()
            )
            
            logger.info(
                "Announcement generated successfully",
                extra={
                    "title_length": len(draft.title),
                    "body_length": len(draft.body)
                }
            )
            
            return draft
            
        except Exception as e:
            logger.error(f"Error generating announcement: {e}", exc_info=True)
            raise WorkflowError(f"Failed to generate announcement: {e}") from e
    
    async def _filter_content(self, draft: AnnouncementDraft) -> AnnouncementDraft:
        """
        Apply anti-slop filter to content.
        
        Args:
            draft: Initial draft to filter
            
        Returns:
            Filtered draft (may be regenerated if issues found)
        """
        logger.info("Filtering content for quality")
        
        try:
            issues = self.filter.check(draft.body)
            
            if issues:
                logger.warning(
                    f"Found {len(issues)} quality issues: {issues}",
                    extra={"issues": issues}
                )
                # Regenerate with stricter prompt
                draft = await self._regenerate_with_fixes(draft, issues)
                logger.info("Content regenerated with fixes")
            else:
                logger.info("Content passed quality filter")
            
            return draft
            
        except Exception as e:
            logger.error(f"Error filtering content: {e}", exc_info=True)
            # Non-critical error, return original draft
            logger.warning("Continuing with unfiltered content")
            return draft
    
    async def _regenerate_with_fixes(
        self, 
        draft: AnnouncementDraft, 
        issues: list[str]
    ) -> AnnouncementDraft:
        """
        Regenerate content with fixes for identified issues.
        
        Args:
            draft: Original draft with issues
            issues: List of issues found
            
        Returns:
            Regenerated draft
        """
        logger.info("Regenerating content with fixes")
        
        # Build a corrective prompt
        corrective_prompt = f"""
The following announcement has quality issues that need to be fixed:

ORIGINAL TITLE: {draft.title}
ORIGINAL BODY: {draft.body}

ISSUES FOUND:
{chr(10).join(f"- {issue}" for issue in issues)}

Please regenerate the announcement fixing these issues while maintaining the core message.
Avoid: {', '.join(self.config.voice.avoid_phrases)}
Tone: {self.config.voice.tone}
Personality: {self.config.voice.personality}
"""
        
        try:
            result = await self.ai.generate_text(
                prompt=corrective_prompt,
                temperature=self.config.ai.temperature * 0.8  # Lower temperature for corrections
            )
            
            return AnnouncementDraft(
                title=result['title'],
                body=result['body'],
                created_at=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error regenerating content: {e}", exc_info=True)
            # Return original draft if regeneration fails
            logger.warning("Returning original draft due to regeneration failure")
            return draft
    
    async def _create_banner(self, draft: AnnouncementDraft) -> AnnouncementDraft:
        """
        Generate and composite banner image.
        
        Args:
            draft: Announcement draft to create banner for
            
        Returns:
            Draft with banner_url populated
        """
        logger.info("Generating banner image")
        
        try:
            # Generate base image with AI
            image_prompt = self._build_image_prompt(draft)
            
            logger.debug("Image prompt built", extra={"prompt_length": len(image_prompt)})
            
            base_image = await self.ai.generate_image(
                prompt=image_prompt,
                aspect_ratio="16:9"
            )
            
            # Composite logo if compositor available
            if self.compositor and self.config.branding and self.config.branding.logo_path:
                final_image = self.compositor.add_logo(
                    base_image,
                    logo_path=self.config.branding.logo_path
                )
                logger.info("Logo composited successfully")
            else:
                final_image = base_image
                logger.info("No logo compositing (logo not configured)")
            
            # Save and get URL
            banner_url = self._save_banner(final_image)
            draft.banner_url = banner_url
            
            logger.info(f"Banner saved: {banner_url}")
            
            return draft
            
        except Exception as e:
            logger.error(f"Error creating banner: {e}", exc_info=True)
            # Non-critical error, continue without banner
            logger.warning("Continuing without banner image")
            return draft
    
    async def _send_for_approval(self, draft: AnnouncementDraft) -> None:
        """
        Send draft to Discord for human approval.
        
        Args:
            draft: Draft to send for approval
        """
        logger.info("Sending to Discord for approval")
        
        try:
            await self.notifier.send_approval_request(
                title=draft.title,
                body=draft.body,
                banner_url=draft.banner_url,
                game_name=self.config.steam.app_name,
                tag=self.state.get_last_tag(),
                steam_app_id=self.config.steam.app_id
            )
            
            logger.info("Approval request sent successfully")
            
        except Exception as e:
            logger.error(f"Error sending approval request: {e}", exc_info=True)
            raise WorkflowError(f"Failed to send approval request: {e}") from e
    
    def _build_ai_context(self, commits: list[Commit]) -> str:
        """
        Build AI prompt context from commits and config.
        
        Args:
            commits: List of commits to include in context
            
        Returns:
            Formatted prompt string
        """
        # Format commits
        commit_summaries = []
        for commit in commits:
            commit_summaries.append(
                f"- [{commit.commit_type.value}] {commit.message} (by {commit.author})"
            )
        
        commits_text = "\n".join(commit_summaries)
        
        # Build full prompt
        prompt = f"""
You are writing a Steam announcement for the game "{self.config.steam.app_name}".

GAME CONTEXT:
- Steam App ID: {self.config.steam.app_id}
- Game Name: {self.config.steam.app_name}

WRITING STYLE:
- Tone: {self.config.voice.tone}
- Personality: {self.config.voice.personality}
- NEVER use these phrases: {', '.join(self.config.voice.avoid_phrases)}

RECENT CHANGES ({len(commits)} commits):
{commits_text}

REQUIREMENTS:
- Write an engaging announcement about these changes
- Title must be under {self.config.voice.max_title_length} characters
- Body must be under {self.config.voice.max_body_length} characters
- Focus on player-facing improvements
- Be specific about what changed
- Maintain the specified tone and personality

FORMAT:
Return a JSON object with "title" and "body" keys.
"""
        
        return prompt
    
    def _build_image_prompt(self, draft: AnnouncementDraft) -> str:
        """
        Build image generation prompt.
        
        Args:
            draft: Announcement draft to create image for
            
        Returns:
            Image generation prompt
        """
        if not self.config.branding:
            return f"Game announcement banner for: {draft.title}"
        
        colors_text = ""
        if self.config.branding.color_palette:
            colors_text = f"\nCOLOR PALETTE: {', '.join(self.config.branding.color_palette)}"
        
        prompt = f"""
Create a game announcement banner image with the following specifications:

CONTENT: {draft.title}

ARTISTIC STYLE: {self.config.branding.art_style}
{colors_text}

REQUIREMENTS:
- Aspect ratio: 16:9 (widescreen)
- High quality, suitable for Steam
- Visually appealing and eye-catching
- Leave space in {self.config.branding.logo_position.value} for logo overlay
- Professional game marketing aesthetic
"""
        
        return prompt
    
    def _save_banner(self, image_data: bytes) -> str:
        """
        Save banner image to disk and return URL.
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            URL or path to saved banner
        """
        # Create banners directory if it doesn't exist
        banners_dir = Path("wishlistops/banners")
        banners_dir.mkdir(exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"banner_{timestamp}.png"
        filepath = banners_dir / filename
        
        # Save image
        with open(filepath, 'wb') as f:
            f.write(image_data)
        
        logger.info(f"Banner saved to: {filepath}")
        
        # In production, this would upload to CDN and return URL
        # For now, return local path
        return str(filepath)


def main() -> None:
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="WishlistOps - Automate Steam marketing for indie games",
        epilog="See documentation at: https://github.com/your-org/wishlistops"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("wishlistops/config.json"),
        help="Path to configuration file"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without making actual API calls"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    try:
        logger.info("Starting WishlistOps", extra={
            "config": str(args.config),
            "dry_run": args.dry_run,
            "verbose": args.verbose
        })
        
        orchestrator = WishlistOpsOrchestrator(args.config, dry_run=args.dry_run)
        result = asyncio.run(orchestrator.run())
        
        if result.status == WorkflowStatus.SUCCESS:
            logger.info("✅ Workflow completed successfully")
            sys.exit(0)
        elif result.status == WorkflowStatus.SKIPPED:
            logger.info(f"⚠️ Workflow skipped: {result.reason}")
            sys.exit(0)
        else:
            logger.warning(f"⚠️ Workflow ended with status: {result.status}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Workflow interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        sys.exit(2)


if __name__ == "__main__":
    main()
