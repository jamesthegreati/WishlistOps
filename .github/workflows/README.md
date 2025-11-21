# WishlistOps GitHub Actions Workflow

This directory contains the GitHub Actions workflow for automating Steam marketing announcements.

## Workflow File

- `wishlistops.yml` - Main automation workflow

## Setup Instructions

### 1. Configure Repository Secrets

Navigate to your GitHub repository settings and add the following secrets:

**Settings → Secrets and variables → Actions → New repository secret**

| Secret Name | Description | How to Get |
|-------------|-------------|------------|
| `STEAM_API_KEY` | Steam Web API key | [Steam API Key Registration](https://steamcommunity.com/dev/apikey) |
| `GOOGLE_AI_KEY` | Google AI (Gemini) API key | [Google AI Studio](https://makersuite.google.com/app/apikey) |
| `DISCORD_WEBHOOK_URL` | Discord webhook for notifications | Discord Server Settings → Integrations → Webhooks |

### 2. Create Configuration File

Ensure `wishlistops/config.json` exists in your repository with your game configuration.

### 3. Trigger the Workflow

The workflow can be triggered in three ways:

#### A. Git Tag Push (Recommended)
```bash
git tag v1.0.0
git push origin v1.0.0
```

#### B. Manual Dispatch
1. Go to **Actions** tab in GitHub
2. Select **WishlistOps Automation** workflow
3. Click **Run workflow**
4. Configure options:
   - **Dry run**: Test without posting to Steam
   - **Force run**: Bypass rate limiting
   - **Verbose**: Enable debug logging

#### C. Scheduled Run (Optional)
Uncomment the `schedule` section in `wishlistops.yml` to enable weekly automation.

## Workflow Steps

1. **Checkout repository** - Fetches full Git history
2. **Set up Python** - Installs Python 3.11 with pip caching
3. **Install dependencies** - Installs packages from requirements.txt
4. **Verify configuration** - Checks config.json exists
5. **Run automation** - Executes main WishlistOps script
6. **Upload artifacts** - Saves logs and drafts for debugging
7. **Upload images** - Saves generated banners (if any)
8. **Notify on failure** - Sends Discord alert if workflow fails

## Debugging

### View Workflow Logs
1. Go to **Actions** tab
2. Click on the workflow run
3. Expand each step to see detailed logs

### Download Artifacts
1. Go to **Actions** tab
2. Click on the workflow run
3. Scroll to **Artifacts** section
4. Download `wishlistops-logs-XXX` or `wishlistops-images-XXX`

### Common Issues

**"Missing required secrets"**
- Add STEAM_API_KEY, GOOGLE_AI_KEY, and DISCORD_WEBHOOK_URL to repository secrets

**"config.json not found"**
- Create wishlistops/config.json with your game configuration

**"Workflow timeout"**
- Check logs for API errors or network issues
- Workflow has 10-minute timeout to prevent runaway costs

**"Rate limit exceeded"**
- Steam allows max 1 post per week
- Use `force_run` option to bypass (use sparingly)

## Testing Locally

### Option 1: Using `act` (GitHub Actions locally)
```bash
# Install act: https://github.com/nektos/act
act -W .github/workflows/wishlistops.yml --secret-file .secrets
```

### Option 2: Direct Python execution
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Run with dry-run mode
python -m wishlistops.main --config wishlistops/config.json --dry-run
```

## Workflow Permissions

The workflow uses minimal permissions:
- `contents: read` - Read repository files
- `actions: write` - Upload artifacts

It does NOT have permission to:
- Write to repository
- Create releases
- Modify issues/PRs

## Cost Considerations

**This workflow costs $0** when run on:
- Public repositories (GitHub Actions free tier: unlimited minutes)
- Private repositories (GitHub Actions free tier: 2,000 minutes/month)

Average execution time: **2-3 minutes** per run

## Monitoring

### Success Indicators
- ✅ All steps complete successfully
- 📤 Draft sent to Discord for approval
- 📊 Artifacts uploaded with logs and images

### Failure Indicators
- ❌ Red X on workflow run
- 🔔 Discord notification sent
- 📋 Error logs in artifacts

## Security Notes

- Never commit API keys to the repository
- All secrets are stored encrypted in GitHub
- Secrets are only accessible during workflow execution
- Logs automatically redact secret values

## Further Reading

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [WishlistOps Architecture](../../04_WishlistOps_System_Architecture_Diagrams.md)
- [Build Plan](../../BUILD_PLAN_Week1_Critical_Features.md)
