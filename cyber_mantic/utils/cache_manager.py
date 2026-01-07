"""
缓存管理器 - 提升系统性能

支持：
- LRU缓存（最近最少使用）
- TTL过期（时间到期自动清除）
- 缓存统计（命中率、缓存大小）
- 线程安全
"""
from functools import wraps
from typing import Any, Callable, Dict, Optional, Tuple
from datetime import datetime, timedelta
import hashlib
import json
import threading
from collections import OrderedDict
from utils.logger import get_logger


class CacheEntry:
    """缓存条目"""

    def __init__(self, value: Any, ttl_seconds: Optional[int] = None):
        self.value = value
        self.created_at = datetime.now()
        self.ttl_seconds = ttl_seconds
        self.access_count = 0
        self.last_accessed = self.created_at

    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.ttl_seconds is None:
            return False
        return datetime.now() > self.created_at + timedelta(seconds=self.ttl_seconds)

    def access(self) -> Any:
        """访问缓存值"""
        self.access_count += 1
        self.last_accessed = datetime.now()
        return self.value


class LRUCache:
    """LRU缓存实现（线程安全）"""

    def __init__(self, max_size: int = 1000, default_ttl: Optional[int] = None):
        """
        初始化LRU缓存

        Args:
            max_size: 最大缓存条目数
            default_ttl: 默认过期时间（秒），None表示不过期
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0
        self.logger = get_logger(__name__)

    def _make_key(self, *args, **kwargs) -> str:
        """生成缓存键"""
        # 将参数转为可哈希的字符串
        key_parts = []

        # 处理位置参数
        for arg in args:
            if isinstance(arg, (dict, list)):
                key_parts.append(json.dumps(arg, sort_keys=True, ensure_ascii=False))
            else:
                key_parts.append(str(arg))

        # 处理关键字参数
        if kwargs:
            key_parts.append(json.dumps(kwargs, sort_keys=True, ensure_ascii=False))

        # 生成哈希
        key_str = '|'.join(key_parts)
        return hashlib.md5(key_str.encode('utf-8')).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None

            entry = self._cache[key]

            # 检查是否过期
            if entry.is_expired():
                del self._cache[key]
                self._misses += 1
                return None

            # 移动到末尾（最近使用）
            self._cache.move_to_end(key)
            self._hits += 1
            return entry.access()

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """设置缓存值"""
        with self._lock:
            # 如果已存在，删除旧的
            if key in self._cache:
                del self._cache[key]

            # 如果超过最大大小，删除最旧的
            if len(self._cache) >= self.max_size:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                self.logger.debug(f"缓存已满，删除最旧条目: {oldest_key[:8]}...")

            # 添加新条目
            ttl = ttl if ttl is not None else self.default_ttl
            self._cache[key] = CacheEntry(value, ttl)

    def clear(self):
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
            self.logger.info("缓存已清空")

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0

            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate,
                "total_requests": total_requests
            }

    def cleanup_expired(self):
        """清理过期条目"""
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            for key in expired_keys:
                del self._cache[key]

            if expired_keys:
                self.logger.info(f"清理了 {len(expired_keys)} 个过期缓存条目")


class CacheManager:
    """全局缓存管理器"""

    # 不同类型的缓存实例
    _caches: Dict[str, LRUCache] = {}
    _lock = threading.Lock()
    _logger = get_logger(__name__)

    @classmethod
    def get_cache(cls, cache_name: str, max_size: int = 1000, default_ttl: Optional[int] = None) -> LRUCache:
        """获取或创建指定缓存"""
        with cls._lock:
            if cache_name not in cls._caches:
                cls._caches[cache_name] = LRUCache(max_size, default_ttl)
                cls._logger.info(f"创建缓存: {cache_name} (max_size={max_size}, ttl={default_ttl})")
            return cls._caches[cache_name]

    @classmethod
    def clear_all(cls):
        """清空所有缓存"""
        with cls._lock:
            for cache in cls._caches.values():
                cache.clear()
            cls._logger.info("所有缓存已清空")

    @classmethod
    def get_all_stats(cls) -> Dict[str, Dict[str, Any]]:
        """获取所有缓存统计"""
        with cls._lock:
            return {
                name: cache.get_stats()
                for name, cache in cls._caches.items()
            }

    @classmethod
    def cleanup_all_expired(cls):
        """清理所有过期缓存"""
        with cls._lock:
            for cache in cls._caches.values():
                cache.cleanup_expired()


def cached(
    cache_name: str = "default",
    max_size: int = 1000,
    ttl: Optional[int] = None,
    key_prefix: str = ""
):
    """
    缓存装饰器

    Args:
        cache_name: 缓存名称
        max_size: 最大缓存大小
        ttl: 过期时间（秒）
        key_prefix: 键前缀

    Example:
        @cached(cache_name="lunar", ttl=3600)
        def solar_to_lunar(date):
            # 耗时计算
            return result
    """
    def decorator(func: Callable) -> Callable:
        cache = CacheManager.get_cache(cache_name, max_size, ttl)

        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = cache._make_key(key_prefix, func.__name__, *args, **kwargs)

            # 尝试从缓存获取
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # 执行函数
            result = func(*args, **kwargs)

            # 存入缓存
            cache.set(cache_key, result, ttl)

            return result

        # 添加缓存控制方法
        wrapper.cache = cache
        wrapper.cache_clear = cache.clear
        wrapper.cache_stats = cache.get_stats

        return wrapper
    return decorator


# 性能监控装饰器
def performance_monitor(log_threshold_ms: float = 100.0):
    """
    性能监控装饰器

    Args:
        log_threshold_ms: 日志记录阈值（毫秒），超过此时间才记录
    """
    def decorator(func: Callable) -> Callable:
        logger = get_logger(func.__module__)

        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = datetime.now()

            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed = (datetime.now() - start_time).total_seconds() * 1000

                if elapsed > log_threshold_ms:
                    logger.warning(
                        f"⏱️ {func.__name__} 执行耗时: {elapsed:.2f}ms (超过阈值 {log_threshold_ms}ms)"
                    )
                else:
                    logger.debug(f"⏱️ {func.__name__} 执行耗时: {elapsed:.2f}ms")

        return wrapper
    return decorator
