"""Steam context helper.

WishlistOps can optionally fetch public game context to improve announcement
writing. This uses the public Storefront API (no key required) and is designed
to fail soft (return None) if unavailable.

Note: Steamworks posting is not automated; this is read-only context.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import aiohttp


logger = logging.getLogger(__name__)


class SteamClient:
    def __init__(self, api_key: Optional[str] = None) -> None:
        # api_key is reserved for future Steam Web API calls; Storefront API is keyless.
        self.api_key = api_key

    async def get_game_context(self, app_id: str) -> Optional[dict[str, Any]]:
        """Fetch basic public game info from Steam Storefront API."""

        url = "https://store.steampowered.com/api/appdetails"
        params = {"appids": app_id}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status != 200:
                        logger.warning("Steam storefront request failed", extra={"status": resp.status})
                        return None
                    payload = await resp.json()
        except Exception as exc:
            logger.warning("Failed to fetch Steam game context", extra={"error": str(exc)})
            return None

        try:
            app_payload = payload.get(str(app_id), {})
            if not app_payload.get("success"):
                return None
            data = app_payload.get("data", {})

            return {
                "name": data.get("name"),
                "short_description": data.get("short_description"),
                "genres": [g.get("description") for g in data.get("genres", []) if isinstance(g, dict)],
                "categories": [c.get("description") for c in data.get("categories", []) if isinstance(c, dict)],
                "developers": data.get("developers", []) if isinstance(data.get("developers"), list) else [],
                "recent_news": [],
            }
        except Exception:
            return None
