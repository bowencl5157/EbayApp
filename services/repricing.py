import os
import sys
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api import BrowseAPIClient, InventoryAPIClient, TradingAPIClient, AccountAPIClient
from models import CompetitorPrice, InventorySnapshot


class RepricingService:
    """Service for automated repricing based on competitor analysis"""
    
    def __init__(self, db: Session):
        self.db = db
        self.browse_client = BrowseAPIClient()
        self.inventory_client = InventoryAPIClient()
        self.trading_client = TradingAPIClient()
        self.account_client = AccountAPIClient()
    
    async def analyze_competitor_pricing(
        self,
        query: str,
        own_sku: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze competitor pricing for a product"""
        
        # Get competitor listings
        search_results = await self.browse_client.search_items(
            query=query,
            limit=100,
            use_cache=False
        )
        
        items = search_results.get("itemSummaries", [])
        
        # Get own inventory price if SKU provided
        own_price = None
        if own_sku:
            try:
                inventory_item = await self.inventory_client.get_inventory_item(sku=own_sku)
                own_price = float(inventory_item.get("offers", [{}])[0].get("price", {}).get("value", 0)) if isinstance(inventory_item.get("offers"), list) else 0
            except Exception as e:
                print(f"Error getting own inventory: {e}")
        
        # Analyze competitor prices
        prices = [float(item.get("price", {}).get("value", 0)) for item in items if item.get("price")]
        
        if not prices:
            return {"error": "No price data available"}
        
        price_stats = {
            "min": min(prices),
            "max": max(prices),
            "average": sum(prices) / len(prices),
            "median": sorted(prices)[len(prices) // 2]
        }
        
        # Determine optimal price
        optimal_price = price_stats["average"] * 0.95  # 5% below average
        
        if own_price:
            price_difference = optimal_price - own_price
            recommendation = {
                "current_price": own_price,
                "optimal_price": optimal_price,
                "difference": price_difference,
                "action": "lower" if price_difference < -5 else "raise" if price_difference > 5 else "maintain"
            }
        else:
            recommendation = {
                "optimal_price": optimal_price,
                "action": "set_price"
            }
        
        # Store competitor prices in database
        for item in items[:20]:
            comp_price = CompetitorPrice(
                item_id=item.get("itemId"),
                competitor_seller=item.get("seller", {}).get("username"),
                competitor_price=float(item.get("price", {}).get("value", 0)),
                our_price=own_price,
                price_difference=own_price - float(item.get("price", {}).get("value", 0)) if own_price else None
            )
            self.db.add(comp_price)
        self.db.commit()
        
        return {
            "query": query,
            "competitors_analyzed": len(items),
            "price_statistics": price_stats,
            "recommendation": recommendation,
            "competitor_prices": [
                {
                    "seller": item.get("seller", {}).get("username"),
                    "price": float(item.get("price", {}).get("value", 0)),
                    "condition": item.get("condition")
                }
                for item in items[:10]
            ]
        }
    
    async def auto_reprice_item(
        self,
        item_id: str,
        target_price: float,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """Automatically reprice an item"""
        
        # Validate price against limits
        if min_price and target_price < min_price:
            target_price = min_price
        if max_price and target_price > max_price:
            target_price = max_price
        
        # Update listing via Trading API
        try:
            result = await self.trading_client.revise_item(
                item_id=item_id,
                price=target_price
            )
            success = True
        except Exception as e:
            print(f"Error repricing item: {e}")
            result = str(e)
            success = False
        
        return {
            "item_id": item_id,
            "target_price": target_price,
            "min_price": min_price,
            "max_price": max_price,
            "success": success,
            "result": result
        }
    
    async def get_repricing_rules(self) -> Dict[str, Any]:
        """Get current repricing rules (from database or config)"""
        
        # This would typically be stored in a database
        # For now, return default rules
        return {
            "rules": [
                {
                    "name": "beat_lowest",
                    "description": "Price 1% below lowest competitor",
                    "enabled": True,
                    "parameters": {
                        "percentage_below_lowest": 1
                    }
                },
                {
                    "name": "match_average",
                    "description": "Match average competitor price",
                    "enabled": True,
                    "parameters": {
                        "percentage_of_average": 100
                    }
                },
                {
                    "name": "minimum_margin",
                    "description": "Maintain minimum profit margin",
                    "enabled": True,
                    "parameters": {
                        "minimum_margin_percent": 15
                    }
                }
            ]
        }
    
    async def apply_repricing_rules(
        self,
        sku: str,
        query: str
    ) -> Dict[str, Any]:
        """Apply repricing rules to a product"""
        
        # Get competitor analysis
        analysis = await self.analyze_competitor_pricing(query, sku)
        
        if "error" in analysis:
            return analysis
        
        # Get repricing rules
        rules = await self.get_repricing_rules()
        
        # Apply rules
        current_price = analysis["recommendation"].get("current_price")
        optimal_price = analysis["recommendation"]["optimal_price"]
        
        # Apply minimum margin rule
        min_margin_rule = next((r for r in rules["rules"] if r["name"] == "minimum_margin" and r["enabled"]), None)
        if min_margin_rule:
            min_margin = min_margin_rule["parameters"]["minimum_margin_percent"]
            # Assuming cost is 70% of current price (would need real cost data)
            cost = current_price * 0.7 if current_price else 0
            min_price = cost * (1 + min_margin / 100)
            if optimal_price < min_price:
                optimal_price = min_price
        
        # Get inventory item ID from SKU
        try:
            inventory_item = await self.inventory_client.get_inventory_item(sku=sku)
            offers = inventory_item.get("offers", [])
            if offers and isinstance(offers, list):
                item_id = offers[0].get("offerId")
                
                # Apply repricing
                result = await self.auto_reprice_item(
                    item_id=item_id,
                    target_price=optimal_price
                )
                
                return {
                    "sku": sku,
                    "rules_applied": [r["name"] for r in rules["rules"] if r["enabled"]],
                    "analysis": analysis,
                    "repricing_result": result
                }
        except Exception as e:
            print(f"Error applying repricing: {e}")
        
        return {
            "sku": sku,
            "error": "Could not apply repricing",
            "analysis": analysis
        }
