# 🎮 WishlistOps

**Automated Steam Marketing for Indie Game Developers**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Production Ready](https://img.shields.io/badge/status-production--ready-brightgreen.svg)](https://github.com/jamesthegreati/WishlistOps)

Transform your Git commits into Steam announcements automatically. Save 4+ hours per week on marketing and focus on building your game.

---

## ✨ Features

### 🎮 Web Dashboard & CLI
- **Web Interface** - Beautiful dashboard at `http://localhost:8080` for configuration and monitoring
- **Interactive CLI** - Full-featured terminal UI with `wishlistops-cli` (optional)
- **Multi-commit Selection** - Select and batch process multiple commits at once
- **Image Upload** - Upload logo and banner images directly from the dashboard

### 🤖 AI-Powered Automation
- **Smart Generation** - Google Gemini writes Steam-ready announcements from your commits
- **Game Context** - AI understands your game's genre, style, and previous announcements
- **Banner Creation** - Auto-crop screenshots + logo overlay for Steam's 1920x1080 format
- **Quality Filtering** - Removes generic AI language and keeps your authentic voice

### 🔒 Safe & Private
- **Discord Approval** - Human-in-the-loop workflow with download links
- **100% Local** - Runs on your machine, your data never touches our servers
- **Rate Limiting** - Prevents spam and accidental over-posting
- **Configurable Voice** - Set tone, personality, and words to avoid

---

## 🚀 Installation

### Option 1: Web Dashboard (Recommended)

```bash
# Install package
pip install wishlistops

# Launch web interface
wishlistops setup
```

Visit `http://localhost:8080/setup` and follow the 4-step wizard:
1. **GitHub** - Connect your game repository  
2. **Discord** - Set up approval webhook  
3. **Google AI** - Get free API key from [Google AI Studio](https://aistudio.google.com/app/apikey)  
4. **Images** - Upload your game logo and banner

### Option 2: Interactive CLI

```bash
# Install with CLI dependencies
pip install wishlistops[cli]

# Launch terminal UI
wishlistops-cli
```

The CLI provides a rich terminal interface with:
- 🎯 Interactive commit selection
- ⚙️ Configuration wizard
- 📤 Image upload from terminal
- 📊 Formatted commit history
- 🎨 Beautiful tables and progress bars

---

## 🎯 Usage

### Web Dashboard

```bash
# Start the dashboard
wishlistops setup

# Navigate to:
# - Setup: http://localhost:8080/setup
# - Commits: http://localhost:8080/commits  
# - Monitor: http://localhost:8080/monitor
# - Test: http://localhost:8080/test
```

### Interactive CLI

```bash
# Launch CLI menu
wishlistops-cli

# Choose from:
# 1. Generate announcement (multi-select commits)
# 2. Configure settings
# 3. Upload images  
# 4. View commit history
# 5. Test configuration
# 6. View logs
# 7. Exit
```

### Automated Workflow

```bash
# Make commits as usual
git commit -m "feat: added boss fight in Fire Temple"

# Tag a release
git tag v1.2.0  
git push origin v1.2.0

# Check Discord - your announcement is ready!
# Download the .txt file and banner
# Upload to Steam Community Hub
```

---

## 💡 How It Works

1. **Monitor** - Watches your Git repository for commits and tags
2. **Analyze** - Extracts meaningful updates using Git history and Steam context
3. **Generate** - AI creates Steam-ready announcements with proper formatting
4. **Review** - Sends to Discord for approval with download links
5. **Upload** - Download .txt and banner files, upload to Steam Community Hub

---

## 📋 Requirements

- **Python 3.11+**
- **Git repository** for your game
- **Free API Keys**:
  - [Google AI Studio](https://aistudio.google.com/app/apikey) - For AI generation
  - Discord Webhook URL - For approval notifications
  - (Optional) Steam API Key - For enhanced game context

---

## 📚 Documentation

- **[User Guide](USER_GUIDE.md)** - Complete walkthrough with examples
- **[Quick Start](docs/QUICK_START.md)** - Get started in 5 minutes
- **[Deployment Guide](docs/DEPLOYMENT_GUIDE.md)** - Deploy to GitHub Actions, Docker, or cloud
- **[Technical Architecture](docs/architecture/)** - System design and diagrams

---

## 🔧 Configuration

WishlistOps stores configuration in `wishlistops/config.json`:

```json
{
  "version": "1.0",
  "steam": {
    "app_id": "480",
    "app_name": "Spacewar"
  },
  "branding": {
    "art_style": "retro arcade space shooter",
    "color_palette": ["#000000", "#FFFFFF"],
    "logo_position": "top-right"
  },
  "voice": {
    "tone": "casual and excited",
    "personality": "friendly indie developer",
    "avoid_phrases": ["monetization", "grind"]
  }
}
```

Secrets (API keys) are stored in environment variables:
- `GOOGLE_AI_KEY`
- `DISCORD_WEBHOOK_URL`  
- `STEAM_API_KEY` (optional)

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details

---

## 💬 Support

- **GitHub Issues**: [Report bugs](https://github.com/jamesthegreati/WishlistOps/issues)
- **Documentation**: [User Guide](USER_GUIDE.md)
- **Discord**: [Join community](https://discord.gg/wishlistops) _(coming soon)_

---

*Built with ❤️ for indie game developers*
