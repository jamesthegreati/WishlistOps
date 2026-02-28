"""
Discord notification system for approval workflow.

Sends draft announcements to Discord for human review before posting to Steam.
This is the critical quality gate that prevents AI mistakes.

Architecture: See 05_WishlistOps_Revised_Architecture.md Fix #2
"""

import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from pathlib import Path

import aiohttp


logger = logging.getLogger(__name__)


class DiscordError(Exception):
    """Base exception for Discord notification errors."""
    pass


class WebhookError(DiscordError):
    """Raised when webhook delivery fails."""
    pass


class DiscordNotifier:
    """
    Send notifications to Discord via webhooks.
    
    This class handles sending draft announcements to Discord channels
    for human approval before posting to Steam.
    
    Attributes:
        webhook_url: Discord webhook URL
        dry_run: If True, log notifications without sending
    """
    
    # Discord limits
    MAX_EMBED_DESCRIPTION = 4096
    MAX_FIELD_VALUE = 1024
    MAX_TITLE = 256
    RATE_LIMIT_DELAY = 2  # seconds between requests
    
    def __init__(self, webhook_url: Optional[str], dry_run: bool = False) -> None:
        """
        Initialize Discord notifier.
        
        Args:
            webhook_url: Discord webhook URL (starts with https://discord.com/api/webhooks/)
            dry_run: If True, log without actually sending
            
        Raises:
            ValueError: If webhook URL format is invalid
        """
        if webhook_url and not webhook_url.startswith('https://discord.com/api/webhooks/'):
            raise ValueError(
                "Invalid Discord webhook URL format.\n"
                "Expected: https://discord.com/api/webhooks/...\n"
                "Get one from: Discord Server Settings > Integrations > Webhooks"
            )
        
        self.webhook_url = webhook_url
        self.dry_run = dry_run
        
        if dry_run:
            logger.info("Discord notifier initialized in DRY RUN mode")
        else:
            logger.info("Discord notifier initialized", extra={
                "webhook_configured": bool(webhook_url)
            })
    
    async def send_approval_request(
        self,
        title: str,
        body: str,
        banner_url: Optional[str] = None,
        banner_path: Optional[str] = None,
        game_name: Optional[str] = None,
        tag: Optional[str] = None,
        steam_app_id: Optional[str] = None
    ) -> bool:
        """
        Send draft announcement to Discord for approval.
        
        Args:
            title: Announcement title
            body: Announcement body (full text)
            banner_url: URL to generated banner image
            banner_path: Local filesystem path to banner (uploaded as attachment)
            game_name: Name of the game
            tag: Git tag (e.g., v1.2.0)
            steam_app_id: Steam App ID for direct links
            
        Returns:
            True if sent successfully, False if dry run or webhook not configured
            
        Raises:
            WebhookError: If webhook delivery fails
        """
        if not self.webhook_url:
            logger.warning("Discord webhook not configured, skipping notification")
            return False
        
        if self.dry_run:
            logger.info("DRY RUN: Would send to Discord", extra={
                "title": title,
                "body_length": len(body),
                "has_banner": bool(banner_url),
                "steam_app_id": steam_app_id
            })
            return False
        
        logger.info("Sending approval request to Discord", extra={
            "title": title,
            "game": game_name,
            "tag": tag
        })
        
        # Build attachments list
        files: List[Dict[str, Any]] = []
        legacy_file_bytes: Optional[bytes] = None
        legacy_filename: Optional[str] = None
        
        # Add banner image if available
        if banner_path:
            path = Path(banner_path)
            if path.exists():
                try:
                    banner_bytes = path.read_bytes()
                    files.append({
                        "name": path.name,
                        "bytes": banner_bytes,
                        "type": "image"
                    })
                    legacy_file_bytes = banner_bytes
                    legacy_filename = path.name
                    logger.info("Attaching banner image for download", extra={"path": str(path)})
                except OSError as exc:
                    logger.warning("Failed to read banner for upload", extra={"path": str(path), "error": str(exc)})
            else:
                logger.warning("Banner path does not exist", extra={"path": str(path)})
        
        # Create announcement text file for easy copy/paste
        announcement_text = f"{title}\n\n{body}"
        text_filename = f"announcement_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        files.append({
            "name": text_filename,
            "bytes": announcement_text.encode('utf-8'),
            "type": "text"
        })
        logger.info("Attaching announcement text for download")

        embed = self._build_approval_embed(
            title=title,
            body=body,
            banner_url=None if files else banner_url,
            game_name=game_name,
            tag=tag,
            steam_app_id=steam_app_id,
            has_attachments=bool(files)
        )
        
        # Set image from first image attachment
        for file in files:
            if file.get("type") == "image":
                embed["image"] = {"url": f"attachment://{file['name']}"}
                break
        
        # Build Action Row with Link Button
        components = []
        if steam_app_id:
            steamworks_url = f"https://partner.steamgames.com/apps/landing/{steam_app_id}"
            components = [
                {
                    "type": 1,  # Action Row
                    "components": [
                        {
                            "type": 2,  # Button
                            "style": 5,  # Link Button
                            "label": "🚀 Open Steamworks",
                            "url": steamworks_url
                        }
                    ]
                }
            ]
        
        # Send to Discord
        try:
            await self._send_webhook(
                embed,
                components,
                files=files,
                file_bytes=legacy_file_bytes,
                filename=legacy_filename,
            )
            logger.info("Approval request sent successfully with downloadable files")
            return True
        except Exception as e:
            logger.error(f"Failed to send approval request: {e}", exc_info=True)
            raise WebhookError(f"Discord notification failed: {e}") from e
    
    def _build_approval_embed(
        self,
        title: str,
        body: str,
        banner_url: Optional[str],
        game_name: Optional[str],
        tag: Optional[str],
        steam_app_id: Optional[str],
        has_attachments: bool = False
    ) -> dict:
        """
        Build Discord embed for approval request.
        
        Args:
            title: Announcement title
            body: Announcement body
            banner_url: Banner image URL
            game_name: Game name
            tag: Git tag
            steam_app_id: Steam App ID
            has_attachments: Whether files are attached for download
            
        Returns:
            Discord embed payload
        """
        # Truncate body for preview (keep embed readable)
        body_preview = body[:700] + "..." if len(body) > 700 else body
        
        # Build title
        embed_title = f"🎮 Steam Announcement Draft: {title[:200]}"
        
        # Build description
        description = (
            f"**Game:** {game_name or 'Unknown'}\n"
            f"**Version/Tag:** {tag or 'Unknown'}\n"
            f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n\n"
            f"**Title**\n{title[:256]}\n\n"
            f"**Body Preview**\n```\n{body_preview}\n```"
        )
        
        # Add download instructions if attachments present
        if has_attachments:
            description += (
                "\n\n📎 **Attachments**\n"
                "- `announcement_*.txt` (copy/paste into Steam)\n"
                "- `banner_*.png` (upload as the announcement image)"
            )
        
        # Add direct link to description if App ID exists
        if steam_app_id:
            steam_url = f"https://partner.steamgames.com/apps/landing/{steam_app_id}"
            description += f"\n\n🔗 [Manage on Steamworks]({steam_url})"
        
        # Truncate if too long
        if len(description) > self.MAX_EMBED_DESCRIPTION:
            description = description[:self.MAX_EMBED_DESCRIPTION - 3] + "..."
        
        # Build embed
        embed = {
            "title": embed_title[:self.MAX_TITLE],
            "description": description,
            "color": 5814783,  # Blue color
            "fields": [
                {
                    "name": "📝 Next Steps",
                    "value": (
                        "1. Download attached files (text + image)\n"
                        "2. Click 'Open Steamworks' button below\n"
                        "3. Create new announcement in Steam\n"
                        "4. Copy/paste text from .txt file\n"
                        "5. Upload the banner image\n"
                        "6. Review and publish!"
                    ),
                    "inline": False
                },
                {
                    "name": "💬 Why Discord?",
                    "value": (
                        "Discord is the human approval checkpoint.\n"
                        "WishlistOps generates a draft + files, then sends them somewhere you can quickly review before you publish in Steamworks.\n"
                        "Steam posting is manual because Steam has no public announcement-posting API."
                    ),
                    "inline": False
                }
            ],
            "footer": {
                "text": f"WishlistOps • App ID: {steam_app_id or 'N/A'}"
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Add banner image if available
        if banner_url:
            embed["image"] = {"url": banner_url}

        return embed
    
    async def send_error(self, error_message: str) -> bool:
        """
        Send error notification to Discord.
        
        Args:
            error_message: Error description
            
        Returns:
            True if sent successfully, False if dry run or webhook not configured
        """
        if not self.webhook_url:
            logger.warning("Discord webhook not configured, skipping error notification")
            return False
        
        if self.dry_run:
            logger.info("DRY RUN: Would send error to Discord", extra={
                "error": error_message
            })
            return False
        
        logger.info("Sending error notification to Discord")
        
        embed = {
            "title": "❌ WishlistOps Workflow Failed",
            "description": (
                f"**Error:**\n```\n{error_message[:500]}\n```\n\n"
                f"**Time:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n\n"
                f"**Actions:**\n"
                f"1. Check GitHub Actions logs\n"
                f"2. Verify API keys are set correctly\n"
                f"3. Try running manually with --dry-run flag"
            ),
            "color": 15158332,  # Red color
            "footer": {
                "text": "WishlistOps • Error Notification"
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            await self._send_webhook(embed)
            return True
        except Exception as e:
            logger.error(f"Failed to send error notification: {e}")
            return False
    
    async def send_success(
        self,
        title: str,
        steam_url: Optional[str] = None
    ) -> bool:
        """
        Send success notification to Discord.
        
        Args:
            title: Announcement title that was posted
            steam_url: URL to the Steam announcement
            
        Returns:
            True if sent successfully
        """
        if not self.webhook_url or self.dry_run:
            return False
        
        logger.info("Sending success notification to Discord")
        
        description = (
            f"✅ **Announcement Posted Successfully**\n\n"
            f"**Title:** {title}\n"
            f"**Time:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n"
        )
        
        components = []
        if steam_url:
            description += f"\n**View on Steam:** {steam_url}"
            components = [
                {
                    "type": 1,
                    "components": [
                        {
                            "type": 2,
                            "style": 5,
                            "label": "👀 View on Steam",
                            "url": steam_url
                        }
                    ]
                }
            ]
        
        embed = {
            "title": "✅ Announcement Published",
            "description": description,
            "color": 5763719,  # Green color
            "footer": {
                "text": "WishlistOps • Success Notification"
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            await self._send_webhook(embed, components)
            return True
        except Exception as e:
            logger.error(f"Failed to send success notification: {e}")
            return False

    async def send_test_message(self, message: str) -> bool:
        """Send a lightweight test message to validate webhook configuration.

        This is intended for local dashboard validation. It sends a single embed
        and does not attach files.
        """
        if not self.webhook_url:
            raise WebhookError("Discord webhook not configured")

        if self.dry_run:
            logger.info("DRY RUN: Would send Discord test message")
            return False

        embed = {
            "title": "✅ WishlistOps Discord Test",
            "description": message[:2000] if message else "Test message from WishlistOps dashboard.",
            "color": 5763719,
            "footer": {"text": "WishlistOps • Webhook Validation"},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        await self._send_webhook(embed)
        return True
    
    async def _send_webhook(
        self,
        embed: dict,
        components: Optional[List[Dict[str, Any]]] = None,
        files: Optional[List[Dict[str, Any]]] = None,
        *,
        # Backwards compatible single-file API (used by older tests/callers)
        file_bytes: Optional[bytes] = None,
        filename: Optional[str] = None,
    ) -> None:
        """
        Send payload to Discord webhook.
        
        Args:
            embed: Discord embed object
            components: Optional list of interactive components (buttons)
            files: Optional list of files to attach (each with 'name', 'bytes', 'type' keys)
            
        Raises:
            WebhookError: If delivery fails
        """
        payload = {
            "username": "WishlistOps",
            "embeds": [embed],
        }
        
        if components:
            payload["components"] = components

        request_kwargs: Dict[str, Any] = {"timeout": aiohttp.ClientTimeout(total=30)}
        
        # If legacy args are provided, map them into the newer `files` structure.
        if file_bytes is not None and filename:
            existing = list(files or [])
            if not any(str(f.get("name") or "") == str(filename) for f in existing):
                existing.insert(0, {"name": filename, "bytes": file_bytes, "type": "binary"})
            files = existing

        if files:
            # Use multipart form data for file uploads.
            # Discord expects file fields named like `files[0]`, `files[1]`.
            form = aiohttp.FormData()

            prepared: list[tuple[int, str, bytes, str]] = []
            attachments: list[dict[str, Any]] = []

            for idx, file in enumerate(list(files)):
                name = str(file.get("name") or f"file_{idx}")
                data = file.get("bytes")
                if not isinstance(data, (bytes, bytearray)):
                    continue

                content_type = "application/octet-stream"
                lower = name.lower()
                if lower.endswith(".png"):
                    content_type = "image/png"
                elif lower.endswith(".jpg") or lower.endswith(".jpeg"):
                    content_type = "image/jpeg"
                elif lower.endswith(".webp"):
                    content_type = "image/webp"
                elif lower.endswith(".txt"):
                    content_type = "text/plain; charset=utf-8"

                attachments.append({"id": idx, "filename": name})
                prepared.append((idx, name, bytes(data), content_type))

            if attachments:
                payload["attachments"] = attachments

            form.add_field("payload_json", json.dumps(payload), content_type="application/json")

            for idx, name, blob, content_type in prepared:
                form.add_field(
                    f"files[{idx}]",
                    blob,
                    filename=name,
                    content_type=content_type,
                )
            request_kwargs["data"] = form
        else:
            request_kwargs["json"] = payload
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.webhook_url,
                **request_kwargs
            ) as response:
                
                if response.status == 429:
                    # Rate limited
                    retry_after = response.headers.get('Retry-After', '60')
                    raise WebhookError(
                        f"Discord rate limit hit. Retry after {retry_after}s"
                    )
                
                if response.status == 404:
                    raise WebhookError(
                        "Discord webhook not found. Check your webhook URL."
                    )
                
                if response.status >= 400:
                    error_text = await response.text()
                    raise WebhookError(
                        f"Discord API error (status {response.status}): {error_text}"
                    )
                
                logger.debug("Discord webhook sent successfully", extra={
                    "status": response.status,
                    "files_count": len(files) if files else 0
                })


# Convenience function for quick notifications
async def notify_discord(
    webhook_url: str,
    message: str,
    dry_run: bool = False
) -> bool:
    """
    Quick notification helper.
    
    Args:
        webhook_url: Discord webhook URL
        message: Message to send
        dry_run: If True, don't actually send
        
    Returns:
        True if sent successfully
    """
    notifier = DiscordNotifier(webhook_url, dry_run=dry_run)
    
    embed = {
        "description": message,
        "color": 5814783,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    try:
        await notifier._send_webhook(embed)
        return True
    except Exception:
        return False
