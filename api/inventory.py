import httpx
import base64
import time
import os
import sys
from fastapi import HTTPException
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.rate_limiter import rate_limiter

load_dotenv()

EBAY_API_BASE = "https://api.ebay.com"
EBAY_CLIENT_ID = os.getenv("EBAY_CLIENT_ID")
EBAY_CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET")
EBAY_USER_TOKEN = os.getenv("EBAY_USER_TOKEN")


class InventoryAPIClient:
    """eBay Inventory API client for inventory management"""
    
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        user_token: Optional[str] = None
    ):
        self.client_id = client_id or EBAY_CLIENT_ID
        self.client_secret = client_secret or EBAY_CLIENT_SECRET
        self.user_token = user_token or EBAY_USER_TOKEN
        self.access_token = None
        self.token_expires_at = 0
    
    async def get_headers(self):
        """Get headers with OAuth token"""
        token = await self.get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
        }
    
    async def get_access_token(self) -> str:
        """Get OAuth token for Inventory API"""
        if self.user_token and not self.user_token.startswith("v^"):
            return self.user_token
        
        raise HTTPException(
            status_code=500,
            detail="Inventory API requires user OAuth token. Set EBAY_USER_TOKEN in .env"
        )
    
    async def get_inventory_items(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get all inventory items"""
        await rate_limiter.wait_if_needed("inventory")
        
        headers = await self.get_headers()
        async with httpx.AsyncClient() as client:
            url = f"{EBAY_API_BASE}/sell/inventory/v1/inventory_item"
            params = {
                "limit": limit,
                "offset": offset
            }
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
    
    async def get_inventory_item(
        self,
        sku: str
    ) -> Dict[str, Any]:
        """Get a specific inventory item by SKU"""
        await rate_limiter.wait_if_needed("inventory")
        
        headers = await self.get_headers()
        async with httpx.AsyncClient() as client:
            url = f"{EBAY_API_BASE}/sell/inventory/v1/inventory_item/{sku}"
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
    
    async def get_inventory_locations(
        self
    ) -> Dict[str, Any]:
        """Get all inventory locations"""
        await rate_limiter.wait_if_needed("inventory")
        
        headers = await self.get_headers()
        async with httpx.AsyncClient() as client:
            url = f"{EBAY_API_BASE}/sell/inventory/v1/location"
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
    
    async def get_offers(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get all offers (published listings)"""
        await rate_limiter.wait_if_needed("inventory")
        
        headers = await self.get_headers()
        async with httpx.AsyncClient() as client:
            url = f"{EBAY_API_BASE}/sell/inventory/v1/offer"
            params = {
                "limit": limit,
                "offset": offset
            }
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
    
    async def get_offer(
        self,
        offer_id: str
    ) -> Dict[str, Any]:
        """Get a specific offer by ID"""
        await rate_limiter.wait_if_needed("inventory")
        
        headers = await self.get_headers()
        async with httpx.AsyncClient() as client:
            url = f"{EBAY_API_BASE}/sell/inventory/v1/offer/{offer_id}"
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
    
    async def get_offer_by_sku(
        self,
        sku: str
    ) -> Dict[str, Any]:
        """Get offers for a specific SKU"""
        await rate_limiter.wait_if_needed("inventory")
        
        headers = await self.get_headers()
        async with httpx.AsyncClient() as client:
            url = f"{EBAY_API_BASE}/sell/inventory/v1/offer"
            params = {"sku": sku}
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
    
    async def bulk_get_inventory_item(
        self,
        skus: List[str]
    ) -> Dict[str, Any]:
        """Get multiple inventory items in bulk"""
        await rate_limiter.wait_if_needed("inventory")
        
        headers = await self.get_headers()
        async with httpx.AsyncClient() as client:
            url = f"{EBAY_API_BASE}/sell/inventory/v1/bulk_inventory_item"
            data = {"requests": [{"sku": sku} for sku in skus]}
            response = await client.post(url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()
    
    async def get_location_inventory(
        self,
        location_id: str
    ) -> Dict[str, Any]:
        """Get inventory for a specific location"""
        await rate_limiter.wait_if_needed("inventory")
        
        headers = await self.get_headers()
        async with httpx.AsyncClient() as client:
            url = f"{EBAY_API_BASE}/sell/inventory/v1/location/{location_id}/inventory_item"
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
