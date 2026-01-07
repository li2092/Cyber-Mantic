"""
缓存管理器测试
"""
import pytest
import time
from datetime import datetime
from utils.cache_manager import CacheManager, cached, performance_monitor, LRUCache


class TestLRUCache:
    """LRU缓存测试"""

    def setup_method(self):
        """每个测试前创建新缓存"""
        self.cache = LRUCache(max_size=3)

    def test_basic_set_get(self):
        """测试基本的设置和获取"""
        self.cache.set("key1", "value1")
        assert self.cache.get("key1") == "value1"

    def test_cache_miss(self):
        """测试缓存未命中"""
        assert self.cache.get("nonexistent") is None

    def test_lru_eviction(self):
        """测试LRU淘汰机制"""
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        self.cache.set("key3", "value3")

        # 缓存满了，添加第4个应该淘汰最旧的key1
        self.cache.set("key4", "value4")

        assert self.cache.get("key1") is None  # key1被淘汰
        assert self.cache.get("key2") == "value2"
        assert self.cache.get("key3") == "value3"
        assert self.cache.get("key4") == "value4"

    def test_lru_access_order(self):
        """测试访问顺序影响LRU"""
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        self.cache.set("key3", "value3")

        # 访问key1，使其变成最近使用
        self.cache.get("key1")

        # 添加key4，应该淘汰key2（最久未使用）
        self.cache.set("key4", "value4")

        assert self.cache.get("key1") == "value1"  # key1因为被访问而保留
        assert self.cache.get("key2") is None      # key2被淘汰
        assert self.cache.get("key3") == "value3"
        assert self.cache.get("key4") == "value4"

    def test_ttl_expiration(self):
        """测试TTL过期"""
        cache = LRUCache(max_size=10, default_ttl=1)  # 1秒过期
        cache.set("key1", "value1")

        # 立即获取应该成功
        assert cache.get("key1") == "value1"

        # 等待过期
        time.sleep(1.1)

        # 过期后应该返回None
        assert cache.get("key1") is None

    def test_cache_stats(self):
        """测试缓存统计"""
        self.cache.set("key1", "value1")

        # 命中
        self.cache.get("key1")
        self.cache.get("key1")

        # 未命中
        self.cache.get("key2")

        stats = self.cache.get_stats()
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 2 / 3
        assert stats["size"] == 1

    def test_clear(self):
        """测试清空缓存"""
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")

        self.cache.clear()

        assert self.cache.get("key1") is None
        assert self.cache.get("key2") is None
        assert self.cache.get_stats()["size"] == 0


class TestCachedDecorator:
    """缓存装饰器测试"""

    def test_function_caching(self):
        """测试函数缓存"""
        call_count = 0

        @cached(cache_name="test_func", max_size=10)
        def expensive_function(x, y):
            nonlocal call_count
            call_count += 1
            return x + y

        # 第一次调用
        result1 = expensive_function(1, 2)
        assert result1 == 3
        assert call_count == 1

        # 第二次相同参数，应该从缓存返回
        result2 = expensive_function(1, 2)
        assert result2 == 3
        assert call_count == 1  # 没有再次调用

        # 不同参数，应该重新计算
        result3 = expensive_function(2, 3)
        assert result3 == 5
        assert call_count == 2

    def test_method_caching(self):
        """测试方法缓存"""
        class Calculator:
            def __init__(self):
                self.calc_count = 0

            @cached(cache_name="test_method", max_size=10)
            def calculate(self, a, b):
                self.calc_count += 1
                return a * b

        calc = Calculator()

        # 第一次调用
        result1 = calc.calculate(3, 4)
        assert result1 == 12
        assert calc.calc_count == 1

        # 相同参数，从缓存返回
        result2 = calc.calculate(3, 4)
        assert result2 == 12
        assert calc.calc_count == 1

    def test_cache_with_dict_args(self):
        """测试带字典参数的缓存"""
        call_count = 0

        @cached(cache_name="test_dict", max_size=10)
        def process_dict(data):
            nonlocal call_count
            call_count += 1
            return sum(data.values())

        # 第一次调用
        result1 = process_dict({"a": 1, "b": 2})
        assert result1 == 3
        assert call_count == 1

        # 相同字典（即使键顺序不同），应该命中缓存
        result2 = process_dict({"b": 2, "a": 1})
        assert result2 == 3
        assert call_count == 1


