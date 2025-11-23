"""
Git operations and deterministic asset parsing for WishlistOps.

Provides enriched commit metadata used by the orchestrator to locate
Screenshot artifacts referenced directly in Git history.

See: 04_WishlistOps_System_Architecture_Diagrams.md Section 3
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, List

import git
from git.exc import GitCommandError, InvalidGitRepositoryError


logger = logging.getLogger(__name__)


SCREENSHOT_DIRECTIVE = re.compile(r"\[shot:\s*([^\]]+)\]", re.IGNORECASE)
SCREENSHOT_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
SCREENSHOT_DIR_HINTS = ("screenshots", "promo", "marketing", "media")


@dataclass
class Commit:
	"""Represents a Git commit with metadata and optional screenshot."""
	sha: str
	message: str
	author: str
	date: datetime
	files_changed: List[str]
	is_player_facing: bool = False
	commit_type: str = "unknown"
	screenshot_path: Optional[Path] = None


class GitParser:
	"""Parse Git commits and classify for announcement generation."""

	CONVENTIONAL_PLAYER_FACING = {"feat", "fix", "perf", "revert"}
	CONVENTIONAL_INTERNAL = {"chore", "docs", "style", "refactor", "test", "build", "ci"}

	PLAYER_FACING_KEYWORDS = [
		r"\b(add|new|implement|introduce)\b.*\b(feature|mechanic|ability|weapon|enemy|level|boss|character|item|power|skill)\b",
		r"\b(add|new)\b.*\b(gameplay|combat|system|mode)\b",
		r"\bfix\b.*\b(bug|crash|issue|problem|glitch|exploit)\b",
		r"\bfix\b.*\b(player|enemy|boss|level|animation|sound|ui|menu|hud)\b",
		r"\bresolve\b.*\b(softlock|stuck|freeze|crash|bug|issue)\b",
		r"\b(add|update|improve|enhance)\b.*\b(art|sprite|sprites|texture|model|animation|sound|music|voice|dialog|dialogue)\b",
		r"\b(new|added)\b.*\b(map|level|area|world|zone|stage)\b",
		r"\bbalance|rebalance|tweak|adjust\b.*\b(damage|health|difficulty|enemy|boss|drop rate)\b",
		r"\bimprov(e|ed)\b.*\b(performance|framerate|loading|fps)\b",
		r"\boptimiz(e|ed)\b.*\b(performance|framerate|memory)\b",
	]

	INTERNAL_KEYWORDS = [
		r"\brefactor\b",
		r"\bcleanup\b",
		r"\bupdate\b.*\b(dependencies|ci|pipeline|workflow|build)\b",
		r"\b(add|update|fix)\b.*\b(test|unit test|integration test|spec)\b",
		r"\bdocs?\b",
		r"\breadme\b",
		r"\btypo\b",
		r"\bformat|formatting|lint\b",
		r"\bversion bump\b",
		r"\bmerge (branch|pull request)\b",
		r"\bwip\b",
		r"\bignore\b",
	]

	def __init__(self, repo_path: Path) -> None:
		try:
			self.repo = git.Repo(repo_path, search_parent_directories=True)
			self.repo_path = Path(self.repo.working_dir)
			logger.info("Git parser initialized", extra={"repo_path": str(self.repo_path)})
		except InvalidGitRepositoryError as exc:
			logger.error("Not a Git repository", extra={"path": str(repo_path)})
			raise InvalidGitRepositoryError(
				f"Not a Git repository: {repo_path}\nInitialize with: git init"
			) from exc

	def get_commits_since_tag(self, tag: Optional[str] = None) -> List[Commit]:
		try:
			if tag:
				commits_iter = self.repo.iter_commits(f"{tag}..HEAD")
				logger.info("Fetching commits since tag", extra={"tag": tag})
			else:
				commits_iter = self.repo.iter_commits("HEAD")
				logger.info("Fetching all commits")

			commits = [self._parse_commit(git_commit) for git_commit in commits_iter]
			logger.info(
				"Commits parsed",
				extra={
					"total": len(commits),
					"player_facing": sum(1 for commit in commits if commit.is_player_facing),
				},
			)
			return commits
		except GitCommandError:
			if tag:
				logger.error("Tag not found", extra={"tag": tag})
			raise

	def get_player_facing_commits(self, since_tag: Optional[str] = None) -> List[Commit]:
		commits = self.get_commits_since_tag(since_tag)
		return [commit for commit in commits if commit.is_player_facing]

	def get_latest_tag(self) -> Optional[str]:
		try:
			tags = sorted(self.repo.tags, key=lambda tag: tag.commit.committed_datetime, reverse=True)
			latest = tags[0].name if tags else None
			logger.info("Latest tag retrieved", extra={"tag": latest})
			return latest
		except Exception as exc:  # pragma: no cover - defensive logging only
			logger.warning("Failed to get latest tag", extra={"error": str(exc)})
			return None

	def get_tags(self) -> List[str]:
		return [tag.name for tag in self.repo.tags]

	def get_commits_since_date(self, since: datetime) -> List[Commit]:
		logger.info("Fetching commits since date", extra={"since": since.isoformat()})
		commits_iter = self.repo.iter_commits("HEAD", since=since)
		commits = [self._parse_commit(commit) for commit in commits_iter]
		logger.info(
			"Commits parsed",
			extra={
				"total": len(commits),
				"player_facing": sum(1 for commit in commits if commit.is_player_facing),
			},
		)
		return commits

	def _parse_commit(self, git_commit) -> Commit:
		message = git_commit.message.strip()
		if git_commit.parents:
			files_changed = [item.a_path for item in git_commit.diff(git_commit.parents[0])]
		else:
			files_changed = list(git_commit.stats.files.keys())

		is_player_facing, commit_type = self._classify_commit(message, files_changed)
		screenshot_path = self._detect_screenshot_path(message, files_changed)

		commit = Commit(
			sha=git_commit.hexsha[:8],
			message=message,
			author=git_commit.author.name,
			date=datetime.fromtimestamp(git_commit.committed_date),
			files_changed=files_changed,
			is_player_facing=is_player_facing,
			commit_type=commit_type,
			screenshot_path=screenshot_path,
		)

		logger.debug(
			"Commit parsed",
			extra={
				"sha": commit.sha,
				"player_facing": commit.is_player_facing,
				"screenshot": str(screenshot_path) if screenshot_path else None,
			},
		)
		return commit

	def _classify_commit(self, message: str, files_changed: List[str]) -> tuple[bool, str]:
		message_lower = message.lower()
		first_line = message.split("\n")[0].strip()

		conventional_regex = r"^([a-z]+)(\([a-z0-9\-_]+\))?(!)?:"
		match = re.match(conventional_regex, first_line)
		if match:
			commit_type = match.group(1)
			is_breaking = bool(match.group(3)) or "breaking change" in message_lower
			if is_breaking:
				return True, "breaking"
			if commit_type in self.CONVENTIONAL_PLAYER_FACING:
				return True, commit_type
			if commit_type in self.CONVENTIONAL_INTERNAL:
				return False, commit_type

		for pattern in self.INTERNAL_KEYWORDS:
			if re.search(pattern, message_lower, re.IGNORECASE):
				return False, "internal"

		for pattern in self.PLAYER_FACING_KEYWORDS:
			if re.search(pattern, message_lower, re.IGNORECASE):
				return True, "feature_or_fix"

		player_facing_paths = ("assets/", "content/", "levels/", "scenes/", "data/")
		internal_paths = ("tests/", "docs/", ".github/", "ci/", "tools/", "venv/")

		if files_changed:
			all_internal = all(any(internal in path for internal in internal_paths) for path in files_changed)
			if all_internal:
				return False, "internal"

			if any(any(player in path for player in player_facing_paths) for path in files_changed):
				return True, "content"

		return False, "unknown"

	def _detect_screenshot_path(self, message: str, files_changed: List[str]) -> Optional[Path]:
		directive_match = SCREENSHOT_DIRECTIVE.search(message)
		if directive_match:
			candidate = self._resolve_repo_path(directive_match.group(1).strip())
			if candidate and candidate.exists():
				logger.debug("Screenshot found via directive", extra={"path": str(candidate)})
				return candidate

		prioritized: List[str] = []
		secondary: List[str] = []
		for relative_path in files_changed:
			suffix = Path(relative_path).suffix.lower()
			if suffix not in SCREENSHOT_EXTENSIONS:
				continue
			if any(hint in Path(relative_path).parts for hint in SCREENSHOT_DIR_HINTS):
				prioritized.append(relative_path)
			else:
				secondary.append(relative_path)

		for relative_path in prioritized + secondary:
			candidate = self._resolve_repo_path(relative_path)
			if candidate and candidate.exists():
				logger.debug("Screenshot found via file diff", extra={"path": str(candidate)})
				return candidate

		return None

	def _resolve_repo_path(self, relative_path: str) -> Optional[Path]:
		if not relative_path:
			return None
		candidate = Path(relative_path)
		if not candidate.is_absolute():
			candidate = self.repo_path / candidate
		try:
			return candidate.resolve()
		except OSError:
			return candidate

	def _is_player_facing(self, message: str, files_changed: List[str]) -> bool:
		is_player_facing, _ = self._classify_commit(message, files_changed)
		return is_player_facing


def get_commits_since(repo_path: Path, tag: Optional[str] = None) -> List[Commit]:
	parser = GitParser(repo_path)
	return parser.get_commits_since_tag(tag)
