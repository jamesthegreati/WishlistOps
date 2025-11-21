"""
Unit tests for Git parser.

Tests commit parsing, classification, and Git operations.
"""

import pytest
from pathlib import Path
from datetime import datetime
from wishlistops.git_parser import GitParser, Commit
from git.exc import InvalidGitRepositoryError


class TestGitParserInitialization:
    """Test GitParser initialization."""
    
    def test_parser_initializes_with_valid_repo(self):
        """Test parser can be created from valid repo."""
        parser = GitParser(Path("."))
        assert parser.repo is not None
        assert parser.repo_path is not None
    
    def test_parser_raises_on_invalid_repo(self, tmp_path):
        """Test parser raises error for non-Git directory."""
        with pytest.raises(InvalidGitRepositoryError):
            GitParser(tmp_path)


class TestCommitClassification:
    """Test commit classification logic."""
    
    @pytest.fixture
    def parser(self):
        """Create parser instance for testing."""
        return GitParser(Path("."))
    
    def test_classify_player_facing_feature(self, parser):
        """Test classification of player-facing feature."""
        assert parser._is_player_facing("Add new double jump mechanic", []) is True
        assert parser._is_player_facing("Implement new boss fight system", []) is True
        assert parser._is_player_facing("New weapon: Plasma Rifle", []) is True
    
    def test_classify_player_facing_bugfix(self, parser):
        """Test classification of user-visible bugfix."""
        assert parser._is_player_facing("Fix boss AI getting stuck", []) is True
        assert parser._is_player_facing("Fix player animation glitch", []) is True
        assert parser._is_player_facing("Resolve crash when loading level 5", []) is True
    
    def test_classify_player_facing_content(self, parser):
        """Test classification of content additions."""
        assert parser._is_player_facing("Add new music track for boss fight", []) is True
        assert parser._is_player_facing("Update character sprites", []) is True
        assert parser._is_player_facing("New level: Ice Cavern", []) is True
    
    def test_classify_player_facing_balance(self, parser):
        """Test classification of balance changes."""
        assert parser._is_player_facing("Balance boss health", []) is True
        assert parser._is_player_facing("Tweak enemy damage values", []) is True
        assert parser._is_player_facing("Improve loading performance", []) is True
    
    def test_classify_internal_refactor(self, parser):
        """Test classification of internal change."""
        assert parser._is_player_facing("Refactor memory management", []) is False
        assert parser._is_player_facing("Cleanup code structure", []) is False
        assert parser._is_player_facing("Refactor rendering pipeline", []) is False
    
    def test_classify_internal_test(self, parser):
        """Test classification of test changes."""
        assert parser._is_player_facing("Add unit tests for parser", []) is False
        assert parser._is_player_facing("Update integration tests", []) is False
        assert parser._is_player_facing("Fix test failures", []) is False
    
    def test_classify_internal_docs(self, parser):
        """Test classification of documentation changes."""
        assert parser._is_player_facing("Update README", []) is False
        assert parser._is_player_facing("Add code comments", []) is False
        assert parser._is_player_facing("Fix typo in docs", []) is False
    
    def test_classify_internal_ci(self, parser):
        """Test classification of CI/CD changes."""
        assert parser._is_player_facing("Update CI pipeline", []) is False
        assert parser._is_player_facing("Update dependencies", []) is False
        assert parser._is_player_facing("Version bump to 1.0.0", []) is False
    
    def test_classify_by_file_path_player_facing(self, parser):
        """Test classification by file paths (player-facing)."""
        assert parser._is_player_facing("Update game files", ["assets/sprites/player.png"]) is True
        assert parser._is_player_facing("Update files", ["content/levels/level1.json"]) is True
        assert parser._is_player_facing("Change files", ["scenes/boss_fight.unity"]) is True
    
    def test_classify_by_file_path_internal(self, parser):
        """Test classification by file paths (internal)."""
        assert parser._is_player_facing("Update files", ["tests/test_player.py"]) is False
        assert parser._is_player_facing("Change files", ["docs/architecture.md"]) is False
        assert parser._is_player_facing("Modify files", [".github/workflows/ci.yml"]) is False
    
    def test_classify_default_internal(self, parser):
        """Test default classification for ambiguous commits."""
        assert parser._is_player_facing("Update some files", []) is False
        assert parser._is_player_facing("Change things", []) is False
        assert parser._is_player_facing("Misc updates", []) is False


