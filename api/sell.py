import httpx
import os
from fastapi import HTTPException
from typing import Optional, Dict, Any, List

EBAY_API_BASE = "https://api.ebay.com"

class SellAPIClient:
    def __init__(self, access_token: str, marketplace_id: str = "EBAY_US"):
        self.access_token = access_token
        self.marketplace_id = marketplace_id
    
    async def get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-EBAY-C-MARKETPLACE-ID": self.marketplace_id,
        }
    
    async def get_orders(
        self,
        limit: int = 200,
        offset: int = 0,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get orders from eBay Sell API"""
        headers = await self.get_headers()
        
        params = {
            "limit": limit,
            "offset": offset,
            "fieldgroups": "FULL"
        }
        
        if start_date:
            params["filter"] = f"creationdate:[{start_date}T00:00:00.000Z..{end_date}T23:59:59.999Z]" if end_date else f"creationdate:[{start_date}T00:00:00.000Z..]"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{EBAY_API_BASE}/sell/fulfillment/v1/order",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            return response.json()
    
    async def get_financial_transactions(
        self,
        limit: int = 200,
        offset: int = 0,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get financial transactions/fees from eBay Sell API"""
        headers = await self.get_headers()
        
        params = {
            "limit": limit,
            "offset": offset
        }
        
        if start_date:
            params["filter"] = f"transactionDate:[{start_date}T00:00:00.000Z..{end_date}T23:59:59.999Z]" if end_date else f"transactionDate:[{start_date}T00:00:00.000Z..]"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{EBAY_API_BASE}/sell/finances/v1/transaction",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            return response.json()
    
    async def get_account(self) -> Dict[str, Any]:
        """Get seller account information from eBay Sell API"""
        headers = await self.get_headers()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{EBAY_API_BASE}/sell/account/v1",
                headers=headers
            )
            response.raise_for_status()
            return response.json()
