from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import os
import re
import secrets
import httpx
from collections import Counter
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from models.database import get_db, init_db
from api import BrowseAPIClient
from api.finding import FindingAPIClient
from api.sell import SellAPIClient
from api.walmart import WalmartAPIClient
from services import (
    ProductResearchService,
    PriceMonitoringService,
    SellerAnalyticsService,
    MarketplaceResearchService,
    RepricingService
)

load_dotenv()

EBAY_API_BASE = "https://api.ebay.com"

# Lifespan events for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    yield
    # Shutdown (if needed)

app = FastAPI(title="eBay Product Research Tool", lifespan=lifespan)

# eBay API Configuration
EBAY_APP_TOKEN = os.getenv("EBAY_APP_TOKEN")
EBAY_ACCESS_TOKEN = os.getenv("EBAY_ACCESS_TOKEN")
EBAY_CLIENT_ID = os.getenv("EBAY_CLIENT_ID")
EBAY_CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET")
EBAY_REDIRECT_URI = os.getenv("EBAY_REDIRECT_URI", "http://localhost:8000/oauth/callback")
EBAY_OAUTH_SCOPES = [
    "sell.account.readonly",
    "sell.finances",
    "sell.fulfillment.readonly"
]

# Store user access tokens (in production, use a database)
user_tokens = {}

token_file_path = "appToken.updated.txt" if os.path.exists("appToken.updated.txt") else "appToken.txt"

if os.path.exists(token_file_path):
    with open(token_file_path, "r", encoding="utf-8") as token_file:
        for line in token_file:
            key, _, value = line.partition(":")
            normalized_key = key.strip().lower()
            normalized_value = value.strip()
            if normalized_key in {"client id", "app id/client id"} and normalized_value:
                EBAY_CLIENT_ID = normalized_value
            elif normalized_key == "client secret" and normalized_value:
                EBAY_CLIENT_SECRET = normalized_value
            elif normalized_key in {"access token", "application access token", "token"} and normalized_value:
                EBAY_ACCESS_TOKEN = normalized_value.removeprefix("Bearer ").strip()
            elif normalized_key == "authorization" and normalized_value.lower().startswith("bearer "):
                EBAY_ACCESS_TOKEN = normalized_value[7:].strip()

# Initialize API clients
browse_client = BrowseAPIClient(
    app_token=EBAY_APP_TOKEN,
    access_token=EBAY_ACCESS_TOKEN,
    client_id=EBAY_CLIENT_ID,
    client_secret=EBAY_CLIENT_SECRET
)

walmart_client = WalmartAPIClient()

finding_client = FindingAPIClient(app_id=EBAY_CLIENT_ID)

# Templates
templates = Jinja2Templates(directory="templates")

# Common words to exclude from keyword analysis
STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with",
    "by", "from", "as", "is", "was", "are", "were", "be", "been", "being", "have",
    "has", "had", "do", "does", "did", "will", "would", "could", "should", "may",
    "might", "must", "can", "new", "used", "great", "good", "best", "top", "free",
    "shipping", "fast", "buy", "get", "now", "sale", "deal", "hot", "cheap", "price"
}

def extract_keywords_from_titles(titles: List[str]) -> Dict[str, Any]:
    """Extract SEO keywords and long-tail keywords from listing titles"""
    all_words = []
    phrases = []
    
    for title in titles:
        # Extract individual words
        words = re.findall(r'\b[a-zA-Z]{3,}\b', title.lower())
        all_words.extend([w for w in words if w not in STOP_WORDS])
        
        # Extract phrases (2-3 word combinations)
        words_clean = [w for w in words if w not in STOP_WORDS]
        for i in range(len(words_clean) - 1):
            phrases.append(f"{words_clean[i]} {words_clean[i+1]}")
        for i in range(len(words_clean) - 2):
            phrases.append(f"{words_clean[i]} {words_clean[i+1]} {words_clean[i+2]}")
    
    # Count word frequencies
    word_counts = Counter(all_words)
    phrase_counts = Counter(phrases)
    
    # Get top keywords (single words)
    top_keywords = [
        {"keyword": word, "count": count, "type": "short-tail"}
        for word, count in word_counts.most_common(20)
    ]
    
    # Get top long-tail keywords (phrases)
    long_tail_keywords = [
        {"keyword": phrase, "count": count, "type": "long-tail"}
        for phrase, count in phrase_counts.most_common(20)
    ]
    
    return {
        "short_tail_keywords": top_keywords,
        "long_tail_keywords": long_tail_keywords,
        "total_listings_analyzed": len(titles)
    }

