# Steam API Integration Notes

## Important: Steam Posting Limitations

**Steam does NOT provide a public Web API for posting announcements.**

After extensive research of Steam's Partner documentation, we found:

### What Steam's Web API Provides ✅

- `ISteamNews/GetNewsForApp` - **Read** news/announcements (public)
- `ISteamNews/GetNewsForAppAuthed` - **Read** news for unreleased games (partner API)
- Various APIs for game libraries, stats, achievements, etc.

### What Steam's Web API Does NOT Provide ❌

- **No API to CREATE/POST announcements**
- **No API to EDIT announcements**
- **No API to DELETE announcements**

## Available Methods for Posting Announcements

### 1. Steamworks Partner Website (Manual) ⭐ CURRENT METHOD

**URL**: `https://partner.steamgames.com/apps/landing/{APP_ID}`

**Process**:
1. Log in to Steamworks Partner site
2. Navigate to your app
3. Go to "Community" → "Events & Announcements"
4. Create announcement manually
5. Publish or save as "Hidden" for later

**WishlistOps Implementation**:
- We generate the announcement content with AI
- Send to Discord for approval
- Provide direct link to Steamworks
- Developer manually posts (takes ~30 seconds)

### 2. Steamworks SDK (C++ Integration)

**Requirements**:
- Integrate Steamworks SDK into your game
- Use `ISteamRemoteStorage` interface
- Requires game to be running with Steam authentication

**Not Practical Because**:
- Requires C++ integration
- Must run from game executable
- Can't be automated externally
- Python-based tools can't use it

### 3. RSS/XML Feed Import (Limited)

Some developers report Steam can import from RSS feeds, but:
- Not officially documented
- Requires manual setup per app
- Limited formatting options
- Not reliable for automation

## WishlistOps Workflow

Our approach maximizes automation while respecting Steam's limitations:

```
1. Git Commit → GitHub Action Trigger
2. AI generates announcement (title, body, banner)
3. Content filtered for quality
4. Send to Discord with preview
5. Developer reviews in Discord
6. Click "Open Steamworks" button
7. Paste pre-generated content
8. Publish (30 seconds)
```

**Time Saved**: 2-4 hours of writing → 30 seconds of copy-paste

## Steam Partner API Authentication

For partner-only APIs that DO exist:

```python
# Partner API endpoint
base_url = "https://partner.steam-api.com"

# Requires publisher Web API key
# Get from: https://partner.steamgames.com/doc/webapi_overview/auth

headers = {
    "Authorization": f"Bearer {STEAM_PUBLISHER_API_KEY}"
}

params = {
    "key": STEAM_PUBLISHER_API_KEY,
    "appid": APP_ID
}
```

**Note**: Even with partner API key, no announcement posting endpoints exist.

## Alternative: Steam Workshop Integration

If your game has Steam Workshop:
- `IPublishedFileService` - Upload/manage Workshop items
- Could theoretically post "update notes" as Workshop items
- Not the same as game announcements
- Users must subscribe to Workshop item

## Community Requests

Many developers have requested announcement APIs:
- Steamworks Discussions forum has multiple threads
- No official response from Valve
- Likely security/abuse prevention

## Best Practices

### Current Workflow
1. ✅ Use WishlistOps for content generation
2. ✅ Use Discord for approval workflow  
3. ✅ Manual posting on Steamworks (30 sec)
4. ✅ Track state in `state.json`

### Future-Proofing
If Valve ever adds announcement APIs:
- We can add `steam_client.py::post_announcement()`
- Update `main.py` orchestrator
- Remove manual Discord step
- Fully automated end-to-end

## Implementation in `steam_client.py`

Current implementation focuses on:
- ✅ Reading game library (`get_owned_games`)
- ✅ App details (`get_app_details`)
- ✅ Multi-game support (`get_developer_games`)

**Not Implemented** (because it doesn't exist):
- ❌ `post_announcement()` - No API available
- ❌ `edit_announcement()` - No API available
- ❌ `delete_announcement()` - No API available

## Testing the Web Interface

New features added:

### 1. Commit History View (`/commits`)
- Shows all commits with metadata
- Filters: All, Player-Facing, Internal, Has Announcements
- Visual timeline with color coding
- Links announcements to commits

### 2. Test Announcement Page (`/test`)
- Create manual announcements
- Live preview
- Character count warnings
- Send to Discord
- Auto-open Steamworks for publishing

### 3. API Endpoints
- `GET /api/commits` - Commit history with announcement associations
- `POST /api/test-announcement` - Create test announcement

## References

- [Steam Web API Overview](https://partner.steamgames.com/doc/webapi_overview)
- [ISteamNews Interface](https://partner.steamgames.com/doc/webapi/ISteamNews)
- [Steamworks Partner Auth](https://partner.steamgames.com/doc/webapi_overview/auth)
- [Community Event Tools](https://partner.steamgames.com/doc/marketing/event_tools)

---

**Last Updated**: November 24, 2025  
**Status**: No announcement posting API exists. Manual posting required.
