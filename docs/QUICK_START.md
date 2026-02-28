# WishlistOps Quick Start Guide
## Get Your First Steam Announcement in 5 Minutes

> **What this tool does:** AI drafts announcement TEXT from your commits + formats YOUR screenshots for Steam.
> 
> **What this tool does NOT do:** Generate images with AI or auto-post to Steam (no public API exists).

---

## 🎯 Choose Your Path

### Path A: I'm a Programmer (Use Git)
**Best for:** Developers comfortable with Git and command line  
**Time:** 5-10 minutes  
**Skills needed:** Git, basic command line

👉 **[Jump to Git Setup](#git-setup-for-programmers)**

---

### Path B: I'm Not a Programmer (Use Dashboard)
**Best for:** Artists, community managers, non-technical team members  
**Time:** 5 minutes  
**Skills needed:** None! Just click buttons

👉 **[Jump to Dashboard Setup](#dashboard-setup-for-non-programmers)**

---

## 🔧 Git Setup (For Programmers)

### Step 1: Get API Keys (2 minutes)

**Google AI Key** (Required)
1. Visit: https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Click "Create API key in new project"
4. Copy the key

**Discord Webhook** (Required)
1. Open Discord Server Settings
2. Go to Integrations → Webhooks
3. Click "New Webhook"
4. Copy the Webhook URL

**Steam API Key** (Required)
1. Visit: https://partner.steamgames.com/doc/webapi_overview/auth
2. Go to Steamworks → Users & Permissions
3. Create WebAPI Key
4. Copy the key

### Step 2: Clone & Configure (2 minutes)

```bash
# Clone the repository
git clone https://github.com/your-username/WishlistOps.git
cd WishlistOps

# Copy environment template
cp .env.example .env

# Edit with your keys
nano .env  # Or use your favorite editor

# Paste in:
GOOGLE_AI_KEY=your_actual_key_here
DISCORD_WEBHOOK_URL=your_webhook_url_here
STEAM_API_KEY=your_steam_key_here
STEAM_APP_ID=your_game_id
```

### Step 3: Configure Your Game (1 minute)

```bash
# Copy config template
cp wishlistops/config.json.example wishlistops/config.json

# Edit with your game details
nano wishlistops/config.json
```

**Fill in:**
```json
{
  "steam": {
    "app_id": "123456",
    "app_name": "My Awesome Game"
  },
  "branding": {
    "art_style": "pixel art fantasy",
    "logo_path": "assets/logo.png"
  },
  "voice": {
    "tone": "casual and excited",
    "personality": "friendly indie developer"
  }
}
```

### Step 4: Test It! (1 minute)

```bash
# Install dependencies
pip install -r requirements.txt

# Test in dry-run mode (won't actually post)
python -m wishlistops.main --dry-run

# Check Discord - you should see a preview!
```

### Step 5: Set Up GitHub Action (1 minute)

```bash
# Copy workflow template
mkdir -p .github/workflows
cp .github/workflows/wishlistops.yml.example .github/workflows/wishlistops.yml

# Add secrets to GitHub
# Go to: Settings → Secrets → Actions → New repository secret
# Add:
# - GOOGLE_AI_KEY
# - DISCORD_WEBHOOK_URL  
# - STEAM_API_KEY
```

### Step 6: Trigger Your First Announcement

```bash
# Tag a new version
git tag v1.0.0
git push origin v1.0.0

# Watch the magic happen:
# 1. GitHub Action runs
# 2. AI generates announcement
# 3. Discord notification appears
# 4. You approve
# 5. Posts to Steam!
```

---

## 🎨 Dashboard Setup (For Non-Programmers)

### Step 1: Sign In (30 seconds)

1. Visit: https://your-username.github.io/WishlistOps
2. Click "Sign in with GitHub"
3. Click "Authorize"

### Step 2: Select Your Game Repository (30 seconds)

1. You'll see a list of your repositories
2. Click on your game's repository
3. WishlistOps opens the configuration page

### Step 3: Get Your API Keys (2 minutes)

**Google AI Key:**
1. Open new tab: https://aistudio.google.com/app/apikey
2. Click "Create API Key" → "Create API key in new project"
3. Copy the key
4. Paste into dashboard

**Discord Webhook:**
1. Open Discord → Server Settings → Integrations
2. Click "Webhooks" → "New Webhook"
3. Copy the URL
4. Paste into dashboard

**Steam API Key:**
1. Open: https://partner.steamgames.com
2. Go to Users & Permissions → Create WebAPI Key
3. Copy the key
4. Paste into dashboard

### Step 4: Fill Out the Form (2 minutes)

**Steam Configuration:**
- Steam App ID: `123456` (find in Steamworks)
- Game Name: `My Awesome Game`

**Branding:**
- Art Style: `pixel art fantasy` (describe your game's look)
- Logo: Click "Upload" and select your logo PNG
- Logo Position: Choose where logo appears on banners

**Writing Voice:**
- Tone: `casual and excited` (how you want to sound)
- Personality: `friendly indie developer`
- Avoid Phrases: `monetization, grind, lootbox` (words to never use)

**Automation:**
- ✅ Enable automation
- ✅ Trigger on Git tags
- Min Days Between Posts: `7` (prevent spam)
- ✅ Require manual approval

### Step 5: Save & Test (30 seconds)

1. Click "💾 Save Configuration"
2. Wait for "Configuration saved!" message
3. You're done! 🎉

### Step 6: How It Works Now

**When you tag a new version:**
1. GitHub Action automatically runs
2. AI reads your commits
3. Generates announcement draft
4. Sends to your Discord
5. You review and approve
6. Posts to Steam!

**You never touch code again!** ✨

---

## 🎓 What Happens Next?

### Automatic Workflow

```
┌─────────────────────┐
│  You push Git tag   │
│  (e.g., v1.1.0)     │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│  GitHub Action      │
│  runs automatically │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│  AI reads commits   │
│  Generates draft    │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│  Discord notifies   │
│  "Review this!"     │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│  You approve/edit   │
│  in Discord         │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│  Posts to Steam!    │
│  ✨ Marketing done  │
└─────────────────────┘
```

### Discord Approval Example

You'll receive a message like:

```
🎮 New Announcement Ready: v1.1.0 Update

Game: My Awesome Game
Version: v1.1.0
Generated: 2025-11-21 14:30 UTC

Preview:
═══════════════════════════════════════
Title: Major Combat Update - New Weapons!

Body:
Hey everyone! 

Version 1.1.0 is here with some awesome new features:

🗡️ Added dual-wielding system
🏹 New legendary bow with special effects  
⚔️ Complete combat rebalance based on your feedback
🐛 Fixed 15 community-reported bugs

Thanks for all your support! Let us know what you think!
═══════════════════════════════════════

[Banner Preview Image]

✅ Approve & Post to Steam
✏️ Edit Before Posting  
❌ Cancel
```

---

## 🆘 Troubleshooting

### "Invalid API Key" Error

**Cause:** Wrong key or expired  
**Fix:**
1. Regenerate key in AI Studio
2. Update in .env or dashboard
3. Try again

### "Discord Webhook Failed"

**Cause:** Wrong webhook URL  
**Fix:**
1. Check webhook URL is complete (starts with `https://discord.com/api/webhooks/`)
2. Test webhook: `curl -X POST <URL> -H "Content-Type: application/json" -d '{"content":"Test"}'`
3. If deleted, create new webhook

### "No Commits Found"

**Cause:** No player-facing commits since last run  
**Fix:**
1. Make sure commits don't start with `chore:`, `docs:`, `test:`
2. Use `feat:` or `fix:` prefixes
3. Or add `[player-facing]` to commit message

### "Rate Limited"

**Cause:** Posted too recently (within 7 days)  
**Fix:**
1. Wait until minimum days passed
2. Or reduce `min_days_between_posts` in config
3. Or use `--force` flag (not recommended)

---

## 💡 Pro Tips

### Tip 1: Write Good Commit Messages

**Bad:**
```
git commit -m "fixed stuff"
```

**Good:**
```
git commit -m "feat: add dual-wielding combat system

Players can now equip weapons in both hands for devastating combos.
New animations and special abilities unlocked at level 10."
```

The AI uses your commit messages to generate announcements!

### Tip 2: Use Tags for Versions

```bash
# Create a tag for each version
git tag v1.0.0
git push origin v1.0.0

# This triggers the workflow automatically
```

### Tip 3: Review in Discord First

Always check the Discord preview before approving. The AI is good, but human oversight ensures quality!

### Tip 4: Customize Your Voice

Edit `wishlistops/config.json` to match your brand:

```json
{
  "voice": {
    "tone": "professional and informative",
    "personality": "veteran game designer",
    "avoid_phrases": ["AI", "algorithm", "procedural"]
  }
}
```

### Tip 5: Test with Dry Run

Before going live, test everything:

```bash
# Test without posting to Steam
DRY_RUN=true python -m wishlistops.main
```

---

## 📚 Next Steps

### Learn More
- Read `README.md` for full documentation
- Check `DEPLOYMENT_GUIDE.md` for advanced setup
- Join Discord community for support

### Upgrade to Pro
- Skip API key setup entirely
- Managed infrastructure
- Priority support
- Advanced features
- One-time payment: $99

### Get Help
- GitHub Issues: Bug reports & feature requests
- Discord: Community support
- Email: support@wishlistops.com (Pro tier)

---

## ✅ Checklist

### Before Your First Run
- [ ] Got Google AI API key
- [ ] Got Discord webhook URL
- [ ] Got Steam API key
- [ ] Configured `config.json` with game details
- [ ] Tested in dry-run mode
- [ ] Discord notifications working
- [ ] Team knows to check Discord for approvals

### After Setup
- [ ] Tag triggered successfully
- [ ] Received Discord notification
- [ ] Reviewed and approved draft
- [ ] Announcement posted to Steam
- [ ] Community responded positively
- [ ] Time saved: 2-4 hours! 🎉

---

**Congratulations! You've automated your Steam marketing! 🚀**

Now you can focus on building your game, not writing announcements.

Questions? Join our Discord or open a GitHub issue. We're here to help!