def parse_ebay_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None

def build_seller_breakdown(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    now = datetime.now(timezone.utc)
    seven_days_ago = now - timedelta(days=7)
    thirty_days_ago = now - timedelta(days=30)
    sellers = {}

    for item in items:
        seller_name = item.get("seller", {}).get("username") or "Unknown"
        price_value = item.get("price", {}).get("value")
        item_created_at = parse_ebay_datetime(item.get("itemCreationDate"))

        if seller_name not in sellers:
            sellers[seller_name] = {
                "seller": seller_name,
                "current_count": 0,
                "count_7d": 0,
                "count_30d": 0,
                "total_price": 0,
                "priced_items": 0,
                "feedback_score": item.get("seller", {}).get("feedbackScore", 0),
                "sample_title": item.get("title", ""),
                "sample_url": item.get("itemWebUrl", "")
            }

        seller = sellers[seller_name]
        seller["current_count"] += 1
        if item_created_at and item_created_at >= seven_days_ago:
            seller["count_7d"] += 1
        if item_created_at and item_created_at >= thirty_days_ago:
            seller["count_30d"] += 1
        if price_value is not None:
            seller["total_price"] += float(price_value)
            seller["priced_items"] += 1

    breakdown = []
    for seller in sellers.values():
        priced_items = seller.pop("priced_items")
        total_price = seller.pop("total_price")
        seller["avg_price"] = total_price / priced_items if priced_items else 0
        breakdown.append(seller)

    return sorted(
        breakdown,
        key=lambda seller: (seller["count_30d"], seller["count_7d"], seller["current_count"]),
        reverse=True
    )

def estimate_ebay_fee(price: float, shipping: float = 0) -> Dict[str, float]:
    total_sale_amount = price + shipping
    final_value_fee_rate = 0.1325
    per_order_fee = 0.40 if total_sale_amount > 10 else 0.30
    estimated_fee = (total_sale_amount * final_value_fee_rate) + per_order_fee
    fee_percentage = (estimated_fee / total_sale_amount) * 100 if total_sale_amount else 0
    return {
        "estimated_fee": estimated_fee,
        "fee_percentage": fee_percentage
    }

def build_store_fee_breakdown(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seller_categories = {}

    for item in items:
        if not item.get("price"):
            continue

        seller_name = item.get("seller", {}).get("username") or "Unknown"
        category_id = item.get("categoryId") or item.get("category", {}).get("categoryId") or "Unknown"
        category_name = (
            item.get("categoryName") or
            item.get("category", {}).get("categoryName") or
            item.get("categories", [{}])[0].get("categoryName") if item.get("categories") else
            f"Category {category_id}" if category_id != "Unknown" else
            "Unknown Category"
        )
        item_price = float(item.get("price", {}).get("value", 0))
        shipping_options = item.get("shippingOptions", [])
        shipping_cost = 0
        if shipping_options:
            shipping_cost = float(shipping_options[0].get("shippingCost", {}).get("value", 0))
        fee_estimate = estimate_ebay_fee(item_price, shipping_cost)

        key = f"{seller_name}||{category_id}"
        if key not in seller_categories:
            seller_categories[key] = {
                "store": seller_name,
                "category_id": category_id,
                "category_name": category_name,
                "listing_count": 0,
                "total_price": 0,
                "total_fee_percentage": 0,
                "total_fee_amount": 0,
                "feedback_score": item.get("seller", {}).get("feedbackScore", 0),
                "sample_title": item.get("title", ""),
                "sample_url": item.get("itemWebUrl", "")
            }

        sc = seller_categories[key]
        sc["listing_count"] += 1
        sc["total_price"] += item_price
        sc["total_fee_percentage"] += fee_estimate["fee_percentage"]
        sc["total_fee_amount"] += fee_estimate["estimated_fee"]

    breakdown = []
    for sc in seller_categories.values():
        listing_count = sc["listing_count"]
        sc["avg_price"] = sc.pop("total_price") / listing_count if listing_count else 0
        sc["avg_fee_percentage"] = sc.pop("total_fee_percentage") / listing_count if listing_count else 0
        sc["avg_fee_amount"] = sc.pop("total_fee_amount") / listing_count if listing_count else 0
        breakdown.append(sc)

    return sorted(
        breakdown,
        key=lambda sc: (sc["listing_count"], sc["avg_fee_percentage"]),
        reverse=True
    )

# API Endpoints
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/search")
async def search_products(query: str, limit: int = 20, sort: str = "price"):
    """Search for products on eBay"""
    try:
        results = await browse_client.search_items(query, limit, sort)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Category name to ID mapping for common categories
CATEGORY_NAME_TO_ID = {
    "electronics": "293",
    "clothing": "11450",
    "shoes": "93427",
    "home": "11700",
    "garden": "625",
    "toys": "220",
    "sports": "888",
    "automotive": "6001",
    "books": "267",
    "music": "11233",
    "movies": "11232",
    "video games": "1249",
    "jewelry": "281",
    "watches": "31387",
    "health": "26395",
    "beauty": "26395",
    "baby": "2984",
    "pet": "1281",
    "art": "550",
    "collectibles": "1",
    "antiques": "20081",
    "crafts": "14339",
    "business": "12576",
    "industrial": "12576",
    "cameras": "625",
    "photo": "625",
    "cell phones": "15032",
    "phones": "15032",
    "computers": "58058",
    "laptops": "177",
    "tablets": "171485",
    "kitchen": "20625",
    "furniture": "3197",
    "tools": "631",
    "hardware": "631",
}

@app.get("/api/trending")
async def get_trending(category_id: Optional[str] = None, limit: int = 20):
    """Get trending/best selling products using Browse API with category filter"""
    try:
        # Convert category name to ID if needed
        if category_id and not category_id.isdigit():
            category_id = CATEGORY_NAME_TO_ID.get(category_id.lower())
        
        # Use Browse API search with category filter
        headers = await browse_client.get_headers()
        async with httpx.AsyncClient() as client:
            url = f"{EBAY_API_BASE}/buy/browse/v1/item_summary/search"
            params = {
                "limit": limit
            }
            if category_id:
                params["category_ids"] = category_id
            else:
                # If no category, use a generic search term
                params["q"] = "best selling"
            
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            result = response.json()
            return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/item/{item_id}")
async def get_item(item_id: str):
    """Get detailed item information including pricing"""
    try:
        results = await browse_client.get_item_details(item_id)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/pricing/{query}")
async def get_pricing_data(query: str, limit: int = 50):
    """Get pricing data for a product category"""
    try:
        results = await browse_client.search_items(query, limit, "price")
        items = results.get("itemSummaries", [])
        
        prices = [float(item.get("price", {}).get("value", 0)) for item in items if item.get("price")]
        
        if not prices:
            return {"error": "No pricing data available"}
        
        fee_estimates = []
        for item in items:
            if not item.get("price"):
                continue
            item_price = float(item.get("price", {}).get("value", 0))
            shipping_options = item.get("shippingOptions", [])
            shipping_cost = 0
            if shipping_options:
                shipping_cost = float(shipping_options[0].get("shippingCost", {}).get("value", 0))
            fee_estimates.append(estimate_ebay_fee(item_price, shipping_cost))
        
        pricing_analysis = {
            "query": query,
            "total_items": len(items),
            "price_range": {
                "min": min(prices),
                "max": max(prices)
            },
            "average_price": sum(prices) / len(prices),
            "median_price": sorted(prices)[len(prices) // 2],
            "estimated_ebay_fees": {
                "average_fee_percentage": sum(fee["fee_percentage"] for fee in fee_estimates) / len(fee_estimates) if fee_estimates else 0,
                "average_fee_amount": sum(fee["estimated_fee"] for fee in fee_estimates) / len(fee_estimates) if fee_estimates else 0,
                "basis": "Estimated from active listing price plus shipping when available, using a 13.25% final value fee and $0.30-$0.40 per-order fee."
            },
            "store_fee_breakdown": build_store_fee_breakdown(items),
            "sample_items": items[:10]
        }
        
        return pricing_analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/oauth/authorize")
async def oauth_authorize():
    """Redirect user to eBay OAuth authorization page"""
    if not EBAY_CLIENT_ID:
        raise HTTPException(status_code=500, detail="EBAY_CLIENT_ID not configured")

    state = secrets.token_urlsafe(16)
    scopes = " ".join(EBAY_OAUTH_SCOPES)

    auth_url = (
        f"https://signin.ebay.com/authorize"
        f"?client_id={EBAY_CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={EBAY_REDIRECT_URI}"
        f"&scope={scopes}"
        f"&state={state}"
    )

    return RedirectResponse(auth_url)

@app.get("/oauth/callback")
async def oauth_callback(code: Optional[str] = None, state: Optional[str] = None, error: Optional[str] = None, error_description: Optional[str] = None):
    """Handle OAuth callback and exchange code for access token"""
    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error} - {error_description}")

    if not code:
        raise HTTPException(status_code=400, detail="OAuth callback missing authorization code. Please try the authorization flow again.")

    if not EBAY_CLIENT_ID or not EBAY_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="EBAY_CLIENT_ID or EBAY_CLIENT_SECRET not configured")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.ebay.com/identity/v1/oauth2/token",
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Authorization": f"Basic {base64.b64encode(f'{EBAY_CLIENT_ID}:{EBAY_CLIENT_SECRET}'.encode()).decode()}"
                },
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": EBAY_REDIRECT_URI
                }
            )
            response.raise_for_status()
            token_data = response.json()

        # Store the user access token
        user_tokens["user"] = {
            "access_token": token_data["access_token"],
            "refresh_token": token_data.get("refresh_token"),
            "expires_at": time.time() + int(token_data.get("expires_in", 7200)),
            "token_type": token_data.get("token_type", "User Access Token")
        }

        return RedirectResponse("/?oauth=success")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OAuth token exchange failed: {str(e)}")

