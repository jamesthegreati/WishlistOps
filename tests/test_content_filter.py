import pytest
from wishlistops.content_filter import ContentFilter, FilterResult
from wishlistops.models import VoiceConfig


def test_filter_initialization():
    """Test filter can be initialized."""
    filter = ContentFilter()
    assert filter is not None


def test_detect_ai_slop():
    """Test detection of AI buzzwords."""
    filter = ContentFilter()
    
    bad_text = "Let's delve into the robust tapestry of our game's synergy."
    result = filter.check(bad_text)
    
    assert result.passed is False
    assert len(result.issues) > 0
    assert any("slop" in issue.lower() for issue in result.issues)


def test_detect_marketing_speak():
    """Test detection of marketing buzzwords."""
    filter = ContentFilter()
    
    bad_text = "Experience an immersive experience with cutting-edge graphics."
    result = filter.check(bad_text)
    
    assert result.passed is False
    assert any("marketing" in issue.lower() for issue in result.issues)


def test_good_content_passes():
    """Test that good indie dev language passes."""
    filter = ContentFilter()
    
    good_text = (
        "We fixed the boss AI bug that caused softlocks in the final level. "
        "The update also includes a new double-jump mechanic and improved "
        "the framerate in the forest level from 45fps to 60fps. Thanks for your feedback! "
        "This makes combat feel way more responsive and the movement "
        "is now super smooth. Additionally, we fixed several minor crashes that "
        "happened during the cutscenes. The new feature allows players to "
        "chain combos more easily and dodge attacks with better timing windows."
    )
    result = filter.check(good_text)
    
    assert result.passed is True
    assert len(result.issues) == 0
    assert result.score > 0.8


def test_too_short_fails():
    """Test that too-short content fails."""
    filter = ContentFilter()
    
    short_text = "We updated the game."
    result = filter.check(short_text)
    
    assert result.passed is False
    assert any("short" in issue.lower() for issue in result.issues)


def test_repetition_detected():
    """Test that repetition is detected."""
    filter = ContentFilter()
    
    repetitive_text = (
        "We improved the game. The game is better now. "
        "The game has new features. The game is more fun. " * 3
    )
    result = filter.check(repetitive_text)
    
    assert result.passed is False
    assert any("repeat" in issue.lower() for issue in result.issues)


def test_custom_avoid_phrases():
    """Test user-defined avoid phrases."""
    voice_config = VoiceConfig(avoid_phrases=["monetization", "lootbox"])
    filter = ContentFilter(voice_config)
    
    bad_text = (
        "We added new monetization options with lootbox mechanics "
        "to improve player engagement and retention metrics."
    )
    result = filter.check(bad_text)
    
    assert result.passed is False
    assert any("monetization" in issue.lower() for issue in result.issues)
    assert any("lootbox" in issue.lower() for issue in result.issues)


def test_formal_tone_detected():
    """Test overly formal tone is detected."""
    filter = ContentFilter()
    
    formal_text = (
        "We are pleased to announce that pursuant to user feedback, "
        "we have subsequently implemented improvements. Furthermore, "
        "we would like to express our gratitude."
    )
    result = filter.check(formal_text)
    
    assert result.passed is False
    assert any("formal" in issue.lower() for issue in result.issues)


def test_suggest_improvements():
    """Test improvement suggestions are generated."""
    filter = ContentFilter()
    
    bad_text = "Let's delve into our robust solution."
    result = filter.check(bad_text)
    
    suggestions = filter.suggest_improvements(bad_text, result.issues)
    assert len(suggestions) > 0
    assert "buzzword" in suggestions.lower() or "concrete" in suggestions.lower()


def test_regeneration_prompt():
    """Test regeneration prompt is created."""
    filter = ContentFilter()
    
    bad_text = "Delve into the tapestry"
    issues = ["AI slop detected: 'delve'", "AI slop detected: 'tapestry'"]
    
    prompt = filter.generate_regeneration_prompt(bad_text, issues)
    
    assert "delve" in prompt.lower()
    assert "tapestry" in prompt.lower()
    assert "rewrite" in prompt.lower()
