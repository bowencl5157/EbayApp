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


class TradingAPIClient:
    """eBay Trading API client for seller operations"""
    
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
    
    async def get_user_token(self) -> str:
        """Get user OAuth token for Trading API operations"""
        if self.user_token and not self.user_token.startswith("v^"):
            return self.user_token
        
        raise HTTPException(
            status_code=500,
            detail="Trading API requires user OAuth token. Set EBAY_USER_TOKEN in .env"
        )
    
    async def get_my_ebay_selling(
        self,
        active_list: bool = True,
        sold_list: bool = False,
        limit: int = 200
    ) -> Dict[str, Any]:
        """Get seller's active and sold listings"""
        await rate_limiter.wait_if_needed("trading")
        
        token = await self.get_user_token()
        
        async with httpx.AsyncClient() as client:
            url = f"{EBAY_API_BASE}/ws/api.dll"
            headers = {
                "X-EBAY-API-CALL-NAME": "GetMyeBaySelling",
                "X-EBAY-API-APP-NAME": self.client_id,
                "X-EBAY-API-DEV-NAME": self.client_id,
                "X-EBAY-API-CERT-NAME": self.client_id,
                "X-EBAY-API-SITEID": "0",
                "X-EBAY-API-COMPATIBILITY-LEVEL": "967",
                "Content-Type": "text/xml"
            }
            
            xml_body = f"""<?xml version="1.0" encoding="utf-8"?>
            <GetMyeBaySellingRequest xmlns="urn:ebay:apis:eBLBaseComponents">
                <RequesterCredentials>
                    <eBayAuthToken>{token}</eBayAuthToken>
                </RequesterCredentials>
                <ActiveList>
                    <Include>{str(active_list).lower()}</Include>
                    <ListingType>FixedPriceItem</ListingType>
                    <Pagination>
                        <EntriesPerPage>{limit}</EntriesPerPage>
                    </Pagination>
                </ActiveList>
                <SoldList>
                    <Include>{str(sold_list).lower()}</Include>
                    <Pagination>
                        <EntriesPerPage>{limit}</EntriesPerPage>
                    </Pagination>
                </SoldList>
            </GetMyeBaySellingRequest>"""
            
            response = await client.post(url, headers=headers, data=xml_body)
            response.raise_for_status()
            return response.text
    
    async def get_seller_list(
        self,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 200
    ) -> Dict[str, Any]:
        """Get seller's listings within a time range"""
        await rate_limiter.wait_if_needed("trading")
        
        token = await self.get_user_token()
        
        async with httpx.AsyncClient() as client:
            url = f"{EBAY_API_BASE}/ws/api.dll"
            headers = {
                "X-EBAY-API-CALL-NAME": "GetSellerList",
                "X-EBAY-API-APP-NAME": self.client_id,
                "X-EBAY-API-DEV-NAME": self.client_id,
                "X-EBAY-API-CERT-NAME": self.client_id,
                "X-EBAY-API-SITEID": "0",
                "X-EBAY-API-COMPATIBILITY-LEVEL": "967",
                "Content-Type": "text/xml"
            }
            
            xml_body = f"""<?xml version="1.0" encoding="utf-8"?>
            <GetSellerListRequest xmlns="urn:ebay:apis:eBLBaseComponents">
                <RequesterCredentials>
                    <eBayAuthToken>{token}</eBayAuthToken>
                </RequesterCredentials>
                <GranularityLevel>Coarse</GranularityLevel>
                <StartTimeFrom>{start_time}</StartTimeFrom>
                <StartTimeTo>{end_time}</StartTimeTo>
                <Pagination>
                    <EntriesPerPage>{limit}</EntriesPerPage>
                    <PageNumber>1</PageNumber>
                </Pagination>
            </GetSellerListRequest>"""
            
            response = await client.post(url, headers=headers, data=xml_body)
            response.raise_for_status()
            return response.text
    
    async def get_account(
        self
    ) -> Dict[str, Any]:
        """Get seller account information"""
        await rate_limiter.wait_if_needed("trading")
        
        token = await self.get_user_token()
        
        async with httpx.AsyncClient() as client:
            url = f"{EBAY_API_BASE}/ws/api.dll"
            headers = {
                "X-EBAY-API-CALL-NAME": "GetAccount",
                "X-EBAY-API-APP-NAME": self.client_id,
                "X-EBAY-API-DEV-NAME": self.client_id,
                "X-EBAY-API-CERT-NAME": self.client_id,
                "X-EBAY-API-SITEID": "0",
                "X-EBAY-API-COMPATIBILITY-LEVEL": "967",
                "Content-Type": "text/xml"
            }
            
            xml_body = f"""<?xml version="1.0" encoding="utf-8"?>
            <GetAccountRequest xmlns="urn:ebay:apis:eBLBaseComponents">
                <RequesterCredentials>
                    <eBayAuthToken>{token}</eBayAuthToken>
                </RequesterCredentials>
                <AccountHistorySelection>LastInvoice</AccountHistorySelection>
            </GetAccountRequest>"""
            
            response = await client.post(url, headers=headers, data=xml_body)
            response.raise_for_status()
            return response.text
    
    async def revise_item(
        self,
        item_id: str,
        price: Optional[float] = None,
        quantity: Optional[int] = None,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """Revise an existing listing (for repricing)"""
        await rate_limiter.wait_if_needed("trading")
        
        token = await self.get_user_token()
        
        async with httpx.AsyncClient() as client:
            url = f"{EBAY_API_BASE}/ws/api.dll"
            headers = {
                "X-EBAY-API-CALL-NAME": "ReviseItem",
                "X-EBAY-API-APP-NAME": self.client_id,
                "X-EBAY-API-DEV-NAME": self.client_id,
                "X-EBAY-API-CERT-NAME": self.client_id,
                "X-EBAY-API-SITEID": "0",
                "X-EBAY-API-COMPATIBILITY-LEVEL": "967",
                "Content-Type": "text/xml"
            }
            
            xml_body = f"""<?xml version="1.0" encoding="utf-8"?>
            <ReviseItemRequest xmlns="urn:ebay:apis:eBLBaseComponents">
                <RequesterCredentials>
                    <eBayAuthToken>{token}</eBayAuthToken>
                </RequesterCredentials>
                <ItemID>{item_id}</ItemID>"""
            
            if price:
                xml_body += f"<StartPrice>{price}</StartPrice>"
            if quantity:
                xml_body += f"<Quantity>{quantity}</Quantity>"
            if title:
                xml_body += f"<Title>{title}</Title>"
            
            xml_body += "</ReviseItemRequest>"
            
            response = await client.post(url, headers=headers, data=xml_body)
            response.raise_for_status()
            return response.text
