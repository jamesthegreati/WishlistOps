# WishlistOps Production Deployment Guide

> **Deploy WishlistOps for reliable, automated Steam announcements**

## Table of Contents

1. [Deployment Options](#deployment-options)
2. [GitHub Actions (Recommended)](#github-actions-recommended)
3. [Local Server](#local-server)
4. [Docker Deployment](#docker-deployment)
5. [Security Best Practices](#security-best-practices)
6. [Monitoring](#monitoring)
7. [Backup and Recovery](#backup-and-recovery)

---

## Deployment Options

### Option 1: GitHub Actions (Recommended)
- **Best for**: Automated announcements on every commit
- **Cost**: Free (GitHub Actions included)
- **Maintenance**: Minimal
- **Setup time**: 10 minutes

### Option 2: Local Server
- **Best for**: Manual control, testing, development
- **Cost**: Free (runs on your machine)
- **Maintenance**: Manual startup
- **Setup time**: 5 minutes

### Option 3: Docker
- **Best for**: Cloud deployment, scaling, production
- **Cost**: Variable (hosting costs)
- **Maintenance**: Automated
- **Setup time**: 20 minutes

---

## GitHub Actions (Recommended)

### Prerequisites

- GitHub repository with your game's code
- GitHub Secrets configured

### Step 1: Add GitHub Secrets

Go to: **Your Repository** → **Settings** → **Secrets and variables** → **Actions**

Add these secrets:

```
STEAM_API_KEY=your_steam_web_api_key
GOOGLE_AI_KEY=your_google_gemini_api_key
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
STEAM_ID=your_17_digit_steamid64 (optional)
```

### Step 2: Create Workflow File

Create `.github/workflows/wishlistops.yml`:

```yaml
name: WishlistOps - Automated Announcements

on:
  push:
    branches: [main, master]
    paths-ignore:
      - 'docs/**'
      - '*.md'
      - '.github/**'
      - 'tests/**'

  # Allow manual triggering
  workflow_dispatch:

  # Optional: Run on schedule (e.g., weekly)
  # schedule:
  #   - cron: '0 0 * * 0'  # Every Sunday at midnight

jobs:
  generate-announcement:
    name: Generate Steam Announcement
    runs-on: ubuntu-latest
    
    permissions:
      contents: read
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for commit analysis
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.14'
          cache: 'pip'
      
      - name: Install WishlistOps
        run: |
          python -m pip install --upgrade pip
          pip install wishlistops
      
      - name: Generate announcement
        env:
          STEAM_API_KEY: ${{ secrets.STEAM_API_KEY }}
          GOOGLE_AI_KEY: ${{ secrets.GOOGLE_AI_KEY }}
          DISCORD_WEBHOOK_URL: ${{ secrets.DISCORD_WEBHOOK_URL }}
          STEAM_ID: ${{ secrets.STEAM_ID }}
        run: |
          wishlistops --log-level INFO
      
      - name: Upload artifacts (optional)
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: wishlistops-output
          path: |
            wishlistops/banners/
            wishlistops/state/
          retention-days: 30
```

### Step 3: Configure WishlistOps

Add `config.json` to your repository:

```json
{
  "version": "1.0",
  "steam": {
    "app_id": "YOUR_APP_ID",
    "app_name": "Your Game Name"
  },
  "branding": {
    "art_style": "your game's art style description",
    "color_palette": ["#color1", "#color2"],
    "logo_path": "assets/logo.png"
  },
  "voice": {
    "tone": "friendly and enthusiastic",
    "personality": "excited indie developer"
  },
  "automation": {
    "enabled": true,
    "min_commits": 3,
    "require_approval": true
  }
}
```

### Step 4: Add Logo Asset

Place your game logo at `assets/logo.png` (transparent PNG recommended)

### Step 5: Test the Workflow

1. Commit and push to `main` branch
2. Check **Actions** tab in GitHub
3. Verify workflow runs successfully
4. Check Discord for announcement approval

### Customization

#### Run on specific branches

```yaml
on:
  push:
    branches: [main, release/*]
```

#### Run only with specific tags

```yaml
on:
  push:
    tags:
      - 'v*'  # Triggers on v1.0.0, v2.1.0, etc.
```

#### Add conditions

```yaml
- name: Generate announcement
  if: github.event_name == 'push' && startsWith(github.ref, 'refs/tags/v')
  env:
    STEAM_API_KEY: ${{ secrets.STEAM_API_KEY }}
    ...
```

---

## Local Server

### Prerequisites

- Python 3.11+
- pip

### Setup

```bash
# Install
pip install wishlistops

# Create .env file
cat > .env << EOF
STEAM_API_KEY=your_steam_key
GOOGLE_AI_KEY=your_google_key
DISCORD_WEBHOOK_URL=your_discord_webhook
STEAM_ID=your_steamid64
EOF

# Launch web interface
wishlistops-web
```

### Run as Background Service

#### Linux/macOS (systemd)

Create `/etc/systemd/system/wishlistops.service`:

```ini
[Unit]
Description=WishlistOps Web Dashboard
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/your/project
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
EnvironmentFile=/path/to/your/.env
ExecStart=/usr/local/bin/wishlistops-web
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable wishlistops
sudo systemctl start wishlistops
sudo systemctl status wishlistops
```

#### Windows (NSSM)

```powershell
# Install NSSM
choco install nssm

# Install service
nssm install WishlistOps "C:\Python314\Scripts\wishlistops-web.exe"
nssm set WishlistOps AppDirectory "C:\path\to\your\project"
nssm set WishlistOps AppEnvironmentExtra STEAM_API_KEY=your_key GOOGLE_AI_KEY=your_key DISCORD_WEBHOOK_URL=your_webhook

# Start service
nssm start WishlistOps
```

---

## Docker Deployment

### Dockerfile

Create `Dockerfile`:

```dockerfile
FROM python:3.14-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy application
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Expose web interface port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/api/health || exit 1

# Run web interface by default
CMD ["wishlistops-web"]
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  wishlistops:
    build: .
    container_name: wishlistops
    restart: unless-stopped
    ports:
      - "8080:8080"
    environment:
      - STEAM_API_KEY=${STEAM_API_KEY}
      - GOOGLE_AI_KEY=${GOOGLE_AI_KEY}
      - DISCORD_WEBHOOK_URL=${DISCORD_WEBHOOK_URL}
      - STEAM_ID=${STEAM_ID}
    volumes:
      - ./config.json:/app/wishlistops/config.json:ro
      - ./assets:/app/assets:ro
      - banners:/app/wishlistops/banners
      - state:/app/wishlistops/state
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

volumes:
  banners:
  state:
```

### Deploy

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Update and restart
git pull
docker-compose up -d --build
```

### Cloud Deployment

#### AWS ECS

```bash
# Build and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin your-account.dkr.ecr.us-east-1.amazonaws.com
docker build -t wishlistops .
docker tag wishlistops:latest your-account.dkr.ecr.us-east-1.amazonaws.com/wishlistops:latest
docker push your-account.dkr.ecr.us-east-1.amazonaws.com/wishlistops:latest

# Create ECS task definition and service (via AWS Console or CLI)
```

#### Google Cloud Run

```bash
# Build and deploy
gcloud builds submit --tag gcr.io/your-project/wishlistops
gcloud run deploy wishlistops \
  --image gcr.io/your-project/wishlistops \
  --platform managed \
  --region us-central1 \
  --set-env-vars STEAM_API_KEY=your_key,GOOGLE_AI_KEY=your_key,DISCORD_WEBHOOK_URL=your_webhook
```

---

## Security Best Practices

### 1. Secret Management

**DO**:
- Use environment variables for all secrets
- Use GitHub Secrets for CI/CD
- Use cloud provider secret managers (AWS Secrets Manager, Google Secret Manager)
- Rotate API keys regularly

**DON'T**:
- Commit secrets to Git
- Share API keys in plain text
- Use same keys across environments

### 2. Network Security

```bash
# Allow only specific IPs (if self-hosting)
iptables -A INPUT -p tcp --dport 8080 -s YOUR_IP -j ACCEPT
iptables -A INPUT -p tcp --dport 8080 -j DROP

# Use reverse proxy (nginx)
server {
    listen 80;
    server_name wishlistops.yourdomain.com;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. Access Control

- Use strong passwords
- Enable 2FA on GitHub account
- Limit repository access
- Audit webhook URLs regularly

### 4. Rate Limiting

WishlistOps has built-in rate limiting:
- Google AI: 60 requests/minute
- Steam API: Respects API limits
- Discord: 2-second delays between webhooks

### 5. Data Privacy

- Announcements stored locally only
- No telemetry or tracking
- Logs contain no sensitive data
- State files can be encrypted

---

## Monitoring

### Health Checks

```bash
# Check if service is running
curl http://localhost:8080/api/health

# Expected response
{
  "status": "healthy",
  "timestamp": "2025-11-24T12:00:00",
  "version": "1.0.0",
  "services": {
    "config": true,
    "web_server": true
  },
  "environment": {
    "STEAM_API_KEY": true,
    "GOOGLE_AI_KEY": true,
    "DISCORD_WEBHOOK_URL": true
  }
}
```

### Logging

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
wishlistops-web

# Log to file
wishlistops-web > wishlistops.log 2>&1

# Rotate logs (logrotate)
cat > /etc/logrotate.d/wishlistops << EOF
/var/log/wishlistops.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
}
EOF
```

### Metrics

Track these metrics:
- Announcement success rate
- Average generation time
- API call failures
- Discord delivery rate

### Alerts

Set up alerts for:
- Service downtime
- API key expiration
- Repeated failures
- Disk space (for banners)

---

## Backup and Recovery

### What to Backup

```bash
# Configuration
wishlistops/config.json

# State (announcement history)
wishlistops/state/runs.json

# Generated banners
wishlistops/banners/

# Logo assets
assets/logo.png
```

### Automated Backup Script

```bash
#!/bin/bash
# backup-wishlistops.sh

BACKUP_DIR="/backups/wishlistops"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Backup config and state
tar -czf "$BACKUP_DIR/wishlistops_$DATE.tar.gz" \
    wishlistops/config.json \
    wishlistops/state/ \
    wishlistops/banners/ \
    assets/

# Keep only last 30 days
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_DIR/wishlistops_$DATE.tar.gz"
```

### Recovery

```bash
# Restore from backup
tar -xzf wishlistops_20251124_120000.tar.gz -C /path/to/your/project

# Verify config
wishlistops --dry-run

# Restart service
sudo systemctl restart wishlistops
```

---

## Performance Tuning

### Optimize for Large Repos

```json
{
  "automation": {
    "min_commits": 5,
    "max_commits_analyzed": 20,
    "commit_lookback_days": 7
  }
}
```

### Cache Steam API Responses

```python
# Future enhancement: Add caching layer
# For now, Steam API calls are minimal (1-2 per announcement)
```

### Reduce Banner Size

```json
{
  "branding": {
    "banner_quality": 85,
    "banner_width": 1920,
    "banner_height": 1080
  }
}
```

---

## Scaling

### Horizontal Scaling

Not needed for typical usage (1-10 announcements/day)

For high-volume scenarios:
- Use message queue (Redis, RabbitMQ)
- Separate web server from workers
- Load balance multiple instances

### Vertical Scaling

Minimum requirements:
- **CPU**: 1 core
- **RAM**: 512MB
- **Disk**: 1GB (for banners)

Recommended:
- **CPU**: 2 cores
- **RAM**: 2GB
- **Disk**: 10GB

---

## Troubleshooting Production

### Service Won't Start

```bash
# Check logs
journalctl -u wishlistops -n 50

# Verify Python version
python --version  # Should be 3.11+

# Verify dependencies
pip list | grep wishlistops

# Reinstall
pip uninstall wishlistops
pip install wishlistops
```

### High Memory Usage

```bash
# Check Python process
ps aux | grep wishlistops

# Limit memory (systemd)
[Service]
MemoryLimit=1G
```

### Disk Space Issues

```bash
# Check banner directory
du -sh wishlistops/banners/

# Clean old banners (keep last 30 days)
find wishlistops/banners/ -name "*.png" -mtime +30 -delete
```

---

## Updates

### Update WishlistOps

```bash
# Using pip
pip install --upgrade wishlistops

# From source
git pull
pip install -e .

# Restart service
sudo systemctl restart wishlistops
```

### Breaking Changes

Check CHANGELOG.md before updating:
- https://github.com/jamesthegreati/WishlistOps/blob/main/CHANGELOG.md

---

## Support

Production deployment issues?

- 📖 **Documentation**: https://github.com/jamesthegreati/WishlistOps
- 🐛 **Issues**: https://github.com/jamesthegreati/WishlistOps/issues
- 💬 **Discussions**: https://github.com/jamesthegreati/WishlistOps/discussions
- 📧 **Email**: support@wishlistops.dev

---

*Production-ready deployment for indie game developers*
