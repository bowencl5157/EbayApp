import pytest
from datetime import datetime
from models import (
    ProductSearch, ItemDetails, PriceHistory, KeywordAnalysis,
    TrendingItem, SellerPerformance, MarketTrend, CompetitorPrice,
    InventorySnapshot, APIUsage
)


@pytest.mark.database
class TestDatabaseModels:
    """Test cases for database models"""
    
    def test_product_search_model(self, db_session):
        """Test ProductSearch model"""
        search = ProductSearch(
            query="test query",
            category_id="12345",
            results={"items": []},
            result_count=0
        )
        db_session.add(search)
        db_session.commit()
        
        retrieved = db_session.query(ProductSearch).first()
        assert retrieved.query == "test query"
        assert retrieved.category_id == "12345"
        assert retrieved.result_count == 0
    
    def test_item_details_model(self, db_session):
        """Test ItemDetails model"""
        item = ItemDetails(
            item_id="v1|123456789|0",
            title="Test Product",
            price=29.99,
            condition="New",
            seller_username="testseller",
            seller_feedback_score=1000,
            details={"description": "Test description"}
        )
        db_session.add(item)
        db_session.commit()
        
        retrieved = db_session.query(ItemDetails).first()
        assert retrieved.item_id == "v1|123456789|0"
        assert retrieved.title == "Test Product"
        assert retrieved.price == 29.99
    
    def test_price_history_model(self, db_session):
        """Test PriceHistory model"""
        history = PriceHistory(
            item_id="v1|123456789|0",
            title="Test Product",
            price=25.00,
            currency="USD",
            condition="Used",
            seller_username="seller1",
            listing_type="fixed_price",
            is_completed=True
        )
        db_session.add(history)
        db_session.commit()
        
        retrieved = db_session.query(PriceHistory).first()
        assert retrieved.item_id == "v1|123456789|0"
        assert retrieved.price == 25.00
        assert retrieved.is_completed == True
    
    def test_keyword_analysis_model(self, db_session):
        """Test KeywordAnalysis model"""
        analysis = KeywordAnalysis(
            query="test query",
            category_id="12345",
            short_tail_keywords=[{"keyword": "test", "count": 10}],
            long_tail_keywords=[{"keyword": "test product", "count": 5}],
            total_listings_analyzed=100
        )
        db_session.add(analysis)
        db_session.commit()
        
        retrieved = db_session.query(KeywordAnalysis).first()
        assert retrieved.query == "test query"
        assert retrieved.total_listings_analyzed == 100
    
    def test_trending_item_model(self, db_session):
        """Test TrendingItem model"""
        trending = TrendingItem(
            item_id="v1|123456789|0",
            title="Trending Product",
            price=49.99,
            category_id="12345",
            trend_score=8.5,
            is_active=True
        )
        db_session.add(trending)
        db_session.commit()
        
        retrieved = db_session.query(TrendingItem).first()
        assert retrieved.item_id == "v1|123456789|0"
        assert retrieved.trend_score == 8.5
        assert retrieved.is_active == True
    
    def test_seller_performance_model(self, db_session):
        """Test SellerPerformance model"""
        performance = SellerPerformance(
            seller_username="testseller",
            feedback_score=1000,
            feedback_percentage=99.5,
            positive_feedback_count=950,
            neutral_feedback_count=30,
            negative_feedback_count=20,
            active_listings_count=50,
            total_listings_count=200
        )
        db_session.add(performance)
        db_session.commit()
        
        retrieved = db_session.query(SellerPerformance).first()
        assert retrieved.seller_username == "testseller"
        assert retrieved.feedback_score == 1000
        assert retrieved.active_listings_count == 50
    
    def test_market_trend_model(self, db_session):
        """Test MarketTrend model"""
        trend = MarketTrend(
            category_id="12345",
            category_name="Electronics",
            trend_data={"growth_rate": 15.5},
            price_distribution={"min": 10, "max": 100},
            seller_performance_benchmarks={"avg_feedback": 98.0}
        )
        db_session.add(trend)
        db_session.commit()
        
        retrieved = db_session.query(MarketTrend).first()
        assert retrieved.category_id == "12345"
        assert retrieved.category_name == "Electronics"
    
    def test_competitor_price_model(self, db_session):
        """Test CompetitorPrice model"""
        comp_price = CompetitorPrice(
            item_id="v1|123456789|0",
            competitor_item_id="v1|987654321|0",
            competitor_seller="competitor1",
            competitor_price=27.99,
            our_price=29.99,
            price_difference=2.00
        )
        db_session.add(comp_price)
        db_session.commit()
        
        retrieved = db_session.query(CompetitorPrice).first()
        assert retrieved.item_id == "v1|123456789|0"
        assert retrieved.competitor_price == 27.99
    
    def test_inventory_snapshot_model(self, db_session):
        """Test InventorySnapshot model"""
        snapshot = InventorySnapshot(
            seller_username="testseller",
            sku="TEST-SKU-123",
            title="Test Product",
            quantity=100,
            price=29.99,
            location="Warehouse A"
        )
        db_session.add(snapshot)
        db_session.commit()
        
        retrieved = db_session.query(InventorySnapshot).first()
        assert retrieved.seller_username == "testseller"
        assert retrieved.sku == "TEST-SKU-123"
        assert retrieved.quantity == 100
    
    def test_api_usage_model(self, db_session):
        """Test APIUsage model"""
        usage = APIUsage(
            api_name="browse",
            endpoint="search",
            call_count=100,
            date=datetime.utcnow()
        )
        db_session.add(usage)
        db_session.commit()
        
        retrieved = db_session.query(APIUsage).first()
        assert retrieved.api_name == "browse"
        assert retrieved.endpoint == "search"
        assert retrieved.call_count == 100
    
    def test_model_relationships(self, db_session):
        """Test model relationships and constraints"""
        # Create a price history entry
        history = PriceHistory(
            item_id="v1|123456789|0",
            title="Test Product",
            price=25.00,
            is_completed=True
        )
        db_session.add(history)
        db_session.commit()
        
        # Query by item_id
        results = db_session.query(PriceHistory).filter(
            PriceHistory.item_id == "v1|123456789|0"
        ).all()
        
        assert len(results) == 1
        assert results[0].item_id == "v1|123456789|0"
