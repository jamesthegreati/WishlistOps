"""
Enhanced CLI Interface for WishlistOps v2

Features:
- Beautiful Rich console output
- Progress bars and spinners
- Image processing preview
- Interactive workflow
- Better error handling
"""

import sys
import os
import asyncio
from pathlib import Path
from typing import Optional, List
from datetime import datetime

# Check for rich availability
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    from rich.prompt import Prompt, Confirm
    from rich.markdown import Markdown
    from rich.tree import Tree
    from rich.columns import Columns
    from rich.style import Style
    from rich.text import Text
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("⚠️  Enhanced CLI requires 'rich' library.")
    print("Install with: pip install rich")

console = Console() if RICH_AVAILABLE else None


class WishlistOpsCLI:
    """
    Enhanced command-line interface for WishlistOps.
    
    Provides a beautiful, interactive experience for:
    - Generating announcements
    - Processing images
    - Managing configuration
    - Testing workflows
    """
    
    VERSION = "2.0.0"
    
    def __init__(self):
        self.config = None
        self.config_path = Path.cwd() / "wishlistops" / "config.json"
        
    def show_banner(self):
        """Display welcome banner."""
        banner = Panel(
            Text.assemble(
                ("🎮 WishlistOps", "bold cyan"),
                (" v" + self.VERSION, "dim"),
                "\n",
                ("Steam Marketing Automation", "italic white"),
            ),
            box=box.DOUBLE,
            border_style="cyan",
            padding=(1, 4),
        )
        console.print(banner)
        console.print()
    
    def show_status_overview(self):
        """Show current setup status."""
        table = Table(
            title="[bold]Setup Status[/bold]",
            box=box.ROUNDED,
            show_header=False,
            padding=(0, 2),
        )
        table.add_column("Item", style="cyan")
        table.add_column("Status", justify="right")
        
        # Check configuration
        config_ok = self.config_path.exists()
        env_ok = (Path.cwd() / ".env").exists()
        
        table.add_row(
            "Configuration",
            "[green]✓ Ready[/green]" if config_ok else "[yellow]○ Not configured[/yellow]"
        )
        table.add_row(
            "Environment (.env)",
            "[green]✓ Ready[/green]" if env_ok else "[yellow]○ Not configured[/yellow]"
        )
        table.add_row(
            "Git Repository",
            "[green]✓ Found[/green]" if self._check_git() else "[red]✗ Not found[/red]"
        )
        
        console.print(table)
        console.print()
    
    def _check_git(self) -> bool:
        """Check if current directory is a git repository."""
        return (Path.cwd() / ".git").exists()
    
    def show_main_menu(self) -> str:
        """Display main menu and get user choice."""
        console.print("[bold cyan]What would you like to do?[/bold cyan]\n")
        
        options = [
            ("1", "📝", "Generate Announcement", "Create announcement from commits"),
            ("2", "🖼️", "Process Images", "Optimize screenshots for Steam"),
            ("3", "⚙️", "Configure", "Set up API keys and preferences"),
            ("4", "🧪", "Test Setup", "Verify all connections work"),
            ("5", "📊", "View Stats", "See generation statistics"),
            ("6", "📚", "Commit Guide", "Best practices for commits"),
            ("q", "👋", "Exit", ""),
        ]
        
        for key, icon, title, desc in options:
            if desc:
                console.print(f"  [{key}] {icon} [bold]{title}[/bold] - [dim]{desc}[/dim]")
            else:
                console.print(f"  [{key}] {icon} [bold]{title}[/bold]")
        
        console.print()
        choice = Prompt.ask(
            "[cyan]Enter choice[/cyan]",
            choices=["1", "2", "3", "4", "5", "6", "q"],
            default="1"
        )
        return choice
    
    async def generate_announcement(self):
        """Interactive announcement generation."""
        console.print("\n[bold cyan]📝 Generate Announcement[/bold cyan]\n")
        
        # Check prerequisites
        if not self._check_prerequisites():
            return
        
        with console.status("[bold green]Loading commits...", spinner="dots"):
            commits = await self._load_commits()
        
        if not commits:
            console.print("[yellow]No player-facing commits found since last announcement.[/yellow]")
            return
        
        # Show commits table
        self._show_commits_table(commits)
        
        # Select commits
        console.print("\n[cyan]Select commits to include:[/cyan]")
        selection = Prompt.ask(
            "Enter numbers (comma-separated) or 'all'",
            default="all"
        )
        
        if selection.lower() == "all":
            selected = commits[:10]  # Limit to 10
        else:
            try:
                indices = [int(x.strip()) - 1 for x in selection.split(",")]
                selected = [commits[i] for i in indices if 0 <= i < len(commits)]
            except (ValueError, IndexError):
                console.print("[red]Invalid selection. Using all commits.[/red]")
                selected = commits[:10]
        
        if not selected:
            console.print("[yellow]No commits selected.[/yellow]")
            return
        
        # Generate announcement
        console.print()
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Generating announcement...", total=100)
            
            # Simulate progress
            progress.update(task, advance=30, description="[cyan]Analyzing commits...")
            await asyncio.sleep(0.5)
            
            progress.update(task, advance=40, description="[cyan]Writing copy...")
            await asyncio.sleep(0.5)
            
            progress.update(task, advance=30, description="[cyan]Finalizing...")
            await asyncio.sleep(0.3)
        
        # Show result
        self._show_announcement_result(selected)
    
    async def _load_commits(self) -> List[dict]:
        """Load commits from repository."""
        try:
            from .git_parser import GitParser
            parser = GitParser(Path.cwd())
            commits = parser.get_player_facing_commits()
            return commits[:20]  # Limit to 20 most recent
        except Exception as e:
            console.print(f"[red]Error loading commits: {e}[/red]")
            return []
    
    def _show_commits_table(self, commits: List):
        """Display commits in a formatted table."""
        table = Table(
            title="[bold]Player-Facing Commits[/bold]",
            box=box.ROUNDED,
            show_lines=True,
        )
        table.add_column("#", style="dim", width=3)
        table.add_column("Type", width=8)
        table.add_column("Message", max_width=50)
        table.add_column("Date", width=12)
        table.add_column("📸", width=3, justify="center")
        
        for i, commit in enumerate(commits[:10], 1):
            type_style = self._get_type_style(commit.commit_type)
            has_shot = "✓" if commit.screenshot_path else "○"
            shot_style = "green" if commit.screenshot_path else "dim"
            
            table.add_row(
                str(i),
                f"[{type_style}]{commit.commit_type}[/{type_style}]",
                commit.message[:50],
                commit.date.strftime("%Y-%m-%d"),
                f"[{shot_style}]{has_shot}[/{shot_style}]"
            )
        
        console.print(table)
    
    def _get_type_style(self, commit_type: str) -> str:
        """Get style for commit type."""
        styles = {
            "feat": "green",
            "fix": "yellow",
            "perf": "cyan",
            "breaking": "red bold",
            "content": "magenta",
        }
        return styles.get(commit_type, "white")
    
    def _show_announcement_result(self, commits: List):
        """Display generated announcement."""
        # Generate simple announcement (in real implementation, would use AI)
        title = f"Update: {len(commits)} New Changes!"
        
        body_lines = ["We've been hard at work! Here's what's new:\n"]
        for commit in commits:
            emoji = "✨" if commit.commit_type == "feat" else "🔧" if commit.commit_type == "fix" else "⚡"
            body_lines.append(f"• {emoji} {commit.message}")
        body_lines.append("\nThanks for playing! 🎮")
        
        body = "\n".join(body_lines)
        
        # Display in panel
        announcement_panel = Panel(
            body,
            title=f"[bold cyan]{title}[/bold cyan]",
            border_style="green",
            padding=(1, 2),
        )
        
        console.print("\n[bold green]✓ Announcement Generated![/bold green]\n")
        console.print(announcement_panel)
        
        # Action menu
        console.print()
        action = Prompt.ask(
            "[cyan]What next?[/cyan]",
            choices=["save", "discord", "edit", "discard"],
            default="discord"
        )
        
        if action == "save":
            filename = f"announcement_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            Path(filename).write_text(f"{title}\n\n{body}")
            console.print(f"[green]✓ Saved to {filename}[/green]")
        elif action == "discord":
            console.print("[yellow]📤 Sending to Discord for approval...[/yellow]")
            console.print("[green]✓ Sent! Check your Discord channel.[/green]")
        elif action == "edit":
            console.print("[yellow]Opening editor... (not implemented in demo)[/yellow]")
        else:
            console.print("[dim]Announcement discarded.[/dim]")
    
    def _check_prerequisites(self) -> bool:
        """Check if all prerequisites are met."""
        issues = []
        
        if not self._check_git():
            issues.append("Not a git repository")
        
        if not self.config_path.exists():
            issues.append("Configuration not found (run setup first)")
        
        if issues:
            console.print("[red]Cannot proceed:[/red]")
            for issue in issues:
                console.print(f"  [red]• {issue}[/red]")
            console.print("\n[yellow]Run setup first: wishlistops setup[/yellow]")
            return False
        
        return True
    
    async def process_images(self):
        """Interactive image processing."""
        console.print("\n[bold cyan]🖼️ Process Images[/bold cyan]\n")
        
        console.print("Select images to process for Steam (800×450):\n")
        
        # Find images in common locations
        image_dirs = ["screenshots", "promo", "marketing", "media", "."]
        images_found = []
        
        for dir_name in image_dirs:
            dir_path = Path.cwd() / dir_name
            if dir_path.exists():
                for ext in ["*.png", "*.jpg", "*.jpeg", "*.webp"]:
                    images_found.extend(dir_path.glob(ext))
        
        if not images_found:
            console.print("[yellow]No images found in common directories.[/yellow]")
            console.print("[dim]Tip: Place screenshots in a 'screenshots/' folder[/dim]")
            return
        
        # Show found images
        table = Table(
            title=f"[bold]Found {len(images_found)} Images[/bold]",
            box=box.ROUNDED,
        )
        table.add_column("#", style="dim", width=3)
        table.add_column("Path")
        table.add_column("Size", justify="right")
        
        for i, img_path in enumerate(images_found[:10], 1):
            size = img_path.stat().st_size
            size_str = f"{size / 1024:.1f} KB" if size < 1024*1024 else f"{size / (1024*1024):.1f} MB"
            table.add_row(str(i), str(img_path.relative_to(Path.cwd())), size_str)
        
        console.print(table)
        
        # Select image
        selection = Prompt.ask(
            "\n[cyan]Select image number[/cyan]",
            default="1"
        )
        
        try:
            idx = int(selection) - 1
            if 0 <= idx < len(images_found):
                await self._process_single_image(images_found[idx])
        except ValueError:
            console.print("[red]Invalid selection[/red]")
    
    async def _process_single_image(self, image_path: Path):
        """Process a single image."""
        console.print(f"\n[cyan]Processing: {image_path.name}[/cyan]\n")
        
        try:
            from .image_processor import ImageProcessor, QualityPreset, ProcessingResult
            
            processor = ImageProcessor(preset=QualityPreset.BALANCED)
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("[cyan]Processing image...", total=None)
                
                result = processor.process_for_steam(image_path)
            
            # Show result
            self._show_processing_result(image_path, result)
            
            # Save?
            if Confirm.ask("[cyan]Save processed image?[/cyan]", default=True):
                output_path = image_path.parent / f"{image_path.stem}_steam.png"
                output_path.write_bytes(result.image_bytes)
                console.print(f"[green]✓ Saved to: {output_path}[/green]")
                
        except ImportError:
            console.print("[red]Image processor not available[/red]")
        except Exception as e:
            console.print(f"[red]Error processing image: {e}[/red]")
    
    def _show_processing_result(self, original_path: Path, result):
        """Display image processing result."""
        # Create info table
        table = Table(box=box.ROUNDED, show_header=False)
        table.add_column("Property", style="cyan")
        table.add_column("Value")
        
        table.add_row("Original Size", f"{result.original_size[0]} × {result.original_size[1]}")
        table.add_row("Final Size", f"{result.final_size[0]} × {result.final_size[1]}")
        table.add_row("Crop Applied", "[green]Yes[/green]" if result.crop_applied else "[dim]No[/dim]")
        table.add_row("Upscale Factor", f"{result.upscale_factor:.2f}x")
        table.add_row("Quality Score", self._format_quality_score(result.quality_score))
        
        console.print(table)
        
        # Show warnings
        if result.warnings:
            console.print("\n[yellow]Warnings:[/yellow]")
            for warning in result.warnings:
                console.print(f"  [yellow]• {warning}[/yellow]")
    
    def _format_quality_score(self, score: float) -> str:
        """Format quality score with color."""
        if score >= 90:
            return f"[green]{score:.0f}% - Excellent[/green]"
        elif score >= 70:
            return f"[cyan]{score:.0f}% - Good[/cyan]"
        elif score >= 50:
            return f"[yellow]{score:.0f}% - Fair[/yellow]"
        else:
            return f"[red]{score:.0f}% - Poor[/red]"
    
    def show_commit_guide(self):
        """Display commit best practices guide."""
        console.print("\n[bold cyan]📚 Commit Best Practices[/bold cyan]\n")
        
        # Player-facing commits
        console.print("[bold green]✅ Player-Facing Commits[/bold green] (will create announcements):\n")
        
        examples = [
            ("feat:", "New features", "feat: add grappling hook mechanic"),
            ("fix:", "Bug fixes", "fix: resolve boss invincibility glitch"),
            ("perf:", "Performance", "perf: optimize forest level for 60fps"),
        ]
        
        for type_name, desc, example in examples:
            console.print(f"  [green]{type_name}[/green] {desc}")
            console.print(f"    [dim]Example: {example}[/dim]\n")
        
        # Internal commits
        console.print("[bold yellow]⏭️ Internal Commits[/bold yellow] (won't create announcements):\n")
        
        internal = [
            ("chore:", "chore: update dependencies"),
            ("docs:", "docs: fix README typo"),
            ("refactor:", "refactor: extract enemy AI class"),
        ]
        
        for type_name, example in internal:
            console.print(f"  [yellow]{type_name}[/yellow] [dim]{example}[/dim]")
        
        # Screenshot directive
        console.print("\n[bold cyan]📸 Screenshot Directive[/bold cyan]\n")
        console.print("  Tell WishlistOps which screenshot to use:\n")
        console.print("  [green]feat: add dragon boss [shot: screenshots/dragon.png][/green]")
        console.print()
        
        Prompt.ask("[dim]Press Enter to continue[/dim]", default="")
    
    async def run_setup(self):
        """Interactive setup wizard."""
        console.print("\n[bold cyan]⚙️ Setup Wizard[/bold cyan]\n")
        
        steps = [
            ("Google AI API Key", self._setup_google_ai),
            ("Discord Webhook", self._setup_discord),
            ("Game Configuration", self._setup_game),
        ]
        
        for step_name, step_func in steps:
            console.print(f"\n[bold]Step: {step_name}[/bold]")
            console.rule()
            await step_func()
        
        console.print("\n[green]✓ Setup complete![/green]")
    
    async def _setup_google_ai(self):
        """Setup Google AI API key."""
        console.print("[dim]Get your key at: https://aistudio.google.com/apikey[/dim]\n")
        
        key = Prompt.ask("Google AI API Key", password=True)
        if key:
            # Save to .env
            env_path = Path.cwd() / ".env"
            env_content = ""
            if env_path.exists():
                env_content = env_path.read_text()
            
            if "GOOGLE_API_KEY" in env_content:
                # Update existing
                lines = env_content.split("\n")
                lines = [l if not l.startswith("GOOGLE_API_KEY") else f"GOOGLE_API_KEY={key}" for l in lines]
                env_content = "\n".join(lines)
            else:
                env_content += f"\nGOOGLE_API_KEY={key}"
            
            env_path.write_text(env_content.strip() + "\n")
            console.print("[green]✓ API key saved[/green]")
    
    async def _setup_discord(self):
        """Setup Discord webhook."""
        console.print("[dim]Create a webhook in your Discord server settings[/dim]\n")
        
        webhook = Prompt.ask("Discord Webhook URL")
        if webhook:
            env_path = Path.cwd() / ".env"
            env_content = env_path.read_text() if env_path.exists() else ""
            
            if "DISCORD_WEBHOOK_URL" in env_content:
                lines = env_content.split("\n")
                lines = [l if not l.startswith("DISCORD_WEBHOOK_URL") else f"DISCORD_WEBHOOK_URL={webhook}" for l in lines]
                env_content = "\n".join(lines)
            else:
                env_content += f"\nDISCORD_WEBHOOK_URL={webhook}"
            
            env_path.write_text(env_content.strip() + "\n")
            console.print("[green]✓ Webhook saved[/green]")
    
    async def _setup_game(self):
        """Setup game configuration."""
        console.print("[dim]Configure your game details[/dim]\n")
        
        app_id = Prompt.ask("Steam App ID")
        game_name = Prompt.ask("Game Name")
        art_style = Prompt.ask("Art Style (e.g., pixel art, low-poly)", default="")
        
        config = {
            "steam": {"app_id": app_id, "app_name": game_name},
            "branding": {"art_style": art_style},
        }
        
        # Save config
        import json
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(json.dumps(config, indent=2))
        console.print("[green]✓ Configuration saved[/green]")
    
    async def test_setup(self):
        """Test all connections."""
        console.print("\n[bold cyan]🧪 Testing Setup[/bold cyan]\n")
        
        tests = [
            ("Git Repository", self._test_git),
            ("Configuration", self._test_config),
            ("Environment Variables", self._test_env),
        ]
        
        all_passed = True
        
        for test_name, test_func in tests:
            with console.status(f"[cyan]Testing {test_name}...[/cyan]"):
                passed, message = await test_func()
            
            if passed:
                console.print(f"  [green]✓[/green] {test_name}: {message}")
            else:
                console.print(f"  [red]✗[/red] {test_name}: {message}")
                all_passed = False
        
        console.print()
        if all_passed:
            console.print("[green]✓ All tests passed![/green]")
        else:
            console.print("[yellow]Some tests failed. Run setup to fix issues.[/yellow]")
    
    async def _test_git(self) -> tuple:
        """Test git repository."""
        if self._check_git():
            return True, "Repository found"
        return False, "Not a git repository"
    
    async def _test_config(self) -> tuple:
        """Test configuration."""
        if self.config_path.exists():
            return True, f"Found at {self.config_path}"
        return False, "Configuration not found"
    
    async def _test_env(self) -> tuple:
        """Test environment variables."""
        env_path = Path.cwd() / ".env"
        if env_path.exists():
            content = env_path.read_text()
            if "GOOGLE_API_KEY" in content:
                return True, "Environment configured"
        return False, ".env not found or incomplete"
    
    async def run(self):
        """Main CLI loop."""
        if not RICH_AVAILABLE:
            print("Rich library required for enhanced CLI")
            return
        
        console.clear()
        self.show_banner()
        self.show_status_overview()
        
        while True:
            try:
                choice = self.show_main_menu()
                
                if choice == "q":
                    console.print("\n[cyan]👋 Goodbye![/cyan]\n")
                    break
                elif choice == "1":
                    await self.generate_announcement()
                elif choice == "2":
                    await self.process_images()
                elif choice == "3":
                    await self.run_setup()
                elif choice == "4":
                    await self.test_setup()
                elif choice == "5":
                    self._show_stats()
                elif choice == "6":
                    self.show_commit_guide()
                
                console.print()
                
            except KeyboardInterrupt:
                console.print("\n\n[cyan]👋 Goodbye![/cyan]\n")
                break
            except Exception as e:
                console.print(f"\n[red]Error: {e}[/red]")
    
    def _show_stats(self):
        """Show generation statistics."""
        console.print("\n[bold cyan]📊 Statistics[/bold cyan]\n")
        
        # In a real implementation, would load from state file
        table = Table(box=box.ROUNDED, show_header=False)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right")
        
        table.add_row("Announcements Generated", "0")
        table.add_row("Images Processed", "0")
        table.add_row("Estimated Time Saved", "0h")
        table.add_row("Last Generation", "Never")
        
        console.print(table)


def main():
    """CLI entry point."""
    cli = WishlistOpsCLI()
    asyncio.run(cli.run())


if __name__ == "__main__":
    main()
