import httpx
import os
import sys
from fastapi import HTTPException
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.rate_limiter import rate_limiter

load_dotenv()

EBAY_API_BASE = "https://api.ebay.com"
EBAY_APP_ID = os.getenv("EBAY_CLIENT_ID")  # Finding API uses APP_ID


class FindingAPIClient:
    """eBay Finding API client for completed items and advanced search"""
    
    def __init__(self, app_id: Optional[str] = None):
        self.app_id = app_id or EBAY_APP_ID
        self.base_url = "https://svcs.ebay.com/services/search/FindingService/v1"
    
    async def find_completed_items(
        self,
        query: str,
        category_id: Optional[str] = None,
        limit: int = 100,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        condition: Optional[str] = None
    ) -> Dict[str, Any]:
        """Find completed/sold items for price history analysis"""
        await rate_limiter.wait_if_needed("finding")
        
        params = {
            "OPERATION-NAME": "findCompletedItems",
            "SERVICE-VERSION": "1.13.0",
            "SECURITY-APPNAME": self.app_id,
            "RESPONSE-DATA-FORMAT": "JSON",
            "REST-PAYLOAD": "",
            "keywords": query,
            "paginationInput.entriesPerPage": min(limit, 100)
        }
        
        if category_id:
            params["categoryId"] = category_id
        if min_price:
            params["itemFilter(0).name"] = "MinPrice"
            params["itemFilter(0).value"] = str(min_price)
        if max_price:
            params["itemFilter(1).name"] = "MaxPrice"
            params["itemFilter(1).value"] = str(max_price)
        if condition:
            params["itemFilter(2).name"] = "Condition"
            params["itemFilter(2).value"] = condition
        
        async with httpx.AsyncClient() as client:
            response = await client.get(self.base_url, params=params)
            response.raise_for_status()
            return response.json()
    
    async def find_items_by_category(
        self,
        category_id: str,
        limit: int = 100,
        sort_order: str = "BestMatch"
    ) -> Dict[str, Any]:
        """Find items in a specific category"""
        await rate_limiter.wait_if_needed("finding")
        
        params = {
            "OPERATION-NAME": "findItemsByCategory",
            "SERVICE-VERSION": "1.13.0",
            "SECURITY-APPNAME": self.app_id,
            "RESPONSE-DATA-FORMAT": "JSON",
            "REST-PAYLOAD": "",
            "categoryId": category_id,
            "paginationInput.entriesPerPage": min(limit, 100),
            "sortOrder": sort_order
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(self.base_url, params=params)
            response.raise_for_status()
            return response.json()
    
    async def find_items_advanced(
        self,
        query: str,
        category_id: Optional[str] = None,
        exclude_seller: Optional[str] = None,
        seller: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Advanced item search with filters"""
        await rate_limiter.wait_if_needed("finding")
        
        params = {
            "OPERATION-NAME": "findItemsAdvanced",
            "SERVICE-VERSION": "1.13.0",
            "SECURITY-APPNAME": self.app_id,
            "RESPONSE-DATA-FORMAT": "JSON",
            "REST-PAYLOAD": "",
            "keywords": query,
            "paginationInput.entriesPerPage": min(limit, 100)
        }
        
        if category_id:
            params["categoryId"] = category_id
        if exclude_seller:
            params["itemFilter(0).name"] = "ExcludeSeller"
            params["itemFilter(0).value"] = exclude_seller
        if seller:
            params["itemFilter(1).name"] = "Seller"
            params["itemFilter(1).value"] = seller
        
        async with httpx.AsyncClient() as client:
            response = await client.get(self.base_url, params=params)
            response.raise_for_status()
            return response.json()
    
    async def get_category_info(self, category_id: str) -> Dict[str, Any]:
        """Get category information and hierarchy"""
        await rate_limiter.wait_if_needed("finding")
        
        params = {
            "OPERATION-NAME": "getCategoryInfo",
            "SERVICE-VERSION": "1.13.0",
            "SECURITY-APPNAME": self.app_id,
            "RESPONSE-DATA-FORMAT": "JSON",
            "REST-PAYLOAD": "",
            "categoryId": category_id
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(self.base_url, params=params)
            response.raise_for_status()
            return response.json()
    
    async def get_popular_items(
        self,
        category_id: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get popular/trending items"""
        await rate_limiter.wait_if_needed("finding")
        
        params = {
            "OPERATION-NAME": "findPopularItems",
            "SERVICE-VERSION": "1.13.0",
            "SECURITY-APPNAME": self.app_id,
            "RESPONSE-DATA-FORMAT": "JSON",
            "REST-PAYLOAD": "",
            "paginationInput.entriesPerPage": min(limit, 100)
        }
        
        if category_id:
            params["categoryId"] = category_id
        
        async with httpx.AsyncClient() as client:
            response = await client.get(self.base_url, params=params)
            response.raise_for_status()
            return response.json()
