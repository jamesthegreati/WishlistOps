# 🎮 WishlistOps - Quick Reference Card

**Save this for easy access to common commands and workflows**

---

## 📦 Installation

```bash
pip install wishlistops
```

---

## 🚀 Commands

### Launch Web Dashboard
```bash
wishlistops setup
```
Opens browser at `http://127.0.0.1:8080` with:
- Setup wizard
- Project monitor
- Documentation

### Run Automation
```bash
# Normal run
wishlistops run

# Test without posting
wishlistops run --dry-run

# With debug logs
wishlistops run --verbose

# Custom config location
wishlistops run --config path/to/config.json
```

---

## 📝 Git Workflow

### Good Commit Messages
```bash
git commit -m "feat: added underwater boss battle"
git commit -m "fix: enemies no longer spawn in walls"
git commit -m "content: 15 new armor sets added"
git commit -m "improve: 30% faster performance on low-end PCs"
```

### Link Screenshots
```bash
git commit -m "feat: new forest level [shot: screenshots/forest.png]"
```

### Trigger Announcement
```bash
git tag v1.2.0
git push origin v1.2.0
# Check Discord for approval!
```

---

## 🔧 Configuration

### Config File
Location: `wishlistops/config.json`

Edit via web dashboard or manually:
```json
{
  "steam": {"app_id": "YOUR_APP_ID"},
  "voice": {
    "tone": "casual and excited",
    "avoid_phrases": ["monetization", "grind"]
  },
  "automation": {
    "min_days_between_posts": 7
  }
}
```

### Environment Variables
```bash
export GOOGLE_AI_KEY="AIza..."
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
export STEAM_API_KEY="..." # Future feature
```

---

## 🌐 Web Dashboard

### URLs
- **Welcome:** http://127.0.0.1:8080/
- **Setup:** http://127.0.0.1:8080/setup
- **Monitor:** http://127.0.0.1:8080/monitor
- **Docs:** http://127.0.0.1:8080/docs

### OAuth Setup
1. **GitHub:** Settings → Tokens → New (classic) → `repo`, `workflow` scopes
2. **Discord:** Server Settings → Integrations → Webhooks → New
3. **Google AI:** https://aistudio.google.com/app/apikey

---

## 📊 Monitoring

### Check Announcement History
Web dashboard at `/monitor` shows:
- Total announcements sent
- Recent activity
- Pending approvals
- Per-project stats

### Discord Workflow
1. WishlistOps sends draft
2. Review announcement + banner
3. React with ✅ to approve
4. React with ❌ to cancel
5. Reply to edit text

---

## 🐛 Troubleshooting

### No announcements generated?
- Check commit messages use prefixes (`feat:`, `fix:`, etc.)
- Verify `min_days_between_posts` not blocking
- Need 3+ commits by default

### Discord not receiving?
- Test webhook: `curl -X POST WEBHOOK_URL -H "Content-Type: application/json" -d '{"content":"test"}'`
- Check channel permissions
- Verify webhook URL format

### Web dashboard won't open?
- Check port 8080 not in use
- Try different port: `wishlistops setup --port 8081`
- Check firewall settings

### Package not found?
- Upgrade pip: `pip install --upgrade pip`
- Clear cache: `pip cache purge`
- Try: `pip install --no-cache-dir wishlistops`

---

## 📚 Best Practices

### Posting Frequency
- **Weekly:** Ideal for active development
- **Bi-weekly:** Good for small teams
- **Monthly:** Minimum to maintain momentum

### Screenshot Guidelines
- Min resolution: 1920x1080
- Format: PNG (preferred) or JPEG
- No debug overlays or FPS counters
- Show exciting gameplay, not menus

### Commit Batching
```bash
# Bad: Too frequent
git tag v1.0.1  # Minor fix
git tag v1.0.2  # Another fix

# Good: Batch related changes
# Work for a week, then:
git tag v1.1.0  # Announces all changes together
```

---

## 🆘 Quick Help

### Get Help
```bash
wishlistops --help
wishlistops run --help
wishlistops setup --help
```

### Documentation
- Built-in: http://127.0.0.1:8080/docs
- GitHub: https://github.com/jamesthegreati/WishlistOps
- Issues: https://github.com/jamesthegreati/WishlistOps/issues

### Community
- Discord: [Join Community](#)
- Reddit: r/WishlistOps
- Twitter: @WishlistOps

---

## ⚡ Pro Tips

1. **Screenshot hotkey:** Script F9 in your engine to capture marketing screenshots automatically
2. **Batch commits:** Group related changes for better announcements
3. **Review in Discord:** Always check before approving
4. **Use prefixes:** `feat:`, `fix:`, `content:` help AI understand changes
5. **Tag strategically:** Don't tag every commit, batch significant updates

---

## 📋 Cheat Sheet

| Task | Command |
|------|---------|
| Install | `pip install wishlistops` |
| Setup | `wishlistops setup` |
| Run | `wishlistops run` |
| Test | `wishlistops run --dry-run` |
| Debug | `wishlistops run --verbose` |
| Tag release | `git tag v1.0.0 && git push origin v1.0.0` |
| Check status | Open http://127.0.0.1:8080/monitor |
| Read docs | Open http://127.0.0.1:8080/docs |

---

## 🎯 Common Workflows

### First Time Setup
```bash
# 1. Install
pip install wishlistops

# 2. Launch dashboard
wishlistops setup

# 3. Connect services (in browser)
# - GitHub token
# - Discord webhook
# - Google AI key

# 4. Select project

# 5. Done! Start making commits
```

### Regular Usage
```bash
# 1. Work on your game
git commit -m "feat: new boss fight"
git commit -m "fix: improved performance"

# 2. Tag when ready
git tag v1.2.0
git push origin v1.2.0

# 3. Check Discord
# Review and approve

# 4. Announcement posted!
```

### Multi-Project
```bash
# 1. Open dashboard
wishlistops setup

# 2. Go to /monitor

# 3. See all projects

# 4. Each project auto-announces
```

---

**Print this card and keep it handy! 📄**

*Last updated: November 2025*
