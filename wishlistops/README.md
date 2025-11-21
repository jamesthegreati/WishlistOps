# WishlistOps Python Package

This directory contains the main Python package for WishlistOps automation.

## Structure

```
wishlistops/
├── __init__.py              # Package initialization
├── main.py                  # Main orchestrator (COMPLETED)
├── models.py                # Pydantic data models (COMPLETED)
├── config_manager.py        # Configuration loader (COMPLETED)
├── git_parser.py            # Git operations (STUB)
├── ai_client.py             # Google Gemini API (STUB)
├── content_filter.py        # Anti-slop filter (COMPLETED)
├── image_compositor.py      # Logo compositing (STUB)
├── discord_notifier.py      # Discord webhooks (STUB)
├── state_manager.py         # State persistence (COMPLETED)
└── config.json              # Sample configuration
```

## Completion Status

### ✅ Completed Components

1. **main.py** - Main orchestrator with complete workflow
   - All methods implemented with type hints
   - Comprehensive error handling
   - Structured logging throughout
   - CLI argument parsing
   - Async/await workflow

2. **models.py** - Pydantic data models
   - Config, WorkflowState, AnnouncementDraft
   - Commit, BrandingConfig, VoiceConfig
   - Full validation with field validators
   - Type-safe throughout

3. **config_manager.py** - Configuration management
   - JSON file loading
   - Environment variable overrides
   - Pydantic validation

4. **content_filter.py** - Quality filtering
   - Anti-slop phrase detection
   - Length validation
   - Quality checks

5. **state_manager.py** - State persistence
   - JSON-based state storage
   - Run tracking
   - Post history

### 🚧 Stub Components (To Be Implemented)

These components have proper structure but need implementation:

1. **git_parser.py** - Needs actual Git log parsing
2. **ai_client.py** - Needs Gemini API integration
3. **image_compositor.py** - Needs Pillow-based compositing
4. **discord_notifier.py** - Needs webhook HTTP calls

## Usage

### Running the CLI

```bash
# Basic run
python -m wishlistops.main --config wishlistops/config.json

# Dry run (no API calls)
python -m wishlistops.main --config wishlistops/config.json --dry-run

# Verbose logging
python -m wishlistops.main --config wishlistops/config.json --verbose
```

### Using as a Library

```python
from pathlib import Path
from wishlistops.main import WishlistOpsOrchestrator

# Initialize
orch = WishlistOpsOrchestrator(
    config_path=Path("wishlistops/config.json"),
    dry_run=False
)

# Run workflow
import asyncio
result = asyncio.run(orch.run())

print(f"Status: {result.status}")
if result.draft:
    print(f"Title: {result.draft.title}")
```

## Configuration

Configuration is loaded from `config.json` with environment variable overrides:

### Required Environment Variables

```bash
export GOOGLE_AI_KEY="your-google-ai-api-key"
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
```

### Config File Structure

See `config.json` for a complete example. Key sections:

- `steam_app_id`, `steam_app_name` - Steam game info
- `branding` - Visual identity (colors, logo, art style)
- `voice` - Writing style and tone
- `automation` - Trigger rules and rate limits
- `ai` - AI model settings

## Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=wishlistops --cov-report=html

# Run specific test file
pytest tests/test_main.py -v
```

## Quality Checks

```bash
# Type checking
mypy wishlistops/ --strict

# Linting
pylint wishlistops/

# Formatting
black wishlistops/
isort wishlistops/
```

## Next Steps

To complete the implementation:

1. Implement `git_parser.py` - Parse Git commits with GitPython
2. Implement `ai_client.py` - Integrate Google Gemini API
3. Implement `image_compositor.py` - Add logo overlay with Pillow
4. Implement `discord_notifier.py` - Send webhook messages with aiohttp

See `BUILD_PLAN_Week1_Critical_Features.md` for detailed implementation guides.
