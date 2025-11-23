"""
Tests for Discord notification system.

Tests webhook formatting, error handling, and integration with Discord API.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from wishlistops.discord_notifier import DiscordNotifier, DiscordError, WebhookError


def test_notifier_initialization():
    """Test notifier can be initialized with valid webhook URL."""
    notifier = DiscordNotifier("https://discord.com/api/webhooks/123/abc")
    assert notifier.webhook_url is not None
    assert notifier.dry_run is False


def test_notifier_initialization_with_none_webhook():
    """Test notifier can be initialized with None webhook."""
    notifier = DiscordNotifier(None)
    assert notifier.webhook_url is None
    assert notifier.dry_run is False


def test_invalid_webhook_url_raises_error():
    """Test invalid webhook URL is rejected."""
    with pytest.raises(ValueError, match="Invalid Discord webhook"):
        DiscordNotifier("https://example.com/webhook")


def test_dry_run_mode():
    """Test dry run mode doesn't send."""
    notifier = DiscordNotifier(
        "https://discord.com/api/webhooks/123/abc",
        dry_run=True
    )
    assert notifier.dry_run is True


@pytest.mark.asyncio
async def test_send_without_webhook():
    """Test sending without webhook configured returns False."""
    notifier = DiscordNotifier(None)
    result = await notifier.send_approval_request(
        title="Test",
        body="Test body"
    )
    assert result is False


@pytest.mark.asyncio
async def test_send_in_dry_run_mode():
    """Test dry run mode returns False without sending."""
    notifier = DiscordNotifier(
        "https://discord.com/api/webhooks/123/abc",
        dry_run=True
    )
    result = await notifier.send_approval_request(
        title="Test",
        body="Test body"
    )
    assert result is False


@pytest.mark.asyncio
async def test_build_approval_embed():
    """Test approval embed is built correctly."""
    notifier = DiscordNotifier("https://discord.com/api/webhooks/123/abc")
    
    embed = notifier._build_approval_embed(
        title="Test Title",
        body="This is a test body with some content.",
        banner_url="https://example.com/banner.png",
        game_name="Test Game",
        tag="v1.0.0",
        steam_app_id="480"
    )
    
    assert "title" in embed
    assert "Test Title" in embed["title"]
    assert "description" in embed
    assert "Test Game" in embed["description"]
    assert "v1.0.0" in embed["description"]
    assert embed["color"] == 5814783
    assert "fields" in embed
    assert len(embed["fields"]) == 2
    assert "image" in embed
    assert embed["image"]["url"] == "https://example.com/banner.png"


@pytest.mark.asyncio
async def test_build_approval_embed_truncates_long_body():
    """Test long body is truncated in preview."""
    notifier = DiscordNotifier("https://discord.com/api/webhooks/123/abc")
    
    long_body = "a" * 1000
    embed = notifier._build_approval_embed(
        title="Test",
        body=long_body,
        banner_url=None,
        game_name="Game",
        tag="v1.0.0",
        steam_app_id="480"
    )
    
    # Body should be truncated to 500 chars + "..."
    assert "..." in embed["description"]
    assert len(embed["description"]) <= notifier.MAX_EMBED_DESCRIPTION


@pytest.mark.asyncio
async def test_build_approval_embed_truncates_long_title():
    """Test long title is truncated."""
    notifier = DiscordNotifier("https://discord.com/api/webhooks/123/abc")
    
    long_title = "t" * 300
    embed = notifier._build_approval_embed(
        title=long_title,
        body="Body",
        banner_url=None,
        game_name="Game",
        tag="v1.0.0",
        steam_app_id="480"
    )
    
    assert len(embed["title"]) <= notifier.MAX_TITLE


@pytest.mark.asyncio
async def test_build_approval_embed_without_optional_fields():
    """Test embed builds correctly without optional fields."""
    notifier = DiscordNotifier("https://discord.com/api/webhooks/123/abc")
    
    embed = notifier._build_approval_embed(
        title="Test",
        body="Body",
        banner_url=None,
        game_name=None,
        tag=None,
        steam_app_id=None
    )
    
    assert "Unknown" in embed["description"]
    assert "image" not in embed


@pytest.mark.asyncio
async def test_send_error_notification():
    """Test error notification is formatted correctly."""
    notifier = DiscordNotifier("https://discord.com/api/webhooks/123/abc")
    
    with patch.object(notifier, '_send_webhook', new=AsyncMock()) as mock_send:
        result = await notifier.send_error("Test error message")
        
        assert result is True
        mock_send.assert_called_once()
        
        # Check the embed structure
        call_args = mock_send.call_args
        embed = call_args[0][0]
        assert "❌" in embed["title"]
        assert "Test error message" in embed["description"]
        assert embed["color"] == 15158332  # Red


