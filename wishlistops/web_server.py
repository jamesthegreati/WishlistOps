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

from .config_manager import load_config, save_config
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
            logger.info("No config found, will create new")
    
    def _setup_routes(self):
        """Setup all web routes."""
        # Static files
        static_dir = Path(__file__).parent.parent / "dashboard"
        self.app.router.add_static('/static/', static_dir, name='static')
        
        # Main pages
        self.app.router.add_get('/', self.handle_index)
        self.app.router.add_get('/setup', self.handle_setup)
        self.app.router.add_get('/monitor', self.handle_monitor)
        self.app.router.add_get('/docs', self.handle_docs)
        
        # API endpoints
        self.app.router.add_get('/api/status', self.handle_status)
        self.app.router.add_get('/api/projects', self.handle_projects)
        self.app.router.add_post('/api/config', self.handle_save_config)
        self.app.router.add_get('/api/announcements', self.handle_announcements)
        self.app.router.add_get('/api/steam/games', self.handle_steam_games)
        
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
        """Detect Steam games from GitHub repos."""
        session = await get_session(request)
        
        if not session.get('github_token'):
            return web.json_response({"error": "Not authenticated"}, status=401)
        
        # TODO: Implement Steam game detection
        # This would scan repos for Steam app IDs in configs
        return web.json_response({"games": []})
    
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
