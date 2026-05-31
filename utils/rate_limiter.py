import time
from typing import Dict
from collections import defaultdict
from datetime import datetime, timedelta

class RateLimiter:
    """Rate limiter for API calls with sliding window"""
    
    def __init__(self):
        self._requests = defaultdict(list)
        self._limits = {
            "browse": {"calls": 5000, "period": 86400},  # 5000 calls per day
            "finding": {"calls": 5000, "period": 86400},
            "trading": {"calls": 10000, "period": 86400},
            "inventory": {"calls": 10000, "period": 86400},
            "account": {"calls": 5000, "period": 86400},
            "marketplace_insights": {"calls": 1000, "period": 86400},
        }
    
    def check_limit(self, api_name: str) -> bool:
        """Check if API call is within rate limits"""
        if api_name not in self._limits:
            return True  # No limit set
        
        limit = self._limits[api_name]
        now = datetime.utcnow()
        period_start = now - timedelta(seconds=limit["period"])
        
        # Clean old requests
        self._requests[api_name] = [
            req_time for req_time in self._requests[api_name]
            if req_time > period_start
        ]
        
        # Check if under limit
        return len(self._requests[api_name]) < limit["calls"]
    
    def record_call(self, api_name: str):
        """Record an API call"""
        self._requests[api_name].append(datetime.utcnow())
    
    def get_remaining_calls(self, api_name: str) -> int:
        """Get remaining API calls for the period"""
        if api_name not in self._limits:
            return float('inf')
        
        limit = self._limits[api_name]
        now = datetime.utcnow()
        period_start = now - timedelta(seconds=limit["period"])
        
        # Clean old requests
        self._requests[api_name] = [
            req_time for req_time in self._requests[api_name]
            if req_time > period_start
        ]
        
        return limit["calls"] - len(self._requests[api_name])
    
    def get_reset_time(self, api_name: str) -> datetime:
        """Get time when rate limit resets"""
        if api_name not in self._limits or not self._requests[api_name]:
            return datetime.utcnow()
        
        limit = self._limits[api_name]
        oldest_request = min(self._requests[api_name])
        return oldest_request + timedelta(seconds=limit["period"])
    
    async def wait_if_needed(self, api_name: str):
        """Wait if rate limit is exceeded"""
        if not self.check_limit(api_name):
            reset_time = self.get_reset_time(api_name)
            wait_seconds = (reset_time - datetime.utcnow()).total_seconds()
            if wait_seconds > 0:
                print(f"Rate limit reached for {api_name}. Waiting {wait_seconds:.2f} seconds...")
                time.sleep(wait_seconds)
        
        self.record_call(api_name)


# Global rate limiter instance
rate_limiter = RateLimiter()
