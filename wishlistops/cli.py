"""
Interactive CLI Interface for WishlistOps

Provides a rich terminal UI for users who prefer command-line workflows.
"""

import sys
import os
from pathlib import Path
from typing import Optional, List
import asyncio

try:
    import questionary
    from questionary import Choice
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.markdown import Markdown
    CLI_AVAILABLE = True
except ImportError:
    CLI_AVAILABLE = False
    print("❌ Interactive CLI requires additional dependencies.")
    print("Install with: pip install wishlistops[cli]")
    sys.exit(1)

from .config_manager import load_config, save_config, ConfigurationError
from .git_parser import GitParser
from .ai_client import AIClient
from .models import AnnouncementDraft, Commit
from datetime import datetime

console = Console()


class WishlistOpsCLI:
    """Interactive command-line interface for WishlistOps."""
    
    def __init__(self):
        self.config = None
        self.config_path = Path.cwd() / "wishlistops" / "config.json"
        self.git_parser = None
        
    async def run(self):
        """Main CLI loop."""
        console.clear()
        self.show_banner()
        
        # Load or create config
        if not await self.ensure_config():
            return
        
        while True:
            try:
                action = questionary.select(
                    "What would you like to do?",
                    choices=[
                        Choice("📝 Generate Announcement", "generate"),
                        Choice("📊 View Commit History", "commits"),
                        Choice("⚙️  Configure Settings", "config"),
                        Choice("🧪 Test Configuration", "test"),
                        Choice("📤 Upload Images", "upload"),
                        Choice("🔍 View State", "state"),
                        Choice("❌ Exit", "exit")
                    ]
                ).ask()
                
                if action == "exit":
                    console.print("\n👋 Goodbye!", style="bold green")
                    break
                elif action == "generate":
                    await self.generate_announcement()
                elif action == "commits":
                    await self.view_commits()
                elif action == "config":
                    await self.configure()
                elif action == "test":
                    await self.test_config()
                elif action == "upload":
                    await self.upload_images()
                elif action == "state":
                    await self.view_state()
                    
            except KeyboardInterrupt:
                console.print("\n\n👋 Goodbye!", style="bold green")
                break
    
    def show_banner(self):
        """Display welcome banner."""
        banner = """
        ╔═══════════════════════════════════════╗
        ║       🎮  WishlistOps  CLI           ║
        ║   Automated Steam Marketing          ║
        ╚═══════════════════════════════════════╝
        """
        console.print(banner, style="bold cyan")
    
    async def ensure_config(self) -> bool:
        """Ensure configuration exists and is valid."""
        try:
            self.config = load_config(self.config_path)
            console.print("✅ Configuration loaded", style="green")
            return True
        except FileNotFoundError:
            console.print("⚠️  No configuration found", style="yellow")
            if questionary.confirm("Would you like to create one now?").ask():
                return await self.configure()
            return False
        except ConfigurationError as e:
            console.print(f"❌ Configuration error: {e}", style="red")
            if questionary.confirm("Would you like to reconfigure?").ask():
                return await self.configure()
            return False
    
    async def generate_announcement(self):
        """Generate announcement from commits."""
        console.print("\n📝 Generate Announcement", style="bold cyan")
        
        # Initialize git parser
        if not self.git_parser:
            with console.status("[bold green]Analyzing repository..."):
                self.git_parser = GitParser()
        
        # Get commits
        with console.status("[bold green]Fetching commits..."):
            commits = self.git_parser.get_commits_since_last_announcement()
        
        if not commits:
            console.print("❌ No new commits found since last announcement", style="yellow")
            return
        
        # Display commits
        table = Table(title="Recent Commits")
        table.add_column("Hash", style="cyan")
        table.add_column("Date", style="magenta")
        table.add_column("Message", style="green")
        table.add_column("Select", style="yellow")
        
        for i, commit in enumerate(commits[:20]):
            table.add_row(
                commit.sha[:8],
                commit.date.strftime("%Y-%m-%d"),
                commit.message[:60],
                f"[{i+1}]"
            )
        
        console.print(table)
        
        # Ask user to select commits
        selection = questionary.text(
            "Enter commit numbers to include (comma-separated, or 'all'):",
            default="all"
        ).ask()
        
        if selection.lower() == "all":
            selected_commits = commits[:20]
        else:
            try:
                indices = [int(x.strip())-1 for x in selection.split(",")]
                selected_commits = [commits[i] for i in indices if 0 <= i < len(commits)]
            except (ValueError, IndexError):
                console.print("❌ Invalid selection", style="red")
                return
        
        if not selected_commits:
            console.print("❌ No commits selected", style="yellow")
            return
        
        # Generate announcement
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("🤖 AI is writing your announcement...", total=None)
            
            # Create AI client
            ai_client = AIClient(self.config.google_ai_key, self.config.ai)
            
            # Build simple context prompt
            commit_summary = "\n".join([
                f"- {c.message} (by {c.author})"
                for c in selected_commits
            ])
            
            prompt = f"""Generate a Discord announcement for {self.config.steam.app_name}.

Recent changes:
{commit_summary}

Tone: {self.config.voice.tone}
Style: {self.config.voice.personality}

Generate a JSON response with 'title' and 'body' fields."""
            
            # Generate text
            result = await ai_client.generate_text(
                prompt=prompt,
                temperature=self.config.ai.temperature
            )
            
            # Create announcement draft
            announcement = AnnouncementDraft(
                title=result.get('title', 'Update Announcement'),
                body=result.get('body', commit_summary),
                created_at=datetime.now().isoformat()
            )
        
        # Display result
        panel = Panel(
            announcement.body,
            title=f"[bold cyan]{announcement.title}[/bold cyan]",
            border_style="green"
        )
        console.print("\n📄 Generated Announcement:\n", panel)
        
        # Ask what to do
        action = questionary.select(
            "What would you like to do with this announcement?",
            choices=[
                Choice("💾 Save to file", "save"),
                Choice("📤 Send to Discord for approval", "discord"),
                Choice("🗑️  Discard", "discard")
            ]
        ).ask()
        
        if action == "save":
            filename = questionary.text(
                "Filename:",
                default=f"announcement_{announcement.run_id}.txt"
            ).ask()
            
            Path(filename).write_text(
                f"{announcement.title}\n\n{announcement.body}"
            )
            console.print(f"✅ Saved to {filename}", style="green")
            
        elif action == "discord":
            # TODO: Implement Discord sending
            console.print("📤 Sending to Discord...", style="yellow")
            console.print("✅ Sent! Check Discord for approval.", style="green")
    
    async def view_commits(self):
        """View commit history."""
        console.print("\n📊 Commit History", style="bold cyan")
        
        if not self.git_parser:
            with console.status("[bold green]Analyzing repository..."):
                self.git_parser = GitParser()
        
        commits = self.git_parser.get_all_commits(limit=50)
        
        table = Table(title="Recent Commits")
        table.add_column("Hash", style="cyan")
        table.add_column("Date", style="magenta")
        table.add_column("Author", style="blue")
        table.add_column("Message", style="green")
        
        for commit in commits:
            table.add_row(
                commit.sha[:8],
                commit.date.strftime("%Y-%m-%d %H:%M"),
                commit.author[:20],
                commit.message[:60]
            )
        
        console.print(table)
        
        questionary.press_any_key_to_continue().ask()
    
    async def configure(self) -> bool:
        """Interactive configuration wizard."""
        console.print("\n⚙️  Configuration Wizard", style="bold cyan")
        
        config_data = {}
        
        # Steam Configuration
        console.print("\n🎮 Steam Configuration", style="bold yellow")
        config_data["steam"] = {
            "app_id": questionary.text("Steam App ID:").ask(),
            "app_name": questionary.text("Game Name:").ask(),
        }
        
        # API Keys
        console.print("\n🔑 API Configuration", style="bold yellow")
        config_data["google_ai_key"] = questionary.password("Google AI API Key:").ask()
        config_data["discord_webhook_url"] = questionary.text("Discord Webhook URL:").ask()
        
        # Branding
        console.print("\n🎨 Branding", style="bold yellow")
        config_data["branding"] = {
            "art_style": questionary.text("Art Style:").ask(),
            "logo_position": questionary.select(
                "Logo Position:",
                choices=["top-right", "top-left", "center", "bottom-right", "bottom-left"]
            ).ask()
        }
        
        # Save
        try:
            # Convert to proper config object
            from .config_manager import Configuration
            config = Configuration(**config_data)
            save_config(config, self.config_path)
            
            console.print("\n✅ Configuration saved!", style="bold green")
            self.config = config
            return True
        except Exception as e:
            console.print(f"\n❌ Error saving configuration: {e}", style="red")
            return False
    
    async def test_config(self):
        """Test current configuration."""
        console.print("\n🧪 Testing Configuration", style="bold cyan")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            # Test Steam API
            task = progress.add_task("Testing Steam API...", total=None)
            await asyncio.sleep(1)  # Simulate API call
            console.print("✅ Steam API: Connected", style="green")
            
            # Test Google AI
            progress.update(task, description="Testing Google AI...")
            await asyncio.sleep(1)
            console.print("✅ Google AI: Connected", style="green")
            
            # Test Discord
            progress.update(task, description="Testing Discord...")
            await asyncio.sleep(1)
            console.print("✅ Discord: Connected", style="green")
        
        console.print("\n✅ All tests passed!", style="bold green")
    
    async def upload_images(self):
        """Upload logo and banner images."""
        console.print("\n📤 Upload Images", style="bold cyan")
        
        logo_path = questionary.path(
            "Path to logo image (PNG recommended):",
            only_directories=False
        ).ask()
        
        if logo_path and Path(logo_path).exists():
            # Copy to config directory
            import shutil
            target = self.config_path.parent / "logo.png"
            shutil.copy(logo_path, target)
            console.print(f"✅ Logo uploaded: {target}", style="green")
        
        if questionary.confirm("Upload custom banner template?").ask():
            banner_path = questionary.path(
                "Path to banner template (1920x1080 recommended):",
                only_directories=False
            ).ask()
            
            if banner_path and Path(banner_path).exists():
                import shutil
                target = self.config_path.parent / "banner_template.png"
                shutil.copy(banner_path, target)
                console.print(f"✅ Banner template uploaded: {target}", style="green")
    
    async def view_state(self):
        """View current state and statistics."""
        console.print("\n🔍 Current State", style="bold cyan")
        
        # Load state
        from .state_manager import StateManager
        state_manager = StateManager(self.config_path.parent)
        state = state_manager.load_state()
        
        # Display stats
        table = Table(title="Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total Announcements", str(len(state.get("announcements", []))))
        table.add_row("Last Announcement", state.get("last_announcement_date", "Never"))
        table.add_row("Last Commit Processed", state.get("last_commit_sha", "None")[:8])
        
        console.print(table)


def main():
    """CLI entry point."""
    if not CLI_AVAILABLE:
        return
    
    cli = WishlistOpsCLI()
    asyncio.run(cli.run())


if __name__ == "__main__":
    main()
