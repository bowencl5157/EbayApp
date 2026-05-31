import pytest
from unittest.mock import AsyncMock
from api.finding import FindingAPIClient


@pytest.mark.unit
class TestFindingAPIClient:
    """Test cases for Finding API client"""
    
    def test_init(self):
        """Test client initialization"""
        client = FindingAPIClient(app_id="test_app_id")
        assert client.app_id == "test_app_id"
    
    @pytest.mark.asyncio
    async def test_find_completed_items(self, mock_finding_client):
        """Test finding completed items"""
        mock_response = {"findCompletedItemsResponse": [{"searchResult": [{"item": []}]}]}
        mock_finding_client.find_completed_items = AsyncMock(return_value=mock_response)
        result = await mock_finding_client.find_completed_items("test query", limit=50)
        assert result == mock_response
        mock_finding_client.find_completed_items.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_find_items_by_category(self, mock_finding_client):
        """Test finding items by category"""
        mock_response = {"findItemsByCategoryResponse": [{"searchResult": [{"item": []}]}]}
        mock_finding_client.find_items_by_category = AsyncMock(return_value=mock_response)
        result = await mock_finding_client.find_items_by_category("12345", limit=100)
        assert result == mock_response
        mock_finding_client.find_items_by_category.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_find_items_advanced(self, mock_finding_client):
        """Test advanced item search"""
        mock_response = {"findItemsAdvancedResponse": [{"searchResult": [{"item": []}]}]}
        mock_finding_client.find_items_advanced = AsyncMock(return_value=mock_response)
        result = await mock_finding_client.find_items_advanced("test query", category_id="12345")
        assert result == mock_response
        mock_finding_client.find_items_advanced.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_category_info(self, mock_finding_client):
        """Test getting category information"""
        mock_response = {"category": {"categoryId": "12345", "categoryName": "Test Category"}}
        mock_finding_client.get_category_info = AsyncMock(return_value=mock_response)
        result = await mock_finding_client.get_category_info("12345")
        assert result == mock_response
        mock_finding_client.get_category_info.assert_called_once_with("12345")
    
    @pytest.mark.asyncio
    async def test_get_popular_items(self, mock_finding_client):
        """Test getting popular items"""
        mock_response = {"findPopularItemsResponse": [{"item": []}]}
        mock_finding_client.get_popular_items = AsyncMock(return_value=mock_response)
        result = await mock_finding_client.get_popular_items(category_id="12345", limit=50)
        assert result == mock_response
        mock_finding_client.get_popular_items.assert_called_once()
