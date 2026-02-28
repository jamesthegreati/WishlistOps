"""
Simple test server for WishlistOps dashboard.

Run with: python test_server.py
"""

import webbrowser
from pathlib import Path
from aiohttp import web
import aiohttp_cors

async def handle_index(request):
    """Serve index page."""
    dashboard_dir = Path(__file__).parent / "dashboard"
    return web.FileResponse(dashboard_dir / "index.html")

async def handle_docs(request):
    """Serve docs page."""
    dashboard_dir = Path(__file__).parent / "dashboard"
    return web.FileResponse(dashboard_dir / "docs.html")

async def handle_setup(request):
    """Serve setup page."""
    dashboard_dir = Path(__file__).parent / "dashboard"
    return web.FileResponse(dashboard_dir / "setup.html")

async def handle_monitor(request):
    """Serve monitor page."""
    dashboard_dir = Path(__file__).parent / "dashboard"
    return web.FileResponse(dashboard_dir / "monitor.html")

async def handle_guide(request):
    """Serve guide markdown as HTML."""
    guide_name = request.match_info['name']
    guide_path = Path(__file__).parent / "dashboard" / "guides" / f"{guide_name}.md"
    
    if not guide_path.exists():
        return web.Response(text="Guide not found", status=404)
    
    md_content = guide_path.read_text(encoding='utf-8')
    
    # Simple markdown to HTML conversion
    html = f"""
    <html>
    <head>
        <title>{guide_name.replace('_', ' ').title()} - WishlistOps</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; }}
            h1, h2, h3 {{ color: #333; }}
            code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 3px; }}
            pre {{ background: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; }}
            a {{ color: #0366d6; }}
        </style>
    </head>
    <body>
        <pre>{md_content}</pre>
        <p><a href="/docs">← Back to Documentation</a></p>
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')

def main():
    app = web.Application()
    
    # Setup routes
    dashboard_dir = Path(__file__).parent / "dashboard"
    app.router.add_static('/static', dashboard_dir, name='static')
    app.router.add_get('/', handle_index)
    app.router.add_get('/docs', handle_docs)
    app.router.add_get('/setup', handle_setup)
    app.router.add_get('/monitor', handle_monitor)
    app.router.add_get('/guides/{name}', handle_guide)
    
    # Setup CORS
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
        )
    })
    
    for route in list(app.router.routes()):
        if not isinstance(route.resource, web.StaticResource):
            cors.add(route)
    
    print("Starting WishlistOps Test Server...")
    print("Dashboard: http://localhost:5500")
    print("Documentation: http://localhost:5500/docs")
    print("Setup: http://localhost:5500/setup")
    print("Monitor: http://localhost:5500/monitor")
    print("\nPress Ctrl+C to stop")
    
    # Open browser
    webbrowser.open('http://localhost:5500')
    
    web.run_app(app, host='127.0.0.1', port=5500)

if __name__ == "__main__":
    main()
