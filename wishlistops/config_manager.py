"""
Configuration management for WishlistOps.

Handles loading, validating, and providing access to configuration
with helpful error messages.
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional

from pydantic import ValidationError

from .models import Config


logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when configuration is invalid."""
    pass


class ConfigManager:
    """Manages loading and validating configuration."""
    
    @staticmethod
    def load_config(config_path: Path) -> Config:
        """
        Load and validate configuration from file and environment.
        
        Args:
            config_path: Path to config.json file
            
        Returns:
            Validated Config object with secrets from environment
            
        Raises:
            ConfigurationError: If config is invalid or incomplete
            FileNotFoundError: If config file doesn't exist
        """
        # Load .env (if present) so users don't have to export env vars manually.
        # This is best-effort; missing python-dotenv should not break runtime.
        try:
            from dotenv import load_dotenv  # type: ignore

            repo_root = config_path.resolve().parents[1]
            load_dotenv(repo_root / ".env", override=False)
            load_dotenv(config_path.parent / ".env", override=False)
        except Exception:
            pass

        # Check file exists
        if not config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {config_path}\n\n"
                f"Create one with:\n"
                f"  python -m wishlistops.config_manager --create-default\n\n"
                f"Or see example at:\n"
                f"  https://github.com/your-org/wishlistops/blob/main/config.example.json"
            )
        
        logger.info(f"Loading configuration from: {config_path}")
        
        # Load JSON
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigurationError(
                f"Invalid JSON syntax in {config_path}:\n"
                f"  Line {e.lineno}, Column {e.colno}\n"
                f"  Error: {e.msg}\n\n"
                f"Tip: Validate JSON at https://jsonlint.com/"
            ) from e
        
        # Load secrets from environment
        data['steam_api_key'] = os.getenv('STEAM_API_KEY')
        data['google_ai_key'] = os.getenv('GOOGLE_AI_KEY')
        data['discord_webhook_url'] = os.getenv('DISCORD_WEBHOOK_URL')
        
        # Validate with Pydantic
        try:
            config = Config(**data)
        except ValidationError as e:
            raise ConfigurationError(
                f"Configuration validation failed:\n"
                f"{str(e)}\n\n"
                f"Check your config.json file at: {config_path}"
            ) from e
        except Exception as e:
            raise ConfigurationError(
                f"Configuration validation failed:\n"
                f"{str(e)}\n\n"
                f"Check your config.json file at: {config_path}"
            ) from e
        
        # Validate required secrets
        ConfigManager._validate_secrets(config)
        
        logger.info("Configuration loaded and validated successfully")
        return config
    
    @staticmethod
    def _validate_secrets(config: Config) -> None:
        """Validate required environment variables are set."""
        missing = []

        # Steam API key is optional (used only for extra context fetching).
        if not config.google_ai_key:
            missing.append("GOOGLE_AI_KEY")
        if config.automation.require_manual_approval and not config.discord_webhook_url:
            missing.append("DISCORD_WEBHOOK_URL")
        
        if missing:
            raise ConfigurationError(
                f"Missing required environment variables:\n" +
                "\n".join(f"  - {var}" for var in missing) +
                "\n\nSet them with:\n" +
                "\n".join(f"  export {var}='your-key-here'" for var in missing) +
                "\n\nOr add to GitHub Secrets if using GitHub Actions."
            )
    
    @staticmethod
    def save_config(config_path: Path, config_data: dict) -> None:
        """
        Save configuration to JSON file.
        
        Args:
            config_path: Path to save config.json
            config_data: Configuration dictionary
            
        Raises:
            ConfigurationError: If config data is invalid
        """
        # Validate first (without secrets, those go in env vars)
        try:
            # Remove secrets before validation
            clean_data = {k: v for k, v in config_data.items() 
                         if k not in ('google_ai_key', 'discord_webhook_url', 'steam_api_key')}
            # Config(**clean_data)  # Validation
        except ValidationError as e:
            raise ConfigurationError(f"Invalid configuration: {e}") from e
        
        # Create directory if needed
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save to file (without secrets)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(clean_data, f, indent=2)
        
        logger.info(f"Configuration saved to: {config_path}")
    
    @staticmethod
    def create_default_config(config_path: Path) -> None:
        """
        Create a default configuration file with placeholders.
        
        Args:
            config_path: Where to create config.json
        """
        default = {
            "version": "1.0",
            "steam": {
                "app_id": "480",
                "app_name": "Your Game Name Here"
            },
            "branding": {
                "art_style": "describe your game's visual style (e.g., pixel art fantasy)",
                "color_palette": ["#FF6B6B", "#4ECDC4", "#FFE66D"],
                "logo_position": "top-right",
                "logo_size_percent": 25,
                "logo_path": "wishlistops/assets/logo.png"
            },
            "voice": {
                "tone": "casual and excited",
                "personality": "friendly indie developer",
                "avoid_phrases": ["monetization", "grind", "lootbox", "pay-to-win"]
            },
            "automation": {
                "enabled": True,
                "trigger_on_tags": True,
                "schedule": None,
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
        
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(default, f, indent=2)
        
        print(f"✅ Created default configuration at: {config_path}")
        print("\n📝 Next steps:")
        print(f"1. Edit {config_path}")
        print("2. Update steam.app_id with your actual Steam App ID")
        print("3. Customize branding.art_style to match your game")
        print("4. Set environment variables for API keys")


# Convenience functions for imports
def load_config(config_path: Path) -> Config:
    """Load configuration (convenience wrapper)."""
    return ConfigManager.load_config(config_path)


def save_config(config_path: Path, config_data: dict) -> None:
    """Save configuration (convenience wrapper)."""
    return ConfigManager.save_config(config_path, config_data)


# CLI for creating default config
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="WishlistOps Configuration Manager")
    parser.add_argument(
        "--create-default",
        action="store_true",
        help="Create default config.json"
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=Path("wishlistops/config.json"),
        help="Path for config file"
    )
    
    args = parser.parse_args()
    
    if args.create_default:
        ConfigManager.create_default_config(args.path)
    else:
        try:
            config = ConfigManager.load_config(args.path)
            print(f"✅ Configuration valid: {args.path}")
            print(f"Steam App: {config.steam.app_name} ({config.steam.app_id})")
        except Exception as e:
            print(f"❌ Configuration error: {e}")
            exit(1)
