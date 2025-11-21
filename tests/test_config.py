"""
Tests for WishlistOps configuration management.
"""

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from wishlistops.config_manager import ConfigManager, ConfigurationError
from wishlistops.models import (
    Config,
    SteamConfig,
    BrandingConfig,
    VoiceConfig,
    AutomationConfig,
    AIConfig,
    LogoPosition
)


@pytest.fixture
def valid_config_data() -> dict:
    """Create valid configuration data."""
    return {
        "version": "1.0",
        "steam": {
            "app_id": "480",
            "app_name": "Spacewar"
        },
        "branding": {
            "art_style": "retro arcade space shooter with neon aesthetics",
            "color_palette": ["#FF6B6B", "#4ECDC4", "#FFE66D"],
            "logo_position": "top-right",
            "logo_size_percent": 25,
            "logo_path": "wishlistops/assets/logo.png"
        },
        "voice": {
            "tone": "casual and excited",
            "personality": "friendly indie developer",
            "avoid_phrases": ["monetization", "grind", "lootbox"]
        },
        "automation": {
            "enabled": True,
            "trigger_on_tags": True,
            "min_days_between_posts": 7,
            "require_manual_approval": True
        },
        "ai": {
            "model_text": "gemini-1.5-pro",
            "model_image": "gemini-2.5-flash-image",
            "temperature": 0.7,
            "max_retries": 3
        }
    }


@pytest.fixture
def valid_config_file(tmp_path: Path, valid_config_data: dict) -> Path:
    """Create a valid config file."""
    config_file = tmp_path / "config.json"
    with open(config_file, 'w') as f:
        json.dump(valid_config_data, f)
    return config_file


class TestSteamConfig:
    """Tests for SteamConfig model."""
    
    def test_valid_steam_config(self):
        """Test that valid Steam config is accepted."""
        config = SteamConfig(app_id="480", app_name="Spacewar")
        assert config.app_id == "480"
        assert config.app_name == "Spacewar"
    
    def test_invalid_app_id_non_numeric(self):
        """Test that non-numeric app_id is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            SteamConfig(app_id="abc123", app_name="Test")
        assert "must be numeric" in str(exc_info.value).lower() or "should match pattern" in str(exc_info.value).lower()
    
    def test_invalid_app_id_too_short(self):
        """Test that app_id with less than 3 digits is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            SteamConfig(app_id="12", app_name="Test")
        assert "too short" in str(exc_info.value).lower() or "should match pattern" in str(exc_info.value).lower()
    
    def test_empty_app_name(self):
        """Test that empty app_name is rejected."""
        with pytest.raises(ValidationError):
            SteamConfig(app_id="480", app_name="")


