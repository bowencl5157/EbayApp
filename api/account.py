import httpx
import base64
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
EBAY_USER_TOKEN = os.getenv("EBAY_USER_TOKEN")


class AccountAPIClient:
    """eBay Account API client for account management"""
    
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
        """Get OAuth token for Account API"""
        if self.user_token and not self.user_token.startswith("v^"):
            return self.user_token
        
        raise HTTPException(
            status_code=500,
            detail="Account API requires user OAuth token. Set EBAY_USER_TOKEN in .env"
        )
    
    async def get_account(
        self
    ) -> Dict[str, Any]:
        """Get account information"""
        await rate_limiter.wait_if_needed("account")
        
        headers = await self.get_headers()
        async with httpx.AsyncClient() as client:
            url = f"{EBAY_API_BASE}/sell/account/v1/account"
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
    
    async def get_account_status(
        self
    ) -> Dict[str, Any]:
        """Get account status"""
        await rate_limiter.wait_if_needed("account")
        
        headers = await self.get_headers()
        async with httpx.AsyncClient() as client:
            url = f"{EBAY_API_BASE}/sell/account/v1/account/status"
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
    
    async def get_fulfillment_policies(
        self
    ) -> Dict[str, Any]:
        """Get fulfillment policies"""
        await rate_limiter.wait_if_needed("account")
        
        headers = await self.get_headers()
        async with httpx.AsyncClient() as client:
            url = f"{EBAY_API_BASE}/sell/account/v1/fulfillment_policy"
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
    
    async def get_payment_policies(
        self
    ) -> Dict[str, Any]:
        """Get payment policies"""
        await rate_limiter.wait_if_needed("account")
        
        headers = await self.get_headers()
        async with httpx.AsyncClient() as client:
            url = f"{EBAY_API_BASE}/sell/account/v1/payment_policy"
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
    
    async def get_return_policies(
        self
    ) -> Dict[str, Any]:
        """Get return policies"""
        await rate_limiter.wait_if_needed("account")
        
        headers = await self.get_headers()
        async with httpx.AsyncClient() as client:
            url = f"{EBAY_API_BASE}/sell/account/v1/return_policy"
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
    
    async def get_subscription(
        self
    ) -> Dict[str, Any]:
        """Get subscription information"""
        await rate_limiter.wait_if_needed("account")
        
        headers = await self.get_headers()
        async with httpx.AsyncClient() as client:
            url = f"{EBAY_API_BASE}/sell/account/v1/subscription"
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
    
    async def get_rate_limits(
        self
    ) -> Dict[str, Any]:
        """Get API rate limits"""
        await rate_limiter.wait_if_needed("account")
        
        headers = await self.get_headers()
        async with httpx.AsyncClient() as client:
            url = f"{EBAY_API_BASE}/sell/account/v1/rate_limit"
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
    
    async def get_privileges(
        self
    ) -> Dict[str, Any]:
        """Get account privileges"""
        await rate_limiter.wait_if_needed("account")
        
        headers = await self.get_headers()
        async with httpx.AsyncClient() as client:
            url = f"{EBAY_API_BASE}/sell/account/v1/privilege"
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
