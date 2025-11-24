# Steam Game Context Integration

## Overview

WishlistOps now fetches detailed game information from Steam to generate better, more contextually-aware announcements. The AI receives information about your game's genre, description, recent news, and more.

## What's New

### Enhanced Steam Client (`wishlistops/steam_client.py`)

Three new methods added:

1. **`get_game_context(app_id)`** - Fetches comprehensive game data:
   - Short description
   - Genres and categories
   - Developers and publishers
   - Release date
   - Recent announcements (for tone consistency)
   - Screenshots

2. **`get_app_news(app_id, count=5)`** - Gets recent Steam announcements

3. **`get_player_summary(steam_id)`** - Gets player profile information

### Enhanced Announcement Generation (`wishlistops/main.py`)

The `_generate_announcement()` method now:
1. Fetches game context from Steam via `_fetch_game_context()`
2. Passes game context to `_build_ai_context()` for richer prompts
3. AI receives game description, genres, and recent announcement style examples

### New Web API Endpoints (`wishlistops/web_server.py`)

1. **`GET /api/steam/games`** - Lists user's owned Steam games
   - Requires: `STEAM_API_KEY` and `STEAM_ID` environment variables
   - Returns games sorted by playtime (developer games first)

2. **`GET /api/steam/game/{app_id}`** - Gets detailed game context
   - Used by dashboard to preview game information
   - Same data the AI receives for announcement generation

## Configuration

### Environment Variables

Add these to your `.env` file or environment:

```bash
# Required for basic functionality
STEAM_API_KEY=your_steam_web_api_key_here

# Optional: For fetching owned games library
STEAM_ID=your_17_digit_steamid64_here
```

### Getting Your Steam Credentials

1. **Steam API Key**: Visit https://steamcommunity.com/dev/apikey
   - Domain name: Use `localhost` for local development
   - Copy the generated key

2. **Steam ID** (optional): Visit https://steamid.io/
   - Enter your Steam profile URL
   - Copy your "steamID64" (17 digits)
   - Example: `76561198012345678`

### Configuration Model

The `SteamConfig` now includes an optional `steam_id` field:

```json
{
  "steam": {
    "app_id": "480",
    "app_name": "Spacewar",
    "steam_id": "76561198012345678"
  }
}
```

## How It Works

### Announcement Generation Flow

1. **Commit Detection**: Git commits parsed as usual
2. **Game Context Fetch**: `_fetch_game_context()` calls Steam API
   - Uses `self.config.steam.app_id`
   - Returns game description, genres, tags, recent news
3. **Enhanced AI Prompt**: `_build_ai_context()` builds prompt including:
   ```
   GAME INFORMATION (from Steam):
   - Name: Your Game Name
   - Description: Game description from Steam
   - Genres: Action, Adventure, Indie
   - Categories: Single-player, Steam Achievements
   - Developers: Your Studio
   
   RECENT ANNOUNCEMENTS (for context):
   - Previous announcement titles for tone consistency
   
   RECENT CHANGES (from commits):
   - [feature] Added new weapon system
   - [bugfix] Fixed inventory bug
   ```
4. **AI Generation**: Google Gemini generates contextually-aware announcement
5. **Quality Filter**: Anti-slop filter validates output
6. **Approval Request**: Sent to Discord as before

### Benefits

- **Better Tone Matching**: AI sees your previous announcements
- **Genre-Appropriate Language**: AI knows if it's Action, RPG, Puzzle, etc.
- **Contextual Relevance**: AI understands what your game is about
- **Consistency**: Announcements align with game's Steam presence

## API Usage Examples

### Fetch Game Library

```javascript
// Get user's owned games
const response = await fetch('/api/steam/games');
const data = await response.json();

console.log(data.games); // Array of games with playtime, icons, etc.
```

### Get Game Context

```javascript
// Get detailed info for specific game
const appId = '480';
const response = await fetch(`/api/steam/game/${appId}`);
const context = await response.json();

console.log(context.description);
console.log(context.genres);
console.log(context.recent_news);
```

## Troubleshooting

### "Steam API key not configured"

- Set `STEAM_API_KEY` environment variable
- Verify key is valid at https://steamcommunity.com/dev/apikey

### "Failed to fetch game context"

- Check `app_id` in `config.json` is correct
- Verify game is published on Steam (not unreleased)
- Check Steam API is responding (rate limits: 100k calls/day)

### "Steam ID not configured"

- Only needed for `/api/steam/games` endpoint
- Set `STEAM_ID` environment variable or add to `config.json`
- Get your Steam ID at https://steamid.io/

## Technical Details

### Steam Web API Rate Limits

- 100,000 requests per day per API key
- WishlistOps typically makes 1-2 requests per announcement
- Safe for dozens of announcements per day

### Caching

Currently, game context is fetched fresh each time. Future enhancement could cache:
- Game descriptions (rarely change)
- Genre/category data (static)
- Recent news (cache for 1 hour)

### Fallback Behavior

If Steam API is unavailable:
- `_fetch_game_context()` returns `None`
- AI still generates announcements using commit data only
- No errors thrown, just warning logged
- Graceful degradation ensures workflow continues

## Future Enhancements

Potential improvements:
1. **Game Selection UI**: Dashboard dropdown to select which game to announce for
2. **Multi-game Support**: Track multiple Steam apps in one config
3. **News Analysis**: AI learns from analyzing past successful announcements
4. **Screenshot Integration**: Auto-fetch latest screenshots from Steam
5. **Player Stats**: Include concurrent player counts in context
6. **Review Sentiment**: Incorporate recent review sentiment into tone

## Related Files

- `wishlistops/steam_client.py` - Steam API integration
- `wishlistops/main.py` - Main orchestration with game context
- `wishlistops/models.py` - Configuration models
- `wishlistops/web_server.py` - Web API endpoints
- `docs/STEAM_API_NOTES.md` - Steam API research notes
