import base64
import httpx
import time
from fastapi import HTTPException
from typing import Optional, Dict, Any
import os
from dotenv import load_dotenv
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.cache import cache

load_dotenv()

EBAY_API_BASE = "https://api.ebay.com"
EBAY_APP_TOKEN = os.getenv("EBAY_APP_TOKEN")
EBAY_ACCESS_TOKEN = os.getenv("EBAY_ACCESS_TOKEN")
EBAY_CLIENT_ID = os.getenv("EBAY_CLIENT_ID")
EBAY_CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET")


class BrowseAPIClient:
    """eBay Browse API client for product search and item details"""
    
    def __init__(
        self,
        app_token: Optional[str] = None,
        access_token: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ):
        self.app_token = app_token or EBAY_APP_TOKEN
        self.access_token = access_token or EBAY_ACCESS_TOKEN
        self.client_id = client_id or EBAY_CLIENT_ID
        self.client_secret = client_secret or EBAY_CLIENT_SECRET
        self.token_expires_at = 0
    
    async def get_headers(self):
        """Get Browse API headers with a valid OAuth access token"""
        token = await self.get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
        }

    async def get_access_token(self) -> str:
        """Return an OAuth token for eBay Browse API calls with automatic refresh"""
        if self.access_token:
            if time.time() < self.token_expires_at:
                return self.access_token
            if self.access_token.startswith("v^") and not self.client_secret:
                return self.access_token
        
        if self.app_token and self.app_token.startswith("v^") and not self.client_secret:
            self.access_token = self.app_token
            return self.access_token

        if not self.client_id or not self.client_secret:
            raise HTTPException(
                status_code=500,
                detail=(
                    "Real eBay Browse API data requires OAuth credentials. "
                    "Set EBAY_CLIENT_ID and EBAY_CLIENT_SECRET in .env or appToken.txt. "
                    "The app will automatically exchange these for a valid OAuth token."
                ),
            )

        print("Exchanging OAuth token using client credentials...")
        credentials = f"{self.client_id}:{self.client_secret}".encode("utf-8")
        encoded_credentials = base64.b64encode(credentials).decode("utf-8")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{EBAY_API_BASE}/identity/v1/oauth2/token",
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Authorization": f"Basic {encoded_credentials}",
                },
                data={
                    "grant_type": "client_credentials",
                    "scope": "https://api.ebay.com/oauth/api_scope",
                },
            )
            if response.status_code == 401:
                raise HTTPException(
                    status_code=401,
                    detail=(
                        "eBay OAuth token exchange failed with 401 Unauthorized. "
                        "The client ID/client secret from appToken.txt were sent to eBay, "
                        "but eBay rejected them. Verify the production Client ID and Cert ID/client secret "
                        "in the eBay Developer Portal."
                    ),
                )
            response.raise_for_status()
            token_data = response.json()
            self.access_token = token_data["access_token"]
            self.token_expires_at = time.time() + int(token_data.get("expires_in", 7200)) - 60
            print(f"OAuth token refreshed successfully. Expires in {int(token_data.get('expires_in', 7200))} seconds.")
            return self.access_token
    
    async def search_items(self, query: str, limit: int = 20, sort: str = "price", use_cache: bool = True) -> Dict[str, Any]:
        """Search for items on eBay using Browse API v2"""
        if use_cache:
            cached = cache.get("search", query=query, limit=limit, sort=sort)
            if cached:
                return cached
        
        headers = await self.get_headers()
        async with httpx.AsyncClient() as client:
            url = f"{EBAY_API_BASE}/buy/browse/v1/item_summary/search"
            params = {
                "q": query,
                "limit": limit,
                "fieldgroups": "PRODUCT,COMPACT"
            }
            try:
                response = await client.get(url, headers=headers, params=params)
                print(f"Search response status: {response.status_code}")
                print(f"Search URL: {response.url}")
                print(f"Response text: {response.text[:500]}")
                response.raise_for_status()
                result = response.json()
                if use_cache:
                    cache.set("search", result, ttl_seconds=1800, query=query, limit=limit, sort=sort)  # 30 min cache
                return result
            except Exception as e:
                print(f"Search error: {type(e).__name__}: {str(e)}")
                print(f"Error details: {e.response.text if hasattr(e, 'response') else 'No response'}")
                raise
    
    async def get_trending_items(self, category_id: Optional[str] = None, limit: int = 20, use_cache: bool = True) -> Dict[str, Any]:
        """Get trending/best selling items using Browse API v2"""
        if use_cache:
            cached = cache.get("trending", category_id=category_id, limit=limit)
            if cached:
                return cached
        
        headers = await self.get_headers()
        async with httpx.AsyncClient() as client:
            url = f"{EBAY_API_BASE}/buy/browse/v1/item_summary/search"
            params = {
                "q": "trending",
                "limit": limit
            }
            if category_id:
                params["category_ids"] = category_id
            try:
                response = await client.get(url, headers=headers, params=params)
                print(f"Trending response status: {response.status_code}")
                print(f"Trending URL: {response.url}")
                print(f"Response text: {response.text[:500]}")
                response.raise_for_status()
                result = response.json()
                if use_cache:
                    cache.set("trending", result, ttl_seconds=3600, category_id=category_id, limit=limit)  # 1 hour cache
                return result
            except Exception as e:
                print(f"Trending error: {e}")
                raise
    
    async def get_item_details(self, item_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific item"""
        headers = await self.get_headers()
        async with httpx.AsyncClient() as client:
            url = f"{EBAY_API_BASE}/buy/browse/v1/item/{item_id}"
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
    
    async def get_item_summary(self, item_ids: list) -> Dict[str, Any]:
        """Get summary for multiple items"""
        headers = await self.get_headers()
        async with httpx.AsyncClient() as client:
            url = f"{EBAY_API_BASE}/buy/browse/v1/item_summary/get_item_summaries"
            params = {"item_ids": ",".join(item_ids)}
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
    
    async def search_by_image(self, image_url: str, limit: int = 20) -> Dict[str, Any]:
        """Search for items by image"""
        headers = await self.get_headers()
        async with httpx.AsyncClient() as client:
            url = f"{EBAY_API_BASE}/buy/browse/v1/search_by_image"
            data = {"imageUrl": image_url}
            response = await client.post(url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()
