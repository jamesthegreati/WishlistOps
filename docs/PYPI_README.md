# 🎮 WishlistOps

**Automated Steam Marketing for Indie Developers**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://badge.fury.io/py/wishlistops.svg)](https://badge.fury.io/py/wishlistops)

Transform your Git commits into Steam announcements automatically. Save 4+ hours per week on marketing and focus on building your game.

---

## ✨ Features

- 🤖 **AI-Powered Announcements** - Google Gemini writes Steam announcements from your commits
- 🎨 **Smart Banner Generation** - Auto-crop screenshots + logo overlay for Steam's format
- ✅ **Human Approval** - Review in Discord before posting (no surprises!)
- 📊 **Beautiful Dashboard** - Web UI for setup, monitoring, and multi-project management
- 🔒 **100% Private** - Runs locally, your data never touches our servers
- 💰 **$0 Infrastructure** - Free GitHub Actions + free Google AI tier

---

## 🚀 Quick Start (2 Minutes)

### Installation

```bash
pip install wishlistops
```

### Setup

```bash
wishlistops setup
```

This launches a beautiful web dashboard that guides you through:
1. **GitHub** - Connect your game repository
2. **Discord** - Set up approval notifications
3. **Google AI** - Free API key from Google AI Studio
4. **Projects** - Select which games to monitor

### Use It

```bash
# Make commits as usual
git commit -m "feat: added boss fight in Fire Temple"

# Tag a release
git tag v1.2.0
git push origin v1.2.0

# Check Discord - your announcement is ready for approval!
# React with ✅ to post to Steam
```

---

## 📸 Screenshots

