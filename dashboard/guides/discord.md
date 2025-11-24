# Discord Webhook Setup Guide

Configure Discord to receive announcement approval requests from WishlistOps.

---

## Prerequisites

- Discord account
- Discord server (or permission to create webhooks)
- 3 minutes

---

## Step-by-Step Instructions

### 1. Open Discord Server Settings

1. Open Discord and navigate to your server
2. Right-click the server name (at the top)
3. Click **"Server Settings"**

**Don't have a server?**
- Click the **"+"** button in the Discord sidebar
- Choose "Create My Own"
- Name it something like "Game Dev Workspace"

---

### 2. Navigate to Integrations

1. In Server Settings, find the left sidebar
2. Click **"Integrations"**
3. You'll see webhooks, bots, and other integrations

---

### 3. Create Webhook

1. Click **"Webhooks"** (or "View Webhooks" if you have existing ones)
2. Click **"New Webhook"** button (top right)
3. A new webhook appears in the list

---

### 4. Configure Webhook

1. **Name**: Change to something descriptive like "WishlistOps Announcements"
2. **Channel**: Select the channel where approvals will be sent
   - Recommended: Create a dedicated `#wishlistops` channel
3. **Avatar** (optional): Upload a custom icon

---

### 5. Copy Webhook URL

1. Click **"Copy Webhook URL"** button
2. The URL is now in your clipboard

**Webhook URL Format**: 
```
https://discord.com/api/webhooks/1234567890/abcdefghijklmnopqrstuvwxyz...
```

---

### 6. Add to WishlistOps

#### Option A: Web Interface (Recommended)

1. In WishlistOps setup wizard, paste the webhook URL into the "Discord Webhook URL" field
2. Click "Test Connection"
3. Check Discord - you should see a test message! ✅

#### Option B: Environment Variable

Add to your `.env` file:
```bash
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/1234567890/abc...
```

Or set as environment variable:
```bash
# Windows (PowerShell)
$env:DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."

# Windows (CMD)
set DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# Linux/Mac
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
```

---

## What You'll See in Discord

When WishlistOps generates an announcement, it sends an **approval request** to your Discord channel:

**Message Contents**:
- 📋 Announcement title and body
- 🎨 Generated banner image
- 📊 Validation results (screenshot match confidence)
- ✅ Approve / ❌ Reject buttons
- 🔗 Link to Steam App page

**Example**:
```
🎮 New Announcement Ready for Review

Title: "Boss Fight Update - Dragon Arena Now Live!"

Body: "We've added an epic dragon boss fight in the new 
volcanic arena. Test your skills against our toughest 
enemy yet!..."

[Banner Image Preview]

Screenshot Validation: ✅ MATCH (confidence: 0.85)

[Approve] [Reject] [Edit]
```

---

## Rate Limits

Discord webhooks have rate limits:
- **30 requests per minute** per webhook
- **Global rate limit**: 50 requests per second per account

**WishlistOps typically uses**: 1-2 requests per week (well within limits!)

---

## Security Best Practices

### ✅ DO:
- Keep webhook URL secret
- Use a private Discord server
- Delete/regenerate webhook if exposed
- Store URL in environment variables

### ❌ DON'T:
- Share webhook URL publicly
- Post webhook URL in Git repositories
- Use the same webhook for multiple projects
- Give webhook access to public channels

---

## Recommended Channel Setup

Create a dedicated setup:

1. **Create Category**: "🤖 Automation"
2. **Create Channels**:
   - `#wishlistops-approvals` ← Use this for webhook
   - `#wishlistops-logs` (optional - for debugging)
   - `#wishlistops-analytics` (optional - for metrics)

3. **Set Permissions**:
   - Make channels private (only admins/developers can see)
   - Enable notifications for approval channel

---

## Troubleshooting

### "Invalid Webhook"

**Cause**: Webhook was deleted or URL is incorrect

**Solution**:
1. Check the URL format (should start with `https://discord.com/api/webhooks/`)
2. Verify webhook exists in Discord server settings
3. Create a new webhook if needed

---

### "Webhook not found"

**Cause**: Webhook was deleted from Discord

**Solution**:
1. Go back to Discord Server Settings → Integrations → Webhooks
2. Create a new webhook
3. Update the URL in WishlistOps

---

### "Messages not appearing"

**Cause**: Channel permissions or Discord outage

**Solutions**:
1. Verify the channel still exists
2. Check if the webhook is still in the webhooks list
3. Try sending a test message from Discord
4. Check Discord status: [https://discordstatus.com](https://discordstatus.com)

---

### "Rate limit exceeded"

**Cause**: Too many requests in short time

**Solutions**:
1. Wait 60 seconds and try again
2. Check if other tools are using the same webhook
3. Increase `min_days_between_posts` in config

---

## Advanced: Webhook Customization

You can customize webhook appearance:

```json
{
  "username": "WishlistOps Bot",
  "avatar_url": "https://example.com/bot-icon.png",
  "embeds": [{
    "title": "Announcement Approved!",
    "color": 3447003,
    "fields": [
      {"name": "Game", "value": "My Awesome Game"},
      {"name": "Platform", "value": "Steam"}
    ]
  }]
}
```

WishlistOps handles this automatically, but you can modify the `discord_notifier.py` file for custom styling.

---

## Additional Resources

- **Discord Webhooks Guide**: [https://discord.com/developers/docs/resources/webhook](https://discord.com/developers/docs/resources/webhook)
- **Rate Limits**: [https://discord.com/developers/docs/topics/rate-limits](https://discord.com/developers/docs/topics/rate-limits)
- **Support**: [Discord Developer Support](https://discord.gg/discord-developers)

---

## Next Steps

After setting up Discord:
1. ✅ Discord webhook configured
2. ⏭️ Configure Steam API key
3. ⏭️ Connect GitHub repository
4. ⏭️ Test your first announcement!

---

**Need help?** Check the [troubleshooting guide](./troubleshooting.md) or [open an issue](https://github.com/your-org/wishlistops/issues).
