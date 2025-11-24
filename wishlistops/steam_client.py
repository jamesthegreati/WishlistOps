"""
Steam Web API Client for WishlistOps.

Integrates with Steam Web API to:
- Detect user's game library
- Retrieve game details
- Support multi-game developers
- Fetch app information

Steam Web API Documentation: https://steamcommunity.com/dev
"""

import logging
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class SteamGame:
    """Represents a Steam game."""
    app_id: str
    name: str
    playtime_minutes: int = 0
    has_community_visible_stats: bool = False
    img_icon_url: Optional[str] = None
    img_logo_url: Optional[str] = None


class SteamClient:
    """
    Client for interacting with Steam Web API.
    
    Provides methods to retrieve user's game library and app details.
    """
    
    BASE_URL = "https://api.steampowered.com"
    STORE_API_URL = "https://store.steampowered.com/api"
    
    def __init__(self, api_key: str):
        """
        Initialize Steam client.
        
        Args:
            api_key: Steam Web API key from https://steamcommunity.com/dev/apikey
        """
        self.api_key = api_key
        
    async def get_owned_games(self, steam_id: str) -> List[SteamGame]:
        """
        Get list of games owned by user.
        
        Args:
            steam_id: Steam ID (64-bit) of the user
            
        Returns:
            List of owned games
            
        Raises:
            aiohttp.ClientError: If API request fails
        """
        logger.info(f"Fetching owned games for Steam ID: {steam_id}")
        
        url = f"{self.BASE_URL}/IPlayerService/GetOwnedGames/v0001/"
        params = {
            "key": self.api_key,
            "steamid": steam_id,
            "format": "json",
            "include_appinfo": 1,
            "include_played_free_games": 1
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                
                games_data = data.get("response", {}).get("games", [])
                
                games = [
                    SteamGame(
                        app_id=str(game["appid"]),
                        name=game.get("name", f"App {game['appid']}"),
                        playtime_minutes=game.get("playtime_forever", 0),
                        has_community_visible_stats=game.get("has_community_visible_stats", False),
                        img_icon_url=game.get("img_icon_url"),
                        img_logo_url=game.get("img_logo_url")
                    )
                    for game in games_data
                ]
                
                logger.info(f"Found {len(games)} owned games")
                return games
    
    async def get_app_details(self, app_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a Steam app.
        
        Args:
            app_id: Steam App ID
            
        Returns:
            Dictionary with app details
            
        Raises:
            aiohttp.ClientError: If API request fails
        """
        logger.info(f"Fetching app details for App ID: {app_id}")
        
        url = f"{self.STORE_API_URL}/appdetails"
        params = {
            "appids": app_id
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                
                app_data = data.get(app_id, {})
                
                if not app_data.get("success"):
                    logger.warning(f"App {app_id} not found or private")
                    return {}
                
                return app_data.get("data", {})
    
    async def get_developer_games(
        self,
        steam_id: str,
        filter_published: bool = True
    ) -> List[SteamGame]:
        """
        Get games that the user has published/developed.
        
        This filters the owned games to find ones where the user
        is likely the developer (has significant playtime for testing).
        
        Args:
            steam_id: Steam ID of the user
            filter_published: Whether to filter for likely published games
            
        Returns:
            List of games user likely developed
        """
        all_games = await self.get_owned_games(steam_id)
        
        if not filter_published:
            return all_games
        
        # Heuristic: Developer likely has high playtime on their own game
        # or the game has community stats enabled (developer feature)
        developer_games = [
            game for game in all_games
            if game.playtime_minutes > 60 or game.has_community_visible_stats
        ]
        
        logger.info(f"Found {len(developer_games)} potential developer games")
        return developer_games
    
    async def search_user_games(
        self,
        steam_id: str,
        search_term: str
    ) -> List[SteamGame]:
        """
        Search user's owned games by name.
        
        Args:
            steam_id: Steam ID of the user
            search_term: Search query
            
        Returns:
            List of matching games
        """
        all_games = await self.get_owned_games(steam_id)
        
        search_lower = search_term.lower()
        matching_games = [
            game for game in all_games
            if search_lower in game.name.lower()
        ]
        
        logger.info(f"Found {len(matching_games)} games matching '{search_term}'")
        return matching_games
    
    async def get_game_context(self, app_id: str) -> Dict[str, Any]:
        """
        Get enriched game context for AI announcement generation.
        
        Fetches detailed information including description, genres, tags,
        developers, and recent news to provide context for better announcements.
        
        Args:
            app_id: Steam App ID
            
        Returns:
            Dictionary with game context including:
                - name: Game name
                - description: Short and detailed descriptions
                - genres: List of genre names
                - tags: Popular user tags
                - developers: Developer names
                - publishers: Publisher names
                - release_date: Release date info
                - recent_news: Last 3 news items
                - header_image: Banner image URL
        """
        logger.info(f"Fetching game context for App ID: {app_id}")
        
        context = {
            "app_id": app_id,
            "name": "",
            "short_description": "",
            "detailed_description": "",
            "about_the_game": "",
            "genres": [],
            "tags": [],
            "developers": [],
            "publishers": [],
            "release_date": {},
            "recent_news": [],
            "header_image": "",
            "screenshots": [],
            "categories": []
        }
        
        # Get app details from Store API
        app_details = await self.get_app_details(app_id)
        
        if app_details:
            context["name"] = app_details.get("name", "")
            context["short_description"] = app_details.get("short_description", "")
            context["detailed_description"] = app_details.get("detailed_description", "")
            context["about_the_game"] = app_details.get("about_the_game", "")
            context["header_image"] = app_details.get("header_image", "")
            context["developers"] = app_details.get("developers", [])
            context["publishers"] = app_details.get("publishers", [])
            context["release_date"] = app_details.get("release_date", {})
            
            # Extract genres
            if "genres" in app_details:
                context["genres"] = [g.get("description", "") for g in app_details["genres"]]
            
            # Extract categories
            if "categories" in app_details:
                context["categories"] = [c.get("description", "") for c in app_details["categories"]]
            
            # Extract screenshots
            if "screenshots" in app_details:
                context["screenshots"] = [
                    s.get("path_full", "") for s in app_details["screenshots"][:5]
                ]
        
        # Get recent news (last 3 items)
        try:
            news_items = await self.get_app_news(app_id, count=3)
            context["recent_news"] = news_items
        except Exception as e:
            logger.warning(f"Failed to fetch news for {app_id}: {e}")
        
        logger.info(f"Game context fetched: {context['name']}")
        return context
    
    async def get_app_news(self, app_id: str, count: int = 5) -> List[Dict[str, Any]]:
        """
        Get recent news/announcements for a game.
        
        Args:
            app_id: Steam App ID
            count: Number of news items to retrieve (default 5)
            
        Returns:
            List of news items with title, contents, date, etc.
        """
        logger.info(f"Fetching news for App ID: {app_id}")
        
        url = f"{self.BASE_URL}/ISteamNews/GetNewsForApp/v2/"
        params = {
            "appid": app_id,
            "count": count,
            "maxlength": 500,  # Truncate long news items
            "format": "json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                
                news_items = data.get("appnews", {}).get("newsitems", [])
                
                # Format news items
                formatted_news = []
                for item in news_items:
                    formatted_news.append({
                        "title": item.get("title", ""),
                        "contents": item.get("contents", ""),
                        "author": item.get("author", ""),
                        "date": item.get("date", 0),
                        "url": item.get("url", "")
                    })
                
                logger.info(f"Found {len(formatted_news)} news items")
                return formatted_news
    
    async def get_player_summary(self, steam_id: str) -> Dict[str, Any]:
        """
        Get player summary information.
        
        Args:
            steam_id: Steam ID (64-bit)
            
        Returns:
            Player profile information
        """
        logger.info(f"Fetching player summary for Steam ID: {steam_id}")
        
        url = f"{self.BASE_URL}/ISteamUser/GetPlayerSummaries/v0002/"
        params = {
            "key": self.api_key,
            "steamids": steam_id
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                
                players = data.get("response", {}).get("players", [])
                
                if players:
                    return players[0]
                
                return {}


async def get_steam_games(api_key: str, steam_id: str) -> List[SteamGame]:
    """
    Convenience function to get owned games.
    
    Args:
        api_key: Steam Web API key
        steam_id: Steam ID of user
        
    Returns:
        List of owned games
    """
    client = SteamClient(api_key)
    return await client.get_owned_games(steam_id)
