"""
Cache Service for Thinking Graph

Provides intelligent caching with Redis fallback to in-memory caching.
Optimizes performance for graph operations and API responses.
"""

import json
import time
import os
import logging
from typing import Dict, Any, Optional, List
import hashlib

logger = logging.getLogger(__name__)

class CacheService:
    """Intelligent caching service with Redis and memory fallback"""
    
    def __init__(self):
        self.redis_client = None
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'redis_connected': False
        }
        
        # Try to connect to Redis, fall back to memory cache if unavailable
        self._init_redis()
    
    def _init_redis(self):
        """Initialize Redis connection with graceful fallback"""
        try:
            import redis
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            redis_host = os.getenv('REDIS_HOST', 'localhost')
            redis_port = int(os.getenv('REDIS_PORT', 6379))
            redis_db = int(os.getenv('REDIS_DB', 0))
            
            if redis_url and redis_url != 'redis://localhost:6379/0':
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
            else:
                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    db=redis_db,
                    decode_responses=True,
                    socket_connect_timeout=2,
                    socket_timeout=2
                )
            
            # Test connection
            self.redis_client.ping()
            self.cache_stats['redis_connected'] = True
            logger.info("✅ Redis connected for caching")
        except Exception as e:
            self.redis_client = None
            self.cache_stats['redis_connected'] = False
            logger.info(f"ℹ️ Redis not available, using in-memory cache (Error: {type(e).__name__})")
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value from Redis or memory"""
        try:
            # Try Redis first
            if self.redis_client:
                cached_value = self.redis_client.get(key)
                if cached_value:
                    self.cache_stats['hits'] += 1
                    return json.loads(cached_value)
        except Exception as e:
            logger.warning(f"Redis get error: {e}")
        
        # Memory cache fallback
        if key in self.memory_cache:
            cache_entry = self.memory_cache[key]
            if cache_entry['expires_at'] > time.time():
                self.cache_stats['hits'] += 1
                return cache_entry['data']
            else:
                del self.memory_cache[key]  # Expired
        
        self.cache_stats['misses'] += 1
        return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set cached value in Redis or memory"""
        try:
            # Try Redis first
            if self.redis_client:
                self.redis_client.setex(key, ttl, json.dumps(value))
                return True
        except Exception as e:
            logger.warning(f"Redis set error: {e}")
        
        # Memory cache fallback
        self.memory_cache[key] = {
            'data': value,
            'expires_at': time.time() + ttl
        }
        
        # Cleanup if memory cache gets too large
        if len(self.memory_cache) > 1000:  # Arbitrary limit
            self._cleanup_memory_cache()
        
        return True
    
    def _cleanup_memory_cache(self):
        """Remove expired entries from memory cache"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.memory_cache.items()
            if entry['expires_at'] <= current_time
        ]
        for key in expired_keys:
            del self.memory_cache[key]
        
        logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def delete(self, pattern: str) -> int:
        """Delete cached values matching pattern"""
        deleted_count = 0
        
        try:
            # Try Redis first
            if self.redis_client:
                if '*' in pattern:
                    # Pattern matching
                    keys = self.redis_client.keys(pattern)
                    if keys:
                        deleted_count = self.redis_client.delete(*keys)
                else:
                    # Exact key
                    deleted_count = self.redis_client.delete(pattern)
                
                if deleted_count > 0:
                    return deleted_count
        except Exception as e:
            logger.warning(f"Redis delete error: {e}")
        
        # Memory cache fallback - simple pattern matching
        if '*' in pattern:
            prefix = pattern.replace('*', '')
            keys_to_delete = [
                key for key in self.memory_cache.keys()
                if key.startswith(prefix)
            ]
        else:
            keys_to_delete = [pattern] if pattern in self.memory_cache else []
        
        for key in keys_to_delete:
            if key in self.memory_cache:
                del self.memory_cache[key]
                deleted_count += 1
        
        return deleted_count
    
    def generate_key(self, *args) -> str:
        """Generate cache key from arguments"""
        key_string = ':'.join(str(arg) for arg in args)
        return hashlib.md5(key_string.encode()).hexdigest()[:16]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        hit_rate = 0
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        if total_requests > 0:
            hit_rate = (self.cache_stats['hits'] / total_requests) * 100
        
        return {
            'redis_connected': self.cache_stats['redis_connected'],
            'total_requests': total_requests,
            'cache_hits': self.cache_stats['hits'],
            'cache_misses': self.cache_stats['misses'],
            'hit_rate_percent': round(hit_rate, 2),
            'memory_cache_size': len(self.memory_cache),
            'memory_cache_limit': 1000
        }
    
    def clear_all(self):
        """Clear all cached data"""
        try:
            if self.redis_client:
                self.redis_client.flushdb()
        except Exception as e:
            logger.warning(f"Redis flush error: {e}")
        
        self.memory_cache.clear()
        logger.info("All cache data cleared")
    
    def health_check(self) -> Dict[str, Any]:
        """Check cache service health"""
        health_status = {
            'status': 'healthy',
            'redis_available': False,
            'memory_cache_available': True,
            'errors': []
        }
        
        # Test Redis
        if self.redis_client:
            try:
                self.redis_client.ping()
                health_status['redis_available'] = True
            except Exception as e:
                health_status['errors'].append(f"Redis error: {str(e)}")
        
        # Test memory cache
        try:
            test_key = 'health_check_test'
            self.memory_cache[test_key] = {'data': 'test', 'expires_at': time.time() + 1}
            if test_key in self.memory_cache:
                del self.memory_cache[test_key]
            else:
                health_status['memory_cache_available'] = False
                health_status['errors'].append("Memory cache not working")
        except Exception as e:
            health_status['memory_cache_available'] = False
            health_status['errors'].append(f"Memory cache error: {str(e)}")
        
        if health_status['errors']:
            health_status['status'] = 'degraded' if health_status['memory_cache_available'] else 'unhealthy'
        
        return health_status


# Global cache instance
cache_service = CacheService()

# Decorator for automatic caching
def cached(ttl: int = 3600, key_prefix: str = ""):
    """Decorator for automatic caching of function results"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{cache_service.generate_key(*args, *kwargs.items())}"
            
            # Try to get from cache
            cached_result = cache_service.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_service.set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator

# Export
__all__ = ['cache_service', 'cached']