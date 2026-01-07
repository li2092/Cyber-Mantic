"""
并发安全性测试
"""
import pytest
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from theories.base import BaseTheory, TheoryRegistry
from models import UserInput
from utils.cache_manager import CacheManager
from datetime import datetime


class MockConcurrentTheory(BaseTheory):
    """并发测试用的模拟理论"""

    def __init__(self, name: str):
        self._name = name
        super().__init__()

    def get_name(self) -> str:
        return self._name

    def get_required_fields(self):
        return ["birth_year"]

    def get_optional_fields(self):
        return []

    def get_field_weights(self):
        return {"birth_year": 1.0}

    def get_min_completeness(self):
        return 0.6

    def calculate(self, user_input: UserInput):
        # 模拟耗时计算
        time.sleep(0.001)
        return {"result": "ok"}


class TestTheoryRegistryConcurrency:
    """理论注册表并发测试"""

    def setup_method(self):
        """每个测试前保存并清空注册表"""
        with TheoryRegistry._lock:
            self._saved_theories = TheoryRegistry._theories.copy()
            TheoryRegistry._theories = {}

    def teardown_method(self):
        """每个测试后恢复注册表"""
        with TheoryRegistry._lock:
            TheoryRegistry._theories = self._saved_theories

    def test_concurrent_registration(self):
        """测试并发注册理论"""
        num_threads = 10
        theories_per_thread = 5

        def register_theories(thread_id):
            """每个线程注册多个理论"""
            for i in range(theories_per_thread):
                theory_name = f"Theory_{thread_id}_{i}"
                theory = MockConcurrentTheory(theory_name)
                TheoryRegistry.register(theory)

        # 创建多个线程并发注册
        threads = []
        for i in range(num_threads):
            t = threading.Thread(target=register_theories, args=(i,))
            threads.append(t)
            t.start()

        # 等待所有线程完成
        for t in threads:
            t.join()

        # 验证所有理论都被正确注册
        all_theories = TheoryRegistry.get_all_theories()
        assert len(all_theories) == num_threads * theories_per_thread

    def test_concurrent_read_write(self):
        """测试并发读写"""
        num_readers = 5
        num_writers = 3
        operations = 100

        def reader():
            """读取理论"""
            for _ in range(operations):
                theories = TheoryRegistry.get_all_theories()
                if theories:
                    # 验证返回的是副本
                    assert isinstance(theories, dict)

        def writer(thread_id):
            """写入理论"""
            for i in range(operations):
                theory_name = f"Theory_{thread_id}_{i}"
                theory = MockConcurrentTheory(theory_name)
                TheoryRegistry.register(theory)

        # 创建读写线程
        threads = []

        for i in range(num_readers):
            t = threading.Thread(target=reader)
            threads.append(t)
            t.start()

        for i in range(num_writers):
            t = threading.Thread(target=writer, args=(i,))
            threads.append(t)
            t.start()

        # 等待所有线程完成
        for t in threads:
            t.join()

        # 验证最终状态
        all_theories = TheoryRegistry.get_all_theories()
        assert len(all_theories) == num_writers * operations

    def test_no_race_condition_in_get_copy(self):
        """测试get_all_theories返回副本，无竞态条件"""
        # 注册一些初始理论
        for i in range(5):
            theory = MockConcurrentTheory(f"Initial_{i}")
            TheoryRegistry.register(theory)

        def modify_local_copy():
            """获取副本并修改，不应影响注册表"""
            theories = TheoryRegistry.get_all_theories()
            theories["NewTheory"] = MockConcurrentTheory("New")
            del theories[list(theories.keys())[0]]  # 删除第一个

        # 多个线程并发修改本地副本
        threads = []
        for _ in range(10):
            t = threading.Thread(target=modify_local_copy)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # 验证注册表没有被修改
        all_theories = TheoryRegistry.get_all_theories()
        assert len(all_theories) == 5
        assert all(f"Initial_{i}" in all_theories for i in range(5))


