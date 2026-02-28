# WishlistOps AI Coding Agent Instructions

## Project Overview
WishlistOps is an AI co-pilot for Steam game marketing that transforms Git commits into Steam announcements. **Critical distinction**: This tool does NOT generate images with AI - it only enhances user-provided screenshots. All images (logos, screenshots) must be provided by users.

## Architecture

### Core Workflow (See [main.py](../wishlistops/main.py))
The `WishlistOpsOrchestrator` coordinates a 7-step async workflow:
1. Rate limit check via `StateManager`
2. Parse Git commits (player-facing only) via `GitParser`
3. Generate announcement text via `AIClient` (Google Gemini)
4. Filter content quality via `ContentFilter` (anti-slop)
5. Composite logo onto screenshots via `ImageCompositor`
6. Send to Discord for approval via `DiscordNotifier`
7. Update state for next run

**Key architectural decision**: Human-in-the-loop via Discord approval (Steam has no public API for posting).

### Component Boundaries
- **wishlistops/**: Core Python package with all business logic
- **dashboard/**: Static HTML/CSS web interface (no backend server yet)
- **tests/**: Pytest-based unit tests with comprehensive mocking
- **marketing-agent/**: Separate component (not yet implemented)

### Data Flow
`Git commits` → `GitParser` → `AIClient` → `ContentFilter` → `ImageCompositor` → `DiscordNotifier` → Human approval

## Development Workflows

### Running the Application
```bash
# Standard run (reads wishlistops/config.json by default)
python -m wishlistops.main

# With custom config
python -m wishlistops.main --config path/to/config.json

# Dry run (skips all API calls)
python -m wishlistops.main --dry-run --verbose
```

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_main.py

# Run with coverage
pytest --cov=wishlistops --cov-report=html
```

**Testing pattern**: All tests use `pytest` fixtures with extensive mocking (`unittest.mock.AsyncMock`). See [test_main.py](../tests/test_main.py) for patterns - tests mock `GitParser`, `AIClient`, etc. to avoid external dependencies.

### Configuration
Configuration lives in [wishlistops/config.json](../wishlistops/config.json). Key sections:
- `steam`: App ID and name (required)
- `branding`: Art style, logo paths, positioning (optional - enables image features)
- `voice`: Tone, personality, avoid_phrases (anti-slop)
- `automation`: Rate limits, commit thresholds, manual approval
- `ai`: Model selection (gemini-1.5-pro for text), temperature

**Environment variables override**: `GOOGLE_AI_KEY`, `DISCORD_WEBHOOK_URL`, `STEAM_API_KEY` (optional)

## Project-Specific Conventions

### Models (Pydantic V2)
All data models in [models.py](../wishlistops/models.py) use Pydantic V2 with `model_config = ConfigDict(extra='forbid')` to prevent typos. Custom validators use `@field_validator` decorator.

**Pattern**: Enums for constants (`CommitType`, `WorkflowStatus`, `LogoPosition`)

### Error Handling
- Custom exceptions inherit from base class: `WorkflowError`, `AIError`, `ConfigurationError`
- All async operations wrapped in try/except with structured logging
- Non-critical failures (e.g., content filter) continue with degraded functionality
- Critical failures (e.g., Git parsing) raise `WorkflowError` and send Discord error notification

### Logging
Structured JSON logging throughout:
```python
logger.info("Message", extra={"key": "value", "count": 42})
```
Output format: `{"timestamp":"...", "level":"INFO", "module":"...", "message":"..."}`

### Async Patterns
- `AIClient` requires async context manager: `async with self.ai:`
- All API calls use `aiohttp.ClientSession` with exponential backoff (tenacity)
- Main orchestrator runs via `asyncio.run(orch.run())`

### Git Commit Classification
[git_parser.py](../wishlistops/git_parser.py) filters commits using:
- **Conventional commits**: `feat:`, `fix:` = player-facing; `chore:`, `refactor:` = internal
- **Keywords**: "add feature", "fix bug" = player-facing; "refactor", "cleanup" = internal
- **Screenshot directive**: `[shot: path/to/image.png]` in commit message links screenshot

**Only player-facing commits** trigger announcements.

### Anti-Slop Filter
[content_filter.py](../wishlistops/content_filter.py) detects AI buzzwords:
- Built-in patterns: "delve", "tapestry", "leverage", "synergy", "robust"
- User-defined in `voice.avoid_phrases` config
- If issues found, regenerates content with stricter prompt (lower temperature)

### State Management
[state_manager.py](../wishlistops/state_manager.py) persists `state.json` with:
- Last run timestamp (for rate limiting)
- Last Git tag processed
- Post history (prevents duplicate announcements)

**No database** - simple JSON file persistence.

## Integration Points

### External APIs
1. **Google Gemini**: Text generation only (models: `gemini-1.5-pro`, `gemini-2.5-flash-image`)
   - Requires API key from https://aistudio.google.com/app/apikey
   - Rate limiting handled by tenacity with exponential backoff
2. **Discord Webhooks**: One-way notification system (no responses parsed)
3. **Steam Web API**: Optional context fetching (requires `steam_api_key`)

### Image Processing
- **Pillow**: Core image operations (crop, resize, composite)
- **RealESRGAN** (optional): AI upscaling via `wishlistops[image-enhancement]` (~3GB)
  - Check availability: `check_optional_dependencies()` in [main.py](../wishlistops/main.py)

### Dependencies
Lightweight core (~100MB). See [requirements.txt](../requirements.txt):
- `google-generativeai` for Gemini
- `GitPython` for Git operations
- `Pillow` for image processing (no ML deps in base install)
- `pydantic>=2.5.0` for validation
- `aiohttp` for async HTTP

## Common Pitfalls

1. **Repo root detection**: `GitParser` needs repo root, not config directory. See [main.py:134-147](../wishlistops/main.py#L134-L147) for fallback logic.

2. **AIClient context manager**: Must use `async with self.ai:` or get "Client not initialized" error.

3. **Branding is optional**: Check `if self.config.branding and self.compositor:` before image operations.

4. **Dry run mode**: Pass `--dry-run` to skip API calls. Mock return values in orchestrator methods.

5. **JSON response parsing**: Gemini returns varied formats. See `_parse_text_response()` in [ai_client.py](../wishlistops/ai_client.py) for robust parsing logic.

## File Locations

- Main orchestrator: [wishlistops/main.py](../wishlistops/main.py)
- Data models: [wishlistops/models.py](../wishlistops/models.py)
- Configuration: [wishlistops/config.json](../wishlistops/config.json) (sample), `config_manager.py` (loader)
- Tests: [tests/test_*.py](../tests/) (pytest with fixtures)
- Web dashboard: [dashboard/index.html](../dashboard/index.html) (static only)
