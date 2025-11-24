"""
State management for WishlistOps workflow persistence.

Stores workflow state in JSON files within the Git repository,
enabling idempotent operations without external database.

Architecture: See 04_WishlistOps_System_Architecture_Diagrams.md Section 10
Philosophy: Git as Database - all state is version controlled
"""

import json
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from filelock import FileLock

from pydantic import BaseModel, Field, ValidationError

from .models import AnnouncementDraft


logger = logging.getLogger(__name__)


class StateError(Exception):
    """Base exception for state management errors."""
    pass


class StateCorruptedError(StateError):
    """Raised when state file is corrupted."""
    pass


class WorkflowRun(BaseModel):
    """Record of a single workflow run."""
    timestamp: str
    tag: Optional[str] = None
    commit_sha: Optional[str] = None
    status: str  # "success", "failed", "skipped"
    draft_title: Optional[str] = None
    error: Optional[str] = None


class StateData(BaseModel):
    """
    Complete state data structure.
    
    This matches the schema in 04_WishlistOps_System_Architecture_Diagrams.md
    Section 10: State Schema (state.json)
    """
    
    # Last run information
    last_run_timestamp: Optional[str] = None
    last_tag: Optional[str] = None
    last_commit_sha: Optional[str] = None
    
    # Last post information (for rate limiting)
    last_post_date: Optional[str] = None
    last_post_title: Optional[str] = None
    
    # Counters
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    skipped_runs: int = 0
    
    # Recent history (last 10 runs)
    recent_runs: list[WorkflowRun] = Field(default_factory=list)
    
    # Current draft (if any)
    current_draft: Optional[AnnouncementDraft] = None
    
    # Metadata
    version: str = "1.0"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class StateManager:
    """
    Manage persistent state for WishlistOps workflows.
    
    Provides thread-safe read/write operations on state.json file
    with atomic writes and backup management.
    
    Attributes:
        state_path: Path to state.json file
        lock_path: Path to lock file for synchronization
        backup_dir: Directory for state backups
        state: Current state data
    """
    
    MAX_RECENT_RUNS = 10
    MAX_BACKUPS = 5
    
    def __init__(self, state_path: Path) -> None:
        """
        Initialize state manager.
        
        Args:
            state_path: Path to state.json file
        """
        self.state_path = state_path
        self.lock_path = state_path.parent / f"{state_path.name}.lock"
        self.backup_dir = state_path.parent / ".state_backups"
        
        # Ensure directories exist
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Load or initialize state
        self.state = self._load_or_initialize()
        
        logger.info("State manager initialized", extra={
            "state_path": str(state_path),
            "total_runs": self.state.total_runs
        })
    
    def _load_or_initialize(self) -> StateData:
        """
        Load state from file or create new state if file doesn't exist.
        
        Returns:
            Loaded or new StateData
            
        Raises:
            StateCorruptedError: If state file exists but is corrupted
        """
        if not self.state_path.exists():
            logger.info("State file not found, creating new state")
            return StateData()
        
        try:
            with open(self.state_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate with Pydantic
            state = StateData(**data)
            
            logger.info("State loaded successfully", extra={
                "total_runs": state.total_runs,
                "last_run": state.last_run_timestamp
            })
            
            return state
            
        except json.JSONDecodeError as e:
            raise StateCorruptedError(
                f"State file corrupted (invalid JSON): {e}\n"
                f"File: {self.state_path}\n"
                f"Consider restoring from backup in {self.backup_dir}"
            ) from e
        
        except ValidationError as e:
            raise StateCorruptedError(
                f"State file has invalid structure: {e}\n"
                f"File: {self.state_path}\n"
                f"Consider restoring from backup in {self.backup_dir}"
            ) from e
    
    def update_last_run(
        self,
        draft: Optional[AnnouncementDraft] = None,
        tag: Optional[str] = None,
        commit_sha: Optional[str] = None,
        status: str = "success",
        error: Optional[str] = None
    ) -> None:
        """
        Update state after a workflow run.
        
        Args:
            draft: Generated announcement draft
            tag: Git tag that triggered the run
            commit_sha: Git commit SHA
            status: Run status ("success", "failed", "skipped")
            error: Error message if failed
        """
        with FileLock(str(self.lock_path)):
            now = datetime.now(timezone.utc).isoformat()
            
            # Update last run info
            self.state.last_run_timestamp = now
            if tag:
                self.state.last_tag = tag
            if commit_sha:
                self.state.last_commit_sha = commit_sha
            
            # Update counters
            self.state.total_runs += 1
            if status == "success":
                self.state.successful_runs += 1
            elif status == "failed":
                self.state.failed_runs += 1
            elif status == "skipped":
                self.state.skipped_runs += 1
            
            # Add to recent runs
            run = WorkflowRun(
                timestamp=now,
                tag=tag,
                commit_sha=commit_sha,
                status=status,
                draft_title=draft.title if draft else None,
                error=error
            )
            self.state.recent_runs.insert(0, run)
            
            # Keep only last N runs
            if len(self.state.recent_runs) > self.MAX_RECENT_RUNS:
                self.state.recent_runs = self.state.recent_runs[:self.MAX_RECENT_RUNS]
            
            # Update draft
            self.state.current_draft = draft
            
            # Update timestamp
            self.state.updated_at = now
            
            # Save
            self._save()
            
            logger.info("State updated", extra={
                "status": status,
                "total_runs": self.state.total_runs,
                "tag": tag
            })
    
    def update_last_post(self, title: str) -> None:
        """
        Update state after posting to Steam.
        
        Args:
            title: Title of posted announcement
        """
        with FileLock(str(self.lock_path)):
            now = datetime.now(timezone.utc).isoformat()
            
            self.state.last_post_date = now
            self.state.last_post_title = title
            self.state.updated_at = now
            
            self._save()
            
            logger.info("Last post updated", extra={
                "title": title,
                "date": now
            })
    
    def get_last_post_date(self) -> Optional[datetime]:
        """
        Get the date of the last Steam post.
        
        Returns:
            Datetime of last post, or None if never posted
        """
        if not self.state.last_post_date:
            return None
        
        try:
            dt = datetime.fromisoformat(self.state.last_post_date)
            # Ensure datetime is timezone-aware
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            logger.warning(f"Invalid last_post_date format: {self.state.last_post_date}")
            return None
    
    def get_last_tag(self) -> Optional[str]:
        """
        Get the last Git tag processed.
        
        Returns:
            Last tag name, or None if never run
        """
        return self.state.last_tag
    
    def get_days_since_last_post(self) -> Optional[float]:
        """
        Calculate days since last post to Steam.
        
        Returns:
            Days since last post, or None if never posted
        """
        last_post = self.get_last_post_date()
        if not last_post:
            return None
        
        delta = datetime.now(timezone.utc) - last_post
        return delta.total_seconds() / 86400  # Convert to days
    
    def should_allow_post(self, min_days: int) -> bool:
        """
        Check if enough time has passed since last post (rate limiting).
        
        Args:
            min_days: Minimum days between posts
            
        Returns:
            True if OK to post, False if rate limited
        """
        days_since = self.get_days_since_last_post()
        
        if days_since is None:
            # Never posted before
            return True
        
        allowed = days_since >= min_days
        
        if not allowed:
            logger.warning(
                f"Rate limit: Only {days_since:.1f} days since last post "
                f"(minimum: {min_days} days)"
            )
        
        return allowed
    
    def get_statistics(self) -> dict:
        """
        Get workflow statistics.
        
        Returns:
            Dictionary with run statistics
        """
        success_rate = 0.0
        if self.state.total_runs > 0:
            success_rate = self.state.successful_runs / self.state.total_runs
        
        return {
            "total_runs": self.state.total_runs,
            "successful_runs": self.state.successful_runs,
            "failed_runs": self.state.failed_runs,
            "skipped_runs": self.state.skipped_runs,
            "success_rate": f"{success_rate:.1%}",
            "last_run": self.state.last_run_timestamp,
            "last_post": self.state.last_post_date,
            "last_tag": self.state.last_tag
        }
    
    def _save(self) -> None:
        """
        Save state to file atomically.
        
        Uses atomic write (write to temp, then rename) to prevent corruption.
        Creates backup before overwriting.
        """
        # Backup existing state
        if self.state_path.exists():
            self._create_backup()
        
        # Write to temporary file
        temp_path = self.state_path.parent / f"{self.state_path.name}.tmp"
        
        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(
                    self.state.model_dump(mode='json'),
                    f,
                    indent=2,
                    ensure_ascii=False
                )
            
            # Atomic rename
            temp_path.replace(self.state_path)
            
            logger.debug("State saved successfully")
            
        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                temp_path.unlink()
            raise StateError(f"Failed to save state: {e}") from e
    
    def _create_backup(self) -> None:
        """Create backup of current state file."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"state_{timestamp}.json"
        
        try:
            shutil.copy2(self.state_path, backup_path)
            logger.debug(f"State backup created: {backup_path}")
            
            # Clean old backups
            self._cleanup_old_backups()
            
        except Exception as e:
            logger.warning(f"Failed to create backup: {e}")
    
    def _cleanup_old_backups(self) -> None:
        """Remove old backups, keeping only last N."""
        backups = sorted(self.backup_dir.glob("state_*.json"), reverse=True)
        
        for backup in backups[self.MAX_BACKUPS:]:
            try:
                backup.unlink()
                logger.debug(f"Removed old backup: {backup}")
            except Exception as e:
                logger.warning(f"Failed to remove backup {backup}: {e}")
    
    def restore_from_backup(self, backup_name: Optional[str] = None) -> None:
        """
        Restore state from backup.
        
        Args:
            backup_name: Specific backup to restore, or None for latest
            
        Raises:
            StateError: If backup doesn't exist or restore fails
        """
        if backup_name:
            backup_path = self.backup_dir / backup_name
        else:
            # Get latest backup
            backups = sorted(self.backup_dir.glob("state_*.json"), reverse=True)
            if not backups:
                raise StateError("No backups found")
            backup_path = backups[0]
        
        if not backup_path.exists():
            raise StateError(f"Backup not found: {backup_path}")
        
        try:
            shutil.copy2(backup_path, self.state_path)
            self.state = self._load_or_initialize()
            logger.info(f"State restored from backup: {backup_path}")
        except Exception as e:
            raise StateError(f"Failed to restore backup: {e}") from e


# Convenience functions
def load_state(state_path: Path) -> StateManager:
    """Load state manager (convenience function)."""
    return StateManager(state_path)
