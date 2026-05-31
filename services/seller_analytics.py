import os
import sys
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api import TradingAPIClient, AccountAPIClient, InventoryAPIClient
from models import SellerPerformance, InventorySnapshot


class SellerAnalyticsService:
    """Service for seller analytics and performance tracking"""
    
    def __init__(self, db: Session):
        self.db = db
        self.trading_client = TradingAPIClient()
        self.account_client = AccountAPIClient()
        self.inventory_client = InventoryAPIClient()
    
    async def get_seller_dashboard(self, seller_username: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive seller analytics dashboard"""
        
        # Get active listings from Trading API
        try:
            active_listings_xml = await self.trading_client.get_my_ebay_selling(
                active_list=True,
                sold_list=False
            )
            # Parse XML response (simplified)
            active_count = active_listings_xml.count("ActiveList") if active_listings_xml else 0
        except Exception as e:
            print(f"Error getting active listings: {e}")
            active_count = 0
        
        # Get sold items
        try:
            sold_listings_xml = await self.trading_client.get_my_ebay_selling(
                active_list=False,
                sold_list=True
            )
            sold_count = sold_listings_xml.count("SoldList") if sold_listings_xml else 0
        except Exception as e:
            print(f"Error getting sold listings: {e}")
            sold_count = 0
        
        # Get account information
        try:
            account_info = await self.account_client.get_account_status()
        except Exception as e:
            print(f"Error getting account info: {e}")
            account_info = {}
        
        # Get inventory
        try:
            inventory = await self.inventory_client.get_inventory_items(limit=100)
            inventory_items = inventory.get("inventoryItems", [])
        except Exception as e:
            print(f"Error getting inventory: {e}")
            inventory_items = []
        
        # Store performance snapshot in database
        performance = SellerPerformance(
            seller_username=seller_username or "self",
            active_listings_count=active_count,
            total_listings_count=active_count + sold_count,
            recorded_at=datetime.utcnow()
        )
        self.db.add(performance)
        self.db.commit()
        
        # Get historical performance
        historical = self.db.query(SellerPerformance).filter(
            SellerPerformance.seller_username == (seller_username or "self")
        ).order_by(SellerPerformance.recorded_at.desc()).limit(30).all()
        
        return {
            "seller_username": seller_username or "self",
            "current_performance": {
                "active_listings": active_count,
                "sold_items": sold_count,
                "total_inventory": len(inventory_items)
            },
            "account_status": account_info,
            "inventory_summary": {
                "total_items": len(inventory_items),
                "items": inventory_items[:10]
            },
            "historical_performance": [
                {
                    "date": h.recorded_at.isoformat(),
                    "active_listings": h.active_listings_count,
                    "total_listings": h.total_listings_count
                }
                for h in historical
            ],
            "trends": self._analyze_performance_trends(historical)
        }
    
    async def track_inventory_levels(self, seller_username: str) -> Dict[str, Any]:
        """Track inventory levels over time"""
        
        try:
            inventory = await self.inventory_client.get_inventory_items(limit=500)
            inventory_items = inventory.get("inventoryItems", [])
        except Exception as e:
            print(f"Error getting inventory: {e}")
            return {"error": str(e)}
        
        # Store inventory snapshot
        for item in inventory_items:
            snapshot = InventorySnapshot(
                seller_username=seller_username,
                sku=item.get("sku"),
                title=item.get("product", {}).get("title"),
                quantity=item.get("availability", {}).get("pickupAtLocationAvailability", [{}])[0].get("quantity") if isinstance(item.get("availability", {}).get("pickupAtLocationAvailability"), list) else 0,
                price=item.get("offers", [{}])[0].get("price", {}).get("value") if isinstance(item.get("offers"), list) else 0
            )
            self.db.add(snapshot)
        
        self.db.commit()
        
        # Get historical snapshots
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        historical = self.db.query(InventorySnapshot).filter(
            InventorySnapshot.seller_username == seller_username,
            InventorySnapshot.snapshot_date >= cutoff_date
        ).all()
        
        return {
            "seller_username": seller_username,
            "current_inventory": {
                "total_items": len(inventory_items),
                "items": inventory_items[:20]
            },
            "historical_snapshots": len(historical),
            "inventory_changes": self._analyze_inventory_changes(historical)
        }
    
    def _analyze_performance_trends(self, historical: List) -> Dict:
        """Analyze seller performance trends"""
        if len(historical) < 2:
            return {"trend": "insufficient_data"}
        
        recent = historical[0]
        older = historical[-1]
        
        active_change = recent.active_listings_count - older.active_listings_count
        
        if active_change > 10:
            trend = "growing"
        elif active_change < -10:
            trend = "declining"
        else:
            trend = "stable"
        
        return {
            "trend": trend,
            "active_listings_change": active_change,
            "recent_active": recent.active_listings_count,
            "older_active": older.active_listings_count
        }
    
    def _analyze_inventory_changes(self, historical: List) -> Dict:
        """Analyze inventory level changes"""
        if len(historical) < 2:
            return {"trend": "insufficient_data"}
        
        # Group by SKU
        sku_changes = {}
        for snapshot in historical:
            sku = snapshot.sku
            if sku not in sku_changes:
                sku_changes[sku] = []
            sku_changes[sku].append(snapshot.quantity)
        
        # Calculate changes
        changes = []
        for sku, quantities in sku_changes.items():
            if len(quantities) >= 2:
                change = quantities[-1] - quantities[0]
                changes.append({
                    "sku": sku,
                    "quantity_change": change,
                    "current_quantity": quantities[-1]
                })
        
        return {
            "total_skus_tracked": len(sku_changes),
            "changes": changes[:10]
        }
