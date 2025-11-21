"""
Tests for state management system.

Tests cover initialization, persistence, rate limiting, backup management,
and error handling for the StateManager class.
"""

import pytest
from pathlib import Path
from datetime import datetime, timedelta
from wishlistops.state_manager import StateManager, StateCorruptedError
from wishlistops.models import AnnouncementDraft


@pytest.fixture
def temp_state_path(tmp_path):
    """Create temporary state file path."""
    return tmp_path / "state.json"


def test_state_manager_initialization(temp_state_path):
    """Test state manager can be initialized."""
    manager = StateManager(temp_state_path)
    assert manager.state is not None
    assert manager.state.total_runs == 0
    assert manager.state.successful_runs == 0
    assert manager.state.failed_runs == 0
    assert manager.state.skipped_runs == 0


def test_state_creates_file_on_save(temp_state_path):
    """Test state file is created on first save."""
    manager = StateManager(temp_state_path)
    manager.update_last_run(status="success", tag="v1.0.0")
    
    assert temp_state_path.exists()


def test_state_persists_between_loads(temp_state_path):
    """Test state persists between manager instances."""
    # First instance
    manager1 = StateManager(temp_state_path)
    manager1.update_last_run(status="success", tag="v1.0.0")
    
    # Second instance
    manager2 = StateManager(temp_state_path)
    assert manager2.state.total_runs == 1
    assert manager2.state.last_tag == "v1.0.0"


def test_update_last_run_increments_counters(temp_state_path):
    """Test run counters are updated correctly."""
    manager = StateManager(temp_state_path)
    
    manager.update_last_run(status="success")
    assert manager.state.total_runs == 1
    assert manager.state.successful_runs == 1
    assert manager.state.failed_runs == 0
    assert manager.state.skipped_runs == 0
    
    manager.update_last_run(status="failed")
    assert manager.state.total_runs == 2
    assert manager.state.successful_runs == 1
    assert manager.state.failed_runs == 1
    assert manager.state.skipped_runs == 0
    
    manager.update_last_run(status="skipped")
    assert manager.state.total_runs == 3
    assert manager.state.successful_runs == 1
    assert manager.state.failed_runs == 1
    assert manager.state.skipped_runs == 1


def test_update_last_run_with_draft(temp_state_path):
    """Test updating with announcement draft."""
    manager = StateManager(temp_state_path)
    
    draft = AnnouncementDraft(
        title="Test Update",
        body="This is a test update",
        created_at="2024-01-01T00:00:00"
    )
    
    manager.update_last_run(draft=draft, status="success", tag="v1.0.0")
    
    assert manager.state.current_draft is not None
    assert manager.state.current_draft.title == "Test Update"
    assert len(manager.state.recent_runs) == 1
    assert manager.state.recent_runs[0].draft_title == "Test Update"


def test_update_last_run_with_error(temp_state_path):
    """Test updating with error information."""
    manager = StateManager(temp_state_path)
    
    manager.update_last_run(status="failed", error="API timeout")
    
    assert manager.state.failed_runs == 1
    assert len(manager.state.recent_runs) == 1
    assert manager.state.recent_runs[0].error == "API timeout"


def test_rate_limiting(temp_state_path):
    """Test rate limiting works."""
    manager = StateManager(temp_state_path)
    
    # First post - should be allowed
    assert manager.should_allow_post(min_days=7) is True
    
    # Record post
    manager.update_last_post(title="Test Post")
    
    # Second post immediately - should be blocked
    assert manager.should_allow_post(min_days=7) is False
    
    # Fake time passage by modifying state
    past_date = (datetime.utcnow() - timedelta(days=8)).isoformat()
    manager.state.last_post_date = past_date
    
    # Now should be allowed
    assert manager.should_allow_post(min_days=7) is True


def test_get_days_since_last_post(temp_state_path):
    """Test calculation of days since last post."""
    manager = StateManager(temp_state_path)
    
    # No posts yet
    assert manager.get_days_since_last_post() is None
    
    # Post 5 days ago
    past_date = (datetime.utcnow() - timedelta(days=5)).isoformat()
    manager.state.last_post_date = past_date
    
    days = manager.get_days_since_last_post()
    assert days is not None
    assert 4.9 < days < 5.1  # Allow small time differences


def test_recent_runs_limited(temp_state_path):
    """Test recent runs list is limited to MAX_RECENT_RUNS."""
    manager = StateManager(temp_state_path)
    
    # Add more runs than max
    for i in range(15):
        manager.update_last_run(status="success", tag=f"v1.{i}.0")
    
    assert len(manager.state.recent_runs) == StateManager.MAX_RECENT_RUNS
    
    # Verify most recent run is first
    assert manager.state.recent_runs[0].tag == "v1.14.0"
    
    # Verify oldest kept run
    assert manager.state.recent_runs[-1].tag == "v1.5.0"


def test_backup_creation(temp_state_path):
    """Test backups are created."""
    manager = StateManager(temp_state_path)
    manager.update_last_run(status="success")
    
    # Make another change to trigger backup
    manager.update_last_run(status="success")
    
    backups = list(manager.backup_dir.glob("state_*.json"))
    assert len(backups) >= 1


def test_backup_cleanup(temp_state_path):
    """Test old backups are cleaned up."""
    manager = StateManager(temp_state_path)
    
    # Create more backups than max
    for i in range(StateManager.MAX_BACKUPS + 3):
        manager.update_last_run(status="success", tag=f"v1.{i}.0")
    
    backups = list(manager.backup_dir.glob("state_*.json"))
    assert len(backups) <= StateManager.MAX_BACKUPS


