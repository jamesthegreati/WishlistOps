# 🚀 WishlistOps Launch Guide

**Complete guide to shipping WishlistOps to PyPI and launching to users**

## Important Clarifications for Marketing

Before launch, ensure all marketing materials clearly state:

1. **AI Co-Pilot, Not Full Automation**: Steam has no public posting API. We draft announcements and prepare images - user does final copy-paste (~30 seconds).

2. **No AI Image Generation**: We ONLY process user-provided screenshots (crop, resize, logo overlay). All images come from the user.

3. **Text Generation Only**: Google Gemini drafts announcement text from Git commits. This is the only AI generation involved.

---

## 📦 Pre-Launch Checklist

### Code Preparation

- [x] Web server implementation complete
- [x] OAuth integrations (GitHub, Discord, Google AI)
- [x] Beautiful web dashboard (welcome, setup, monitor, docs)
- [x] CLI commands (`wishlistops setup`, `wishlistops run`)
- [x] Configuration management with save/load
- [x] Multi-project support
- [x] Built-in documentation
- [x] Screenshot guides for setup
- [ ] Test on Windows, macOS, Linux
- [ ] Test with real Steam account
- [ ] Test with multiple projects

### Package Files

- [x] `setup.py` - Package configuration
- [x] `MANIFEST.in` - Include dashboard files
- [x] `requirements.txt` - Dependencies
- [x] `PYPI_README.md` - PyPI description
- [x] `LICENSE` - MIT License
- [ ] `CHANGELOG.md` - Version history
- [ ] Version bump to 1.0.0

### Documentation

- [x] Built-in web docs
- [x] Commit conventions guide
- [x] Best practices
- [x] Troubleshooting
- [x] FAQ
- [ ] Video walkthrough
- [ ] Screenshot gallery

---

## 🔨 Build & Test Locally

### 1. Install in Development Mode

```bash
cd /path/to/WishlistOps
pip install -e ".[dev,web]"
```

### 2. Test Web Server

```bash
wishlistops setup
# Browser should open at http://127.0.0.1:8080
# Test all 4 pages: welcome, setup, monitor, docs
```

### 3. Test CLI

```bash
# Create test config
wishlistops run --dry-run --verbose

# Check help
wishlistops --help
wishlistops setup --help
wishlistops run --help
```

### 4. Run Tests

```bash
pytest
pytest --cov=wishlistops
```

### 5. Test Package Build

```bash
# Clean previous builds
rm -rf build/ dist/ *.egg-info/

# Build package
python -m build

# Check contents
tar -tzf dist/wishlistops-1.0.0.tar.gz | grep dashboard
# Should include dashboard/*.html, *.css, *.js
```

---

## 📤 Publishing to PyPI

### 1. Create PyPI Account

1. Go to https://pypi.org/account/register/
2. Verify email
3. Enable 2FA (required)

### 2. Create API Token

1. Go to https://pypi.org/manage/account/
2. Scroll to "API tokens"
3. Click "Add API token"
4. Name: "WishlistOps"
5. Scope: "Entire account" (or specific project)
6. Copy token (starts with `pypi-`)

### 3. Configure Twine

```bash
# Install twine
pip install twine

# Create ~/.pypirc (optional)
cat > ~/.pypirc << EOF
[pypi]
username = __token__
password = pypi-YOUR_TOKEN_HERE
EOF

chmod 600 ~/.pypirc
```

### 4. Build Package

```bash
# Install build tools
pip install build twine

# Clean old builds
rm -rf build/ dist/ *.egg-info/

# Build
python -m build

# Verify
twine check dist/*
```

### 5. Test on TestPyPI (Recommended)

```bash
# Upload to TestPyPI
twine upload --repository testpypi dist/*

# Test install
pip install --index-url https://test.pypi.org/simple/ wishlistops

# Test it works
wishlistops setup
```

### 6. Upload to PyPI

```bash
# Upload to real PyPI
twine upload dist/*

# Verify at https://pypi.org/project/wishlistops/
```

---

## 🎯 Launch Day Strategy

### Week Before Launch