class TestGitOperations:
    """Test Git operations."""
    
    @pytest.fixture
    def parser(self):
        """Create parser instance for testing."""
        return GitParser(Path("."))
    
    def test_get_commits_since_tag(self, parser):
        """Test fetching commits since a tag."""
        # This will return empty if no tags exist, or commits if tags exist
        commits = parser.get_commits_since_tag(None)
        assert isinstance(commits, list)
        # Should have at least one commit (this repo has commits)
        assert len(commits) > 0
    
    def test_get_commits_invalid_tag(self, parser):
        """Test fetching commits with invalid tag raises error."""
        with pytest.raises(Exception):  # GitCommandError
            parser.get_commits_since_tag("nonexistent-tag-v999.999.999")
    
    def test_get_commits_since_date(self, parser):
        """Test fetching commits since a date."""
        # Get commits from 30 days ago
        since = datetime.now().replace(year=datetime.now().year - 1)
        commits = parser.get_commits_since_date(since)
        assert isinstance(commits, list)
    
    def test_get_latest_tag(self, parser):
        """Test getting latest tag."""
        latest_tag = parser.get_latest_tag()
        # May be None if no tags exist
        assert latest_tag is None or isinstance(latest_tag, str)
    
    def test_get_tags(self, parser):
        """Test getting all tags."""
        tags = parser.get_tags()
        assert isinstance(tags, list)
    
    def test_get_player_facing_commits(self, parser):
        """Test filtering player-facing commits."""
        commits = parser.get_player_facing_commits(None)
        assert isinstance(commits, list)
        # All returned commits should be player-facing
        for commit in commits:
            assert commit.is_player_facing is True


class TestCommitParsing:
    """Test commit parsing logic."""
    
    @pytest.fixture
    def parser(self):
        """Create parser instance for testing."""
        return GitParser(Path("."))
    
    def test_parse_commit_structure(self, parser):
        """Test parsed commit has correct structure."""
        commits = parser.get_commits_since_tag(None)
        if commits:
            commit = commits[0]
            assert hasattr(commit, 'sha')
            assert hasattr(commit, 'message')
            assert hasattr(commit, 'author')
            assert hasattr(commit, 'date')
            assert hasattr(commit, 'files_changed')
            assert hasattr(commit, 'is_player_facing')
            
            assert isinstance(commit.sha, str)
            assert isinstance(commit.message, str)
            assert isinstance(commit.author, str)
            assert isinstance(commit.date, datetime)
            assert isinstance(commit.files_changed, list)
            assert isinstance(commit.is_player_facing, bool)
            
            # SHA should be 8 characters (short SHA)
            assert len(commit.sha) == 8
    
    def test_commit_dataclass(self):
        """Test Commit dataclass creation."""
        commit = Commit(
            sha="abc12345",
            message="Test commit",
            author="Test Author",
            date=datetime.now(),
            files_changed=["file1.py", "file2.py"],
            is_player_facing=True
        )
        assert commit.sha == "abc12345"
        assert commit.message == "Test commit"
        assert commit.author == "Test Author"
        assert commit.is_player_facing is True
        assert len(commit.files_changed) == 2


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_get_commits_since_function(self):
        """Test get_commits_since convenience function."""
        from wishlistops.git_parser import get_commits_since
        
        commits = get_commits_since(Path("."), None)
        assert isinstance(commits, list)


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    @pytest.fixture
    def parser(self):
        """Create parser instance for testing."""
        return GitParser(Path("."))
    
    def test_empty_commit_message(self, parser):
        """Test handling of empty commit message."""
        # Should classify as internal (default)
        assert parser._is_player_facing("", []) is False
    
    def test_very_long_commit_message(self, parser):
        """Test handling of very long commit message."""
        long_message = "Add new feature " + "x" * 10000 + " with new enemy boss character"
        # Should still detect keywords
        assert parser._is_player_facing(long_message, []) is True
    
    def test_mixed_case_keywords(self, parser):
        """Test case-insensitive keyword matching."""
        assert parser._is_player_facing("ADD NEW FEATURE", []) is True
        assert parser._is_player_facing("FIX PLAYER BUG", []) is True
        assert parser._is_player_facing("REFACTOR CODE", []) is False
    
    def test_multiple_keywords(self, parser):
        """Test commit with multiple keywords (internal wins)."""
        # Internal keywords have higher priority
        assert parser._is_player_facing("Refactor and add new boss enemy", []) is False
    
    def test_no_files_changed(self, parser):
        """Test commit with no files changed."""
        result = parser._is_player_facing("Add new feature", [])
        # Should classify based on message only
        assert isinstance(result, bool)