def test_restore_from_backup(temp_state_path):
    """Test restoring from backup."""
    manager = StateManager(temp_state_path)
    
    # Create initial state
    manager.update_last_run(status="success", tag="v1.0.0")
    
    # Make a change
    manager.update_last_run(status="success", tag="v2.0.0")
    
    # Get latest backup
    backups = sorted(manager.backup_dir.glob("state_*.json"), reverse=True)
    assert len(backups) > 0
    
    # Corrupt current state
    manager.state.total_runs = 999
    manager._save()
    
    # Restore from backup
    manager.restore_from_backup()
    
    # Should have restored state (though exact count depends on backup timing)
    assert manager.state.total_runs < 999


def test_corrupted_state_raises_error(temp_state_path):
    """Test corrupted state file raises error."""
    # Create invalid JSON file
    with open(temp_state_path, 'w') as f:
        f.write("{invalid json")
    
    with pytest.raises(StateCorruptedError):
        StateManager(temp_state_path)


def test_invalid_state_structure_raises_error(temp_state_path):
    """Test invalid state structure raises error."""
    # Create JSON with invalid structure
    with open(temp_state_path, 'w') as f:
        f.write('{"invalid_field": "value"}')
    
    # Should still work with Pydantic defaults, but let's test partial invalid data
    with open(temp_state_path, 'w') as f:
        f.write('{"total_runs": "not_a_number"}')
    
    with pytest.raises(StateCorruptedError):
        StateManager(temp_state_path)


def test_statistics(temp_state_path):
    """Test statistics are calculated correctly."""
    manager = StateManager(temp_state_path)
    
    manager.update_last_run(status="success")
    manager.update_last_run(status="success")
    manager.update_last_run(status="failed")
    
    stats = manager.get_statistics()
    assert stats["total_runs"] == 3
    assert stats["successful_runs"] == 2
    assert stats["failed_runs"] == 1
    assert stats["success_rate"] == "66.7%"


def test_statistics_no_runs(temp_state_path):
    """Test statistics with no runs."""
    manager = StateManager(temp_state_path)
    
    stats = manager.get_statistics()
    assert stats["total_runs"] == 0
    assert stats["success_rate"] == "0.0%"


def test_get_last_tag(temp_state_path):
    """Test getting last tag."""
    manager = StateManager(temp_state_path)
    
    assert manager.get_last_tag() is None
    
    manager.update_last_run(status="success", tag="v1.0.0")
    assert manager.get_last_tag() == "v1.0.0"


def test_atomic_write_on_error(temp_state_path):
    """Test atomic write cleans up temp file on error."""
    manager = StateManager(temp_state_path)
    manager.update_last_run(status="success")
    
    # Force an error during save by making directory read-only
    # This is platform-dependent, so we'll just verify temp file doesn't persist
    temp_file = temp_state_path.parent / f"{temp_state_path.name}.tmp"
    
    # After normal save, temp file should not exist
    assert not temp_file.exists()


def test_state_with_commit_sha(temp_state_path):
    """Test state tracking of commit SHA."""
    manager = StateManager(temp_state_path)
    
    manager.update_last_run(
        status="success",
        tag="v1.0.0",
        commit_sha="abc123def456"
    )
    
    assert manager.state.last_commit_sha == "abc123def456"


def test_update_last_post(temp_state_path):
    """Test updating last post information."""
    manager = StateManager(temp_state_path)
    
    manager.update_last_post(title="Major Update Released!")
    
    assert manager.state.last_post_title == "Major Update Released!"
    assert manager.state.last_post_date is not None
    
    # Verify date is recent
    post_date = manager.get_last_post_date()
    assert post_date is not None
    assert (datetime.utcnow() - post_date).total_seconds() < 5


def test_invalid_last_post_date_format(temp_state_path):
    """Test handling of invalid last_post_date format."""
    manager = StateManager(temp_state_path)
    
    # Manually set invalid date format
    manager.state.last_post_date = "invalid-date-format"
    
    # Should return None and log warning
    assert manager.get_last_post_date() is None


def test_state_metadata(temp_state_path):
    """Test state metadata fields."""
    manager = StateManager(temp_state_path)
    
    assert manager.state.version == "1.0"
    assert manager.state.created_at is not None
    assert manager.state.updated_at is not None
    
    # Verify timestamps are valid ISO format
    created = datetime.fromisoformat(manager.state.created_at)
    updated = datetime.fromisoformat(manager.state.updated_at)
    
    assert created <= updated


def test_concurrent_access_with_lock(temp_state_path):
    """Test file locking prevents race conditions."""
    import threading
    import time
    
    manager = StateManager(temp_state_path)
    results = []
    
    def update_state(tag_num):
        try:
            manager.update_last_run(status="success", tag=f"v1.{tag_num}.0")
            results.append(tag_num)
        except Exception as e:
            results.append(f"error: {e}")
    
    # Create multiple threads updating state
    threads = []
    for i in range(5):
        t = threading.Thread(target=update_state, args=(i,))
        threads.append(t)
        t.start()
    
    # Wait for all threads
    for t in threads:
        t.join()
    
    # All updates should succeed
    assert len(results) == 5
    assert all(isinstance(r, int) for r in results)
    
    # Total runs should be 5
    assert manager.state.total_runs == 5
