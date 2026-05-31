import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import AsyncMock, MagicMock

from main import app
from models.database import Base, get_db
from models import (
    ProductSearch, ItemDetails, PriceHistory, KeywordAnalysis,
    TrendingItem, SellerPerformance, MarketTrend, CompetitorPrice,
    InventorySnapshot, APIUsage
)

# Test database configuration
TEST_DATABASE_URL = "sqlite:///:memory:"

# Create test engine
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

# Create test session
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test"""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database dependency override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def mock_browse_client():
    """Mock Browse API client"""
    from api.browse import BrowseAPIClient
    client = BrowseAPIClient()
    client.search_items = AsyncMock()
    client.get_trending_items = AsyncMock()
    client.get_item_details = AsyncMock()
    client.get_item_summary = AsyncMock()
    return client


@pytest.fixture
def mock_finding_client():
    """Mock Finding API client"""
    from api.finding import FindingAPIClient
    client = FindingAPIClient()
    client.find_completed_items = AsyncMock()
    client.find_items_by_category = AsyncMock()
    client.find_items_advanced = AsyncMock()
    client.get_category_info = AsyncMock()
    client.get_popular_items = AsyncMock()
    return client


@pytest.fixture
def sample_item_data():
    """Sample item data for testing"""
    return {
        "itemId": "v1|123456789|0",
        "title": "Test Product Title",
        "price": {
            "value": "29.99",
            "currency": "USD"
        },
        "condition": "New",
        "seller": {
            "username": "testseller",
            "feedbackScore": 1000,
            "feedbackPercentage": 99.5
        },
        "image": {
            "imageUrl": "https://example.com/image.jpg"
        },
        "itemWebUrl": "https://example.com/item/123456789"
    }


@pytest.fixture
def sample_search_response(sample_item_data):
    """Sample search API response"""
    return {
        "itemSummaries": [sample_item_data],
        "total": 1
    }


@pytest.fixture
def sample_price_history():
    """Sample price history data"""
    return [
        {
            "item_id": "v1|123456789|0",
            "title": "Test Product",
            "price": 25.00,
            "condition": "Used",
            "seller": "seller1"
        },
        {
            "item_id": "v1|123456790|0",
            "title": "Test Product",
            "price": 30.00,
            "condition": "New",
            "seller": "seller2"
        }
    ]


@pytest.fixture
def sample_seller_performance():
    """Sample seller performance data"""
    return {
        "seller_username": "testseller",
        "active_listings_count": 50,
        "total_listings_count": 200
    }


@pytest.fixture
def sample_market_trends():
    """Sample market trends data"""
    return {
        "category_id": "12345",
        "trend_data": {
            "growth_rate": 15.5,
            "total_listings": 10000
        }
    }


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    redis_mock = MagicMock()
    redis_mock.ping.return_value = True
    redis_mock.get.return_value = None
    redis_mock.setex.return_value = True
    redis_mock.delete.return_value = True
    redis_mock.flushdb.return_value = True
    return redis_mock


@pytest.fixture
def mock_cache_manager(mock_redis):
    """Mock cache manager"""
    from utils.cache import CacheManager
    cache_mgr = CacheManager.__new__(CacheManager)
    cache_mgr.redis_client = mock_redis
    cache_mgr._use_redis = False  # Use fallback cache for tests
    cache_mgr._fallback_cache = {}
    cache_mgr._fallback_ttl = {}
    return cache_mgr


# Environment setup for tests
@pytest.fixture(scope="session", autouse=True)
def set_test_environment():
    """Set test environment variables"""
    os.environ["DB_HOST"] = "localhost"
    os.environ["DB_PORT"] = "5432"
    os.environ["DB_USER"] = "testuser"
    os.environ["DB_PASSWORD"] = "testpass"
    os.environ["DB_NAME"] = "testdb"
    os.environ["REDIS_URL"] = "redis://localhost:6379/1"
    yield
    # Cleanup after all tests
