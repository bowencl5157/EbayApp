import os
import httpx
import time
import uuid
import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from dotenv import load_dotenv

load_dotenv()

WALMART_CONSUMER_ID = os.getenv("WALMART_CONSUMER_ID")
WALMART_PRIVATE_KEY_FILE = os.getenv("WALMART_PRIVATE_KEY_FILE")
WALMART_API_BASE = "https://developer.api.walmart.com/api-proxy"


class WalmartAPIClient:
    """Client for Walmart Affiliate API"""
    
    def __init__(self, consumer_id: str = None, private_key_file: str = None, key_version: str = "1"):
        self.consumer_id = consumer_id or WALMART_CONSUMER_ID
        self.private_key_file = private_key_file or WALMART_PRIVATE_KEY_FILE
        self.api_base = WALMART_API_BASE
        self.key_version = key_version
        self.private_key = None
        
        if not self.consumer_id:
            raise ValueError("WALMART_CONSUMER_ID not found in environment variables")
        
        # Load private key if file exists
        if self.private_key_file and os.path.exists(self.private_key_file):
            try:
                with open(self.private_key_file, 'r') as f:
                    self.private_key = f.read()
            except Exception as e:
                print(f"Warning: Could not load private key from {self.private_key_file}: {e}")
    
    def canonicalize_headers(self, headers: dict) -> str:
        """Canonicalize headers for signature generation
        
        Sort keys and create string with values separated by newlines
        """
        sorted_keys = sorted(headers.keys())
        canonicalized = ""
        for key in sorted_keys:
            canonicalized += str(headers[key]).strip() + "\n"
        return canonicalized
    
    def generate_signature(self, intimestamp: str) -> str:
        """Generate RSA signature for Walmart API authentication
        
        Args:
            intimestamp: Unix epoch time in milliseconds
            
        Returns:
            Base64 encoded signature
        """
        if not self.private_key:
            raise ValueError("Private key not loaded")
        
        # Headers to sign
        headers_to_sign = {
            "WM_CONSUMER.ID": self.consumer_id,
            "WM_CONSUMER.INTIMESTAMP": intimestamp,
            "WM_SEC.KEY_VERSION": self.key_version
        }
        
        # Canonicalize headers
        string_to_sign = self.canonicalize_headers(headers_to_sign)
        
        # Load private key - try both PEM and OpenSSH formats
        try:
            private_key = serialization.load_pem_private_key(
                self.private_key.encode(),
                password=None,
                backend=default_backend()
            )
        except Exception:
            try:
                # Try loading as OpenSSH format
                private_key = serialization.load_ssh_private_key(
                    self.private_key.encode(),
                    password=None,
                    backend=default_backend()
                )
            except Exception as e:
                raise ValueError(f"Failed to load private key: {e}")
        
        # Sign the canonicalized string
        signature = private_key.sign(
            string_to_sign.encode('utf-8'),
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        
        # Base64 encode the signature
        return base64.b64encode(signature).decode('utf-8')
    
    async def get_headers(self) -> dict:
        """Get headers for Walmart API requests with signature
        
        Walmart API requires specific headers:
        - WM_CONSUMER.ID: Consumer ID
        - WM_CONSUMER.INTIMESTAMP: Unix epoch time in milliseconds
        - WM_SEC.KEY_VERSION: Private key version
        - WM_SEC.AUTH_SIGNATURE: Generated signature
        - WM_QOS.CORRELATION_ID: Unique ID for each request
        - WM_SVC.NAME: Service name
        - Accept: Content type
        """
        intimestamp = str(int(time.time() * 1000))
        correlation_id = str(uuid.uuid4())
        
        # Generate signature
        signature = self.generate_signature(intimestamp)
        
        headers = {
            "WM_CONSUMER.ID": self.consumer_id,
            "WM_CONSUMER.INTIMESTAMP": intimestamp,
            "WM_SEC.KEY_VERSION": self.key_version,
            "WM_SEC.AUTH_SIGNATURE": signature,
            "WM_QOS.CORRELATION_ID": correlation_id,
            "WM_SVC.NAME": "Walmart Marketplace",
            "Accept": "application/json"
        }
        
        return headers
    
    async def search_products(self, query: str, limit: int = 20, category: str = None) -> dict:
        """Search for products on Walmart using search endpoint
        
        Args:
            query: Search query string
            limit: Number of results to return
            category: Optional category filter
            
        Returns:
            Dictionary with search results
        """
        headers = await self.get_headers()
        limit = min(int(limit), 20)
        
        params = {
            "query": query,
            "numItems": limit
        }
        
        if category:
            params["category"] = category
        
        async with httpx.AsyncClient() as client:
            url = f"{self.api_base}/service/affil/product/v2/search"
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
    
    async def get_product_details(self, item_id: str) -> dict:
        """Get detailed information about a specific product
        
        Args:
            item_id: Walmart item ID
            
        Returns:
            Dictionary with product details
        """
        headers = await self.get_headers()
        
        async with httpx.AsyncClient() as client:
            url = f"{self.api_base}/service/affil/product/v2/paginated/items"
            params = {"count": 1}
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            # Filter for specific item ID from results
            if "items" in data:
                for item in data["items"]:
                    if str(item.get("itemId")) == str(item_id):
                        return item
            return data
    
    async def get_deals(self, category: str = None, limit: int = 20, brand: str = None, special_offer: str = None) -> dict:
        """Get current deals from Walmart using paginated items endpoint
        
        Args:
            category: Optional category filter (from taxonomy API)
            limit: Number of results to return
            brand: Optional brand filter
            special_offer: Special offers like rollback, clearance, specialBuy
            
        Returns:
            Dictionary with deal results
        """
        headers = await self.get_headers()
        
        params = {
            "count": limit
        }
        
        if category:
            params["category"] = category
        if brand:
            params["brand"] = brand
        if special_offer:
            params["specialOffer"] = special_offer
        
        async with httpx.AsyncClient() as client:
            url = f"{self.api_base}/service/affil/product/v2/paginated/items"
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
    
    async def get_reviews(self, item_id: str, limit: int = 10) -> dict:
        """Get reviews for a specific product
        
        Args:
            item_id: Walmart item ID
            limit: Number of reviews to return
            
        Returns:
            Dictionary with review results
        """
        headers = await self.get_headers()
        
        params = {
            "numItems": limit
        }
        
        async with httpx.AsyncClient() as client:
            url = f"{self.api_base}/affil/product/v2/reviews/{item_id}"
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