### Setup Wizard
![Setup Wizard](https://github.com/jamesthegreati/WishlistOps/raw/main/docs/images/setup-wizard.png)

### Monitor Dashboard
![Dashboard](https://github.com/jamesthegreati/WishlistOps/raw/main/docs/images/dashboard.png)

### Discord Approval
![Discord](https://github.com/jamesthegreati/WishlistOps/raw/main/docs/images/discord-approval.png)

---

## 📋 Requirements

- **Python 3.11+**
- **Git repository** for your game
- **Steam Partner Account** (free, for Steamworks API)
- **Google AI API Key** (free tier: 1,500 requests/day)
- **Discord Webhook** (free)

---

## 🎯 How It Works

```
┌─────────────┐
│  Git Commit │  ← You work normally
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  Tag Release    │  ← git tag v1.0.0
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  AI Generates   │  ← Google Gemini reads commits
│  Announcement   │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  Discord        │  ← You approve or edit
│  Notification   │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  Posted to      │  ← Auto-posted after approval
│  Steam!         │
└─────────────────┘
```

---

## 📚 Documentation

### Web Dashboard

Run `wishlistops setup` to access:
- **Welcome Page** - Feature overview and getting started
- **Setup Wizard** - Guided OAuth connections with screenshots
- **Monitor Dashboard** - Track announcements across all projects
- **Built-in Docs** - Best practices and commit conventions

### CLI Commands

```bash
# Launch web dashboard (default)
wishlistops setup

# Run automation workflow
wishlistops run

# Run with custom config
wishlistops run --config path/to/config.json

# Dry run (no actual API calls)
wishlistops run --dry-run

# Verbose logging
wishlistops run --verbose
```

### Configuration

WishlistOps stores config in `wishlistops/config.json`. Edit via web dashboard or manually:

```json
{
  "steam": {
    "app_id": "480",
    "app_name": "My Awesome Game"
  },
  "branding": {
    "art_style": "pixel art fantasy RPG",
    "logo_path": "assets/logo.png",
    "logo_position": "top-right"
  },
  "voice": {
    "tone": "casual and excited",
    "personality": "friendly indie developer",
    "avoid_phrases": ["monetization", "grind"]
  },
  "automation": {
    "min_days_between_posts": 7,
    "require_approval": true
  }
}
```

### Commit Conventions

Write player-facing commits for best results:

✅ **Good:**
```bash
git commit -m "feat: added underwater level with giant squid boss"
git commit -m "fix: enemies no longer spawn inside walls"
git commit -m "content: 15 new medieval armor sets"
```

❌ **Avoid:**
```bash
git commit -m "refactor: reorganized code"
git commit -m "update stuff"
git commit -m "wip"
```

**Pro Tip:** Link screenshots for better banners:
```bash
git commit -m "feat: new boss fight [shot: screenshots/boss.png]"
```

---

## 🎨 Features in Detail

### Multi-Project Support
Monitor announcements for multiple games from one dashboard. Perfect for:
- Solo devs with multiple projects
- Small studios managing a portfolio
- Publishers overseeing indie games

### Smart Screenshot Handling
- Auto-crops to Steam's 800x450 aspect ratio
- Detects screenshots in commits (explicit or implicit)
- Falls back to recent screenshots in `/screenshots/` folder
- Supports PNG, JPG, JPEG, WEBP

### Anti-Slop Quality Filter
Automatically detects and fixes:
- Generic AI language ("dive into", "unleash")
- Overused marketing buzzwords
- Tone violations (based on your config)

### Human-in-the-Loop Safety
Every announcement requires approval:
- ✅ Approve and post
- ❌ Cancel
- ✏️ Edit text before posting

---

## 💰 Cost Breakdown

| Service | Free Tier | Typical Monthly Usage | Cost |
|---------|-----------|----------------------|------|
| Google AI | 1,500 requests/day | ~100 announcements | **$0** |
| GitHub Actions | 3,000 minutes/month | ~50 runs | **$0** |
| Discord | Unlimited webhooks | ∞ | **$0** |
| Steam API | Free for partners | ∞ | **$0** |
| **Total** | | | **$0** |

---

## 🔒 Privacy & Security

- **Local-first**: Runs on your machine or GitHub Actions
- **No cloud storage**: Your data stays in your Git repo
- **API keys never shared**: Stored in environment variables or local config
- **Open source**: Audit the code yourself

---

## 🛠️ Development

### Install from Source

```bash
git clone https://github.com/jamesthegreati/WishlistOps.git
cd WishlistOps
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
pytest --cov=wishlistops  # With coverage
```

### Code Quality

```bash
black wishlistops/
isort wishlistops/
mypy wishlistops/
pylint wishlistops/
```

---

## 🗺️ Roadmap

### v1.0 (Current)
- [x] AI announcement generation
- [x] Screenshot processing
- [x] Discord approval
- [x] Web dashboard
- [x] Multi-project support

### v1.1 (Next)
- [ ] Steam Workshop integration
- [ ] Video trailer support
- [ ] A/B testing for announcements
- [ ] Analytics dashboard

### v2.0 (Future)
- [ ] Multi-platform (Epic, itch.io, GOG)
- [ ] Localization support
- [ ] Automated social media posting
- [ ] Community calendar integration

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repo
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 💬 Community & Support

- **GitHub Issues**: [Report bugs](https://github.com/jamesthegreati/WishlistOps/issues)
- **Discussions**: [Ask questions](https://github.com/jamesthegreati/WishlistOps/discussions)
- **Discord**: [Join the community](https://discord.gg/wishlistops)

---

## 🙏 Credits

Built with:
- [Google Gemini](https://ai.google.dev/) - AI generation
- [GitHub Actions](https://github.com/features/actions) - Serverless automation
- [Discord](https://discord.com/) - Approval notifications
- [Pillow](https://python-pillow.org/) - Image processing

---

## ⭐ Star History

If WishlistOps saves you time, give us a star! ⭐

[![Star History Chart](https://api.star-history.com/svg?repos=jamesthegreati/WishlistOps&type=Date)](https://star-history.com/#jamesthegreati/WishlistOps&Date)

---

**Built by indie developers, for indie developers** 🎮

*Stop context-switching. Start shipping.*
