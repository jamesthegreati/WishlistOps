# 🎮 WishlistOps

**Automated Steam Marketing for Indie Game Developers**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Production Ready](https://img.shields.io/badge/status-production--ready-brightgreen.svg)](https://github.com/jamesthegreati/WishlistOps)

Transform your Git commits into Steam announcements automatically. Save 4+ hours per week on marketing and focus on building your game.

**🎉 NEW**: Download announcements directly from Discord or the web dashboard for easy Steam upload!

---

## 📖 Quick Links

| Resource | Description |
|----------|-------------|
| **[User Guide](USER_GUIDE.md)** | Complete usage guide with examples and troubleshooting |
| **[Production Deployment](PRODUCTION_DEPLOYMENT.md)** | Deploy to GitHub Actions, Docker, or cloud platforms |
| **[Steam Integration](STEAM_GAME_CONTEXT_INTEGRATION.md)** | How game context improves AI announcements |
| **[API Documentation](docs/)** | Technical architecture and build plans |

---

## ✨ Features

- 🤖 **AI-Powered Announcements** - Google Gemini writes Steam announcements from your commits
- 🎨 **Smart Banner Generation** - Auto-crop screenshots + logo overlay for Steam's format
- 💾 **Easy Downloads** - Get announcements as .txt files for copy/paste to Steam
- ✅ **Discord Integration** - Announcements sent with downloadable files attached
- 📊 **Beautiful Dashboard** - Local web UI for setup, monitoring, and testing
- 🎮 **Steam Game Context** - AI knows your game's genre, style, and previous announcements
- 🔒 **100% Private** - Runs locally, your data never touches our servers
- 💰 **$0 Infrastructure** - Free GitHub Actions + free Google AI tier

---

## 🚀 Quick Start (2 Minutes)

### Installation

```bash
pip install wishlistops
```

### Launch Web Dashboard

```bash
wishlistops-web
```

This launches a beautiful web dashboard at `http://localhost:8080` that guides you through:
1. **GitHub** - Connect your game repository
2. **Discord** - Set up approval notifications
3. **Google AI** - Free API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
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

## 🛠️ Technology Stack

- **Python 3.11+** - Core application
- **Google Gemini AI** - Announcement generation and image processing
- **aiohttp** - Async web server
- **GitPython** - Git repository analysis
- **Pillow** - Image composition
- **Discord Webhooks** - Approval notifications

---

## 💡 How It Works

1. **Monitor** - Watches your Git repository for commits and tags
2. **Analyze** - Extracts meaningful updates using Git history
3. **Generate** - AI creates Steam-ready announcements from your commits
4. **Review** - Sends to Discord for your approval
5. **Download** - Get text + banner files to upload to Steam

---

## 🎯 Features

### Core Features
- ✅ AI-powered announcement generation from Git commits
- ✅ Steam game context integration for better quality
- ✅ Smart banner generation with logo overlays
- ✅ Discord approval workflow with downloadable files
- ✅ Web dashboard for configuration and monitoring
- ✅ Multi-commit batch processing
- ✅ Interactive CLI for terminal users

### Quality & Safety
- ✅ Content filtering (no generic AI language)
- ✅ Human-in-the-loop approval required
- ✅ Rate limiting (prevent spam)
- ✅ Configurable voice and tone

---

## 📚 Documentation

For detailed guides and documentation, visit:
- **[User Guide](USER_GUIDE.md)** - Complete usage instructions
- **[Production Deployment](PRODUCTION_DEPLOYMENT.md)** - Deploy to cloud platforms
- **[Steam Integration](STEAM_GAME_CONTEXT_INTEGRATION.md)** - Game context features
- **[Technical Docs](docs/)** - Architecture and build plans

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
