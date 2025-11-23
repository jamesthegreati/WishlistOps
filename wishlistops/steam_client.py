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
