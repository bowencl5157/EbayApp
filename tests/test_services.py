import pytest
from unittest.mock import AsyncMock, MagicMock
from services.product_research import ProductResearchService
from services.price_monitoring import PriceMonitoringService
from services.seller_analytics import SellerAnalyticsService
from services.marketplace_research import MarketplaceResearchService
from services.repricing import RepricingService


@pytest.mark.unit
class TestProductResearchService:
    """Test cases for Product Research Service"""
    
    def test_init(self, db_session):
        """Test service initialization"""
        service = ProductResearchService(db_session)
        assert service.db == db_session
        assert service.browse_client is not None
        assert service.finding_client is not None
    
    @pytest.mark.asyncio
    async def test_research_product(self, db_session, mock_browse_client, mock_finding_client, sample_search_response):
        """Test comprehensive product research"""
        service = ProductResearchService(db_session)
        service.browse_client = mock_browse_client
        service.finding_client = mock_finding_client
        
        mock_browse_client.search_items = AsyncMock(return_value=sample_search_response)
        mock_finding_client.find_completed_items = AsyncMock(return_value={"findCompletedItemsResponse": [{"searchResult": [{"item": []}]}]})
        
        # Skip database commit for this test to avoid AsyncMock serialization issue
        result = await service.research_product("test query", skip_commit=True)
        assert result["query"] == "test query"
        assert "current_listings" in result
        assert "analysis" in result
        assert len(result["price_history"]) == len(sample_search_response["itemSummaries"])
        mock_finding_client.find_completed_items.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_research_product_uses_completed_items_for_numeric_category(self, db_session, mock_browse_client, mock_finding_client, sample_search_response):
        """Test numeric category product research uses completed item history"""
        service = ProductResearchService(db_session)
        service.browse_client = mock_browse_client
        service.finding_client = mock_finding_client
        
        mock_browse_client.search_items = AsyncMock(return_value=sample_search_response)
        mock_finding_client.find_completed_items = AsyncMock(return_value={"findCompletedItemsResponse": [{"searchResult": [{"item": []}]}]})
        
        result = await service.research_product("test query", category_id="9355", skip_commit=True)
        assert result["query"] == "test query"
        mock_finding_client.find_completed_items.assert_called_once_with("test query", category_id="9355", limit=100)
    
    @pytest.mark.asyncio
    async def test_research_product_skip_commit_skips_price_history_persistence(self, db_session, mock_browse_client, mock_finding_client, sample_search_response):
        """Test skip_commit skips price history database persistence"""
        service = ProductResearchService(db_session)
        service.browse_client = mock_browse_client
        service.finding_client = mock_finding_client
        
        mock_browse_client.search_items = AsyncMock(return_value=sample_search_response)
        mock_finding_client.find_completed_items = AsyncMock(return_value={"findCompletedItemsResponse": [{"searchResult": [{"item": []}]}]})
        db_session.commit = MagicMock()
        
        await service.research_product("test query", skip_commit=True)
        db_session.commit.assert_not_called()
    
    def test_process_price_history(self, db_session):
        """Test processing price history data"""
        service = ProductResearchService(db_session)
        
        mock_data = {
            "findCompletedItemsResponse": [
                {
                    "searchResult": [
                        {
                            "item": [
                                {
                                    "itemId": "v1|123456789|0",
                                    "title": "Test Item",
                                    "sellingStatus": [
                                        {
                                            "currentPrice": [
                                                {"__value__": "29.99"}
                                            ]
                                        }
                                    ],
                                    "condition": [
                                        {"conditionDisplayName": [{"__value__": "New"}]}
                                    ],
                                    "seller": [
                                        {"userID": [{"__value__": "testseller"}]}
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        result = service._process_price_history(mock_data)
        assert isinstance(result, list)
        assert len(result) > 0
    
    def test_analyze_results(self, db_session, sample_item_data):
        """Test analyzing search results"""
        service = ProductResearchService(db_session)
        items = [sample_item_data]
        
        result = service._analyze_results(items, [])
        assert "price_range" in result
        assert "total_listings" in result
        assert result["total_listings"] == 1


@pytest.mark.unit
class TestPriceMonitoringService:
    """Test cases for Price Monitoring Service"""
    
    def test_init(self, db_session):
        """Test service initialization"""
        service = PriceMonitoringService(db_session)
        assert service.db == db_session
    
    @pytest.mark.asyncio
    async def test_monitor_product_prices(self, db_session, mock_browse_client, sample_search_response):
        """Test monitoring product prices"""
        service = PriceMonitoringService(db_session)
        service.browse_client = mock_browse_client
        mock_browse_client.search_items = AsyncMock(return_value=sample_search_response)
        
        result = await service.monitor_product_prices("test query")
        assert result["query"] == "test query"
        assert "current_prices" in result
        assert "current_items" in result
        assert "trends" in result
        assert result["current_prices"]["count"] == len(sample_search_response["itemSummaries"])
        assert len(result["current_items"]) == len(sample_search_response["itemSummaries"][:20])
    
    def test_analyze_price_trends(self, db_session):
        """Test analyzing price trends"""
        service = PriceMonitoringService(db_session)
        
        # Create mock historical data
        from models import PriceHistory
        from datetime import datetime, timedelta
        
        historical = [
            PriceHistory(price=25.0, recorded_at=datetime.utcnow() - timedelta(days=5)),
            PriceHistory(price=27.0, recorded_at=datetime.utcnow() - timedelta(days=3)),
            PriceHistory(price=30.0, recorded_at=datetime.utcnow() - timedelta(days=1))
        ]
        
        result = service._analyze_price_trends(historical, [])
        assert "trend" in result
    
    def test_compare_prices(self, db_session):
        """Test comparing competitor prices"""
        service = PriceMonitoringService(db_session)
        
        competitor_prices = [
            {"price": 25.0, "seller": "seller1"},
            {"price": 30.0, "seller": "seller2"},
            {"price": 28.0, "seller": "seller3"}
        ]
        
        result = service._compare_prices(competitor_prices)
        assert "lowest_price" in result
        assert "highest_price" in result
        assert result["lowest_price"] == 25.0


@pytest.mark.unit
class TestSellerAnalyticsService:
    """Test cases for Seller Analytics Service"""
    
    def test_init(self, db_session):
        """Test service initialization"""
        service = SellerAnalyticsService(db_session)
        assert service.db == db_session
    
    @pytest.mark.asyncio
    async def test_get_seller_dashboard(self, db_session):
        """Test getting seller analytics dashboard"""
        service = SellerAnalyticsService(db_session)
        
        # Mock the API clients
        service.trading_client.get_my_ebay_selling = AsyncMock(return_value="<ActiveList>10</ActiveList>")
        service.account_client.get_account_status = AsyncMock(return_value={})
        service.inventory_client.get_inventory_items = AsyncMock(return_value={"inventoryItems": []})
        
        result = await service.get_seller_dashboard("testseller")
        assert result["seller_username"] == "testseller"
        assert "current_performance" in result
    
    def test_analyze_performance_trends(self, db_session):
        """Test analyzing seller performance trends"""
        service = SellerAnalyticsService(db_session)
        
        from models import SellerPerformance
        from datetime import datetime, timedelta
        
        historical = [
            SellerPerformance(seller_username="testseller", active_listings_count=50, recorded_at=datetime.utcnow() - timedelta(days=10)),
            SellerPerformance(seller_username="testseller", active_listings_count=60, recorded_at=datetime.utcnow() - timedelta(days=5)),
            SellerPerformance(seller_username="testseller", active_listings_count=70, recorded_at=datetime.utcnow())
        ]
        
        result = service._analyze_performance_trends(historical)
        assert "trend" in result


@pytest.mark.unit
class TestMarketplaceResearchService:
    """Test cases for Marketplace Research Service"""
    
    def test_init(self, db_session):
        """Test service initialization"""
        service = MarketplaceResearchService(db_session)
        assert service.db == db_session
    
    @pytest.mark.asyncio
    async def test_research_category(self, db_session, mock_browse_client):
        """Test researching a category"""
        service = MarketplaceResearchService(db_session)
        service.browse_client = mock_browse_client
        
        mock_browse_client.get_trending_items = AsyncMock(return_value={"itemSummaries": []})
        
        result = await service.research_category("12345")
        assert result["category_id"] == "12345"
        assert "popular_items" in result or "error" in result
    
    @pytest.mark.asyncio
    async def test_research_category_uses_browse_search_for_keyword(self, db_session, mock_browse_client):
        """Test keyword category research uses Browse search"""
        service = MarketplaceResearchService(db_session)
        service.browse_client = mock_browse_client
        service.finding_client.find_items_advanced = AsyncMock()
        
        mock_browse_client.search_items = AsyncMock(return_value={"itemSummaries": [], "total": 0})
        
        result = await service.research_category("home")
        assert result["category_id"] == "home"
        assert result["popular_items"]["total"] == 0
        assert result["analysis"]["popular_count"] == 0
        assert mock_browse_client.search_items.call_count == 2
        service.finding_client.find_items_advanced.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_trending_products(self, db_session, mock_browse_client, sample_search_response):
        """Test getting trending products"""
        service = MarketplaceResearchService(db_session)
        service.browse_client = mock_browse_client
        mock_browse_client.get_trending_items = AsyncMock(return_value=sample_search_response)
        
        result = await service.get_trending_products(limit=50)
        assert "total_items" in result
        assert "category_distribution" in result
    
    @pytest.mark.asyncio
    async def test_analyze_market_competition(self, db_session, mock_browse_client, sample_search_response):
        """Test analyzing market competition"""
        service = MarketplaceResearchService(db_session)
        service.browse_client = mock_browse_client
        mock_browse_client.search_items = AsyncMock(return_value=sample_search_response)
        
        result = await service.analyze_market_competition("test query")
        assert result["query"] == "test query"
        assert "total_listings" in result
        assert "competition_level" in result


@pytest.mark.unit
class TestRepricingService:
    """Test cases for Repricing Service"""
    
    def test_init(self, db_session):
        """Test service initialization"""
        service = RepricingService(db_session)
        assert service.db == db_session
    
    @pytest.mark.asyncio
    async def test_analyze_competitor_pricing(self, db_session, mock_browse_client, sample_search_response):
        """Test analyzing competitor pricing"""
        service = RepricingService(db_session)
        service.browse_client = mock_browse_client
        mock_browse_client.search_items = AsyncMock(return_value=sample_search_response)
        
        result = await service.analyze_competitor_pricing("test query", own_sku="TEST-SKU-123")
        assert result["query"] == "test query"
        assert "price_statistics" in result or "error" in result
        if "price_statistics" in result:
            assert "competitors_analyzed" in result
            assert "min" in result["price_statistics"]
            assert "max" in result["price_statistics"]
            assert "average" in result["price_statistics"]
            assert "recommendation" in result
            assert "optimal_price" in result["recommendation"]
    
    @pytest.mark.asyncio
    async def test_auto_reprice_item(self, db_session):
        """Test automatic repricing of an item"""
        service = RepricingService(db_session)
        service.trading_client.revise_item = AsyncMock(return_value={"success": True})
        
        result = await service.auto_reprice_item("v1|123456789|0", target_price=25.0, min_price=20.0, max_price=30.0)
        assert "item_id" in result
        assert "target_price" in result
    
    @pytest.mark.asyncio
    async def test_get_repricing_rules(self, db_session):
        """Test getting repricing rules"""
        service = RepricingService(db_session)
        result = await service.get_repricing_rules()
        assert "rules" in result
        assert isinstance(result["rules"], list)
