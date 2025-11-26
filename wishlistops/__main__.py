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

# Check if enhanced CLI is available
try:
    from .cli_v2 import WishlistOpsCLI, main as cli_main
    CLI_V2_AVAILABLE = True
except ImportError:
    CLI_V2_AVAILABLE = False

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
    
    # Use default config path in current directory
    config_path = Path.cwd() / "wishlistops" / "config.json"
    
    # If not found, try common locations
    if not config_path.exists():
        alt_paths = [
            Path.cwd() / "config.json",
            Path.home() / ".wishlistops" / "config.json",
        ]
        for alt_path in alt_paths:
            if alt_path.exists():
                config_path = alt_path
                break
    
    server = WishlistOpsWebServer(config_path)
    
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
    
    # Interactive CLI command (default)
    cli_parser = subparsers.add_parser(
        "cli",
        help="Launch interactive CLI (default)"
    )
    
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
    
    # Process images command
    process_parser = subparsers.add_parser(
        "process",
        help="Process images for Steam"
    )
    process_parser.add_argument(
        "images",
        nargs="+",
        type=Path,
        help="Image files to process"
    )
    process_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Output directory (default: same as input)"
    )
    process_parser.add_argument(
        "--preset",
        choices=["fast", "balanced", "quality"],
        default="balanced",
        help="Quality preset (default: balanced)"
    )
    
    args = parser.parse_args()
    
    # Default to interactive CLI if no command specified
    if not args.command or args.command == "cli":
        if CLI_V2_AVAILABLE:
            cli_main()
        else:
            print("❌ Enhanced CLI requires 'rich' library.")
            print("Install with: pip install rich")
            # Fall back to web interface
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
    elif args.command == "process":
        process_images_command(args)
    else:
        parser.print_help()
        sys.exit(1)


def process_images_command(args):
    """Process images using the image processor."""
    try:
        from .image_processor import ImageProcessor, QualityPreset
        
        preset_map = {
            "fast": QualityPreset.FAST,
            "balanced": QualityPreset.BALANCED,
            "quality": QualityPreset.QUALITY,
        }
        
        processor = ImageProcessor(preset=preset_map[args.preset])
        
        for image_path in args.images:
            if not image_path.exists():
                print(f"❌ File not found: {image_path}")
                continue
            
            print(f"Processing: {image_path.name}...")
            
            output_dir = args.output or image_path.parent
            output_path = output_dir / f"{image_path.stem}_steam.png"
            
            result = processor.process_for_steam(image_path, output_path)
            
            print(f"  ✓ {result.original_size[0]}x{result.original_size[1]} → {result.final_size[0]}x{result.final_size[1]}")
            print(f"  ✓ Quality score: {result.quality_score:.0f}%")
            print(f"  ✓ Saved to: {output_path}")
            
            if result.warnings:
                for warning in result.warnings:
                    print(f"  ⚠️  {warning}")
            
            print()
        
        print("✅ Done!")
        
    except ImportError as e:
        print(f"❌ Image processor not available: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main_cli()