**Monday-Tuesday: Final Testing**
- [ ] Test on fresh VMs (Windows 10/11, macOS, Ubuntu)
- [ ] Test with real Steam account
- [ ] Record demo video (2-3 minutes)
- [ ] Take screenshots for README

**Wednesday-Thursday: Content Preparation**
- [ ] Write launch blog post
- [ ] Prepare Reddit posts (r/IndieGaming, r/gamedev, r/IndieDev)
- [ ] Create Twitter/X thread
- [ ] Set up Discord server for support
- [ ] Create Product Hunt submission

**Friday: Final Push**
- [ ] Upload to PyPI
- [ ] Test install: `pip install wishlistops`
- [ ] Verify PyPI page looks correct
- [ ] Prepare launch posts (but don't publish yet)

### Launch Day (Tuesday 9 AM EST)

**Hour 0-2: Reddit**

Post to r/IndieDev first:

```markdown
Title: I automated my Steam marketing with a local web app (saves 4 hrs/week)

Body:
Hey r/IndieDev!

I was tired of context-switching between coding and writing Steam announcements.
So I built WishlistOps - it reads your Git commits and generates announcements 
automatically.

✨ Features:
- AI writes announcements from your commits
- Beautiful local web dashboard
- Approve in Discord before posting
- 100% free (runs on GitHub Actions)
- 2-minute setup with guided wizard

🔗 Try it: `pip install wishlistops`
📖 GitHub: https://github.com/jamesthegreati/WishlistOps
🎥 Demo: [YouTube link]

Built it for myself, sharing in case it helps anyone else!

What marketing tasks eat your time? Would love feedback.
```

**Hour 2-4: Twitter/X**

Thread (7 tweets):

```
1/ 🎮 Indie devs: Stop switching from code to Steam marketing.

I built a tool that saved me 4 hours this week.

Thread on how it works 👇

2/ Problem: Every game update means:
- Write Steam announcement  
- Design banner
- Post it
- Share on socials

That's 2-4 hours EVERY time you ship.

3/ Solution: WishlistOps

Install: `pip install wishlistops`
Run: `wishlistops setup`

It launches a local web app that connects:
✅ GitHub (your code)
✅ Discord (for approval)
✅ Google AI (free tier)
✅ Steam (auto-post)

[Screenshot of setup wizard]

4/ How it works:
- You: git tag v1.0.0
- AI: Reads commits, writes announcement
- You: Approve in Discord
- Auto: Posts to Steam

No context switching. No manual work.

[GIF of workflow]

5/ Key: Human approval required.

AI drafts, YOU decide what posts.

No surprises. No "AI slop".

[Screenshot of Discord approval]

6/ It's FREE and open source.

Runs on GitHub Actions (3000 min/month free).
Uses Google AI free tier.

$0/month forever.

7/ Try it:
🔗 pip install wishlistops
📖 Docs: http://127.0.0.1:8080/docs
💬 Support: [Discord]

RT if you've ever wished marketing was automated! 🚀
```

**Hour 4-6: Product Hunt**

- Submit product
- Respond to every comment
- Ask beta users to upvote

**Hour 6-12: Engagement**

- Reply to EVERY Reddit comment (< 30 min response time)
- Reply to EVERY Twitter mention
- Monitor PyPI downloads
- Fix any critical bugs immediately

### Week After Launch

**Daily Tasks:**
- Check /r/IndieDev, /r/gamedev for mentions
- Respond to GitHub issues within 24 hours
- Tweet daily tips/features
- Share success stories

**Content Calendar:**
```
Monday: "How to write better commit messages for WishlistOps"
Tuesday: "Case study: Generated 50 announcements in 1 month"
Wednesday: AMA on Reddit
Thursday: "5 mistakes to avoid with automated marketing"
Friday: Week 1 metrics + thank you post
```

---

## 📊 Success Metrics

### Week 1 Targets
- [ ] 500 PyPI downloads
- [ ] 100 GitHub stars
- [ ] 10 active users (sent announcements)
- [ ] 5 Discord members
- [ ] 0 critical bugs

### Month 1 Targets
- [ ] 2,000 PyPI downloads
- [ ] 500 GitHub stars
- [ ] 100 active users
- [ ] 50 Discord members
- [ ] 10 testimonials

### Month 3 Targets
- [ ] 10,000 PyPI downloads
- [ ] 2,000 GitHub stars
- [ ] 500 active users
- [ ] 200 Discord members
- [ ] Featured on IndieDevTools.com

---

## 🐛 Common Launch Issues & Fixes

### "Package not found on PyPI"
- Wait 5-10 minutes after upload (indexing)
- Check https://pypi.org/project/wishlistops/
- Verify version number

### "Dashboard files missing"
- Check `MANIFEST.in` includes dashboard/
- Rebuild: `python -m build`
- Verify: `tar -tzf dist/*.tar.gz | grep dashboard`

### "aiohttp not found"
- User needs web extras: `pip install wishlistops[web]`
- Update docs to mention this

### "Port 8080 in use"
- Add `--port` flag: `wishlistops setup --port 8081`
- Document this option

### Windows-specific issues
- Path separators (use `Path`)
- Browser not auto-opening (Windows security)
- Firewall blocking localhost

---

## 💰 Monetization (Optional - Post-Launch)

### Free Tier (Current)
- Everything is free
- Users bring own API keys (BYOK)
- $0 infrastructure cost

### Pro Tier (Future)
**Price:** $99 one-time or $9/month

**Features:**
- Managed API keys (no setup)
- Priority support
- Advanced analytics
- A/B testing
- Multi-platform (Epic, itch.io)

**Implementation:**
- Stripe integration
- License key system
- Cloudflare Workers for API proxy

### When to Monetize?
- **Wait until:** 1,000+ active users
- **Signal:** Users asking for "easier setup"
- **Approach:** Keep free tier, add premium

---

## 📞 Support Channels

### GitHub Issues
- Bug reports
- Feature requests
- Questions

### Discord Server
- Real-time help
- Community discussions
- Beta testing

### Email
- Create: support@wishlistops.com (forwarding)
- Response time: < 24 hours

---

## 🎓 Post-Launch Content Ideas

### Blog Posts
1. "How I Built WishlistOps in 3 Weeks"
2. "Why Indie Devs Should Automate Marketing"
3. "The Psychology of Steam Wishlists"
4. "Writing Git Commits That Market Your Game"
5. "Case Study: 1000 Wishlists in 30 Days"

### YouTube Videos
1. Complete walkthrough (10 min)
2. Setup tutorial (5 min)
3. Best practices (7 min)
4. Behind the scenes (vlog)
5. User interviews

### Twitter Content
- Daily tips
- Feature highlights
- User success stories
- Development updates
- Memes about game marketing

---

## ✅ Launch Day Checklist

**Morning (9 AM EST):**
- [ ] Final `pip install wishlistops` test
- [ ] PyPI page verified
- [ ] Demo video uploaded
- [ ] Screenshots ready
- [ ] Discord server live

**Launch (9:30 AM):**
- [ ] Post to r/IndieDev
- [ ] Post to r/gamedev
- [ ] Tweet announcement thread
- [ ] Submit to Product Hunt
- [ ] Email beta testers

**Engagement (All Day):**
- [ ] Monitor Reddit comments
- [ ] Respond to tweets
- [ ] Check PyPI downloads
- [ ] Watch for error reports
- [ ] Update Discord

**Evening:**
- [ ] Thank early adopters
- [ ] Share initial metrics
- [ ] Plan tomorrow's content
- [ ] Sleep! 😴

---

## 🚀 Ready to Launch?

**Final Check:**
```bash
# Test installation
pip uninstall wishlistops
pip install wishlistops

# Test setup wizard
wishlistops setup

# Test all pages
# - http://127.0.0.1:8080/ (welcome)
# - http://127.0.0.1:8080/setup
# - http://127.0.0.1:8080/monitor  
# - http://127.0.0.1:8080/docs

# All working? You're ready! 🎉
```

**Now execute the launch plan above and ship it! 🚢**

---

*Built by indie developers, for indie developers.*

*Good luck! 🎮*
