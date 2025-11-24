"""
WishlistOps Local Web Server

Launches a beautiful web interface for easy setup and monitoring.
Handles OAuth integrations with Discord, Steam, GitHub, and Google AI.
"""

import asyncio
import json
import logging
import os
import secrets
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.parse import urlencode, parse_qs, urlparse

import aiohttp
from aiohttp import web
from aiohttp_session import setup as setup_session, get_session
from aiohttp_session.cookie_storage import EncryptedCookieStorage

from .config_manager import load_config, save_config, ConfigurationError
from .state_manager import StateManager

logger = logging.getLogger(__name__)

# OAuth Configuration
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")  # Will be set in production
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID", "")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET", "")

# Server Configuration
HOST = "127.0.0.1"
PORT = 8080
BASE_URL = f"http://{HOST}:{PORT}"


class WishlistOpsWebServer:
    """Local web server for WishlistOps dashboard."""
    
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.app = web.Application()
        self.session_secret = secrets.token_bytes(32)
        self.oauth_states: Dict[str, Dict[str, Any]] = {}
        
        # Setup session middleware
        setup_session(self.app, EncryptedCookieStorage(self.session_secret))
        
        # Setup routes
        self._setup_routes()
        
        # Load or create config
        try:
            self.config = load_config(config_path)
        except FileNotFoundError:
            self.config = None
            logger.info("No config found, will create new via setup wizard")
        except ConfigurationError as e:
            # Allow server to start even if secrets/env vars missing so user can supply them
            logger.warning(f"Configuration incomplete: {e}. Launching setup wizard.")
            self.config = None
    
    def _setup_routes(self):
        """Setup all web routes."""
        # Static files
        static_dir = Path(__file__).parent.parent / "dashboard"
        self.app.router.add_static('/static/', static_dir, name='static')
        
        # Main pages
        self.app.router.add_get('/', self.handle_index)
        self.app.router.add_get('/setup', self.handle_setup)
        self.app.router.add_get('/monitor', self.handle_monitor)
        self.app.router.add_get('/commits', self.handle_commits)
        self.app.router.add_get('/test', self.handle_test)
        self.app.router.add_get('/docs', self.handle_docs)
        
        # API endpoints
        self.app.router.add_get('/api/status', self.handle_status)
        self.app.router.add_get('/api/health', self.handle_health)
        self.app.router.add_get('/api/version', self.handle_version)
        self.app.router.add_get('/api/projects', self.handle_projects)
        self.app.router.add_get('/api/config', self.handle_get_config)
        self.app.router.add_post('/api/config', self.handle_save_config)
        self.app.router.add_get('/api/announcements', self.handle_announcements)
        self.app.router.add_get('/api/commits', self.handle_api_commits)
        self.app.router.add_post('/api/test-announcement', self.handle_test_announcement)
        self.app.router.add_get('/api/steam/games', self.handle_steam_games)
        self.app.router.add_get('/api/steam/game/{app_id}', self.handle_steam_game_context)
        self.app.router.add_get('/api/export/announcement/{run_id}', self.handle_export_announcement)
        self.app.router.add_get('/api/export/banner/{filename}', self.handle_export_banner)
        
        # OAuth callbacks
        self.app.router.add_get('/auth/github', self.handle_github_auth)
        self.app.router.add_get('/auth/github/callback', self.handle_github_callback)
        self.app.router.add_get('/auth/discord', self.handle_discord_auth)
        self.app.router.add_get('/auth/discord/callback', self.handle_discord_callback)
        self.app.router.add_post('/auth/google-ai', self.handle_google_ai_auth)
        
        # Logout
        self.app.router.add_post('/auth/logout', self.handle_logout)
    
    async def handle_index(self, request: web.Request) -> web.Response:
        """Serve main dashboard page."""
        session = await get_session(request)
        
        # Check if user is authenticated
        if not session.get('github_token'):
            return web.FileResponse(
                Path(__file__).parent.parent / "dashboard" / "welcome.html"
            )
        
        return web.FileResponse(
            Path(__file__).parent.parent / "dashboard" / "index.html"
        )
    
    async def handle_setup(self, request: web.Request) -> web.Response:
        """Serve setup wizard page."""
        return web.FileResponse(
            Path(__file__).parent.parent / "dashboard" / "setup.html"
        )
    
    async def handle_monitor(self, request: web.Request) -> web.Response:
        """Serve monitoring page."""
        return web.FileResponse(
            Path(__file__).parent.parent / "dashboard" / "monitor.html"
        )
    
    async def handle_commits(self, request: web.Request) -> web.Response:
        """Serve commit history page."""
        return web.FileResponse(
            Path(__file__).parent.parent / "dashboard" / "commits.html"
        )
    
    async def handle_test(self, request: web.Request) -> web.Response:
        """Serve test announcement page."""
        return web.FileResponse(
            Path(__file__).parent.parent / "dashboard" / "test.html"
        )
    
    async def handle_docs(self, request: web.Request) -> web.Response:
        """Serve documentation page."""
        return web.FileResponse(
            Path(__file__).parent.parent / "dashboard" / "docs.html"
        )
    
    async def handle_status(self, request: web.Request) -> web.Response:
        """Get current authentication and setup status."""
        session = await get_session(request)
        
        status = {
            "authenticated": {
                "github": bool(session.get('github_token')),
                "discord": bool(session.get('discord_webhook')),
                "google_ai": bool(session.get('google_ai_key')),
            },
            "config_exists": self.config is not None,
            "projects": []
        }
        
        if session.get('github_token'):
            # Fetch user's repositories
            try:
                repos = await self._fetch_github_repos(session['github_token'])
                status["projects"] = repos
            except Exception as e:
                logger.error(f"Failed to fetch repos: {e}")
        
        return web.json_response(status)
    
    async def handle_health(self, request: web.Request) -> web.Response:
        """Health check endpoint for monitoring."""
        health_data = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "services": {
                "config": self.config is not None,
                "web_server": True
            }
        }
        
        # Check if critical environment variables are set
        env_checks = {
            "STEAM_API_KEY": bool(os.getenv("STEAM_API_KEY")),
            "GOOGLE_AI_KEY": bool(os.getenv("GOOGLE_AI_KEY")),
            "DISCORD_WEBHOOK_URL": bool(os.getenv("DISCORD_WEBHOOK_URL"))
        }
        health_data["environment"] = env_checks
        
        # Determine overall health
        if not any(env_checks.values()):
            health_data["status"] = "degraded"
            health_data["message"] = "No API keys configured"
        
        return web.json_response(health_data)
    
    async def handle_version(self, request: web.Request) -> web.Response:
        """Version information endpoint."""
        version_data = {
            "version": "1.0.0",
            "name": "WishlistOps",
            "description": "Automated Steam announcement generation from Git commits",
            "author": "Your Name",
            "license": "MIT",
            "repository": "https://github.com/yourusername/wishlistops",
            "features": [
                "AI-powered announcement generation",
                "Discord approval workflow",
                "Steam game context integration",
                "Anti-slop content filtering",
                "Git commit analysis",
                "Beautiful web dashboard"
            ]
        }
        return web.json_response(version_data)
    
    async def handle_projects(self, request: web.Request) -> web.Response:
        """Get user's GitHub projects."""
        session = await get_session(request)
        
        if not session.get('github_token'):
            return web.json_response({"error": "Not authenticated"}, status=401)
        
        try:
            repos = await self._fetch_github_repos(session['github_token'])
            return web.json_response({"projects": repos})
        except Exception as e:
            logger.error(f"Failed to fetch projects: {e}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def handle_get_config(self, request: web.Request) -> web.Response:
        """Get current configuration."""
        try:
            if self.config:
                # Return safe config data (no secrets)
                config_data = {
                    "steam": {
                        "app_id": getattr(self.config.steam, 'app_id', ''),
                        "app_name": getattr(self.config.steam, 'app_name', '')
                    } if hasattr(self.config, 'steam') else {},
                    "branding": {
                        "art_style": getattr(self.config.branding, 'art_style', ''),
                        "color_palette": getattr(self.config.branding, 'color_palette', []),
                        "logo_position": getattr(self.config.branding, 'logo_position', 'center'),
                        "logo_size_percent": getattr(self.config.branding, 'logo_size_percent', 30)
                    } if hasattr(self.config, 'branding') else {},
                    "voice": {
                        "tone": getattr(self.config.voice, 'tone', ''),
                        "personality": getattr(self.config.voice, 'personality', ''),
                        "avoid_phrases": getattr(self.config.voice, 'avoid_phrases', [])
                    } if hasattr(self.config, 'voice') else {},
                    "automation": {
                        "enabled": getattr(self.config.automation, 'enabled', True),
                        "trigger_on_tags": getattr(self.config.automation, 'trigger_on_tags', True),
                        "min_days_between_posts": getattr(self.config.automation, 'min_days_between_posts', 7),
                        "require_manual_approval": getattr(self.config.automation, 'require_manual_approval', True)
                    } if hasattr(self.config, 'automation') else {}
                }
                return web.json_response({"config": config_data})
            else:
                return web.json_response({"config": None})
        except Exception as e:
            logger.error(f"Failed to get config: {e}")
            return web.json_response({"config": None})
    
    async def handle_save_config(self, request: web.Request) -> web.Response:
        """Save configuration."""
        session = await get_session(request)
        
        if not session.get('github_token'):
            return web.json_response({"error": "Not authenticated"}, status=401)
        
        try:
            data = await request.json()
            
            # Merge with session credentials
            data['google_ai_key'] = session.get('google_ai_key', '')
            data['discord_webhook_url'] = session.get('discord_webhook', '')
            data['github_token'] = session.get('github_token', '')
            
            # Save to file
            save_config(self.config_path, data)
            self.config = load_config(self.config_path)
            
            return web.json_response({"success": True})
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def handle_announcements(self, request: web.Request) -> web.Response:
        """Get announcement history."""
        try:
            state_manager = StateManager(self.config_path.parent / "state.json")
            history = state_manager.get_announcement_history()
            
            return web.json_response({
                "announcements": [
                    {
                        "title": h.get("title", ""),
                        "timestamp": h.get("timestamp", ""),
                        "project": h.get("project", ""),
                        "status": h.get("status", "pending")
                    }
                    for h in history
                ]
            })
        except Exception as e:
            logger.error(f"Failed to fetch announcements: {e}")
            return web.json_response({"announcements": []})
    
    async def handle_steam_games(self, request: web.Request) -> web.Response:
        """Detect Steam games from user's library."""
        session = await get_session(request)
        
        # Get Steam credentials from session or config
        steam_api_key = session.get('steam_api_key') or os.getenv('STEAM_API_KEY')
        steam_id = session.get('steam_id') or os.getenv('STEAM_ID')
        
        if not steam_api_key:
            return web.json_response({
                "error": "Steam API key not configured",
                "message": "Please add STEAM_API_KEY to your environment or setup",
                "games": []
            })
        
        if not steam_id:
            return web.json_response({
                "error": "Steam ID not configured",
                "message": "Please add STEAM_ID to your environment or setup",
                "games": []
            })
        
        try:
            from .steam_client import SteamClient
            
            client = SteamClient(steam_api_key)
            
            # Get user's owned games
            games = await client.get_owned_games(steam_id)
            
            # Format for response
            games_data = [{
                "app_id": game.app_id,
                "name": game.name,
                "playtime_minutes": game.playtime_minutes,
                "playtime_hours": round(game.playtime_minutes / 60, 1),
                "has_stats": game.has_community_visible_stats,
                "icon_url": f"https://media.steampowered.com/steamcommunity/public/images/apps/{game.app_id}/{game.img_icon_url}.jpg" if game.img_icon_url else None,
                "logo_url": f"https://media.steampowered.com/steamcommunity/public/images/apps/{game.app_id}/{game.img_logo_url}.jpg" if game.img_logo_url else None
            } for game in games]
            
            # Sort by playtime (likely developer games first)
            games_data.sort(key=lambda x: x['playtime_minutes'], reverse=True)
            
            return web.json_response({
                "games": games_data,
                "total": len(games_data),
                "steam_id": steam_id
            })
            
        except Exception as e:
            logger.error(f"Failed to fetch Steam games: {e}", exc_info=True)
            return web.json_response({
                "error": str(e),
                "games": []
            }, status=500)
    
    async def handle_steam_game_context(self, request: web.Request) -> web.Response:
        """Get detailed game context for announcement generation."""
        app_id = request.match_info.get('app_id')
        
        if not app_id:
            return web.json_response({"error": "App ID required"}, status=400)
        
        # Get Steam API key
        steam_api_key = os.getenv('STEAM_API_KEY')
        
        if not steam_api_key:
            return web.json_response({
                "error": "Steam API key not configured",
                "message": "Please add STEAM_API_KEY to your environment"
            }, status=400)
        
        try:
            from .steam_client import SteamClient
            
            client = SteamClient(steam_api_key)
            
            # Get enriched game context
            context = await client.get_game_context(app_id)
            
            return web.json_response({
                "success": True,
                "context": context
            })
            
        except Exception as e:
            logger.error(f"Failed to fetch game context for {app_id}: {e}", exc_info=True)
            return web.json_response({
                "error": str(e),
                "context": None
            }, status=500)
    
    # OAuth Handlers - GitHub
    
    async def handle_github_auth(self, request: web.Request) -> web.Response:
        """Initiate GitHub OAuth flow."""
        state = secrets.token_urlsafe(32)
        self.oauth_states[state] = {"service": "github", "created_at": datetime.now()}
        
        # If no client ID, use device flow or personal token
        if not GITHUB_CLIENT_ID:
            return web.Response(
                text="""
                <html>
                <head><title>GitHub Authentication</title></head>
                <body style="font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px;">
                    <h2>GitHub Personal Access Token</h2>
                    <p>To connect GitHub, create a Personal Access Token:</p>
                    <ol>
                        <li>Go to <a href="https://github.com/settings/tokens/new" target="_blank">GitHub Settings → Tokens</a></li>
                        <li>Click "Generate new token (classic)"</li>
                        <li>Name it "WishlistOps"</li>
                        <li>Select scopes: <code>repo</code>, <code>workflow</code></li>
                        <li>Click "Generate token"</li>
                        <li>Copy the token and paste below</li>
                    </ol>
                    <form method="POST" action="/auth/github/token">
                        <input type="text" name="token" placeholder="ghp_..." style="width: 100%; padding: 10px; margin: 10px 0;">
                        <button type="submit" style="padding: 10px 20px; background: #28a745; color: white; border: none; cursor: pointer;">Connect</button>
                    </form>
                </body>
                </html>
                """,
                content_type='text/html'
            )
        
        # OAuth flow
        params = {
            "client_id": GITHUB_CLIENT_ID,
            "redirect_uri": f"{BASE_URL}/auth/github/callback",
            "scope": "repo workflow",
            "state": state
        }
        
        auth_url = f"https://github.com/login/oauth/authorize?{urlencode(params)}"
        raise web.HTTPFound(auth_url)
    
    async def handle_github_callback(self, request: web.Request) -> web.Response:
        """Handle GitHub OAuth callback."""
        code = request.query.get('code')
        state = request.query.get('state')
        
        if not code or state not in self.oauth_states:
            return web.Response(text="Invalid OAuth state", status=400)
        
        # Exchange code for token
        async with aiohttp.ClientSession() as client:
            async with client.post(
                "https://github.com/login/oauth/access_token",
                data={
                    "client_id": GITHUB_CLIENT_ID,
                    "client_secret": GITHUB_CLIENT_SECRET,
                    "code": code
                },
                headers={"Accept": "application/json"}
            ) as resp:
                data = await resp.json()
                access_token = data.get('access_token')
        
        if not access_token:
            return web.Response(text="Failed to get access token", status=500)
        
        # Store in session
        session = await get_session(request)
        session['github_token'] = access_token
        
        # Cleanup
        del self.oauth_states[state]
        
        raise web.HTTPFound('/')
    
    # OAuth Handlers - Discord
    
    async def handle_discord_auth(self, request: web.Request) -> web.Response:
        """Guide user to create Discord webhook."""
        return web.Response(
            text="""
            <html>
            <head><title>Discord Webhook Setup</title></head>
            <body style="font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px;">
                <h2>Discord Webhook Setup</h2>
                <p>To receive approval requests in Discord:</p>
                <ol>
                    <li>Open your Discord server</li>
                    <li>Go to Server Settings → Integrations → Webhooks</li>
                    <li>Click "New Webhook"</li>
                    <li>Name it "WishlistOps"</li>
                    <li>Choose a channel (e.g., #game-marketing)</li>
                    <li>Click "Copy Webhook URL"</li>
                    <li>Paste below</li>
                </ol>
                <img src="/static/images/discord-webhook-guide.png" alt="Discord Webhook Guide" style="max-width: 100%; border: 1px solid #ddd; margin: 20px 0;">
                <form method="POST" action="/auth/discord/webhook">
                    <input type="url" name="webhook" placeholder="https://discord.com/api/webhooks/..." style="width: 100%; padding: 10px; margin: 10px 0;" required>
                    <button type="submit" style="padding: 10px 20px; background: #5865F2; color: white; border: none; cursor: pointer;">Connect Discord</button>
                </form>
                <p><small>Your webhook URL is stored securely on your local machine only.</small></p>
            </body>
            </html>
            """,
            content_type='text/html'
        )
    
    async def handle_discord_callback(self, request: web.Request) -> web.Response:
        """Handle Discord webhook submission."""
        data = await request.post()
        webhook_url = data.get('webhook')
        
        if not webhook_url or not webhook_url.startswith('https://discord.com/api/webhooks/'):
            return web.Response(text="Invalid webhook URL", status=400)
        
        # Verify webhook works
        async with aiohttp.ClientSession() as client:
            try:
                async with client.post(
                    webhook_url,
                    json={"content": "✅ WishlistOps connected successfully!"}
                ) as resp:
                    if resp.status not in (200, 204):
                        return web.Response(text="Webhook verification failed", status=400)
            except Exception as e:
                return web.Response(text=f"Webhook error: {e}", status=400)
        
        # Store in session
        session = await get_session(request)
        session['discord_webhook'] = webhook_url
        
        raise web.HTTPFound('/')
    
    # Google AI Setup
    
    async def handle_google_ai_auth(self, request: web.Request) -> web.Response:
        """Handle Google AI API key submission."""
        data = await request.json()
        api_key = data.get('api_key')
        
        if not api_key or not api_key.startswith('AIza'):
            return web.json_response({"error": "Invalid API key format"}, status=400)
        
        # Store in session
        session = await get_session(request)
        session['google_ai_key'] = api_key
        
        return web.json_response({"success": True})
    
    async def handle_logout(self, request: web.Request) -> web.Response:
        """Clear session and logout."""
        session = await get_session(request)
        session.clear()
        
        return web.json_response({"success": True})
    
    # Commit History API
    
    async def handle_api_commits(self, request: web.Request) -> web.Response:
        """Get commit history with announcement associations."""
        try:
            from .git_parser import GitParser
            
            # Get repo path from config or use current directory
            repo_path = Path.cwd()
            if self.config and hasattr(self.config, 'repo_path'):
                repo_path = Path(self.config.repo_path)
            
            parser = GitParser(repo_path)
            
            # Get commits (limit to last 100)
            all_commits = parser.get_commits_since_tag(None)[:100]
            
            # Load state to check which commits triggered announcements
            state_path = self.config_path.parent / "state.json"
            state_manager = StateManager(state_path) if state_path.exists() else None
            
            # Build response with commit details
            commits_data = []
            for commit in all_commits:
                commit_data = {
                    "sha": commit.sha,
                    "message": commit.message.split('\\n')[0][:100],  # First line only
                    "full_message": commit.message,
                    "author": commit.author,
                    "date": commit.date.isoformat(),
                    "is_player_facing": commit.is_player_facing,
                    "commit_type": commit.commit_type,
                    "files_changed": commit.files_changed[:10],  # Limit file list
                    "has_screenshot": commit.screenshot_path is not None,
                    "triggered_announcement": False  # Will be populated from state
                }
                
                # Check if this commit triggered an announcement
                if state_manager:
                    for run in state_manager.state.recent_runs:
                        if run.draft_title and commit.sha in commit.message:
                            commit_data["triggered_announcement"] = True
                            commit_data["announcement_title"] = run.draft_title
                            commit_data["announcement_timestamp"] = run.timestamp
                            break
                
                commits_data.append(commit_data)
            
            return web.json_response({
                "commits": commits_data,
                "total": len(commits_data),
                "player_facing_count": sum(1 for c in commits_data if c["is_player_facing"]),
                "announcement_count": sum(1 for c in commits_data if c["triggered_announcement"])
            })
        
        except Exception as e:
            logger.error(f"Failed to fetch commits: {e}", exc_info=True)
            return web.json_response({"error": str(e), "commits": []}, status=500)
    
    # Test Announcement API
    
    async def handle_test_announcement(self, request: web.Request) -> web.Response:
        """Create and send a test announcement."""
        try:
            from .discord_notifier import DiscordNotifier
            from .models import AnnouncementDraft
            
            data = await request.json()
            title = data.get('title', '')
            body = data.get('body', '')
            
            if not title or not body:
                return web.json_response({"error": "Title and body required"}, status=400)
            
            # Create draft
            draft = AnnouncementDraft(
                title=title,
                body=body,
                created_at=datetime.now().isoformat()
            )
            
            # Send to Discord if configured
            discord_sent = False
            if self.config and hasattr(self.config, 'discord_webhook_url'):
                notifier = DiscordNotifier(self.config.discord_webhook_url)
                try:
                    await notifier.send_approval_request(
                        title=draft.title,
                        body=draft.body,
                        game_name=getattr(self.config.steam, 'app_name', 'Test Game'),
                        tag="manual-test",
                        steam_app_id=getattr(self.config.steam, 'app_id', None)
                    )
                    discord_sent = True
                except Exception as e:
                    logger.warning(f"Failed to send to Discord: {e}")
            
            # Generate Steam URL (manual posting required)
            steam_url = None
            if self.config and hasattr(self.config, 'steam'):
                app_id = getattr(self.config.steam, 'app_id', None)
                if app_id:
                    steam_url = f"https://partner.steamgames.com/apps/landing/{app_id}"
            
            return web.json_response({
                "success": True,
                "draft": {
                    "title": draft.title,
                    "body": draft.body,
                    "created_at": draft.created_at
                },
                "discord_sent": discord_sent,
                "steam_url": steam_url,
                "note": "Steam has no public posting API. Visit the Steam URL to manually publish."
            })
        
        except Exception as e:
            logger.error(f"Failed to create test announcement: {e}", exc_info=True)
            return web.json_response({"error": str(e)}, status=500)
    
    async def handle_export_announcement(self, request: web.Request) -> web.Response:
        """Export announcement as downloadable text file."""
        run_id = request.match_info.get('run_id')
        
        if not run_id:
            return web.json_response({"error": "Run ID required"}, status=400)
        
        try:
            # Load state to find the announcement
            state_manager = StateManager()
            runs = state_manager.load_recent_runs(limit=100)
            
            # Find the specific run
            target_run = None
            for run in runs:
                if run.id == run_id:
                    target_run = run
                    break
            
            if not target_run or not target_run.draft:
                return web.json_response({"error": "Announcement not found"}, status=404)
            
            # Format announcement text
            announcement_text = f"{target_run.draft.title}\n\n{target_run.draft.body}"
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"announcement_{timestamp}.txt"
            
            # Return as downloadable file
            return web.Response(
                body=announcement_text.encode('utf-8'),
                headers={
                    'Content-Type': 'text/plain; charset=utf-8',
                    'Content-Disposition': f'attachment; filename="{filename}"'
                }
            )
        
        except Exception as e:
            logger.error(f"Failed to export announcement: {e}", exc_info=True)
            return web.json_response({"error": str(e)}, status=500)
    
    async def handle_export_banner(self, request: web.Request) -> web.Response:
        """Export banner image as downloadable file."""
        filename = request.match_info.get('filename')
        
        if not filename:
            return web.json_response({"error": "Filename required"}, status=400)
        
        try:
            # Look for banner in banners directory
            banners_dir = Path("wishlistops/banners")
            banner_path = banners_dir / filename
            
            if not banner_path.exists():
                return web.json_response({"error": "Banner not found"}, status=404)
            
            # Read banner file
            banner_bytes = banner_path.read_bytes()
            
            # Return as downloadable file
            return web.Response(
                body=banner_bytes,
                headers={
                    'Content-Type': 'image/png',
                    'Content-Disposition': f'attachment; filename="{filename}"'
                }
            )
        
        except Exception as e:
            logger.error(f"Failed to export banner: {e}", exc_info=True)
            return web.json_response({"error": str(e)}, status=500)
    
    # Helper methods
    
    async def _fetch_github_repos(self, token: str) -> list:
        """Fetch user's GitHub repositories."""
        async with aiohttp.ClientSession() as client:
            async with client.get(
                "https://api.github.com/user/repos",
                headers={
                    "Authorization": f"token {token}",
                    "Accept": "application/vnd.github.v3+json"
                },
                params={"sort": "updated", "per_page": 100}
            ) as resp:
                if resp.status != 200:
                    raise Exception(f"GitHub API error: {resp.status}")
                
                repos = await resp.json()
                return [
                    {
                        "name": repo["name"],
                        "full_name": repo["full_name"],
                        "description": repo.get("description", ""),
                        "url": repo["html_url"],
                        "updated_at": repo["updated_at"]
                    }
                    for repo in repos
                ]
    
    async def start(self):
        """Start the web server."""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, HOST, PORT)
        await site.start()
        
        url = f"{BASE_URL}/"
        logger.info(f"WishlistOps dashboard running at {url}")
        print(f"\n{'='*60}")
        print(f"🎮 WishlistOps Dashboard")
        print(f"{'='*60}")
        print(f"\n✨ Open your browser at: {url}")
        print(f"\n   - Setup wizard: {url}setup")
        print(f"   - Monitor: {url}monitor")
        print(f"   - Docs: {url}docs")
        print(f"\n{'='*60}\n")
        
        # Auto-open browser
        webbrowser.open(url)
        
        # Keep running
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            logger.info("Shutting down server...")
            await runner.cleanup()


def run_server(config_path: Optional[Path] = None):
    """Run the WishlistOps web server."""
    if config_path is None:
        config_path = Path("wishlistops/config.json")
    
    server = WishlistOpsWebServer(config_path)
    asyncio.run(server.start())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_server()