class TestBrandingConfig:
    """Tests for BrandingConfig model."""
    
    def test_valid_branding_config(self):
        """Test that valid branding config is accepted."""
        config = BrandingConfig(
            art_style="pixel art fantasy style",
            color_palette=["#FF6B6B", "#4ECDC4"],
            logo_position=LogoPosition.TOP_RIGHT
        )
        assert config.art_style == "pixel art fantasy style"
        assert len(config.color_palette) == 2
        assert config.logo_position == LogoPosition.TOP_RIGHT
    
    def test_art_style_too_short(self):
        """Test that art_style with less than 10 characters is rejected."""
        with pytest.raises(ValidationError):
            BrandingConfig(
                art_style="short",
                color_palette=[]
            )
    
    def test_invalid_hex_color_missing_hash(self):
        """Test that color without # is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            BrandingConfig(
                art_style="pixel art style description",
                color_palette=["FF6B6B"]
            )
        assert "must start with #" in str(exc_info.value)
    
    def test_invalid_hex_color_wrong_length(self):
        """Test that color with wrong length is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            BrandingConfig(
                art_style="pixel art style description",
                color_palette=["#FF6"]
            )
        assert "7 characters" in str(exc_info.value)
    
    def test_invalid_hex_color_non_hex_chars(self):
        """Test that color with non-hex characters is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            BrandingConfig(
                art_style="pixel art style description",
                color_palette=["#GGGGGG"]
            )
        assert "invalid hex color" in str(exc_info.value).lower()
    
    def test_valid_hex_colors(self):
        """Test that valid hex colors are accepted."""
        config = BrandingConfig(
            art_style="pixel art style description",
            color_palette=["#FF6B6B", "#4ECDC4", "#FFE66D"]
        )
        assert len(config.color_palette) == 3
    
    def test_empty_color_palette_is_valid(self):
        """Test that empty color palette is allowed."""
        config = BrandingConfig(
            art_style="pixel art style description",
            color_palette=[]
        )
        assert config.color_palette == []
    
    def test_logo_size_percent_validation(self):
        """Test that logo size percent is validated."""
        # Valid range
        config = BrandingConfig(
            art_style="pixel art style",
            logo_size_percent=25
        )
        assert config.logo_size_percent == 25
        
        # Too small
        with pytest.raises(ValidationError):
            BrandingConfig(
                art_style="pixel art style",
                logo_size_percent=5
            )
        
        # Too large
        with pytest.raises(ValidationError):
            BrandingConfig(
                art_style="pixel art style",
                logo_size_percent=60
            )


class TestVoiceConfig:
    """Tests for VoiceConfig model."""
    
    def test_default_voice_config(self):
        """Test that VoiceConfig has sensible defaults."""
        config = VoiceConfig()
        assert config.tone == "casual and excited"
        assert config.personality == "friendly indie developer"
        assert "lootbox" in config.avoid_phrases
    
    def test_avoid_phrases_lowercased(self):
        """Test that avoid phrases are converted to lowercase."""
        config = VoiceConfig(avoid_phrases=["DELVE", "Leverage", "PaRaDiGm"])
        assert all(phrase.islower() for phrase in config.avoid_phrases)
    
    def test_custom_voice_config(self):
        """Test that custom voice config is accepted."""
        config = VoiceConfig(
            tone="professional",
            personality="veteran game designer",
            avoid_phrases=["buzzword1", "buzzword2"]
        )
        assert config.tone == "professional"
        assert config.personality == "veteran game designer"
        assert len(config.avoid_phrases) == 2


class TestAutomationConfig:
    """Tests for AutomationConfig model."""
    
    def test_default_automation_config(self):
        """Test that AutomationConfig has sensible defaults."""
        config = AutomationConfig()
        assert config.enabled is True
        assert config.trigger_on_tags is True
        assert config.min_days_between_posts == 7
        assert config.require_manual_approval is True
    
    def test_min_days_validation(self):
        """Test that min_days_between_posts is validated."""
        # Valid
        config = AutomationConfig(min_days_between_posts=14)
        assert config.min_days_between_posts == 14
        
        # Too small
        with pytest.raises(ValidationError):
            AutomationConfig(min_days_between_posts=0)
        
        # Too large
        with pytest.raises(ValidationError):
            AutomationConfig(min_days_between_posts=400)


class TestAIConfig:
    """Tests for AIConfig model."""
    
    def test_default_ai_config(self):
        """Test that AIConfig has sensible defaults."""
        config = AIConfig()
        assert config.model_text == "gemini-1.5-pro"
        assert config.model_image == "gemini-2.5-flash-image"
        assert config.temperature == 0.7
        assert config.max_retries == 3
    
    def test_temperature_validation(self):
        """Test that temperature is validated."""
        # Valid
        config = AIConfig(temperature=0.5)
        assert config.temperature == 0.5
        
        # Too low
        with pytest.raises(ValidationError):
            AIConfig(temperature=-0.1)
        
        # Too high
        with pytest.raises(ValidationError):
            AIConfig(temperature=2.1)


class TestConfig:
    """Tests for main Config model."""
    
    def test_valid_config(self, valid_config_data: dict):
        """Test that valid config loads successfully."""
        config = Config(**valid_config_data)
        assert config.version == "1.0"
        assert config.steam.app_id == "480"
        assert config.steam.app_name == "Spacewar"
        assert config.branding is not None
        assert config.voice is not None
        assert config.automation is not None
        assert config.ai is not None
    
    def test_config_with_secrets(self, valid_config_data: dict):
        """Test that secrets can be added to config."""
        valid_config_data['steam_api_key'] = 'test-steam-key'
        valid_config_data['google_ai_key'] = 'test-google-key'
        valid_config_data['discord_webhook_url'] = 'https://discord.com/api/webhooks/123/abc'
        
        config = Config(**valid_config_data)
        assert config.steam_api_key == 'test-steam-key'
        assert config.google_ai_key == 'test-google-key'
        assert config.discord_webhook_url == 'https://discord.com/api/webhooks/123/abc'
    
    def test_config_defaults(self, valid_config_data: dict):
        """Test that config sections have defaults."""
        # Remove optional sections
        del valid_config_data['voice']
        del valid_config_data['automation']
        del valid_config_data['ai']
        
        config = Config(**valid_config_data)
        assert config.voice is not None
        assert config.automation is not None
        assert config.ai is not None


class TestConfigManager:
    """Tests for ConfigManager class."""
    
    def test_load_valid_config(self, valid_config_file: Path):
        """Test that ConfigManager loads valid config successfully."""
        # Set environment variables
        with patch.dict(os.environ, {
            'STEAM_API_KEY': 'test-steam-key',
            'GOOGLE_AI_KEY': 'test-google-key-1234567890',
            'DISCORD_WEBHOOK_URL': 'https://discord.com/api/webhooks/123/abc'
        }):
            config = ConfigManager.load_config(valid_config_file)
            assert config.steam.app_id == "480"
            assert config.google_ai_key == 'test-google-key-1234567890'
    
    def test_load_nonexistent_file(self, tmp_path: Path):
        """Test that loading nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError) as exc_info:
            ConfigManager.load_config(tmp_path / "nonexistent.json")
        assert "not found" in str(exc_info.value).lower()
    
    def test_load_invalid_json(self, tmp_path: Path):
        """Test that loading invalid JSON raises ConfigurationError."""
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("{invalid json}")
        
        with pytest.raises(ConfigurationError) as exc_info:
            ConfigManager.load_config(invalid_file)
        assert "json syntax" in str(exc_info.value).lower()
    
    def test_load_invalid_config_data(self, tmp_path: Path):
        """Test that loading invalid config data raises ConfigurationError."""
        invalid_config = tmp_path / "invalid_config.json"
        with open(invalid_config, 'w') as f:
            json.dump({
                "version": "1.0",
                "steam": {
                    "app_id": "abc",  # Invalid: non-numeric
                    "app_name": "Test"
                },
                "branding": {
                    "art_style": "test style here for validation"
                }
            }, f)
        
        with patch.dict(os.environ, {
            'GOOGLE_AI_KEY': 'test-key-1234567890',
            'DISCORD_WEBHOOK_URL': 'https://discord.com/api/webhooks/123/abc'
        }):
            with pytest.raises(ConfigurationError):
                ConfigManager.load_config(invalid_config)
    
    def test_missing_required_secrets(self, valid_config_file: Path):
        """Test that missing required secrets raises ConfigurationError."""
        # Clear environment variables
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ConfigurationError) as exc_info:
                ConfigManager.load_config(valid_config_file)
            assert "missing required environment variables" in str(exc_info.value).lower()
    
    def test_create_default_config(self, tmp_path: Path):
        """Test that default config can be created."""
        config_path = tmp_path / "new_config.json"
        ConfigManager.create_default_config(config_path)
        
        assert config_path.exists()
        
        # Verify it's valid JSON
        with open(config_path) as f:
            data = json.load(f)
        
        assert "version" in data
        assert "steam" in data
        assert "branding" in data
    
    def test_environment_variables_override(self, valid_config_file: Path):
        """Test that environment variables override JSON values."""
        with patch.dict(os.environ, {
            'STEAM_API_KEY': 'env-steam-key',
            'GOOGLE_AI_KEY': 'env-google-key-1234567890',
            'DISCORD_WEBHOOK_URL': 'https://discord.com/api/webhooks/999/xyz'
        }):
            config = ConfigManager.load_config(valid_config_file)
            assert config.steam_api_key == 'env-steam-key'
            assert config.google_ai_key == 'env-google-key-1234567890'
            assert config.discord_webhook_url == 'https://discord.com/api/webhooks/999/xyz'
    
    def test_load_config_convenience_function(self, valid_config_file: Path):
        """Test that convenience load_config function works."""
        from wishlistops.config_manager import load_config
        
        with patch.dict(os.environ, {
            'STEAM_API_KEY': 'test-key',
            'GOOGLE_AI_KEY': 'test-key-1234567890',
            'DISCORD_WEBHOOK_URL': 'https://discord.com/api/webhooks/123/abc'
        }):
            config = load_config(valid_config_file)
            assert config is not None
            assert isinstance(config, Config)


class TestConfigManagerCLI:
    """Tests for ConfigManager CLI functionality."""
    
    def test_cli_create_default(self, tmp_path: Path, capsys):
        """Test CLI can create default config."""
        import sys
        from wishlistops.config_manager import ConfigManager
        
        config_path = tmp_path / "cli_config.json"
        ConfigManager.create_default_config(config_path)
        
        captured = capsys.readouterr()
        assert "created" in captured.out.lower()
        assert config_path.exists()
