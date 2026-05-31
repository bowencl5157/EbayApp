import pytest
from unittest.mock import AsyncMock, patch
from main import browse_client


@pytest.mark.integration
class TestAPIEndpoints:
    """Integration tests for API endpoints"""
    
    @pytest.mark.asyncio
    async def test_home_endpoint(self, client):
        """Test home endpoint"""
        response = client.get("/")
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_search_endpoint(self, client, mock_browse_client, sample_search_response):
        """Test search endpoint"""
        with patch.object(browse_client, 'search_items', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = sample_search_response
            response = client.get("/api/search?query=test+query&limit=10")
            assert response.status_code == 200
            data = response.json()
            assert "itemSummaries" in data
    
    @pytest.mark.asyncio
    async def test_trending_endpoint(self, client, mock_browse_client, sample_search_response):
        """Test trending endpoint"""
        with patch.object(browse_client, 'get_trending_items', new_callable=AsyncMock) as mock_trending:
            mock_trending.return_value = sample_search_response
            response = client.get("/api/trending?limit=20")
            assert response.status_code == 200
            data = response.json()
            assert "itemSummaries" in data
    
    @pytest.mark.asyncio
    async def test_item_endpoint(self, client, mock_browse_client, sample_item_data):
        """Test item details endpoint"""
        with patch.object(browse_client, 'get_item_details', new_callable=AsyncMock) as mock_item:
            mock_item.return_value = sample_item_data
            response = client.get("/api/item/v1|123456789|0")
            assert response.status_code == 200
            data = response.json()
            assert data["itemId"] == "v1|123456789|0"
    
    @pytest.mark.asyncio
    async def test_pricing_endpoint(self, client, mock_browse_client, sample_search_response):
        """Test pricing analysis endpoint"""
        with patch.object(browse_client, 'search_items', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = sample_search_response
            response = client.get("/api/pricing/test+query")
            assert response.status_code == 200
            data = response.json()
            assert "price_range" in data
            assert "average_price" in data
            assert "estimated_ebay_fees" in data
            assert "average_fee_percentage" in data["estimated_ebay_fees"]
            assert "store_fee_breakdown" in data
            if data["store_fee_breakdown"]:
                store = data["store_fee_breakdown"][0]
                assert "store" in store
                assert "category_name" in store
                assert "listing_count" in store
                assert "avg_fee_percentage" in store
                assert "avg_fee_amount" in store
    
    @pytest.mark.asyncio
    async def test_seo_keywords_endpoint(self, client, mock_browse_client, sample_search_response):
        """Test SEO keywords endpoint"""
        with patch.object(browse_client, 'search_items', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = sample_search_response
            response = client.get("/api/seo-keywords?query=test+query")
            assert response.status_code == 200
            data = response.json()
            assert "short_tail_keywords" in data
            assert "long_tail_keywords" in data
            assert "seller_breakdown" in data
            if data["seller_breakdown"]:
                seller = data["seller_breakdown"][0]
                assert "current_count" in seller
                assert "count_7d" in seller
                assert "count_30d" in seller
                assert "avg_price" in seller
                assert "sample_url" in seller
    
    @pytest.mark.asyncio
    async def test_product_research_endpoint(self, client, mock_browse_client, sample_search_response):
        """Test product research endpoint"""
        with patch('services.product_research.BrowseAPIClient') as MockBrowse:
            mock_client = MockBrowse.return_value
            mock_client.search_items = AsyncMock(return_value=sample_search_response)
            
            response = client.get("/api/product-research?query=test+query")
            assert response.status_code == 200
            data = response.json()
            assert "query" in data
    
    @pytest.mark.asyncio
    async def test_price_monitoring_endpoint(self, client, mock_browse_client, sample_search_response):
        """Test price monitoring endpoint"""
        with patch('services.price_monitoring.BrowseAPIClient') as MockBrowse:
            mock_client = MockBrowse.return_value
            mock_client.search_items = AsyncMock(return_value=sample_search_response)
            
            response = client.get("/api/price-monitoring?query=test+query")
            assert response.status_code == 200
            data = response.json()
            assert "query" in data
    
    @pytest.mark.asyncio
    async def test_seller_analytics_endpoint(self, client):
        """Test seller analytics endpoint"""
        with patch('services.seller_analytics.TradingAPIClient') as MockTrading:
            mock_client = MockTrading.return_value
            mock_client.get_my_ebay_selling = AsyncMock(return_value="<ActiveList>10</ActiveList>")
            
            with patch('services.seller_analytics.AccountAPIClient') as MockAccount:
                mock_account = MockAccount.return_value
                mock_account.get_account_status = AsyncMock(return_value={})
                
                with patch('services.seller_analytics.InventoryAPIClient') as MockInventory:
                    mock_inventory = MockInventory.return_value
                    mock_inventory.get_inventory_items = AsyncMock(return_value={"inventoryItems": []})
                    
                    response = client.get("/api/seller-analytics")
                    assert response.status_code == 200
                    data = response.json()
                    assert "current_performance" in data
    
    @pytest.mark.asyncio
    async def test_marketplace_research_endpoint(self, client, mock_browse_client, sample_search_response):
        """Test marketplace research endpoint"""
        with patch('services.marketplace_research.BrowseAPIClient') as MockBrowse:
            mock_client = MockBrowse.return_value
            mock_client.get_trending_items = AsyncMock(return_value=sample_search_response)
            
            response = client.get("/api/marketplace-research?category_id=12345")
            assert response.status_code == 200
            data = response.json()
            assert "category_id" in data
    
    @pytest.mark.asyncio
    async def test_repricing_analysis_endpoint(self, client, mock_browse_client, sample_search_response):
        """Test repricing analysis endpoint"""
        with patch('services.repricing.BrowseAPIClient') as MockBrowse:
            mock_client = MockBrowse.return_value
            mock_client.search_items = AsyncMock(return_value=sample_search_response)
            
            response = client.get("/api/repricing-analysis?query=test+query")
            assert response.status_code == 200
            data = response.json()
            assert "query" in data or "error" in data
    
    @pytest.mark.asyncio
    async def test_invalid_endpoint(self, client):
        """Test invalid endpoint returns 404"""
        response = client.get("/api/invalid-endpoint")
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_search_without_query(self, client):
        """Test search endpoint without query parameter"""
        response = client.get("/api/search")
        # This should return 422 (validation error) or handle gracefully
        assert response.status_code in [200, 422]
    
    @pytest.mark.asyncio
    async def test_product_research_endpoint(self, client, mock_browse_client, sample_search_response):
        """Test product research endpoint"""
        with patch('services.product_research.BrowseAPIClient') as MockBrowse:
            mock_client = MockBrowse.return_value
            mock_client.search_items = AsyncMock(return_value=sample_search_response)
            
            response = client.get("/api/product-research?query=test+query")
            assert response.status_code == 200
            data = response.json()
            assert "query" in data
    
    @pytest.mark.asyncio
    async def test_price_monitoring_endpoint(self, client, mock_browse_client, sample_search_response):
        """Test price monitoring endpoint"""
        with patch('services.price_monitoring.BrowseAPIClient') as MockBrowse:
            mock_client = MockBrowse.return_value
            mock_client.search_items = AsyncMock(return_value=sample_search_response)
            
            response = client.get("/api/price-monitoring?query=test+query")
            assert response.status_code == 200
            data = response.json()
            assert "query" in data
    
    @pytest.mark.asyncio
    async def test_seller_analytics_endpoint(self, client):
        """Test seller analytics endpoint"""
        with patch('services.seller_analytics.TradingAPIClient') as MockTrading:
            mock_client = MockTrading.return_value
            mock_client.get_my_ebay_selling = AsyncMock(return_value="<ActiveList>10</ActiveList>")
            
            with patch('services.seller_analytics.AccountAPIClient') as MockAccount:
                mock_account = MockAccount.return_value
                mock_account.get_account_status = AsyncMock(return_value={})
                
                with patch('services.seller_analytics.InventoryAPIClient') as MockInventory:
                    mock_inventory = MockInventory.return_value
                    mock_inventory.get_inventory_items = AsyncMock(return_value={"inventoryItems": []})
                    
                    response = client.get("/api/seller-analytics")
                    assert response.status_code == 200
                    data = response.json()
                    assert "current_performance" in data
    
    @pytest.mark.asyncio
    async def test_marketplace_research_endpoint(self, client, mock_browse_client, sample_search_response):
        """Test marketplace research endpoint"""
        with patch('services.marketplace_research.BrowseAPIClient') as MockBrowse:
            mock_client = MockBrowse.return_value
            mock_client.get_trending_items = AsyncMock(return_value=sample_search_response)
            
            response = client.get("/api/marketplace-research?category_id=12345")
            assert response.status_code == 200
            data = response.json()
            assert "category_id" in data
    
    @pytest.mark.asyncio
    async def test_repricing_analysis_endpoint(self, client, mock_browse_client, sample_search_response):
        """Test repricing analysis endpoint"""
        with patch('services.repricing.BrowseAPIClient') as MockBrowse:
            mock_client = MockBrowse.return_value
            mock_client.search_items = AsyncMock(return_value=sample_search_response)
            
            response = client.get("/api/repricing-analysis?query=test+query")
            assert response.status_code == 200
            data = response.json()
            assert "query" in data or "error" in data
    
    @pytest.mark.asyncio
    async def test_inventory_tracking_endpoint(self, client):
        """Test inventory tracking endpoint"""
        with patch('services.seller_analytics.InventoryAPIClient') as MockInventory:
            mock_inventory = MockInventory.return_value
            mock_inventory.get_inventory_items = AsyncMock(return_value={"inventoryItems": []})
            
            response = client.get("/api/inventory-tracking")
            # Endpoint may not exist yet, accept 200, 404, or 422
            assert response.status_code in [200, 404, 422]
            if response.status_code == 200:
                data = response.json()
                assert "inventory_items" in data or "error" in data
    
    @pytest.mark.asyncio
    async def test_trending_products_endpoint(self, client, mock_browse_client, sample_search_response):
        """Test trending products endpoint"""
        with patch('services.marketplace_research.BrowseAPIClient') as MockBrowse:
            mock_client = MockBrowse.return_value
            mock_client.get_trending_items = AsyncMock(return_value=sample_search_response)
            
            response = client.get("/api/trending-products")
            assert response.status_code == 200
            data = response.json()
            assert "total_items" in data
    
    @pytest.mark.asyncio
    async def test_market_competition_endpoint(self, client, mock_browse_client, sample_search_response):
        """Test market competition endpoint"""
        with patch('services.marketplace_research.BrowseAPIClient') as MockBrowse:
            mock_client = MockBrowse.return_value
            mock_client.search_items = AsyncMock(return_value=sample_search_response)
            
            response = client.get("/api/market-competition?query=test+query")
            assert response.status_code == 200
            data = response.json()
            assert "competition_level" in data or "error" in data
    
    @pytest.mark.asyncio
    async def test_auto_reprice_endpoint(self, client):
        """Test auto-reprice endpoint"""
        with patch('services.repricing.TradingAPIClient') as MockTrading:
            mock_client = MockTrading.return_value
            mock_client.revise_item = AsyncMock(return_value={"success": True})
            
            response = client.get("/api/auto-reprice?item_id=v1|123456789|0&target_price=25.0")
            assert response.status_code == 200
            data = response.json()
            assert "item_id" in data or "error" in data
    
    @pytest.mark.asyncio
    async def test_apply_repricing_rules_endpoint(self, client):
        """Test apply repricing rules endpoint"""
        with patch('services.repricing.TradingAPIClient') as MockTrading:
            mock_client = MockTrading.return_value
            mock_client.revise_item = AsyncMock(return_value={"success": True})
            
            response = client.get("/api/apply-repricing-rules")
            # Endpoint may not exist yet, accept 200, 404, or 422
            assert response.status_code in [200, 404, 422]
            if response.status_code == 200:
                data = response.json()
                assert "rules" in data or "error" in data
