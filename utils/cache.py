import json
import os
from typing import Optional, Any
from datetime import datetime, timedelta
import hashlib
import redis

class CacheManager:
    """Redis-based cache manager with TTL support"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_url = redis_url
        self.redis_client = None
        self._fallback_cache = {}
        self._fallback_ttl = {}
        self._use_redis = False
        self._init_redis()
    
    def _init_redis(self):
        """Initialize Redis connection, fallback to in-memory if unavailable"""
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            self.redis_client.ping()
            self._use_redis = True
            print("Redis cache initialized successfully")
        except Exception as e:
            print(f"Redis unavailable, using in-memory fallback: {e}")
            self._use_redis = False
    
    def _generate_key(self, prefix: str, **kwargs) -> str:
        """Generate a unique cache key from parameters"""
        key_str = f"{prefix}:" + ":".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, prefix: str, **kwargs) -> Optional[Any]:
        """Get cached value if it exists and hasn't expired"""
        key = self._generate_key(prefix, **kwargs)
        
        if self._use_redis:
            try:
                value = self.redis_client.get(key)
                if value:
                    return json.loads(value)
            except Exception as e:
                print(f"Redis get error: {e}")
                return self._get_fallback(key)
        else:
            return self._get_fallback(key)
        
        return None
    
    def _get_fallback(self, key: str) -> Optional[Any]:
        """Get from fallback in-memory cache"""
        if key not in self._fallback_cache:
            return None
        
        # Check if expired
        if key in self._fallback_ttl:
            expiry = self._fallback_ttl[key]
            if datetime.utcnow() > expiry:
                del self._fallback_cache[key]
                del self._fallback_ttl[key]
                return None
        
        return self._fallback_cache[key]
    
    def set(self, prefix: str, value: Any, ttl_seconds: int = 3600, **kwargs):
        """Set a cached value with TTL"""
        key = self._generate_key(prefix, **kwargs)
        serialized_value = json.dumps(value)
        
        if self._use_redis:
            try:
                self.redis_client.setex(key, ttl_seconds, serialized_value)
            except Exception as e:
                print(f"Redis set error: {e}")
                self._set_fallback(key, value, ttl_seconds)
        else:
            self._set_fallback(key, value, ttl_seconds)
    
    def _set_fallback(self, key: str, value: Any, ttl_seconds: int):
        """Set in fallback in-memory cache"""
        self._fallback_cache[key] = value
        if ttl_seconds > 0:
            expiry = datetime.utcnow() + timedelta(seconds=ttl_seconds)
            self._fallback_ttl[key] = expiry
    
    def delete(self, prefix: str, **kwargs):
        """Delete a cached value"""
        key = self._generate_key(prefix, **kwargs)
        
        if self._use_redis:
            try:
                self.redis_client.delete(key)
            except Exception as e:
                print(f"Redis delete error: {e}")
        
        if key in self._fallback_cache:
            del self._fallback_cache[key]
        if key in self._fallback_ttl:
            del self._fallback_ttl[key]
    
    def clear(self):
        """Clear all cached values"""
        if self._use_redis:
            try:
                self.redis_client.flushdb()
            except Exception as e:
                print(f"Redis clear error: {e}")
        
        self._fallback_cache.clear()
        self._fallback_ttl.clear()
    
    def cleanup_expired(self):
        """Remove all expired entries (for fallback cache)"""
        if self._use_redis:
            # Redis handles TTL automatically
            return
        
        now = datetime.utcnow()
        expired_keys = [k for k, v in self._fallback_ttl.items() if v <= now]
        
        for key in expired_keys:
            if key in self._fallback_cache:
                del self._fallback_cache[key]
            del self._fallback_ttl[key]


# Global cache instance
_cache_instance = None

def get_cache(redis_url: str = None) -> CacheManager:
    """Get or create the global cache instance"""
    global _cache_instance
    if _cache_instance is None:
        redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        _cache_instance = CacheManager(redis_url)
    return _cache_instance

cache = get_cache()
