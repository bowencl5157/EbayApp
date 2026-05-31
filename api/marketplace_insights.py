import httpx
import time
import os
import sys
from fastapi import HTTPException
from typing import Optional, Dict, Any
from dotenv import load_dotenv
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.rate_limiter import rate_limiter

load_dotenv()

EBAY_API_BASE = "https://api.ebay.com"
EBAY_CLIENT_ID = os.getenv("EBAY_CLIENT_ID")
EBAY_CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET")


class MarketplaceInsightsClient:
    """eBay Marketplace Insights API client for market trend data"""
    
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None
    ):
        self.client_id = client_id or EBAY_CLIENT_ID
        self.client_secret = client_secret or EBAY_CLIENT_SECRET
        self.access_token = None
        self.token_expires_at = 0
    
    async def get_access_token(self) -> str:
        """Get OAuth token for Marketplace Insights API"""
        if self.access_token and time.time() < self.token_expires_at:
            return self.access_token
        
        if not self.client_id or not self.client_secret:
            raise HTTPException(
                status_code=500,
                detail="Marketplace Insights API requires EBAY_CLIENT_ID and EBAY_CLIENT_SECRET"
            )
        
        # This would need proper OAuth implementation
        # Marketplace Insights API may have different auth requirements
        raise HTTPException(
            status_code=501,
            detail="Marketplace Insights API authentication not yet implemented"
        )
    
    async def get_market_trends(
        self,
        category_id: str,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """Get market trend data for a category"""
        await rate_limiter.wait_if_needed("marketplace_insights")
        
        token = await self.get_access_token()
        
        async with httpx.AsyncClient() as client:
            url = f"{EBAY_API_BASE}/marketplace_insights/v1/category_trends"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            params = {
                "category_id": category_id,
                "start_date": start_date,
                "end_date": end_date
            }
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
    
    async def get_category_performance(
        self,
        category_id: str
    ) -> Dict[str, Any]:
        """Get performance metrics for a category"""
        await rate_limiter.wait_if_needed("marketplace_insights")
        
        token = await self.get_access_token()
        
        async with httpx.AsyncClient() as client:
            url = f"{EBAY_API_BASE}/marketplace_insights/v1/category_performance"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            params = {"category_id": category_id}
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
    
    async def get_seller_benchmarks(
        self,
        category_id: str
    ) -> Dict[str, Any]:
        """Get seller performance benchmarks for a category"""
        await rate_limiter.wait_if_needed("marketplace_insights")
        
        token = await self.get_access_token()
        
        async with httpx.AsyncClient() as client:
            url = f"{EBAY_API_BASE}/marketplace_insights/v1/seller_benchmarks"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            params = {"category_id": category_id}
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
