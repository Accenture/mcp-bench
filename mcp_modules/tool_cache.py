#!/usr/bin/env python3
"""
Tool Call Cache Module using SQLite
Implements tool call caching with multi-process safe access
"""

import json
import hashlib
import time
import sqlite3
from pathlib import Path
from typing import Any, Dict, Optional
import logging
import threading

logger = logging.getLogger(__name__)

class ToolCache:
    """
    Tool call caching system implemented with SQLite for multi-process safety
    """
    
    def __init__(self, cache_dir: str = "./cache", ttl_hours: int = 0, enabled: bool = False, 
                 server_whitelist: Optional[list] = None):
        """
        Initialize the cache system
        
        Args:
            cache_dir: Cache directory path
            ttl_hours: Cache time-to-live in hours, 0 means permanent cache
            enabled: Whether caching is enabled
            server_whitelist: Server whitelist, only cache tool calls from these servers (None or empty list means cache all)
        """
        self.enabled = enabled
        if not self.enabled:
            logger.info("Tool cache is disabled")
            return
            
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.cache_dir / "tool_cache.db"
        self.ttl_seconds = ttl_hours * 3600 if ttl_hours > 0 else 0
        self.server_whitelist = server_whitelist or []
        
        # Thread-local storage, one connection per thread
        self.local = threading.local()
        
        # Initialize database
        self._init_db()
        
        whitelist_msg = f" with whitelist: {self.server_whitelist}" if self.server_whitelist else ""
        logger.info(f"Tool cache initialized at {self.db_path} with TTL={ttl_hours} hours{whitelist_msg}")
        
    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection"""
        if not hasattr(self.local, 'conn'):
            self.local.conn = sqlite3.connect(str(self.db_path), timeout=30.0)
            # Enable WAL mode for better concurrency
            self.local.conn.execute('PRAGMA journal_mode=WAL')
            self.local.conn.execute('PRAGMA synchronous=NORMAL')
        return self.local.conn
        
    def _init_db(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        try:
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS cache (
                    cache_key TEXT PRIMARY KEY,
                    server_name TEXT NOT NULL,
                    tool_name TEXT NOT NULL,
                    params TEXT NOT NULL,
                    result TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    access_count INTEGER DEFAULT 1
                )
            ''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON cache(timestamp)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_server_tool ON cache(server_name, tool_name)')
            conn.commit()
        finally:
            conn.close()
    
    def _generate_cache_key(self, server_name: str, tool_name: str, params: Dict[str, Any]) -> str:
        """
        Generate cache key
        
        Args:
            server_name: Server name (e.g., Yahoo Finance)
            tool_name: Tool name (e.g., get_stock_info)
            params: Tool parameters
        
        Returns:
            Cache key
        """
        # Normalize and sort parameters to ensure same params generate same key
        normalized_params = json.dumps(params, sort_keys=True)
        key_string = f"{server_name}:{tool_name}:{normalized_params}"
        cache_key = hashlib.md5(key_string.encode()).hexdigest()
        return cache_key
    
    def get(self, server_name: str, tool_name: str, params: Dict[str, Any]) -> Optional[Any]:
        """
        Get cached tool call result
        
        Args:
            server_name: Server name
            tool_name: Tool name
            params: Tool parameters
        
        Returns:
            Cached result, or None if not found or expired
        """
        if not self.enabled:
            return None
            
        # Check if server is in whitelist
        if self.server_whitelist and server_name not in self.server_whitelist:
            return None
            
        cache_key = self._generate_cache_key(server_name, tool_name, params)
        current_time = time.time()
        
        try:
            conn = self._get_connection()
            cursor = conn.execute(
                'SELECT result, timestamp FROM cache WHERE cache_key = ?',
                (cache_key,)
            )
            row = cursor.fetchone()
            
            if row:
                result_json, timestamp = row
                # Check if expired (ttl_seconds=0 means never expire)
                if self.ttl_seconds == 0 or current_time - timestamp < self.ttl_seconds:
                    # Update access count
                    conn.execute(
                        'UPDATE cache SET access_count = access_count + 1 WHERE cache_key = ?',
                        (cache_key,)
                    )
                    conn.commit()
                    
                    result = json.loads(result_json)
                    age_minutes = (current_time - timestamp) / 60
                    logger.info(f"Cache HIT: {server_name}:{tool_name} (age: {age_minutes:.1f} minutes)")
                    logger.info(f"  Cached params: {json.dumps(params, indent=2)}")
                    return result
                else:
                    # Expired, delete it
                    conn.execute('DELETE FROM cache WHERE cache_key = ?', (cache_key,))
                    conn.commit()
                    logger.debug(f"Cache expired: {server_name}:{tool_name}")
                    
        except (sqlite3.Error, json.JSONDecodeError) as e:
            logger.error(f"Cache read error: {e}")
        
        logger.info(f"Cache MISS: {server_name}:{tool_name}")
        logger.debug(f"  Params: {json.dumps(params, indent=2)}")
        return None
    
    def set(self, server_name: str, tool_name: str, params: Dict[str, Any], result: Any) -> bool:
        """
        Set tool call result cache
        
        Args:
            server_name: Server name
            tool_name: Tool name
            params: Tool parameters
            result: Tool call result
        
        Returns:
            Whether cache was successfully set
        """
        if not self.enabled:
            return False
            
        # Check if server is in whitelist
        if self.server_whitelist and server_name not in self.server_whitelist:
            logger.info(f"Server '{server_name}' not in cache whitelist {self.server_whitelist}, skipping cache")
            return False
            
        # Don't cache empty results
        if not result or result == {} or result == [] or result == "" or result is None:
            logger.debug(f"Not caching empty result for {server_name}:{tool_name}")
            return False
            
        # Don't cache error responses
        if isinstance(result, dict) and 'error' in result:
            logger.debug(f"Not caching error response for {server_name}:{tool_name}")
            return False
            
        # Check for error keywords (rate limit, 503, 429, etc.)
        result_str = str(result).lower()
        error_keywords = [
            '503', '429', 
            'rate limit', 'rate-limit', 'rate_limit', 'ratelimit',
            'too many requests', 'too-many-requests',
            'service unavailable', 'service-unavailable',
            'quota exceeded', 'quota-exceeded',
            'throttled', 'blocked'
        ]
        if any(keyword in result_str for keyword in error_keywords):
            logger.debug(f"Not caching result with error keywords for {server_name}:{tool_name}")
            return False
            
        # If result has success field, it must be True
        if isinstance(result, dict) and 'success' in result and not result.get('success'):
            logger.debug(f"Not caching failed result (success=False) for {server_name}:{tool_name}")
            return False
            
        cache_key = self._generate_cache_key(server_name, tool_name, params)
        
        try:
            result_json = json.dumps(result, default=str)
            params_json = json.dumps(params, sort_keys=True)
            
            conn = self._get_connection()
            conn.execute(
                '''INSERT OR REPLACE INTO cache 
                   (cache_key, server_name, tool_name, params, result, timestamp, access_count)
                   VALUES (?, ?, ?, ?, ?, ?, 
                           COALESCE((SELECT access_count FROM cache WHERE cache_key = ?), 0) + 1)''',
                (cache_key, server_name, tool_name, params_json, result_json, time.time(), cache_key)
            )
            conn.commit()
            
            result_size = len(result_json)
            logger.info(f"Cache SET: {server_name}:{tool_name} (size: {result_size} bytes)")
            logger.debug(f"  Params: {json.dumps(params, indent=2)}")
            return True
            
        except (sqlite3.Error, json.JSONEncodeError) as e:
            logger.error(f"Cache write error: {e}")
            return False
    
    def clear_expired(self) -> int:
        """
        Clear expired cache entries
        
        Returns:
            Number of entries cleared
        """
        if not self.enabled or self.ttl_seconds == 0:
            return 0  # Permanent cache doesn't clear expired items
            
        try:
            conn = self._get_connection()
            cutoff = time.time() - self.ttl_seconds
            cursor = conn.execute(
                'DELETE FROM cache WHERE timestamp < ?',
                (cutoff,)
            )
            deleted = cursor.rowcount
            conn.commit()
            
            if deleted > 0:
                logger.info(f"Cleared {deleted} expired cache entries")
            return deleted
                        
        except sqlite3.Error as e:
            logger.error(f"Failed to clear expired cache: {e}")
            return 0
    
    def clear_all(self) -> int:
        """
        Clear all cache entries
        
        Returns:
            Number of entries cleared
        """
        if not self.enabled:
            return 0
            
        try:
            conn = self._get_connection()
            cursor = conn.execute('DELETE FROM cache')
            deleted = cursor.rowcount
            conn.commit()
            logger.info(f"Cleared all {deleted} cache entries")
            return deleted
        except sqlite3.Error as e:
            logger.error(f"Failed to clear cache: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.enabled:
            return {'enabled': False}
            
        try:
            conn = self._get_connection()
            
            # Overall statistics
            cursor = conn.execute(
                'SELECT COUNT(*), SUM(access_count), MIN(timestamp), MAX(timestamp) FROM cache'
            )
            total_entries, total_accesses, oldest_timestamp, newest_timestamp = cursor.fetchone()
            
            # Statistics by server
            cursor = conn.execute('''
                SELECT server_name, COUNT(*), SUM(access_count) 
                FROM cache 
                GROUP BY server_name
            ''')
            server_stats = {}
            for row in cursor.fetchall():
                server_stats[row[0]] = {
                    'entries': row[1],
                    'accesses': row[2] or 0
                }
            
            # Hot tools
            cursor = conn.execute('''
                SELECT server_name, tool_name, access_count 
                FROM cache 
                ORDER BY access_count DESC 
                LIMIT 10
            ''')
            hot_tools = []
            for row in cursor.fetchall():
                hot_tools.append({
                    'server': row[0],
                    'tool': row[1],
                    'accesses': row[2]
                })
            
            # Calculate cache age
            current_time = time.time()
            oldest_age = (current_time - oldest_timestamp) / 3600 if oldest_timestamp else 0
            newest_age = (current_time - newest_timestamp) / 3600 if newest_timestamp else 0
            
            return {
                'enabled': True,
                'total_entries': total_entries or 0,
                'total_accesses': total_accesses or 0,
                'oldest_entry_hours': round(oldest_age, 1),
                'newest_entry_hours': round(newest_age, 1),
                'server_stats': server_stats,
                'hot_tools': hot_tools,
                'cache_file': str(self.db_path),
                'ttl_hours': self.ttl_seconds / 3600
            }
        except sqlite3.Error as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {'enabled': True, 'error': str(e)}
    
    def close(self):
        """Close database connection"""
        if hasattr(self.local, 'conn'):
            self.local.conn.close()
            del self.local.conn


# Global cache instance
_cache_instance: Optional[ToolCache] = None

def get_cache(**kwargs) -> ToolCache:
    """
    Get cache instance (singleton pattern)
    
    Args:
        **kwargs: Arguments to pass to cache constructor
    
    Returns:
        Cache instance
    """
    global _cache_instance
    if _cache_instance is None:
        # Read cache settings from config file
        from config import config_loader
        
        # If no arguments provided, use config file settings
        if not kwargs:
            kwargs = {
                'enabled': config_loader.is_cache_enabled(),
                'cache_dir': config_loader.get_cache_dir(),
                'ttl_hours': config_loader.get_cache_ttl(),
                'server_whitelist': config_loader.get_cache_server_whitelist()
            }
        
        _cache_instance = ToolCache(**kwargs)
    return _cache_instance

def set_cache_instance(cache: ToolCache):
    """Set global cache instance"""
    global _cache_instance
    _cache_instance = cache