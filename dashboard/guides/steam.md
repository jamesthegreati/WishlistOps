# Steam Web API Setup Guide

Get your Steam Web API key to integrate with Steamworks.

---

## Prerequisites

- Steam account
- Published or upcoming Steam game (with App ID)
- 5 minutes

---

## Step-by-Step Instructions

### 1. Navigate to Steam Web API Key Page

**URL**: [https://steamcommunity.com/dev/apikey](https://steamcommunity.com/dev/apikey)

Open this page in your browser.

---

### 2. Sign In to Steam

If not already signed in, click "Sign in through Steam" and log in with your Steam account.

---

### 3. Register Your Domain

1. You'll see a form titled "Register for a new Steam Web API Key"
2. **Domain Name**: Enter `localhost` (for local development)
   - For production, use your actual domain (e.g., `yourgame.com`)
3. **Agree to Terms**: Check the box to agree to Steam Web API Terms of Use
4. Click **"Register"**

**Note**: You can have only ONE API key per Steam account. If you already have a key, it will be displayed.

---

### 4. Copy Your API Key

1. Your API key appears on the page after registration
2. It's a 32-character hexadecimal string
3. Click to select and copy the key

**API Key Format**: `1234567890ABCDEF1234567890ABCDEF` (32 hex characters)

---

### 5. Find Your Steam ID

You'll also need your Steam ID (64-bit):

#### Method 1: Steam Profile URL
1. Go to your Steam profile
2. If you have a custom URL: `steamcommunity.com/id/yourname`
   - Click "Edit Profile" → Look for the numeric ID in the URL
3. If you have a numeric URL: `steamcommunity.com/profiles/76561198012345678`
   - The number after `/profiles/` is your Steam ID

#### Method 2: Use steamidfinder.com
1. Visit [https://steamidfinder.com](https://steamidfinder.com)
2. Enter your Steam profile URL or username
3. Copy the **steamID64** value

**Steam ID Format**: `76561198...` (17 digits)

---

### 6. Add to WishlistOps

#### Option A: Web Interface (Recommended)

1. In WishlistOps setup wizard:
   - Paste API key into "Steam Web API Key" field
   - Paste Steam ID into "Steam ID" field
2. Click "Detect Games"
3. You should see your Steam library! ✅

#### Option B: Environment Variable

Add to your `.env` file:
```bash
STEAM_API_KEY=1234567890ABCDEF...
STEAM_ID=76561198...
```

Or set as environment variables:
```bash
# Windows (PowerShell)
$env:STEAM_API_KEY="1234567890ABCDEF..."
$env:STEAM_ID="76561198..."

# Windows (CMD)
set STEAM_API_KEY=1234567890ABCDEF...
set STEAM_ID=76561198...

# Linux/Mac
export STEAM_API_KEY="1234567890ABCDEF..."
export STEAM_ID="76561198..."
```

---

## Get Your Steam App ID

For WishlistOps to post announcements, you need your game's Steam App ID:

### Method 1: Steamworks Partner Portal
1. Go to [https://partner.steamgames.com](https://partner.steamgames.com)
2. Click on your game
3. The App ID is shown at the top (e.g., "App ID: 480")

### Method 2: Steam Store Page
1. Visit your game's Steam store page
2. Look at the URL: `store.steampowered.com/app/123456/YourGame`
3. The number after `/app/` is your App ID

**Add to `wishlistops/config.json`**:
```json
{
  "steam": {
    "app_id": "123456",
    "app_name": "Your Game Name"
  }
}
```

---

## Rate Limits

Steam Web API has generous rate limits:
- **100,000 requests per day** per API key
- No per-minute restrictions

**WishlistOps typically uses**: 1-5 requests per week (far below limits!)

---

## What APIs WishlistOps Uses

WishlistOps calls these Steam Web API endpoints:

1. **IPlayerService/GetOwnedGames** - Fetch your game library
2. **ISteamNews/PostNewsItem** - Post announcements (via Steamworks)
3. **ISteamApps/GetAppDetails** - Get game information

All calls are read-only except for posting announcements (which requires your approval).

---

## Security Best Practices

### ✅ DO:
- Keep API key secret
- Use environment variables
- Regenerate if exposed
- Use separate keys for dev/production (if possible)

### ❌ DON'T:
- Commit API key to  Git repositories
- Share key publicly
- Hardcode in source code
- Use for commercial API reselling

---

## Troubleshooting

### "Invalid API Key"

**Cause**: Key was typed incorrectly or revoked

**Solution**:
1. Double-check the key (should be 32 hex characters)
2. Ensure no extra spaces
3. Visit [steamcommunity.com/dev/apikey](https://steamcommunity.com/dev/apikey) to verify
4. Regenerate key if needed (revokes old key!)

---

### "Access Denied"

**Cause**: Privacy settings or incorrect Steam ID

**Solutions**:
1. Make sure your Steam profile is public:
   - Profile → Edit Profile → Privacy Settings → "My Profile" = Public
2. Verify Steam ID is correct (17 digits)
3. Check that you're using Steam ID64 format

---

### "Game not found"

**Cause**: App ID is incorrect or game not published

**Solutions**:
1. Verify App ID from Steamworks Partner dashboard
2. Ensure game is at least in "Coming Soon" state
3. Check that you're logged in to the correct Steam account

---

###  "Rate limit exceeded"

**Cause**: Too many API calls (rare with WishlistOps)

**Solutions**:
1. Wait 24 hours for quota reset
2. Check if other tools are using your API key
3. Contact Steam support if issue persists

---

## Steamworks Integration

For posting announcements, you'll also need Steamworks Web API access:

1. **Steamworks Account**: Required to publish games
2. **App Configuration**: Set up in Partner dashboard
3. **Permissions**: Ensure your account has "Edit App Metadata" permission

WishlistOps uses the Steam Web API for reading data and Steamworks API for posting announcements.

---

## Additional Resources

- **Steam Web API Documentation**: [https://partner.steamgames.com/doc/webapi_overview](https://partner.steamgames.com/doc/webapi_overview)
- **Steamworks Documentation**: [https://partner.steamgames.com/doc/home](https://partner.steamgames.com/doc/home)
- **Steam ID Finder**: [https://steamidfinder.com](https://steamidfinder.com)
- **API Key Registration**: [https://steamcommunity.com/dev/apikey](https://steamcommunity.com/dev/apikey)

---

## Next Steps

After setting up Steam:
1. ✅ Steam API configured
2. ⏭️ Connect GitHub repository
3. ⏭️ Configure your first project
4. ⏭️ Test announcement workflow

---

**Need help?** Check the [troubleshooting guide](./troubleshooting.md) or [open an issue](https://github.com/your-org/wishlistops/issues).