@pytest.mark.asyncio
async def test_send_error_without_webhook():
    """Test sending error without webhook returns False."""
    notifier = DiscordNotifier(None)
    result = await notifier.send_error("Test error")
    assert result is False


@pytest.mark.asyncio
async def test_send_error_in_dry_run():
    """Test error notification in dry run mode."""
    notifier = DiscordNotifier(
        "https://discord.com/api/webhooks/123/abc",
        dry_run=True
    )
    result = await notifier.send_error("Test error")
    assert result is False


@pytest.mark.asyncio
async def test_send_success_notification():
    """Test success notification is formatted correctly."""
    notifier = DiscordNotifier("https://discord.com/api/webhooks/123/abc")
    
    with patch.object(notifier, '_send_webhook', new=AsyncMock()) as mock_send:
        result = await notifier.send_success(
            title="Test Announcement",
            steam_url="https://store.steampowered.com/news/app/123"
        )
        
        assert result is True
        mock_send.assert_called_once()
        
        # Check the embed structure
        call_args = mock_send.call_args
        embed = call_args[0][0]
        assert "✅" in embed["title"]
        assert "Test Announcement" in embed["description"]
        assert "https://store.steampowered.com/news/app/123" in embed["description"]
        assert embed["color"] == 5763719  # Green


@pytest.mark.asyncio
async def test_send_success_without_steam_url():
    """Test success notification without Steam URL."""
    notifier = DiscordNotifier("https://discord.com/api/webhooks/123/abc")
    
    with patch.object(notifier, '_send_webhook', new=AsyncMock()) as mock_send:
        result = await notifier.send_success(title="Test")
        
        assert result is True
        mock_send.assert_called_once()


@pytest.mark.asyncio
async def test_send_success_in_dry_run():
    """Test success notification in dry run mode."""
    notifier = DiscordNotifier(
        "https://discord.com/api/webhooks/123/abc",
        dry_run=True
    )
    result = await notifier.send_success("Test")
    assert result is False


@pytest.mark.asyncio
async def test_send_approval_request_with_local_banner(tmp_path):
    """Local banner path should be uploaded as attachment."""
    notifier = DiscordNotifier("https://discord.com/api/webhooks/123/abc")
    banner_path = tmp_path / "screenshots" / "boss.png"
    banner_path.parent.mkdir(parents=True, exist_ok=True)
    banner_path.write_bytes(b"image-bytes")

    with patch.object(notifier, '_send_webhook', new=AsyncMock()) as mock_send:
        await notifier.send_approval_request(
            title="Test",
            body="Body",
            banner_path=str(banner_path)
        )

        mock_send.assert_awaited_once()
        embed = mock_send.await_args.args[0]
        assert embed["image"]["url"].startswith("attachment://")
        assert mock_send.await_args.kwargs["file_bytes"] == b"image-bytes"
        assert mock_send.await_args.kwargs["filename"] == "boss.png"


@pytest.mark.asyncio
async def test_send_webhook_success():
    """Test _send_webhook with successful response."""
    notifier = DiscordNotifier("https://discord.com/api/webhooks/123/abc")
    
    # Create a mock response that properly supports async context manager
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    
    # Create a mock session
    mock_session = MagicMock()
    mock_session.post = MagicMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        embed = {"title": "Test"}
        await notifier._send_webhook(embed)
        
        mock_session.post.assert_called_once()


@pytest.mark.asyncio
async def test_send_webhook_with_file_payload():
    """_send_webhook should send multipart form when file bytes provided."""
    notifier = DiscordNotifier("https://discord.com/api/webhooks/123/abc")

    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.post = MagicMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with patch('aiohttp.ClientSession', return_value=mock_session):
        embed = {"title": "Test"}
        await notifier._send_webhook(embed, file_bytes=b"123", filename="banner.png")

        kwargs = mock_session.post.call_args.kwargs
        assert "data" in kwargs
        assert "json" not in kwargs


@pytest.mark.asyncio
async def test_send_webhook_rate_limit():
    """Test _send_webhook handles rate limit error."""
    notifier = DiscordNotifier("https://discord.com/api/webhooks/123/abc")
    
    mock_response = MagicMock()
    mock_response.status = 429
    mock_response.headers = {"Retry-After": "60"}
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    
    mock_session = MagicMock()
    mock_session.post = MagicMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        embed = {"title": "Test"}
        
        with pytest.raises(WebhookError, match="rate limit"):
            await notifier._send_webhook(embed)


