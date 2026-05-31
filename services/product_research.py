import os
import sys
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api import BrowseAPIClient, FindingAPIClient, MarketplaceInsightsClient
from models import ProductSearch, ItemDetails, PriceHistory
from utils.cache import cache


class ProductResearchService:
    """Service for product research combining multiple APIs"""
    
    def __init__(self, db: Session):
        self.db = db
        self.browse_client = BrowseAPIClient()
        self.finding_client = FindingAPIClient()
        self.marketplace_client = MarketplaceInsightsClient()
    
    async def research_product(self, query: str, category_id: Optional[str] = None, include_price_history: bool = True, skip_commit: bool = False) -> Dict[str, Any]:
        """Comprehensive product research using multiple APIs"""
        
        # Get current listings from Browse API
        current_results = await self.browse_client.search_items(query, limit=50)
        
        # Get item details for top results
        items = current_results.get("itemSummaries", [])
        detailed_items = []
        
        for item in items[:10]:
            try:
                details = await self.browse_client.get_item_details(item["itemId"])
                detailed_items.append(details)
                
                # Store in database
                db_item = self.db.query(ItemDetails).filter(
                    ItemDetails.item_id == item["itemId"]
                ).first()
                if db_item:
                    db_item.title = item.get("title")
                    db_item.price = float(item.get("price", {}).get("value", 0))
                    db_item.condition = item.get("condition")
                    db_item.seller_username = item.get("seller", {}).get("username")
                    db_item.seller_feedback_score = item.get("seller", {}).get("feedbackScore")
                    db_item.details = details
                else:
                    db_item = ItemDetails(
                        item_id=item["itemId"],
                        title=item.get("title"),
                        price=float(item.get("price", {}).get("value", 0)),
                        condition=item.get("condition"),
                        seller_username=item.get("seller", {}).get("username"),
                        seller_feedback_score=item.get("seller", {}).get("feedbackScore"),
                        details=details
                    )
                    self.db.add(db_item)
            except Exception as e:
                print(f"Error getting details for item {item['itemId']}: {e}")
        
        if not skip_commit:
            self.db.commit()
        
        # Get completed items for price history
        price_history = None
        if include_price_history:
            if category_id and category_id.isdigit():
                try:
                    completed = await self.finding_client.find_completed_items(query, category_id=category_id, limit=100)
                    price_history = self._process_price_history(completed)
                except Exception as e:
                    print(f"Error getting price history: {e}")
                    price_history = self._process_current_price_history(items)
            else:
                price_history = self._process_current_price_history(items)
            
            if not skip_commit:
                # Store price history in database
                for record in price_history:
                    db_record = PriceHistory(
                        item_id=record.get("item_id"),
                        title=record.get("title"),
                        price=record.get("price"),
                        condition=record.get("condition"),
                        seller_username=record.get("seller"),
                        is_completed=record.get("is_completed", False)
                    )
                    self.db.add(db_record)
                self.db.commit()
        
        # Get marketplace trends (if available)
        market_trends = None
        if category_id:
            try:
                market_trends = await self.marketplace_client.get_market_trends(
                    category_id,
                    start_date="2024-01-01",
                    end_date="2024-12-31"
                )
            except Exception as e:
                print(f"Error getting market trends: {e}")
        
        return {
            "query": query,
            "current_listings": {
                "total": len(items),
                "items": items[:20],
                "detailed_items": detailed_items
            },
            "price_history": price_history,
            "market_trends": market_trends,
            "analysis": self._analyze_results(items, price_history)
        }
    
    def _process_price_history(self, completed_data: Dict) -> List[Dict]:
        """Process completed items data for price history"""
        processed = []
        
        try:
            items = completed_data.get("findCompletedItemsResponse", [{}])[0].get("searchResult", [{}])[0].get("item", [])
            
            for item in items:
                if isinstance(item, dict):
                    processed.append({
                        "item_id": item.get("itemId", [{}])[0].get("__value__") if isinstance(item.get("itemId"), list) else item.get("itemId"),
                        "title": item.get("title", [{}])[0].get("__value__") if isinstance(item.get("title"), list) else item.get("title"),
                        "price": float(item.get("sellingStatus", [{}])[0].get("currentPrice", [{}])[0].get("__value__", 0)) if isinstance(item.get("sellingStatus"), list) else 0,
                        "condition": item.get("condition", [{}])[0].get("conditionDisplayName", [{}])[0].get("__value__") if isinstance(item.get("condition"), list) else item.get("condition"),
                        "seller": item.get("seller", [{}])[0].get("userID", [{}])[0].get("__value__") if isinstance(item.get("seller"), list) else item.get("seller", {}).get("userID")
                    })
        except Exception as e:
            print(f"Error processing price history: {e}")
        
        return processed
    
    def _process_current_price_history(self, current_items: List[Dict]) -> List[Dict]:
        processed = []
        
        for item in current_items:
            if isinstance(item, dict):
                processed.append({
                    "item_id": item.get("itemId"),
                    "title": item.get("title"),
                    "price": float(item.get("price", {}).get("value", 0)),
                    "condition": item.get("condition"),
                    "seller": item.get("seller", {}).get("username"),
                    "is_completed": False
                })
        
        return processed
    
    def _analyze_results(self, current_items: List, price_history: List) -> Dict:
        """Analyze research results"""
        if not current_items:
            return {}
        
        prices = [float(item.get("price", {}).get("value", 0)) for item in current_items if item.get("price")]
        
        analysis = {
            "price_range": {
                "min": min(prices) if prices else 0,
                "max": max(prices) if prices else 0,
                "average": sum(prices) / len(prices) if prices else 0
            },
            "total_listings": len(current_items),
            "conditions": {}
        }
        
        # Count conditions
        for item in current_items:
            condition = item.get("condition", "Unknown")
            analysis["conditions"][condition] = analysis["conditions"].get(condition, 0) + 1
        
        return analysis