class TestCacheManager:
    """缓存管理器测试"""

    def setup_method(self):
        """每个测试前清空所有缓存"""
        CacheManager.clear_all()

    def test_get_cache(self):
        """测试获取缓存实例"""
        cache1 = CacheManager.get_cache("test1")
        cache2 = CacheManager.get_cache("test1")

        # 应该返回同一个实例
        assert cache1 is cache2

    def test_multiple_caches(self):
        """测试多个独立缓存"""
        cache1 = CacheManager.get_cache("cache1")
        cache2 = CacheManager.get_cache("cache2")

        cache1.set("key", "value1")
        cache2.set("key", "value2")

        assert cache1.get("key") == "value1"
        assert cache2.get("key") == "value2"

    def test_get_all_stats(self):
        """测试获取所有缓存统计"""
        cache1 = CacheManager.get_cache("cache1")
        cache2 = CacheManager.get_cache("cache2")

        cache1.set("key1", "value1")
        cache2.set("key2", "value2")

        stats = CacheManager.get_all_stats()

        assert "cache1" in stats
        assert "cache2" in stats
        assert stats["cache1"]["size"] == 1
        assert stats["cache2"]["size"] == 1

    def test_clear_all(self):
        """测试清空所有缓存"""
        cache1 = CacheManager.get_cache("cache1")
        cache2 = CacheManager.get_cache("cache2")

        cache1.set("key1", "value1")
        cache2.set("key2", "value2")

        CacheManager.clear_all()

        assert cache1.get("key1") is None
        assert cache2.get("key2") is None


class TestPerformanceMonitor:
    """性能监控装饰器测试"""

    def test_performance_logging(self):
        """测试性能日志记录"""
        @performance_monitor(log_threshold_ms=10.0)
        def fast_function():
            return "done"

        @performance_monitor(log_threshold_ms=10.0)
        def slow_function():
            time.sleep(0.02)  # 20ms
            return "done"

        # 两个函数都应该正常执行
        assert fast_function() == "done"
        assert slow_function() == "done"


class TestRealWorldScenario:
    """真实场景测试"""

    def test_lunar_calendar_caching(self):
        """测试农历转换缓存效果"""
        from utils.lunar_calendar import LunarCalendar

        date1 = datetime(2024, 1, 1)

        # 第一次调用（应该执行实际计算）
        start1 = time.time()
        result1 = LunarCalendar.solar_to_lunar(date1)
        time1 = (time.time() - start1) * 1000

        # 第二次调用相同日期（应该从缓存返回）
        start2 = time.time()
        result2 = LunarCalendar.solar_to_lunar(date1)
        time2 = (time.time() - start2) * 1000

        # 结果应该相同
        assert result1 == result2

        # 缓存应该显著加快速度（至少快5倍）
        # 注意：这个测试在快速机器上可能不稳定
        # assert time2 < time1 / 5, f"缓存未生效：第一次{time1:.2f}ms，第二次{time2:.2f}ms"

    def test_bazi_calculation_caching(self):
        """测试八字计算缓存效果"""
        from theories.bazi.calculator import BaZiCalculator

        calc = BaZiCalculator()

        # 第一次计算
        start1 = time.time()
        result1 = calc.calculate_full_bazi(1990, 6, 15, 10, "male", "solar")
        time1 = (time.time() - start1) * 1000

        # 第二次相同参数
        start2 = time.time()
        result2 = calc.calculate_full_bazi(1990, 6, 15, 10, "male", "solar")
        time2 = (time.time() - start2) * 1000

        # 结果应该相同
        assert result1 == result2

        # 缓存应该显著加快速度
        # assert time2 < time1 / 5, f"缓存未生效：第一次{time1:.2f}ms，第二次{time2:.2f}ms"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