@pytest.mark.asyncio
async def test_send_webhook_not_found():
    """Test _send_webhook handles 404 error."""
    notifier = DiscordNotifier("https://discord.com/api/webhooks/123/abc")
    
    mock_response = MagicMock()
    mock_response.status = 404
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    
    mock_session = MagicMock()
    mock_session.post = MagicMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        embed = {"title": "Test"}
        
        with pytest.raises(WebhookError, match="not found"):
            await notifier._send_webhook(embed)


@pytest.mark.asyncio
async def test_send_webhook_server_error():
    """Test _send_webhook handles server error."""
    notifier = DiscordNotifier("https://discord.com/api/webhooks/123/abc")
    
    mock_response = MagicMock()
    mock_response.status = 500
    mock_response.text = AsyncMock(return_value="Internal Server Error")
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    
    mock_session = MagicMock()
    mock_session.post = MagicMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        embed = {"title": "Test"}
        
        with pytest.raises(WebhookError, match="status 500"):
            await notifier._send_webhook(embed)


@pytest.mark.asyncio
async def test_send_approval_raises_webhook_error_on_failure():
    """Test send_approval_request raises WebhookError on failure."""
    notifier = DiscordNotifier("https://discord.com/api/webhooks/123/abc")
    
    with patch.object(notifier, '_send_webhook', side_effect=Exception("Network error")):
        with pytest.raises(WebhookError, match="Discord notification failed"):
            await notifier.send_approval_request(
                title="Test",
                body="Body"
            )


@pytest.mark.asyncio
async def test_notify_discord_helper_success():
    """Test notify_discord convenience function."""
    from wishlistops.discord_notifier import notify_discord
    
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    
    mock_session = MagicMock()
    mock_session.post = MagicMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        result = await notify_discord(
            webhook_url="https://discord.com/api/webhooks/123/abc",
            message="Test message"
        )
        
        assert result is True


@pytest.mark.asyncio
async def test_notify_discord_helper_failure():
    """Test notify_discord convenience function on failure."""
    from wishlistops.discord_notifier import notify_discord
    
    mock_session = MagicMock()
    mock_session.post = MagicMock(side_effect=Exception("Network error"))
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        result = await notify_discord(
            webhook_url="https://discord.com/api/webhooks/123/abc",
            message="Test message"
        )
        
        assert result is False


# Integration tests converted to use mocks
@pytest.mark.asyncio
async def test_send_approval_request_real():
    """Test sending to Discord webhook with mock."""
    import os
    from unittest.mock import AsyncMock, patch
    
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL', 'https://discord.com/api/webhooks/test/token')
    
    notifier = DiscordNotifier(webhook_url)
    
    with patch.object(notifier, '_send_webhook', new_callable=AsyncMock) as mock_send:
        result = await notifier.send_approval_request(
            title="Test Announcement from WishlistOps",
            body="This is a test announcement body with some content. It includes multiple sentences to test the preview functionality.",
            game_name="Test Game",
            tag="v1.0.0",
            banner_url="https://via.placeholder.com/800x450.png?text=Test+Banner"
        )
        
        assert result is True
        mock_send.assert_called_once()


@pytest.mark.asyncio
async def test_send_error_notification_real():
    """Test sending error notification to webhook with mock."""
    import os
    from unittest.mock import AsyncMock, patch
    
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL', 'https://discord.com/api/webhooks/test/token')
    
    notifier = DiscordNotifier(webhook_url)
    
    with patch.object(notifier, '_send_webhook', new_callable=AsyncMock) as mock_send:
        result = await notifier.send_error("Test error message from WishlistOps integration test")
        
        assert result is True
        mock_send.assert_called_once()


@pytest.mark.asyncio
async def test_send_success_notification_real():
    """Test sending success notification to webhook with mock."""
    import os
    from unittest.mock import AsyncMock, patch
    
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL', 'https://discord.com/api/webhooks/test/token')
    
    notifier = DiscordNotifier(webhook_url)
    
    with patch.object(notifier, '_send_webhook', new_callable=AsyncMock) as mock_send:
        result = await notifier.send_success(
            title="Test Update Published",
            steam_url="https://store.steampowered.com/news/app/123456"
        )
        
        assert result is True
        mock_send.assert_called_once()