@app.get("/api/account")
async def get_account_data(start_date: str, end_date: str):
    """Get seller account data including sales, fees, and profit breakdown"""
    try:
        # Check if user has authorized OAuth
        if "user" not in user_tokens:
            return {
                "error": "Please authorize your eBay account first. Click the 'Connect eBay Account' button below.",
                "period": f"{start_date} to {end_date}",
                "sales": [],
                "needs_auth": True
            }

        user_token = user_tokens["user"]["access_token"]
        sell_client = SellAPIClient(access_token=user_token, marketplace_id=EBAY_MARKETPLACE_ID)

        # Fetch orders and financial transactions
        orders_response = await sell_client.get_orders(limit=200, start_date=start_date, end_date=end_date)
        finances_response = await sell_client.get_financial_transactions(limit=200, start_date=start_date, end_date=end_date)

        orders = orders_response.get("orders", [])
        transactions = finances_response.get("transactions", [])

        # Process orders into sales data
        sales = []
        for order in orders:
            for line_item in order.get("lineItems", []):
                sold_price = float(line_item.get("lineItemCost", {}).get("value", 0))
                
                # Calculate fees from transactions
                order_id = order.get("orderId")
                order_fees = [t for t in transactions if t.get("orderId") == order_id]
                
                seller_fee = sum(float(f.get("amount", {}).get("value", 0)) for f in order_fees if f.get("feeType") == "FINAL_VALUE_FEE")
                promo_fee = sum(float(f.get("amount", {}).get("value", 0)) for f in order_fees if f.get("feeType") == "PROMOTIONAL_LISTING_FEE")
                tax = sum(float(f.get("amount", {}).get("value", 0)) for f in order_fees if f.get("category") == "TAX")
                
                total_fees = seller_fee + promo_fee + tax
                revenue = sold_price
                profit = revenue - total_fees

                sales.append({
                    "date": order.get("creationDate", "")[:10] if order.get("creationDate") else "N/A",
                    "item_title": line_item.get("title", "N/A"),
                    "sold_price": sold_price,
                    "seller_fee": seller_fee,
                    "promotional_fee": promo_fee,
                    "tax": tax,
                    "total_fees": total_fees,
                    "revenue": revenue,
                    "profit": profit
                })

        return {
            "period": f"{start_date} to {end_date}",
            "sales": sales,
            "auth_status": "authorized"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching account data: {str(e)}")

@app.get("/api/seo-keywords")
async def get_seo_keywords(query: str, limit: int = 50):
    """Analyze SEO keywords from best-selling items for a category"""
    try:
        results = await browse_client.search_items(query, limit, "bestmatch")
        items = results.get("itemSummaries", [])
        
        if not items:
            return {"error": "No items found for this query"}
        
        titles = [item.get("title", "") for item in items if item.get("title")]
        keyword_analysis = extract_keywords_from_titles(titles)
        
        keyword_analysis["query"] = query
        keyword_analysis["top_sellers"] = [
            {
                "title": item.get("title", ""),
                "price": item.get("price", {}),
                "seller": item.get("seller", {}).get("username", ""),
                "feedback_score": item.get("seller", {}).get("feedbackScore", 0)
            }
            for item in items[:5]
        ]
        keyword_analysis["seller_breakdown"] = build_seller_breakdown(items)
        keyword_analysis["seller_breakdown_basis"] = "Current Browse API results. 7-day and 30-day counts use eBay itemCreationDate when available."
        
        return keyword_analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# New Service Endpoints

@app.get("/api/product-research")
async def product_research(
    query: str,
    category_id: Optional[str] = None,
    include_price_history: bool = True,
    db: Session = Depends(get_db)
):
    """Comprehensive product research using multiple APIs"""
    try:
        service = ProductResearchService(db)
        results = await service.research_product(query, category_id, include_price_history)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/price-monitoring")
async def price_monitoring(
    query: str,
    category_id: Optional[str] = None,
    days_back: int = 30,
    db: Session = Depends(get_db)
):
    """Monitor prices for a product over time"""
    try:
        service = PriceMonitoringService(db)
        results = await service.monitor_product_prices(query, category_id, days_back)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/competitor-prices")
async def competitor_prices(
    item_id: str,
    competitor_sellers: str,  # Comma-separated list
    db: Session = Depends(get_db)
):
    """Monitor competitor prices for a specific item"""
    try:
        service = PriceMonitoringService(db)
        sellers = competitor_sellers.split(",")
        results = await service.monitor_competitor_prices(item_id, sellers)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/seller-analytics")
async def seller_analytics(
    seller_username: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get comprehensive seller analytics dashboard"""
    try:
        service = SellerAnalyticsService(db)
        results = await service.get_seller_dashboard(seller_username)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/inventory-tracking")
async def inventory_tracking(
    seller_username: str,
    db: Session = Depends(get_db)
):
    """Track inventory levels over time"""
    try:
        service = SellerAnalyticsService(db)
        results = await service.track_inventory_levels(seller_username)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/marketplace-research")
async def marketplace_research(
    category_id: str,
    days_back: int = 30,
    db: Session = Depends(get_db)
):
    """Research a specific category for market insights"""
    try:
        service = MarketplaceResearchService(db)
        results = await service.research_category(category_id, days_back)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/trending-products")
async def trending_products(
    limit: int = 100,
    category_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get trending products across categories"""
    try:
        service = MarketplaceResearchService(db)
        results = await service.get_trending_products(limit, category_id)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/market-competition")
async def market_competition(
    query: str,
    category_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Analyze competition for a product or category"""
    try:
        service = MarketplaceResearchService(db)
        results = await service.analyze_market_competition(query, category_id)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/repricing-analysis")
async def repricing_analysis(
    query: str,
    own_sku: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Analyze competitor pricing for repricing"""
    try:
        service = RepricingService(db)
        results = await service.analyze_competitor_pricing(query, own_sku)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/auto-reprice")
async def auto_reprice(
    item_id: str,
    target_price: float,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """Automatically reprice an item"""
    try:
        service = RepricingService(db)
        results = await service.auto_reprice_item(item_id, target_price, min_price, max_price)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/apply-repricing-rules")
async def apply_repricing_rules(
    sku: str,
    query: str,
    db: Session = Depends(get_db)
):
    """Apply repricing rules to a product"""
    try:
        service = RepricingService(db)
        results = await service.apply_repricing_rules(sku, query)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Walmart API endpoints
@app.get("/api/walmart/taxonomy")
async def get_walmart_taxonomy():
    """Test Walmart API credentials by fetching taxonomy"""
    try:
        headers = await walmart_client.get_headers()
        async with httpx.AsyncClient() as client:
            url = f"{walmart_client.api_base}/service/affil/product/v2/taxonomy"
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/walmart/search")
async def search_walmart(query: str, limit: int = 20, category: str = None):
    """Search for products on Walmart"""
    try:
        results = await walmart_client.search_products(query, limit, category)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/walmart/item/{item_id}")
async def get_walmart_item(item_id: str):
    """Get detailed information about a Walmart product"""
    try:
        results = await walmart_client.get_product_details(item_id)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/walmart/deals")
async def get_walmart_deals(category: str = None, limit: int = 20):
    """Get current deals from Walmart"""
    try:
        results = await walmart_client.get_deals(category, limit)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
