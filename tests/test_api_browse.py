import pytest
from unittest.mock import AsyncMock, patch
from api.browse import BrowseAPIClient


@pytest.mark.unit
class TestBrowseAPIClient:
    """Test cases for Browse API client"""
    
    def test_init(self):
        """Test client initialization"""
        client = BrowseAPIClient(
            app_token="test_token",
            access_token="test_access",
            client_id="test_client",
            client_secret="test_secret"
        )
        assert client.app_token == "test_token"
        assert client.access_token == "test_access"
        assert client.client_id == "test_client"
        assert client.client_secret == "test_secret"
    
    @pytest.mark.asyncio
    async def test_get_headers(self, mock_browse_client):
        """Test getting headers with token"""
        mock_browse_client.get_access_token = AsyncMock(return_value="test_token")
        headers = await mock_browse_client.get_headers()
        assert headers["Authorization"] == "Bearer test_token"
        assert headers["Content-Type"] == "application/json"
        assert headers["X-EBAY-C-MARKETPLACE-ID"] == "EBAY_US"
    
    @pytest.mark.asyncio
    async def test_search_items(self, mock_browse_client, sample_search_response):
        """Test searching for items"""
        mock_browse_client.search_items = AsyncMock(return_value=sample_search_response)
        result = await mock_browse_client.search_items("test query", limit=10)
        assert result == sample_search_response
        mock_browse_client.search_items.assert_called_once_with("test query", limit=10)
    
    @pytest.mark.asyncio
    async def test_search_items_with_cache(self, mock_browse_client, sample_search_response, mock_cache_manager):
        """Test searching for items with caching"""
        mock_browse_client.search_items = AsyncMock(return_value=sample_search_response)
        result = await mock_browse_client.search_items("test query", limit=10, use_cache=True)
        assert result == sample_search_response
    
    @pytest.mark.asyncio
    async def test_get_trending_items(self, mock_browse_client, sample_search_response):
        """Test getting trending items"""
        mock_browse_client.get_trending_items = AsyncMock(return_value=sample_search_response)
        result = await mock_browse_client.get_trending_items(category_id="12345", limit=20)
        assert result == sample_search_response
        mock_browse_client.get_trending_items.assert_called_once_with(category_id="12345", limit=20)
    
    @pytest.mark.asyncio
    async def test_get_item_details(self, mock_browse_client, sample_item_data):
        """Test getting item details"""
        mock_browse_client.get_item_details = AsyncMock(return_value=sample_item_data)
        result = await mock_browse_client.get_item_details("v1|123456789|0")
        assert result == sample_item_data
        mock_browse_client.get_item_details.assert_called_once_with("v1|123456789|0")
    
    @pytest.mark.asyncio
    async def test_get_item_summary(self, mock_browse_client):
        """Test getting item summary for multiple items"""
        mock_response = {"itemSummaries": []}
        mock_browse_client.get_item_summary = AsyncMock(return_value=mock_response)
        result = await mock_browse_client.get_item_summary(["v1|123456789|0", "v1|123456790|0"])
        assert result == mock_response
        mock_browse_client.get_item_summary.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_by_image(self, mock_browse_client):
        """Test searching by image"""
        mock_response = {"itemSummaries": []}
        mock_browse_client.search_by_image = AsyncMock(return_value=mock_response)
        result = await mock_browse_client.search_by_image("https://example.com/image.jpg")
        assert result == mock_response
        mock_browse_client.search_by_image.assert_called_once_with("https://example.com/image.jpg")
