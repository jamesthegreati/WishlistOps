# Changelog

All notable changes to WishlistOps will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-11-23

### 🎉 Initial Release

#### Added
- **Local Web Dashboard** - Beautiful web interface that launches automatically
  - Welcome page with feature overview
  - Setup wizard with guided OAuth integrations
  - Monitor dashboard for tracking announcements across projects
  - Built-in documentation with best practices
  
- **OAuth Integrations** with visual guides
  - GitHub - Personal access token or OAuth
  - Discord - Webhook setup with screenshots
  - Google AI - API key integration (Google AI Studio)
  
- **Multi-Project Support**
  - Monitor multiple game repositories from one dashboard
  - Per-project configuration
  - Unified announcement history
  
- **CLI Commands**
  - `wishlistops setup` - Launch web dashboard
  - `wishlistops run` - Execute automation workflow
  - `--dry-run` flag for testing
  - `--verbose` flag for debugging
  
- **Core Features**
  - AI-powered announcement generation (Google Gemini)
  - Smart screenshot handling with auto-cropping
  - Logo overlay and Steam-ready formatting
  - Discord approval workflow
  - Anti-slop quality filter
  - Human-in-the-loop safety
  
- **Developer Experience**
  - Conventional commit support
  - Screenshot tagging (`[shot: path.png]`)
  - Detailed logging
  - Comprehensive error messages
  
- **Documentation**
  - In-app documentation accessible at `/docs`
  - Commit message conventions
  - Best practices guide
  - Troubleshooting section
  - FAQ
  
- **Package Management**
  - PyPI distribution ready
  - Entry point scripts
  - Proper package data inclusion
  - Development extras for testing

#### Technical Details
- Python 3.11+ requirement
- aiohttp-based web server
- Encrypted session management
- GitHub API integration
- Discord Webhook support
- Google Generative AI integration
- Git repository parsing
- Image processing with Pillow
- State management with JSON

### Known Issues
- Web dashboard requires manual browser open on some Windows configurations
- OAuth flow uses personal tokens (full OAuth coming in v1.1)
- Steam game detection not yet implemented

### Coming Soon (v1.1)
- Full GitHub OAuth flow
- Steam Workshop integration
- Steam game auto-detection
- Video trailer support
- Analytics dashboard
- A/B testing for announcements

---

## [Unreleased]

### Planned Features
- Multi-platform support (Epic, itch.io, GOG)
- Localization for announcements
- Automated social media posting
- Community calendar integration
- Advanced analytics
- Team collaboration features

---

[1.0.0]: https://github.com/jamesthegreati/WishlistOps/releases/tag/v1.0.0
