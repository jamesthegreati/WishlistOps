# GitHub OAuth App Setup Guide

Configure GitHub authentication to let WishlistOps access your repositories.

---

## Prerequisites

- GitHub account
- Repository with your game code
- 10 minutes

---

## Why GitHub OAuth?

WishlistOps needs to:
- Read your commit history
- Detect player-facing changes
- Monitor for new commits
- Access repository files (for screenshots)

**Security**: You create your own OAuth app, so WishlistOps never has access to your GitHub credentials.

---

## Step-by-Step Instructions

### 1. Navigate to GitHub Developer Settings

**URL**: [https://github.com/settings/developers](https://github.com/settings/developers)

Or manually:
1. Click your profile picture (top right)
2. Settings → Developer settings

---

### 2. Create OAuth App

1. Click **"OAuth Apps"** in the left sidebar
2. Click **"New OAuth App"** button (top right)
3. You'll see the "Register a new OAuth application" form

---

### 3. Fill Out Application Details

**Application name**: `WishlistOps - [Your Game Name]`
- Example: "WishlistOps - Space Adventure"
- This helps you identify the app later

**Homepage URL**: `http://localhost:5500`
- For local development
- Or use your game's website if you have one

**Application description** (optional):
```
Automated Steam marketing for my indie game. 
Monitors Git commits and generates announcements.
```

**Authorization callback URL**: `http://localhost:5500/auth/github/callback`
- **Critical**: Must be exactly this for local WishlistOps
- For production: Use your actual domain

---

### 4. Register Application

1. Click **"Register application"** button
2. You'll be redirected to your new OAuth app page

---

### 5. Generate Client Secret

1. On the OAuth app page, you'll see:
   - **Client ID**: Already visible (e.g., `Iv1.abc123def456...`)
   - **Client secrets**: Section below

2. Click **"Generate a new client secret"**
3. Confirm with your GitHub password if prompted
4. **Copy the client secret immediately** - you won't be able to see it again!

**Client Secret Format**: Random string like `a1b2c3d4e5f6...` (40 characters)

---

### 6. Copy Client ID and Secret

You now have both:
- **Client ID**: `Iv1.abc123...` (visible anytime)
- **Client Secret**: `a1b2c3...` (copy now, won't show again!)

---

### 7. Add to WishlistOps

#### Option A: Web Interface (Recommended)

1. In WishlistOps setup wizard:
   - Paste Client ID into "GitHub Client ID" field
   - Paste Client Secret into "GitHub Client Secret" field
2. Click "Connect GitHub"  
3. You'll be redirected to GitHub to authorize
4. Click "Authorize" to grant access
5. You'll be redirected back to WishlistOps ✅

#### Option B: Environment Variables

Add to your `.env` file:
```bash
WISHLISTOPS_GITHUB_CLIENT_ID=Iv1.abc123...
WISHLISTOPS_GITHUB_CLIENT_SECRET=a1b2c3d4e5f6...
```

Or set as environment variables:
```bash
# Windows (PowerShell)
$env:WISHLISTOPS_GITHUB_CLIENT_ID="Iv1.abc123..."
$env:WISHLISTOPS_GITHUB_CLIENT_SECRET="a1b2c3..."

# Windows (CMD)
set WISHLISTOPS_GITHUB_CLIENT_ID=Iv1.abc123...
set WISHLISTOPS_GITHUB_CLIENT_SECRET=a1b2c3...

# Linux/Mac
export WISHLISTOPS_GITHUB_CLIENT_ID="Iv1.abc123..."
export WISHLISTOPS_GITHUB_CLIENT_SECRET="a1b2c3..."
```

---

## OAuth Scopes

WishlistOps requests these permissions:

- **`repo`**: Access to private repositories (to read commits)
- **`user`**: Read basic user information (name, avatar)

**WishlistOps never**:
- Writes to your repositories
- Deletes anything
- modifies code
- Shares your data

---

## What Happens During Authorization

1. **You click "Connect GitHub"** in WishlistOps
2. **Redirected to GitHub** - shows permission request
3. **You click "Authorize"** - grants WishlistOps access
4. **Redirected back** - WishlistOps receives access token
5. **Token stored locally** - used to read your commits

You can revoke access anytime from GitHub settings.

---

## Security Best Practices

### ✅ DO:
- Create separate OAuth app per project
- Use localhost callback URL for development
- Revoke access if you stop using WishlistOps
- Keep Client Secret in environment variables

### ❌ DON'T:
- Share Client ID/Secret publicly
- Commit secrets to Git repositories
- Use the same OAuth app for multiple tools
- Grant access to untrusted applications

---

## Managing Access

### View Connected Apps
1. Go to [https://github.com/settings/applications](https://github.com/settings/applications)
2. Click "Authorized OAuth Apps" tab
3. You'll see "WishlistOps" in the list

### Revoke Access
1. Click on "WishlistOps" in the authorized apps list
2. Scroll down and click "Revoke access"
3. Confirm revocation

**Note**: You'll need to re-authorize when you use WishlistOps again.

---

## Troubleshooting

### "Invalid client_id"

**Cause**: Client ID was copied incorrectly

**Solution**:
1. Go back to [github.com/settings/developers](https://github.com/settings/developers)
2. Click on your OAuth app
3. Copy the Client ID again (starts with `Iv1.`)
4. Ensure no extra spaces

---

### "Redirect URI mismatch"

**Cause**: Callback URL doesn't match registered URL

**Solution**:
1. Check the Authorization callback URL in your OAuth app settings
2. Must be exactly: `http://localhost:5500/auth/github/callback`
3. Update if different
4. Restart WishlistOps web server

---

### "Client secret is invalid"

**Cause**: Secret was revoked or copied incorrectly

**Solution**:
1. Generate a new client secret:
   - Go to OAuth app settings
   - Click "Generate a new client secret"
   - Copy the new secret immediately
2. Update environment variable with new secret
3. Old secret is now revoked

---

### "Access denied"

**Cause**: User didn't authorize or cancelled

**Solution**:
1. Try connecting GitHub again
2. Click "Authorize" when prompted
3. If still failing, revoke and re-create OAuth app

---

## Rate Limits

GitHub API rate limits (with OAuth):
- **5,000 requests per hour** (authenticated)
- **60 requests per hour** (unauthenticated)

**WishlistOps typically uses**: 5-10 requests per week (well within limits!)

---

## Advanced: Multiple Repositories

To monitor multiple game projects:

**Option 1: Single OAuth App**
- One OAuth app can access all your repositories
- Select different repos in WishlistOps dashboard

**Option 2: Multiple OAuth Apps**
- Create separate OAuth apps for each game
- Better separation of concerns
- Easier to revoke access per-game

---

## Additional Resources

- **GitHub OAuth Documentation**: [https://docs.github.com/en/developers/apps/building-oauth-apps](https://docs.github.com/en/developers/apps/building-oauth-apps)
- **Authorized Applications**: [https://github.com/settings/applications](https://github.com/settings/applications)
- **Developer Settings**: [https://github.com/settings/developers](https://github.com/settings/developers)
- **API Rate Limits**: [https://docs.github.com/en/rest/rate-limit](https://docs.github.com/en/rest/rate-limit)

---

## Next Steps

After setting up GitHub OAuth:
1. ✅ GitHub connected
2. ⏭️ Select repository to monitor
3. ⏭️ Configure commit monitoring
4. ⏭️ Test first announcement!

---

**Need help?** Check the [troubleshooting guide](./troubleshooting.md) or [open an issue](https://github.com/your-org/wishlistops/issues).
