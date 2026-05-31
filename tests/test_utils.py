import pytest
import time
from datetime import datetime, timedelta
from utils.cache import CacheManager
from utils.rate_limiter import RateLimiter


@pytest.mark.unit
class TestCacheManager:
    """Test cases for Cache Manager"""
    
    def test_init(self):
        """Test cache manager initialization"""
        cache = CacheManager(redis_url="redis://localhost:6379/1")
        assert cache.redis_url == "redis://localhost:6379/1"
        assert cache._fallback_cache == {}
    
    def test_generate_key(self):
        """Test key generation"""
        cache = CacheManager()
        key1 = cache._generate_key("search", query="test", limit=10)
        key2 = cache._generate_key("search", query="test", limit=10)
        key3 = cache._generate_key("search", query="different", limit=10)
        
        assert key1 == key2
        assert key1 != key3
    
    def test_set_and_get(self, mock_cache_manager):
        """Test setting and getting cached values"""
        mock_cache_manager.set("test", {"data": "value"}, ttl_seconds=60, key="test_key")
        result = mock_cache_manager.get("test", key="test_key")
        assert result == {"data": "value"}
    
    def test_get_nonexistent(self, mock_cache_manager):
        """Test getting non-existent cached value"""
        result = mock_cache_manager.get("test", key="nonexistent_key")
        assert result is None
    
    def test_delete(self, mock_cache_manager):
        """Test deleting cached value"""
        mock_cache_manager.set("test", {"data": "value"}, ttl_seconds=60, key="test_key")
        mock_cache_manager.delete("test", key="test_key")
        result = mock_cache_manager.get("test", key="test_key")
        assert result is None
    
    def test_clear(self, mock_cache_manager):
        """Test clearing all cached values"""
        mock_cache_manager.set("test1", {"data": "value1"}, ttl_seconds=60, key="key1")
        mock_cache_manager.set("test2", {"data": "value2"}, ttl_seconds=60, key="key2")
        mock_cache_manager.clear()
        
        result1 = mock_cache_manager.get("test1", key="key1")
        result2 = mock_cache_manager.get("test2", key="key2")
        
        assert result1 is None
        assert result2 is None
    
    def test_fallback_cache_expiration(self):
        """Test fallback cache expiration"""
        cache = CacheManager(redis_url="invalid")  # Force fallback
        cache._use_redis = False
        
        # Set with short TTL
        cache.set("test", {"data": "value"}, ttl_seconds=1, key="test_key")
        result = cache.get("test", key="test_key")
        assert result == {"data": "value"}
        
        # Wait for expiration
        time.sleep(2)
        result = cache.get("test", key="test_key")
        assert result is None
    
    def test_get_cache_singleton(self):
        """Test cache singleton pattern"""
        from utils.cache import get_cache
        cache1 = get_cache()
        cache2 = get_cache()
        assert cache1 is cache2


@pytest.mark.unit
class TestRateLimiter:
    """Test cases for Rate Limiter"""
    
    def test_init(self):
        """Test rate limiter initialization"""
        limiter = RateLimiter()
        assert limiter._requests == {}
        assert "browse" in limiter._limits
    
    def test_check_limit(self):
        """Test checking rate limits"""
        limiter = RateLimiter()
        result = limiter.check_limit("browse")
        assert result == True
    
    def test_record_call(self):
        """Test recording API calls"""
        limiter = RateLimiter()
        limiter.record_call("browse")
        assert len(limiter._requests["browse"]) == 1
    
    def test_get_remaining_calls(self):
        """Test getting remaining calls"""
        limiter = RateLimiter()
        remaining = limiter.get_remaining_calls("browse")
        assert remaining > 0
    
    def test_get_reset_time(self):
        """Test getting reset time"""
        limiter = RateLimiter()
        reset_time = limiter.get_reset_time("browse")
        assert isinstance(reset_time, datetime)
    
    def test_rate_limit_exceeded(self):
        """Test behavior when rate limit is exceeded"""
        limiter = RateLimiter()
        
        # Set a very low limit for testing
        limiter._limits["test_api"] = {"calls": 2, "period": 3600}
        
        # Record calls up to limit
        limiter.record_call("test_api")
        limiter.record_call("test_api")
        
        # Check if limit is reached
        result = limiter.check_limit("test_api")
        assert result == False
    
    def test_cleanup_old_requests(self):
        """Test cleanup of old requests"""
        limiter = RateLimiter()
        
        # Record a call
        limiter.record_call("browse")
        
        # Manually set old timestamp
        old_time = datetime.utcnow() - timedelta(seconds=100000)
        limiter._requests["browse"][0] = old_time
        
        # Check limit should clean up old requests
        result = limiter.check_limit("browse")
        assert result == True
        assert len(limiter._requests["browse"]) == 0
    
    @pytest.mark.asyncio
    async def test_wait_if_needed(self):
        """Test wait if needed (should not wait for under-limit case)"""
        limiter = RateLimiter()
        # This should not wait since we're under limit
        await limiter.wait_if_needed("browse")
        assert True  # If we get here, it didn't wait
    
    def test_multiple_api_tracking(self):
        """Test tracking multiple APIs separately"""
        limiter = RateLimiter()
        
        limiter.record_call("browse")
        limiter.record_call("finding")
        limiter.record_call("trading")
        
        assert len(limiter._requests["browse"]) == 1
        assert len(limiter._requests["finding"]) == 1
        assert len(limiter._requests["trading"]) == 1