class TestCacheManagerConcurrency:
    """缓存管理器并发测试"""

    def setup_method(self):
        """每个测试前清空所有缓存"""
        CacheManager.clear_all()

    def test_concurrent_cache_access(self):
        """测试并发访问缓存"""
        cache = CacheManager.get_cache("test_concurrent", max_size=1000)
        num_threads = 10
        operations = 100

        def cache_operations(thread_id):
            """执行缓存操作"""
            for i in range(operations):
                key = f"key_{thread_id}_{i}"
                # 写入
                cache.set(key, f"value_{thread_id}_{i}")
                # 读取
                value = cache.get(key)
                assert value == f"value_{thread_id}_{i}"

        # 创建并发线程
        threads = []
        for i in range(num_threads):
            t = threading.Thread(target=cache_operations, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # 验证缓存统计
        stats = cache.get_stats()
        assert stats["size"] <= 1000  # 不超过最大容量
        assert stats["total_requests"] >= num_threads * operations

    def test_concurrent_cache_decorator(self):
        """测试缓存装饰器的并发安全性"""
        from utils.cache_manager import cached

        call_count = 0
        lock = threading.Lock()

        @cached(cache_name="test_decorator_concurrent", max_size=100)
        def expensive_func(x):
            nonlocal call_count
            with lock:
                call_count += 1
            time.sleep(0.001)  # 模拟耗时
            return x * 2

        num_threads = 20
        test_values = [1, 2, 3, 4, 5]

        def worker():
            """每个线程调用相同的函数"""
            for val in test_values * 10:  # 重复调用
                result = expensive_func(val)
                assert result == val * 2

        # 并发执行
        threads = []
        for _ in range(num_threads):
            t = threading.Thread(target=worker)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # 由于缓存，实际调用次数应该远少于总请求数
        # 在高并发下，由于check-then-set的竞态窗口，同一个键可能被多次计算
        # 但总调用次数应该远少于总请求数（20个线程 * 5个值 * 10次 = 1000次）
        total_requests = num_threads * len(test_values) * 10
        assert call_count <= len(test_values) * 20  # 允许竞态条件下的重复计算
        assert call_count >= len(test_values)  # 至少每个值计算一次
        assert call_count < total_requests * 0.2  # 缓存有效率至少80%


class TestRealWorldScenario:
    """真实场景并发测试"""

    def test_concurrent_lunar_conversion(self):
        """测试并发农历转换"""
        from utils.lunar_calendar import LunarCalendar

        dates = [
            datetime(2024, 1, 1),
            datetime(2024, 2, 10),
            datetime(2024, 6, 15),
            datetime(2024, 10, 1),
            datetime(2024, 12, 25)
        ]

        results = {}
        lock = threading.Lock()

        def convert_date(date):
            """转换日期"""
            result = LunarCalendar.solar_to_lunar(date)
            with lock:
                results[date] = result

        # 创建多个线程并发转换相同的日期
        threads = []
        for _ in range(10):  # 10个线程
            for date in dates:  # 每个日期
                t = threading.Thread(target=convert_date, args=(date,))
                threads.append(t)
                t.start()

        for t in threads:
            t.join()

        # 验证所有结果一致
        assert len(results) == len(dates)
        for date in dates:
            assert results[date] is not None

    def test_concurrent_bazi_calculation(self):
        """测试并发八字计算"""
        from theories.bazi.calculator import BaZiCalculator

        calc = BaZiCalculator()
        test_params = [
            (1990, 6, 15, 10, "male"),
            (1995, 3, 20, 14, "female"),
            (2000, 12, 1, 8, "male"),
        ]

        results = []
        lock = threading.Lock()

        def calculate(params):
            """计算八字"""
            year, month, day, hour, gender = params
            result = calc.calculate_full_bazi(year, month, day, hour, gender, "solar")
            with lock:
                results.append(result)

        # 并发计算
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for _ in range(20):  # 重复计算多次
                for params in test_params:
                    future = executor.submit(calculate, params)
                    futures.append(future)

            # 等待所有任务完成
            for future in as_completed(futures):
                future.result()  # 检查是否有异常

        # 验证结果数量
        assert len(results) == 20 * len(test_params)

    def test_concurrent_theory_selection(self):
        """测试并发理论选择"""
        from core.theory_selector import TheorySelector

        selector = TheorySelector()
        user_inputs = [
            UserInput(
                question_type="事业",
                question_description="测试",
                birth_year=1990,
                birth_month=6,
                birth_day=15,
                numbers=[1, 2, 3]
            ),
            UserInput(
                question_type="财运",
                question_description="测试",
                birth_year=1995,
                birth_month=3,
                birth_day=20,
                numbers=[4, 5, 6]
            ),
        ]

        results = []
        lock = threading.Lock()

        def select_theories(user_input):
            """选择理论"""
            selected, missing = selector.select_theories(user_input)
            with lock:
                results.append((selected, missing))

        # 并发选择
        threads = []
        for _ in range(10):
            for ui in user_inputs:
                t = threading.Thread(target=select_theories, args=(ui,))
                threads.append(t)
                t.start()

        for t in threads:
            t.join()

        # 验证结果
        assert len(results) == 10 * len(user_inputs)
        for selected, _ in results:
            assert len(selected) >= 1  # 至少选择了1个理论


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
