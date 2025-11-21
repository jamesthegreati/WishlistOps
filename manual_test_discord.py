#!/usr/bin/env python3
"""
Manual test script for Discord notifier.

Usage:
    export DISCORD_WEBHOOK_URL='https://discord.com/api/webhooks/YOUR_WEBHOOK'
    python manual_test_discord.py
"""

import asyncio
import os
from wishlistops.discord_notifier import DiscordNotifier


async def test_approval_request():
    """Test sending an approval request."""
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    
    if not webhook_url:
        print("❌ DISCORD_WEBHOOK_URL environment variable not set")
        print("\nTo test with a real webhook:")
        print("1. Go to Discord Server Settings > Integrations > Webhooks")
        print("2. Create a new webhook")
        print("3. Copy the webhook URL")
        print("4. Run: export DISCORD_WEBHOOK_URL='<your_webhook_url>'")
        print("\nRunning in dry-run mode instead...\n")
        webhook_url = "https://discord.com/api/webhooks/123/abc"
        dry_run = True
    else:
        dry_run = False
        print(f"✅ Using webhook: {webhook_url[:50]}...")
    
    # Create notifier
    notifier = DiscordNotifier(webhook_url, dry_run=dry_run)
    
    # Test approval request
    print("\n📤 Sending approval request...")
    result = await notifier.send_approval_request(
        title="v1.2.0 - New Features and Bug Fixes",
        body=(
            "We've added several exciting features in this update:\n\n"
            "- New weapon system with dual-wielding\n"
            "- Improved graphics for explosions\n"
            "- Fixed bug where players could walk through walls\n"
            "- Added 5 new achievements\n"
            "- Performance improvements on older hardware\n\n"
            "Thanks to everyone who reported bugs and provided feedback!"
        ),
        game_name="Awesome Game",
        tag="v1.2.0",
        banner_url="https://via.placeholder.com/800x450.png?text=New+Update+Banner"
    )
    
    if result:
        print("✅ Approval request sent successfully!")
        print("   Check your Discord channel for the message.")
    else:
        print("ℹ️  Dry-run mode: No actual message sent")
    
    # Test error notification
    print("\n📤 Sending error notification...")
    result = await notifier.send_error(
        "AI generation failed: Rate limit exceeded. Will retry in 60 seconds."
    )
    
    if result:
        print("✅ Error notification sent successfully!")
    else:
        print("ℹ️  Dry-run mode: No actual message sent")
    
    # Test success notification
    print("\n📤 Sending success notification...")
    result = await notifier.send_success(
        title="v1.2.0 - New Features and Bug Fixes",
        steam_url="https://store.steampowered.com/news/app/123456"
    )
    
    if result:
        print("✅ Success notification sent successfully!")
    else:
        print("ℹ️  Dry-run mode: No actual message sent")
    
    print("\n✨ All tests completed!")


if __name__ == "__main__":
    asyncio.run(test_approval_request())
