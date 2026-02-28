# WishlistOps Deployment Ready Guide

## Best deployment form (recommended)

For this codebase, the fastest reliable production setup is:

1. **Dockerized web service** for dashboard + API (`wishlistops.web_server` via `python -m wishlistops.main setup`)
2. **Managed platform deployment** (Render first, Railway as fallback)
3. **GitHub Actions CI** gating deploys on tests

This matches the product architecture (single Python web process, async HTTP calls, local file operations for banners/screenshots).

## Why this is the best fit right now

- Render supports auto-deploys and CI-gated deploy behavior.
- Render and Railway both support Docker-first deployments with minimal ops burden.
- Your app already has a health endpoint at `/api/health`.
- Steam requires manual post publishing anyway, so a lightweight web service is enough for v1.

## Internet-research constraints that affect architecture

- Steam announcements still require manual posting flow through Steamworks event tools.
- Steam wishlist outcomes improve when updates are announced consistently and tied to meaningful events (updates/discounts/releases).
- Render filesystems are ephemeral unless using attached storage/services; persist important data outside local disk.
- Stripe subscriptions require webhook-driven entitlement handling (`invoice.paid`, failures, cancellation).

## What was added to make this deployable now

- `Dockerfile` for reproducible cloud deployment
- `.dockerignore` to keep image clean and avoid shipping secrets
- `render.yaml` blueprint with health check and env vars
- Host/port runtime config (`--host`, `PORT`, `WISHLISTOPS_HOST`) so service can bind publicly in cloud

## Deploy on Render (10-15 min)

1. Push this repo to GitHub.
2. In Render, create a new Blueprint or Web Service from repo.
3. If using Blueprint, Render reads `render.yaml` automatically.
4. Set secrets in Render environment:
   - `GOOGLE_AI_KEY`
   - `DISCORD_WEBHOOK_URL`
   - `STEAM_API_KEY` (optional but recommended)
5. Deploy and verify health endpoint:
   - `https://<your-service>.onrender.com/api/health`
6. Open app root URL and run setup flow.

## Deploy on Railway (alternative)

1. Create new Railway project from GitHub repo.
2. Railway auto-detects root `Dockerfile`.
3. Add env vars:
   - `PORT=8080` (or Railway-provided `PORT`)
   - `WISHLISTOPS_HOST=0.0.0.0`
   - `GOOGLE_AI_KEY`, `DISCORD_WEBHOOK_URL`, `STEAM_API_KEY`
4. Deploy and validate `/api/health`.

## Hardening needed for larger scale (next)

1. Move `state.json` and generated assets to managed storage (Postgres + object storage).
2. Add auth (team accounts) for hosted mode.
3. Add usage limits and billing gates before opening paid plans.
4. Add queue worker for long-running generation jobs.
5. Add structured observability (error tracking + request metrics).
