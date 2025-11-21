# GitHub Actions Workflow Validation Guide

This guide helps you validate the WishlistOps GitHub Actions workflow before deployment.

## Prerequisites

Install validation tools:

```bash
# Install yamllint (YAML syntax validator)
pip install yamllint

# Install actionlint (GitHub Actions linter)
# macOS
brew install actionlint

# Linux
wget https://github.com/rhysd/actionlint/releases/latest/download/actionlint_linux_amd64.tar.gz
tar xf actionlint_linux_amd64.tar.gz
sudo mv actionlint /usr/local/bin/

# Windows (using Scoop)
scoop install actionlint

# Or download from: https://github.com/rhysd/actionlint/releases
```

## Validation Steps

### 1. Validate YAML Syntax

```bash
yamllint .github/workflows/wishlistops.yml
```

**Expected output:**
```
.github/workflows/wishlistops.yml
  <no errors>
```

**Common issues:**
- Indentation errors (use 2 spaces, not tabs)
- Missing quotes around special characters
- Invalid YAML structure

### 2. Lint GitHub Actions Workflow

```bash
actionlint .github/workflows/wishlistops.yml
```

**Expected output:**
```
.github/workflows/wishlistops.yml: <no errors>
```

**Common warnings you can ignore:**
- `Context access might be invalid: STEAM_API_KEY` - This warning appears because secrets don't exist yet
- `Context access might be invalid: GOOGLE_AI_KEY` - Same as above
- `Context access might be invalid: DISCORD_WEBHOOK_URL` - Same as above

These will resolve once you configure repository secrets.

**Critical errors to fix:**
- Deprecated action versions
- Invalid step syntax
- Missing required fields
- Incorrect environment variable syntax

### 3. Test Locally with `act` (Optional)

```bash
# Install act
# macOS
brew install act

# Linux
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Windows
choco install act-cli

# Test workflow
act -W .github/workflows/wishlistops.yml --list
```

**Expected output:**
```
Stage  Job ID                 Job name                       Workflow name           Workflow file
0      generate-and-notify    Generate Announcement & Notify WishlistOps Automation   wishlistops.yml
```

**Run dry-run test:**
```bash
# Create .secrets file with test values
cat > .secrets << EOF
STEAM_API_KEY=test_key
GOOGLE_AI_KEY=test_key
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/test
EOF

# Run workflow locally
act -W .github/workflows/wishlistops.yml --secret-file .secrets -n
```

The `-n` flag does a dry-run without executing steps.

## Checklist

Before committing the workflow:

- [ ] YAML syntax is valid (`yamllint` passes)
- [ ] Workflow structure is correct (`actionlint` passes)
- [ ] All action versions are latest (v4, v5)
- [ ] Secrets are referenced correctly (not hardcoded)
- [ ] Timeouts are set on all steps
- [ ] Artifacts upload on both success and failure
- [ ] Error notifications are configured
- [ ] Comments explain each step
- [ ] Indentation is consistent (2 spaces)

## Deployment

Once validated:

1. **Commit the workflow:**
   ```bash
   git add .github/workflows/wishlistops.yml
   git commit -m "Add GitHub Actions workflow for WishlistOps automation"
   git push origin main
   ```

2. **Configure repository secrets:**
   - Go to GitHub repository → Settings → Secrets and variables → Actions
   - Add: `STEAM_API_KEY`, `GOOGLE_AI_KEY`, `DISCORD_WEBHOOK_URL`

3. **Test the workflow:**
   ```bash
   # Trigger manually
   gh workflow run wishlistops.yml
   
   # Or create a test tag
   git tag v0.0.1-test
   git push origin v0.0.1-test
   ```

4. **Monitor execution:**
   - Go to Actions tab in GitHub
   - Watch the workflow run in real-time
   - Check logs for any errors

## Troubleshooting

### "Invalid workflow file"
- Run `yamllint` to find syntax errors
- Check indentation (must be 2 spaces)
- Verify all quotes are balanced

### "Action not found"
- Check action versions are correct (@v4, @v5)
- Ensure action names are spelled correctly
- Verify actions exist (e.g., actions/checkout@v4)

### "Missing required secret"
- Add secrets in repository settings
- Verify secret names match workflow file
- Check secret values are not empty

### "Workflow doesn't trigger"
- Verify trigger conditions (tags must match `v*.*.*`)
- Check branch protection rules
- Ensure you have push access

### "Timeout error"
- Check if step timeout is too short
- Verify network connectivity
- Look for infinite loops in scripts

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [yamllint Documentation](https://yamllint.readthedocs.io/)
- [actionlint Repository](https://github.com/rhysd/actionlint)
- [act - Run GitHub Actions locally](https://github.com/nektos/act)

## Quick Reference

```bash
# Validate everything
yamllint .github/workflows/wishlistops.yml && \
actionlint .github/workflows/wishlistops.yml && \
echo "✅ Workflow is valid!"

# Test locally
act -W .github/workflows/wishlistops.yml --list

# Trigger manually (after pushing)
gh workflow run wishlistops.yml

# View workflow runs
gh run list --workflow=wishlistops.yml

# View latest run logs
gh run view --log
```
