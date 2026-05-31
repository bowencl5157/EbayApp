import os
import sys
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api import BrowseAPIClient, FindingAPIClient, InventoryAPIClient
from models import PriceHistory, CompetitorPrice
from utils.cache import cache


class PriceMonitoringService:
    """Service for monitoring prices across products and competitors"""
    
    def __init__(self, db: Session):
        self.db = db
        self.browse_client = BrowseAPIClient()
        self.finding_client = FindingAPIClient()
        self.inventory_client = InventoryAPIClient()
    
    async def monitor_product_prices(
        self,
        query: str,
        category_id: Optional[str] = None,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """Monitor prices for a product over time"""
        
        # Get current prices
        current_results = await self.browse_client.search_items(query, limit=100)
        current_items = current_results.get("itemSummaries", [])
        
        # Get historical prices from database
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        historical = self.db.query(PriceHistory).filter(
            PriceHistory.recorded_at >= cutoff_date
        ).all()
        
        # Store current prices in database
        for item in current_items:
            price_record = PriceHistory(
                item_id=item.get("itemId"),
                title=item.get("title"),
                price=float(item.get("price", {}).get("value", 0)),
                condition=item.get("condition"),
                seller_username=item.get("seller", {}).get("username"),
                is_completed=False
            )
            self.db.merge(price_record)
        self.db.commit()
        
        # Analyze price trends
        price_analysis = self._analyze_price_trends(historical, current_items)
        
        return {
            "query": query,
            "current_prices": {
                "count": len(current_items),
                "min_price": min([float(i.get("price", {}).get("value", 0)) for i in current_items if i.get("price")]) if current_items else 0,
                "max_price": max([float(i.get("price", {}).get("value", 0)) for i in current_items if i.get("price")]) if current_items else 0,
                "avg_price": sum([float(i.get("price", {}).get("value", 0)) for i in current_items if i.get("price")]) / len([i for i in current_items if i.get("price")]) if current_items else 0
            },
            "current_items": current_items[:20],
            "historical_data": {
                "records_analyzed": len(historical),
                "date_range": f"{days_back} days"
            },
            "trends": price_analysis
        }
    
    async def monitor_competitor_prices(
        self,
        item_id: str,
        competitor_sellers: List[str]
    ) -> Dict[str, Any]:
        """Monitor competitor prices for a specific item"""
        
        # Get competitor listings
        competitor_prices = []
        
        for seller in competitor_sellers:
            try:
                results = await self.finding_client.find_items_advanced(
                    query=item_id,
                    seller=seller,
                    limit=50
                )
                items = results.get("findItemsAdvancedResponse", [{}])[0].get("searchResult", [{}])[0].get("item", [])
                
                for item in items:
                    if isinstance(item, dict):
                        competitor_prices.append({
                            "seller": seller,
                            "item_id": item.get("itemId"),
                            "price": float(item.get("sellingStatus", [{}])[0].get("currentPrice", [{}])[0].get("__value__", 0)) if isinstance(item.get("sellingStatus"), list) else 0,
                            "title": item.get("title")
                        })
            except Exception as e:
                print(f"Error getting competitor {seller} prices: {e}")
        
        # Store in database
        for cp in competitor_prices:
            db_record = CompetitorPrice(
                item_id=item_id,
                competitor_seller=cp["seller"],
                competitor_item_id=cp["item_id"],
                competitor_price=cp["price"]
            )
            self.db.add(db_record)
        self.db.commit()
        
        return {
            "item_id": item_id,
            "competitors_monitored": len(competitor_sellers),
            "competitor_prices": competitor_prices,
            "price_comparison": self._compare_prices(competitor_prices)
        }
    
    def _analyze_price_trends(self, historical: List, current: List) -> Dict:
        """Analyze price trends from historical data"""
        if not historical:
            return {"trend": "insufficient_data"}
        
        # Group by date
        price_by_date = {}
        for record in historical:
            date = record.recorded_at.date()
            if date not in price_by_date:
                price_by_date[date] = []
            price_by_date[date].append(record.price)
        
        # Calculate daily averages
        daily_avg = {date: sum(prices)/len(prices) for date, prices in price_by_date.items()}
        
        # Determine trend
        if len(daily_avg) < 2:
            return {"trend": "insufficient_data"}
        
        sorted_dates = sorted(daily_avg.keys())
        recent_avg = daily_avg[sorted_dates[-1]]
        older_avg = daily_avg[sorted_dates[0]]
        
        if recent_avg > older_avg * 1.05:
            trend = "increasing"
        elif recent_avg < older_avg * 0.95:
            trend = "decreasing"
        else:
            trend = "stable"
        
        return {
            "trend": trend,
            "price_change_percent": ((recent_avg - older_avg) / older_avg) * 100 if older_avg > 0 else 0,
            "recent_average": recent_avg,
            "older_average": older_avg
        }
    
    def _compare_prices(self, competitor_prices: List) -> Dict:
        """Compare competitor prices"""
        if not competitor_prices:
            return {}
        
        prices = [cp["price"] for cp in competitor_prices]
        
        return {
            "lowest_price": min(prices),
            "highest_price": max(prices),
            "average_price": sum(prices) / len(prices),
            "price_range": max(prices) - min(prices)
        }
