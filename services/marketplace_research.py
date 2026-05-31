import os
import sys
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api import BrowseAPIClient, FindingAPIClient, MarketplaceInsightsClient
from models import TrendingItem, MarketTrend


class MarketplaceResearchService:
    """Service for marketplace research and trend analysis"""
    
    def __init__(self, db: Session):
        self.db = db
        self.browse_client = BrowseAPIClient()
        self.finding_client = FindingAPIClient()
        self.marketplace_client = MarketplaceInsightsClient()
    
    async def research_category(
        self,
        category_id: str,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """Research a specific category for market insights"""
        is_numeric_category = category_id.isdigit()
        
        try:
            if is_numeric_category:
                popular = await self.finding_client.find_items_by_category(
                    category_id=category_id,
                    limit=100,
                    sort_order="BestMatch"
                )
            else:
                popular = await self.browse_client.search_items(
                    query=category_id,
                    limit=100,
                    use_cache=False
                )
        except Exception as e:
            print(f"Error getting popular items: {e}")
            popular = {}
        
        try:
            if is_numeric_category:
                trending = await self.browse_client.get_trending_items(
                    category_id=category_id,
                    limit=50
                )
            else:
                trending = await self.browse_client.search_items(
                    query=category_id,
                    limit=50,
                    use_cache=False
                )
        except Exception as e:
            print(f"Error getting trending items: {e}")
            trending = {}
        
        # Store trending items in database
        if trending:
            items = trending.get("itemSummaries", [])
            for item in items:
                item_id = item.get("itemId")
                trending_item = self.db.query(TrendingItem).filter(
                    TrendingItem.item_id == item_id
                ).first()
                if trending_item:
                    trending_item.title = item.get("title")
                    trending_item.price = float(item.get("price", {}).get("value", 0))
                    trending_item.category_id = category_id
                    trending_item.is_active = True
                else:
                    trending_item = TrendingItem(
                        item_id=item_id,
                        title=item.get("title"),
                        price=float(item.get("price", {}).get("value", 0)),
                        category_id=category_id,
                        is_active=True
                    )
                    self.db.add(trending_item)
            self.db.commit()
        
        # Get market trends from Marketplace Insights
        market_trends = None
        if is_numeric_category:
            try:
                market_trends = await self.marketplace_client.get_market_trends(
                    category_id=category_id,
                    start_date="2024-01-01",
                    end_date="2024-12-31"
                )
                
                if market_trends:
                    db_trend = MarketTrend(
                        category_id=category_id,
                        trend_data=market_trends
                    )
                    self.db.add(db_trend)
                    self.db.commit()
            except Exception as e:
                print(f"Error getting market trends: {e}")
        
        category_performance = None
        if is_numeric_category:
            try:
                category_performance = await self.marketplace_client.get_category_performance(
                    category_id=category_id
                )
            except Exception as e:
                print(f"Error getting category performance: {e}")
        
        return {
            "category_id": category_id,
            "popular_items": popular,
            "trending_items": trending,
            "market_trends": market_trends,
            "category_performance": category_performance,
            "analysis": self._analyze_category_data(trending, popular)
        }
    
    async def get_trending_products(
        self,
        limit: int = 100,
        category_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get trending products across categories"""
        
        trending_results = await self.browse_client.get_trending_items(
            category_id=category_id,
            limit=limit
        )
        
        items = trending_results.get("itemSummaries", [])
        
        # Analyze trending patterns
        categories = {}
        price_ranges = {"under_10": 0, "10_50": 0, "50_100": 0, "100_500": 0, "over_500": 0}
        
        for item in items:
            # Category analysis
            cat = item.get("categoryId", "unknown")
            categories[cat] = categories.get(cat, 0) + 1
            
            # Price range analysis
            price = float(item.get("price", {}).get("value", 0))
            if price < 10:
                price_ranges["under_10"] += 1
            elif price < 50:
                price_ranges["10_50"] += 1
            elif price < 100:
                price_ranges["50_100"] += 1
            elif price < 500:
                price_ranges["100_500"] += 1
            else:
                price_ranges["over_500"] += 1
        
        return {
            "total_items": len(items),
            "items": items[:50],
            "category_distribution": categories,
            "price_distribution": price_ranges,
            "top_categories": sorted(categories.items(), key=lambda x: x[1], reverse=True)[:10]
        }
    
    async def analyze_market_competition(
        self,
        query: str,
        category_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze competition for a product or category"""
        
        # Get search results
        search_results = await self.browse_client.search_items(
            query=query,
            limit=100,
            use_cache=False
        )
        
        items = search_results.get("itemSummaries", [])
        
        # Analyze sellers
        sellers = {}
        for item in items:
            seller = item.get("seller", {}).get("username", "unknown")
            if seller not in sellers:
                sellers[seller] = {
                    "count": 0,
                    "total_price": 0,
                    "avg_feedback": 0
                }
            sellers[seller]["count"] += 1
            sellers[seller]["total_price"] += float(item.get("price", {}).get("value", 0))
            sellers[seller]["avg_feedback"] = item.get("seller", {}).get("feedbackPercentage", 0)
        
        # Calculate averages
        for seller in sellers:
            sellers[seller]["avg_price"] = sellers[seller]["total_price"] / sellers[seller]["count"]
        
        # Sort by listing count
        top_sellers = sorted(sellers.items(), key=lambda x: x[1]["count"], reverse=True)[:20]
        
        return {
            "query": query,
            "total_listings": len(items),
            "total_sellers": len(sellers),
            "top_sellers": [
                {
                    "username": seller,
                    "listings": data["count"],
                    "avg_price": data["avg_price"],
                    "feedback_percentage": data["avg_feedback"]
                }
                for seller, data in top_sellers
            ],
            "competition_level": "high" if len(sellers) > 50 else "medium" if len(sellers) > 20 else "low"
        }
    
    def _analyze_category_data(self, trending: Dict, popular: Dict) -> Dict:
        """Analyze category data for insights"""
        trending_items = trending.get("itemSummaries", []) if trending else []
        popular_items = []
        if popular:
            if "itemSummaries" in popular:
                popular_items = popular.get("itemSummaries", [])
            else:
                popular_items = popular.get("findItemsByCategoryResponse", [{}])[0].get("searchResult", [{}])[0].get("item", [])
        
        if isinstance(popular_items, list) and len(popular_items) > 0 and isinstance(popular_items[0], dict):
            popular_count = len(popular_items)
        else:
            popular_count = 0
        
        return {
            "trending_count": len(trending_items),
            "popular_count": popular_count,
            "overlap": len(set(item.get("itemId") for item in trending_items) & set(item.get("itemId", "") for item in popular_items if isinstance(item, dict)))
        }
