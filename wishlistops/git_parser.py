"""
Git operations and commit parsing for WishlistOps.

Parses Git history to identify player-facing changes that should be
announced to the Steam community.

See: 04_WishlistOps_System_Architecture_Diagrams.md Section 3
"""

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import git
from git.exc import GitCommandError, InvalidGitRepositoryError


logger = logging.getLogger(__name__)


@dataclass
class Commit:
    """Represents a Git commit with metadata."""
    
    sha: str
    message: str
    author: str
    date: datetime
    files_changed: list[str]
    is_player_facing: bool = False


class GitParser:
    """
    Parse Git commits and classify for announcement generation.
    
    Attributes:
        repo: GitPython Repository object
        repo_path: Path to the Git repository
    """
    
    # Keywords that indicate player-facing changes
    PLAYER_FACING_KEYWORDS = [
        # Features
        r'\b(add|new|implement|introduce)\b.*\b(feature|mechanic|ability|weapon|enemy|level|boss|character|item|power|skill)\b',
        r'\b(add|new)\b.*\b(gameplay|combat|system|mode)\b',
        
        # Bugfixes (user-visible)
        r'\bfix\b.*\b(bug|crash|issue|problem|glitch)\b',
        r'\bfix\b.*\b(player|enemy|boss|level|animation|sound|ui|menu)\b',
        r'\bresolve\b.*\b(softlock|stuck|freeze|crash|bug|issue)\b',
        
        # Content
        r'\b(add|update|improve|enhance)\b.*\b(art|sprite|sprites|texture|model|animation|sound|music|voice|dialog|dialogue)\b',
        r'\b(new|added)\b.*\b(map|level|area|world|zone|stage)\b',
        
        # Balance/Polish
        r'\bbalance|rebalance|tweak|adjust\b.*\b(damage|health|difficulty|enemy|boss)\b',
        r'\bimprov(e|ed)\b.*\b(performance|framerate|loading)\b',
        r'\boptimiz(e|ed)\b.*\b(performance|framerate)\b',
    ]
    
    # Keywords that indicate internal changes (NOT player-facing)
    INTERNAL_KEYWORDS = [
        r'\brefactor',
        r'\bcleanup',
        r'\bupdate\b.*\b(dependencies|ci|pipeline|workflow)\b',
        r'\b(add|update|fix)\b.*\b(test|unit test|integration test)\b',
        r'\bdocs?\b',
        r'\breadme',
        r'\bcomment',
        r'\btypo',
        r'\bformat|formatting|lint',
        r'\bversion bump',
        r'\bmerge (branch|pull request)',
    ]
    
    def __init__(self, repo_path: Path) -> None:
        """
        Initialize Git parser.
        
        Args:
            repo_path: Path to Git repository
            
        Raises:
            InvalidGitRepositoryError: If path is not a Git repo
        """
        try:
            self.repo = git.Repo(repo_path, search_parent_directories=True)
            self.repo_path = Path(self.repo.working_dir)
            logger.info("Git parser initialized", extra={
                "repo_path": str(self.repo_path)
            })
        except InvalidGitRepositoryError as e:
            logger.error("Not a Git repository", extra={"path": str(repo_path)})
            raise InvalidGitRepositoryError(
                f"Not a Git repository: {repo_path}\n"
                f"Initialize with: git init"
            ) from e
    
    def get_commits_since_tag(self, tag: Optional[str] = None) -> list[Commit]:
        """
        Get all commits since a specific tag.
        
        Args:
            tag: Git tag to start from (e.g., 'v1.0.0'). If None, returns all commits.
            
        Returns:
            List of Commit objects
            
        Raises:
            GitCommandError: If tag doesn't exist
        """
        try:
            if tag:
                # Get commits between tag and HEAD
                commit_range = f"{tag}..HEAD"
                commits_iter = self.repo.iter_commits(commit_range)
                logger.info("Fetching commits since tag", extra={"tag": tag})
            else:
                # Get all commits
                commits_iter = self.repo.iter_commits('HEAD')
                logger.info("Fetching all commits")
            
            commits = []
            for git_commit in commits_iter:
                commit = self._parse_commit(git_commit)
                commits.append(commit)
            
            logger.info("Commits parsed", extra={
                "total": len(commits),
                "player_facing": sum(1 for c in commits if c.is_player_facing)
            })
            
            return commits
            
        except GitCommandError as e:
            if tag:
                logger.error("Tag not found", extra={"tag": tag})
                raise GitCommandError(
                    f"Tag not found: {tag}\n"
                    f"Available tags: {', '.join(self.get_tags())}"
                ) from e
            raise
    
    def get_commits_since_date(self, since: datetime) -> list[Commit]:
        """
        Get all commits since a specific date.
        
        Args:
            since: Date to start from
            
        Returns:
            List of Commit objects
        """
        logger.info("Fetching commits since date", extra={"since": since.isoformat()})
        commits_iter = self.repo.iter_commits('HEAD', since=since)
        commits = [self._parse_commit(c) for c in commits_iter]
        
        logger.info("Commits parsed", extra={
            "total": len(commits),
            "player_facing": sum(1 for c in commits if c.is_player_facing)
        })
        
        return commits
    
    def get_latest_tag(self) -> Optional[str]:
        """
        Get the most recent Git tag.
        
        Returns:
            Tag name or None if no tags exist
        """
        try:
            tags = sorted(
                self.repo.tags, 
                key=lambda t: t.commit.committed_datetime, 
                reverse=True
            )
            latest = tags[0].name if tags else None
            logger.info("Latest tag retrieved", extra={"tag": latest})
            return latest
        except Exception as e:
            logger.warning("Failed to get latest tag", extra={"error": str(e)})
            return None
    
    def get_tags(self) -> list[str]:
        """
        Get all Git tags.
        
        Returns:
            List of tag names
        """
        return [tag.name for tag in self.repo.tags]
    
    def _parse_commit(self, git_commit) -> Commit:
        """
        Parse a GitPython commit into our Commit dataclass.
        
        Args:
            git_commit: GitPython Commit object
            
        Returns:
            Parsed Commit with classification
        """
        message = git_commit.message.strip()
        
        # Get files changed (handle initial commit with no parents)
        if git_commit.parents:
            files_changed = [
                item.a_path for item in git_commit.diff(git_commit.parents[0])
            ]
        else:
            # Initial commit - use stats
            files_changed = list(git_commit.stats.files.keys())
        
        commit = Commit(
            sha=git_commit.hexsha[:8],  # Short SHA
            message=message,
            author=git_commit.author.name,
            date=datetime.fromtimestamp(git_commit.committed_date),
            files_changed=files_changed,
            is_player_facing=self._is_player_facing(message, files_changed)
        )
        
        logger.debug("Commit parsed", extra={
            "sha": commit.sha,
            "is_player_facing": commit.is_player_facing,
            "message": message[:50]
        })
        
        return commit
    
    def _is_player_facing(self, message: str, files_changed: list[str]) -> bool:
        """
        Determine if a commit is player-facing.
        
        Args:
            message: Commit message
            files_changed: List of changed file paths
            
        Returns:
            True if player-facing, False if internal
        """
        message_lower = message.lower()
        
        # Check internal keywords first (higher priority)
        for pattern in self.INTERNAL_KEYWORDS:
            if re.search(pattern, message_lower, re.IGNORECASE):
                logger.debug("Classified as internal", extra={
                    "message": message[:50],
                    "pattern": pattern
                })
                return False
        
        # Check player-facing keywords
        for pattern in self.PLAYER_FACING_KEYWORDS:
            if re.search(pattern, message_lower, re.IGNORECASE):
                logger.debug("Classified as player-facing", extra={
                    "message": message[:50],
                    "pattern": pattern
                })
                return True
        
        # Check file paths for clues
        player_facing_paths = ['assets/', 'content/', 'levels/', 'scenes/']
        internal_paths = ['tests/', 'docs/', '.github/', 'ci/']
        
        for file_path in files_changed:
            for path in internal_paths:
                if path in file_path:
                    logger.debug("Classified as internal by path", extra={
                        "message": message[:50],
                        "path": file_path
                    })
                    return False
            for path in player_facing_paths:
                if path in file_path:
                    logger.debug("Classified as player-facing by path", extra={
                        "message": message[:50],
                        "path": file_path
                    })
                    return True
        
        # Default: assume internal if we can't determine
        logger.debug("Classified as internal (default)", extra={
            "message": message[:50]
        })
        return False
    
    def get_player_facing_commits(self, since_tag: Optional[str] = None) -> list[Commit]:
        """
        Get only player-facing commits since a tag.
        
        This is a convenience method that filters commits.
        
        Args:
            since_tag: Tag to start from
            
        Returns:
            List of player-facing commits only
        """
        all_commits = self.get_commits_since_tag(since_tag)
        player_commits = [c for c in all_commits if c.is_player_facing]
        
        logger.info("Filtered player-facing commits", extra={
            "total": len(all_commits),
            "player_facing": len(player_commits)
        })
        
        return player_commits


# Convenience functions for backward compatibility
def get_commits_since(repo_path: Path, tag: Optional[str] = None) -> list[Commit]:
    """
    Get commits since tag (convenience function).
    
    Args:
        repo_path: Path to Git repository
        tag: Git tag to start from
        
    Returns:
        List of Commit objects
    """
    parser = GitParser(repo_path)
    return parser.get_commits_since_tag(tag)
