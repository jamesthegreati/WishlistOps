# Google AI Studio Setup Guide

Get your Google AI API key to power WishlistOps announcement generation.

---

## Prerequisites

- Google account
- 5 minutes

---

## Step-by-Step Instructions

### 1. Navigate to Google AI Studio

**URL**: [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

Open the Google AI Studio API Keys page in your browser.

---

### 2. Sign In

If not already signed in, click "Sign in" and use your Google account.

---

### 3. Create API Key

1. Click the **"Get API key"** button (blue button on the page)
2. You'll see two options:
   - **Create API key in new project** (recommended for first-time users)
   - **Create API key in existing project**

3. Choose **"Create API key in new project"** unless you have an existing Google Cloud project

---

### 4. Copy Your API Key

1. Your API key will appear in a dialog box
2. Click the **copy icon** (📋) to copy the key to your clipboard
3. **Important**: Save this key securely - you won't be able to see it again!

**API Key Format**: `AIzaSy...` (starts with "AIzaSy" followed by random characters)

---

### 5. Add to WishlistOps

#### Option A: Web Interface (Recommended)

1. In the WishlistOps setup wizard, paste the API key into the "Google AI API Key" field
2. Click "Verify Connection"
3. You should see a green checkmark ✅

#### Option B: Environment Variable

Add to your `.env` file:
```bash
GOOGLE_AI_KEY=AIzaSy...your-actual-key-here...
```

Or set as environment variable:
```bash
# Windows (PowerShell)
$env:GOOGLE_AI_KEY="AIzaSy...your-actual-key-here..."

# Windows (CMD)
set GOOGLE_AI_KEY=AIzaSy...your-actual-key-here...

# Linux/Mac
export GOOGLE_AI_KEY="AIzaSy...your-actual-key-here..."
```

---

## Usage Limits

**Free Tier** (Gemini 1.5 Flash):
- 15 requests per minute (RPM)
- 1 million tokens per minute (TPM)
- 1,500 requests per day (RPD)

**More than enough for WishlistOps!** Typical announcement generation uses ~1,000 tokens and happens 1-2 times per week.

---

## Pricing

**Free tier is sufficient** for most indie developers. If you exceed limits:

- **Gemini 1.5 Flash**: $0.00 to $0.075 per 1M tokens (input)
- **Gemini 1.5 Pro**: $1.25 per 1M tokens (input)

**Example cost**: 100 announcements/month ≈ $0.01/month 💰

---

## Security Best Practices

### ✅ DO:
- Keep your API key secret
- Store in environment variables
- Use separate keys for development vs production
- Rotate keys periodically

### ❌ DON'T:
- Commit API keys to Git repositories
- Share keys publicly
- Use the same key across multiple projects
- Hardcode keys in source code

---

## Troubleshooting

### "API key not valid"

**Cause**: Key was copied incorrectly or has been revoked

**Solution**:
1. Double-check the key (should start with `AIzaSy`)
2. Ensure no extra spaces or characters
3. Create a new API key if needed

---

### "Quota exceeded"

**Cause**: You've hit the free tier limits

**Solutions**:
1. Wait for the quota to reset (resets daily)
2. Reduce announcement frequency
3. Upgrade to paid tier (rarely needed)

---

### "Connection refused"

**Cause**: Network/firewall blocking Google AI Studio

**Solutions**:
1. Check internet connection
2. Try disabling VPN
3. Check firewall settings
4. Test connection: `curl https://generativelanguage.googleapis.com`

---

## Additional Resources

- **API Documentation**: [https://ai.google.dev/docs](https://ai.google.dev/docs)
- **Pricing**: [https://ai.google.dev/pricing](https://ai.google.dev/pricing)
- **Support**: [https://ai.google.dev/support](https://ai.google.dev/support)

---

## Next Steps

After setting up Google AI:
1. ✅ Google AI configured
2. ⏭️ Set up Discord webhook
3. ⏭️ Configure Steam API
4. ⏭️ Connect GitHub repository

---

**Need help?** Check the [troubleshooting guide](./troubleshooting.md) or [open an issue](https://github.com/your-org/wishlistops/issues).
