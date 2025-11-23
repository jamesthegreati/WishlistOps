"""
WishlistOps CLI Entry Point.

Provides command-line interface for launching the web server
and accessing WishlistOps functionality.
"""

import sys
import asyncio
import logging
from pathlib import Path

# Check if web server is available
try:
    from .web_server import WishlistOpsWebServer
    WEB_SERVER_AVAILABLE = True
except ImportError:
    WEB_SERVER_AVAILABLE = False

from .main import main as run_workflow


logger = logging.getLogger(__name__)


def launch_web_interface():
    """
    Launch the WishlistOps web interface.
    
    This opens a browser automatically to the local web server.
    """
    if not WEB_SERVER_AVAILABLE:
        print("❌ Web server dependencies not installed.")
        print("Install with: pip install wishlistops[web]")
        sys.exit(1)
    
    print("🚀 Launching WishlistOps Web Interface...")
    server = WishlistOpsWebServer()
    
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def main_cli():
    """
    Main CLI entry point.
    
    Routes to appropriate command based on arguments.
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        prog="wishlistops",
        description="WishlistOps - Automated Steam Marketing for Indie Developers",
        epilog="Visit https://github.com/your-org/wishlistops for documentation"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Web server command
    web_parser = subparsers.add_parser(
        "web",
        help="Launch web interface"
    )
    web_parser.add_argument(
        "--port",
        type=int,
        default=5500,
        help="Port to run server on (default: 5500)"
    )
    web_parser.add_argument(
        "--host",
        default="localhost",
        help="Host to bind to (default: localhost)"
    )
    
    # Workflow command
    workflow_parser = subparsers.add_parser(
        "run",
        help="Run automation workflow"
    )
    workflow_parser.add_argument(
        "--config",
        type=Path,
        default=Path("wishlistops/config.json"),
        help="Path to configuration file"
    )
    workflow_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without making actual API calls"
    )
    workflow_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    # Default to web interface if no command specified
    if not args.command:
        launch_web_interface()
        return
    
    if args.command == "web":
        launch_web_interface()
    elif args.command == "run":
        # Configure logging
        if args.verbose:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)
        
        # Run workflow
        sys.argv = [
            sys.argv[0],
            "--config", str(args.config),
        ]
        if args.dry_run:
            sys.argv.append("--dry-run")
        if args.verbose:
            sys.argv.append("--verbose")
        
        run_workflow()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main_cli()
