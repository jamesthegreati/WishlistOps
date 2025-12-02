# WishlistOps User Guide

> **AI Co-Pilot for Steam Marketing - Drafts announcements from your Git commits**

## Important Notes

### What WishlistOps Does
- **AI Drafts Text**: Google Gemini writes Steam announcements from your Git commits
- **Processes YOUR Screenshots**: Crops, resizes, and optimizes your game screenshots for Steam
- **Discord Approval**: Human-in-the-loop workflow with download links
- **100% Local**: Runs on your machine, your data stays private

### What WishlistOps Does NOT Do
- ❌ **No AI Image Generation**: We NEVER create images with AI - all images must be provided by you
- ❌ **No Automatic Steam Posting**: Steam has no public posting API - you copy-paste the final result (~30 seconds)
- ❌ **No Cloud Storage**: Your data never leaves your machine

> **Image Clarification**: When we say "banner images", we mean YOUR screenshots that we've resized and formatted for Steam (800x450). We only enhance what you provide - cropping, resizing, adding your logo overlay. No AI-generated imagery.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Using the Web Dashboard](#using-the-web-dashboard)
5. [Downloading Announcements](#downloading-announcements)
6. [Publishing to Steam](#publishing-to-steam)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

---

## Quick Start

### 5-Minute Setup

```bash
# 1. Install WishlistOps
pip install wishlistops

# 2. Launch the web dashboard
wishlistops-web

# 3. Follow the setup wizard in your browser
# http://localhost:8080/setup
```

That's it! The setup wizard will guide you through:
- Connecting GitHub
- Connecting Discord
- Connecting Google AI
- Configuring your Steam game details

---

## Installation

### Prerequisites

- **Python 3.11+** (Python 3.14 recommended)
- **pip** package manager
- **Git** installed and configured

### Install via pip

```bash
pip install wishlistops
```

### Install from source

```bash
git clone https://github.com/jamesthegreati/WishlistOps.git
cd WishlistOps
pip install -e .
```

### Verify Installation

```bash
wishlistops --version
# Output: WishlistOps v1.0.0
```

---

## Configuration

### Environment Variables

Create a `.env` file in your project root:

```bash
# Required
STEAM_API_KEY=your_steam_web_api_key_here
GOOGLE_AI_KEY=your_google_gemini_api_key_here
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# Optional (for game library features)
STEAM_ID=your_17_digit_steamid64_here
```

### Get Your API Keys

#### 1. Steam API Key
1. Visit: https://steamcommunity.com/dev/apikey
2. Enter domain: `localhost` (for development)
3. Copy the generated key

#### 2. Google AI Key (Gemini)
1. Visit: https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key (starts with `AIza...`)
4. **Free tier**: 1,500 requests/day (enough for 100+ announcements/month)

#### 3. Discord Webhook
1. Open your Discord server
2. Go to Server Settings → Integrations → Webhooks
3. Click "New Webhook"
4. Choose the channel for announcements
5. Copy the webhook URL

#### 4. Steam ID (Optional)
1. Visit: https://steamid.io/
2. Enter your Steam profile URL
3. Copy your "steamID64" (17 digits)

### Config File (`config.json`)

The setup wizard creates this automatically, but here's an example:

```json
{
  "version": "1.0",
  "steam": {
    "app_id": "480",
    "app_name": "Spacewar",
    "steam_id": "76561198012345678"
  },
  "branding": {
    "art_style": "retro arcade space shooter with vibrant colors",
    "color_palette": ["#000000", "#FFFFFF", "#FF0000"],
    "logo_position": "top-right",
    "logo_size_percent": 25,
    "logo_path": "wishlistops/assets/logo.png"
  },
  "voice": {
    "tone": "friendly and enthusiastic",
    "personality": "excited gamer",
    "avoid_phrases": ["leverage", "synergy", "revolutionize"],
    "max_title_length": 120,
    "max_body_length": 10000
  },
  "automation": {
    "enabled": true,
    "min_commits": 3,
    "require_approval": true
  }
}
```

---

## Using the Web Dashboard

### Launch the Dashboard

```bash
wishlistops-web
```

Your browser will open to `http://localhost:8080`

### Dashboard Pages

#### 1. **Setup Wizard** (`/setup`)
- Connect all your services (GitHub, Discord, Google AI, Steam)
- Configure game details
- Set announcement style and tone

#### 2. **Test Page** (`/test`)
- Create test announcements manually
- Preview before sending
- Download text files for Steam
- Send to Discord for approval

#### 3. **Commits Page** (`/commits`)
- View all Git commits
- See which commits were used for announcements
- Filter by type (player-facing, internal, bugfixes)
- Timeline visualization

#### 4. **Monitor Page** (`/monitor`)
- Real-time workflow status
- Recent announcements
- Error logs
- Performance metrics

### Test Your First Announcement

1. Go to `http://localhost:8080/test`
2. Fill in:
   - **Title**: "Update v1.0.0 - New Features!"
   - **Body**: Your announcement text
3. Click **"Create & Send Test Announcement"**
4. Check your Discord channel for approval
5. Click **"Download Announcement (.txt)"**
6. Upload to Steam manually

---

## Downloading Announcements

WishlistOps provides multiple ways to download announcements for manual Steam upload:

### Method 1: Discord (Automatic)

When an announcement is generated, Discord receives:
- **📎 announcement_YYYYMMDD_HHMMSS.txt** - Ready to copy/paste
- **🖼️ banner_YYYYMMDD_HHMMSS.png** - Ready to upload

Just click the files in Discord to download!

### Method 2: Web Dashboard

On the Test page (`/test`):
1. Generate an announcement
2. Click **"💾 Download Announcement (.txt)"**
3. The text file downloads to your computer
4. Copy/paste into Steam

### Method 3: API Endpoint

For programmatic access:

```bash
# Download announcement text
curl http://localhost:8080/api/export/announcement/{run_id} -o announcement.txt

# Download banner image
curl http://localhost:8080/api/export/banner/{filename} -o banner.png
```

### File Locations

Announcements are saved in:
```
wishlistops/
  banners/          # Generated banner images
    banner_20251124_120000.png
    banner_20251124_130000.png
  state/            # Workflow state and history
    runs.json       # All announcement runs
```

---

## Publishing to Steam

**Important**: Steam does **NOT** have a public posting API. You must manually publish announcements.

### Step-by-Step Publishing

1. **Generate Announcement** (via WishlistOps)
   - Run the workflow or use the test page
   - Announcement sent to Discord

2. **Download Files**
   - Download `.txt` file from Discord or web dashboard
   - Download `.png` banner image

3. **Open Steamworks**
   - Click the "🚀 Open Steamworks" button in Discord
   - Or visit: `https://partner.steamgames.com/apps/landing/{your_app_id}`

4. **Create Announcement**
   - Go to: **Community** → **Event & Announcements**
   - Click **"Create Event/Announcement"**
   - Select **"Regular Announcement"**

5. **Paste Content**
   - **Title**: Copy from `.txt` file (first line)
   - **Body**: Copy from `.txt` file (rest of content)
   - **Image**: Upload the `.png` banner

6. **Review & Publish**
   - Preview the announcement
   - Click **"Publish"** (or save as draft)

### Time Savings

- **Before WishlistOps**: 2-4 hours to write + design
- **With WishlistOps**: 30 seconds to copy/paste

---

## Troubleshooting

### Common Issues

#### 1. "Steam API key not configured"

**Solution**:
```bash
export STEAM_API_KEY=your_key_here
# Or add to .env file
```

#### 2. "Discord webhook not found"

**Solution**:
- Check webhook URL is correct
- Verify channel still exists
- Recreate webhook if deleted

#### 3. "Google AI API error"

**Solution**:
- Verify API key is correct
- Check free tier limit (1,500/day)
- Enable Gemini API in Google Cloud Console

#### 4. "Failed to fetch game context"

**Solution**:
- Verify `app_id` in `config.json` is correct
- Check game is published on Steam (not unreleased)
- Test API: `curl "https://store.steampowered.com/api/appdetails?appids=YOUR_APP_ID"`

#### 5. Banner images not generating

**Solution**:
- Check `logo_path` in config points to valid PNG file
- Verify Pillow is installed: `pip install Pillow`
- Check logs: `wishlistops --log-level DEBUG`

### Enable Debug Logging

```bash
# Run with detailed logs
wishlistops --log-level DEBUG

# Save logs to file
wishlistops --log-level DEBUG > wishlistops.log 2>&1
```

### Check Health Status

```bash
curl http://localhost:8080/api/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-24T12:00:00",
  "version": "1.0.0",
  "services": {
    "config": true,
    "web_server": true
  },
  "environment": {
    "STEAM_API_KEY": true,
    "GOOGLE_AI_KEY": true,
    "DISCORD_WEBHOOK_URL": true
  }
}
```

### Get Help

- **Issues**: https://github.com/jamesthegreati/WishlistOps/issues
- **Discussions**: https://github.com/jamesthegreati/WishlistOps/discussions
- **Discord**: [Coming soon]

---

## Best Practices

### 1. Commit Message Hygiene

Use conventional commit format:

```bash
# Good commits (will be included in announcements)
git commit -m "feat: Add new laser weapon with particle effects"
git commit -m "fix: Resolve crash when inventory full"
git commit -m "content: Add 5 new character skins"

# Internal commits (filtered out)
git commit -m "chore: Update dependencies"
git commit -m "docs: Fix typo in README"
git commit -m "test: Add unit tests for combat system"
```

### 2. Announcement Cadence

- **Weekly**: For active development (many commits)
- **Bi-weekly**: For steady progress (moderate commits)
- **Monthly**: For polish phase (few commits)

### 3. Review Before Publishing

Always review announcements in Discord before publishing:
- Check for AI "hallucinations"
- Verify technical accuracy
- Ensure tone matches your brand
- Fix any grammar/spelling issues

### 4. Customize Your Voice

Update `config.json` to match your game's personality:

```json
{
  "voice": {
    "tone": "quirky and humorous",
    "personality": "friendly indie dev sharing their journey",
    "avoid_phrases": [
      "revolutionize",
      "game-changing",
      "industry-leading",
      "next-generation"
    ]
  }
}
```

### 5. Banner Design Tips

- **Logo Position**: `top-right` or `center` works best
- **Logo Size**: 20-30% of banner width
- **Art Style**: Match your game's aesthetic
- **Color Palette**: Use your game's brand colors

Example:
```json
{
  "branding": {
    "art_style": "pixel art dungeon crawler with dark fantasy theme",
    "color_palette": ["#1a1a2e", "#16213e", "#0f3460", "#e94560"],
    "logo_position": "top-right",
    "logo_size_percent": 25
  }
}
```

### 6. Steam Game Context

Add your Steam ID to get better AI context:

```json
{
  "steam": {
    "app_id": "480",
    "app_name": "Spacewar",
    "steam_id": "76561198012345678"
  }
}
```

Benefits:
- AI knows your game's genre
- Matches tone of previous announcements
- Uses game description for context

### 7. Monitor Workflow Runs

Check the Monitor page regularly:
- Track success rate
- Identify patterns in failures
- Optimize commit cadence

---

## Advanced Usage

### Run from Command Line

```bash
# Generate announcement from recent commits
wishlistops

# Dry run (don't send to Discord)
wishlistops --dry-run

# Specify config file
wishlistops --config path/to/config.json

# Custom log level
wishlistops --log-level DEBUG
```

### GitHub Actions Integration

Add to `.github/workflows/wishlistops.yml`:

```yaml
name: WishlistOps

on:
  push:
    branches: [main]
    paths-ignore:
      - 'docs/**'
      - '*.md'

jobs:
  announce:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history

      - uses: actions/setup-python@v5
        with:
          python-version: '3.14'

      - name: Install WishlistOps
        run: pip install wishlistops

      - name: Generate Announcement
        env:
          STEAM_API_KEY: ${{ secrets.STEAM_API_KEY }}
          GOOGLE_AI_KEY: ${{ secrets.GOOGLE_AI_KEY }}
          DISCORD_WEBHOOK_URL: ${{ secrets.DISCORD_WEBHOOK_URL }}
        run: wishlistops
```

### API Integration

WishlistOps provides REST API endpoints:

```bash
# Health check
GET /api/health

# Version info
GET /api/version

# Current config
GET /api/config

# Create test announcement
POST /api/test-announcement
{
  "title": "Update v1.0",
  "body": "New features..."
}

# Download announcement
GET /api/export/announcement/{run_id}

# Download banner
GET /api/export/banner/{filename}
```

---

## Next Steps

1. ✅ Install WishlistOps
2. ✅ Run setup wizard
3. ✅ Test announcement generation
4. ✅ Customize voice and branding
5. ✅ Publish your first announcement
6. 🚀 Automate with GitHub Actions
7. 📊 Monitor performance
8. 🎮 Focus on game development!

---

## Support

Need help? We're here for you:

- 📖 **Documentation**: https://github.com/jamesthegreati/WishlistOps/blob/main/README.md
- 🐛 **Bug Reports**: https://github.com/jamesthegreati/WishlistOps/issues
- 💬 **Discussions**: https://github.com/jamesthegreati/WishlistOps/discussions
- 📧 **Email**: support@wishlistops.dev

---

*Made with ❤️ for indie game developers*
