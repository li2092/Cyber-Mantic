"""
奇门遁甲计算器V2 - 单元测试

验证完整版奇门遁甲排盘算法的准确性
"""
import pytest
from datetime import datetime
from cyber_mantic.theories.qimen.calculator_v2 import QiMenCalculatorV2


class TestQiMenCalculatorV2:
    """奇门遁甲计算器V2测试类"""

    def setup_method(self):
        """每个测试前初始化"""
        self.calculator = QiMenCalculatorV2()

    def test_basic_calculation(self):
        """测试基本排盘计算"""
        # 测试日期：2026年1月4日 下午3点
        test_time = datetime(2026, 1, 4, 15, 0, 0)

        result = self.calculator.calculate_qimen(
            query_time=test_time,
            use_true_solar_time=False,
            longitude=120.0
        )

        # 验证基本字段存在
        assert result is not None
        assert "起局时间" in result
        assert "阴阳遁" in result
        assert "日干支" in result
        assert "时干支" in result
        assert "元" in result
        assert "局数" in result
        assert "九宫" in result
        assert "值符宫" in result
        assert "值使宫" in result
        assert "格局" in result
        assert "综合评分" in result

        # 验证九宫数量
        assert len(result["九宫"]) == 9

        # 验证每个宫位信息完整
        for palace in result["九宫"]:
            assert "宫位" in palace
            assert "方位" in palace
            assert "九星_地盘" in palace
            assert "九星_天盘" in palace
            assert "八门_天盘" in palace
            assert "九星属性" in palace
            assert "八门属性" in palace

        print(f"✅ 基本计算测试通过")
        print(f"阴阳遁: {result['阴阳遁']}")
        print(f"日干支: {result['日干支']}")
        print(f"时干支: {result['时干支']}")
        print(f"元: {result['元']}")
        print(f"局数: {result['局数']}")
        print(f"值符宫: {result['值符宫']}")
        print(f"值使宫: {result['值使宫']}")

    def test_day_ganzhi_calculation(self):
        """测试日干支计算准确性"""
        # 已知：2000-01-01 为 庚辰日
        test_date = datetime(2000, 1, 1)
        gan, zhi = self.calculator._calculate_day_ganzhi(test_date)

        assert gan == "庚", f"2000-01-01应为庚日，实际为{gan}日"
        assert zhi == "辰", f"2000-01-01应为辰日，实际为{zhi}日"

        # 测试另一个日期：2000-01-02 应为 辛巳日
        test_date2 = datetime(2000, 1, 2)
        gan2, zhi2 = self.calculator._calculate_day_ganzhi(test_date2)

        assert gan2 == "辛", f"2000-01-02应为辛日，实际为{gan2}日"
        assert zhi2 == "巳", f"2000-01-02应为巳日，实际为{zhi2}日"

        print(f"✅ 日干支计算测试通过")

    def test_hour_ganzhi_calculation(self):
        """测试时干支计算"""
        # 子时（23点）应为子时
        test_time = datetime(2026, 1, 4, 23, 0, 0)
        day_gan, _ = self.calculator._calculate_day_ganzhi(test_time)
        hour_gan, hour_zhi = self.calculator._calculate_hour_ganzhi(test_time, day_gan)

        assert hour_zhi == "子", f"23点应为子时，实际为{hour_zhi}时"

        # 午时（12点）应为午时
        test_time2 = datetime(2026, 1, 4, 12, 0, 0)
        hour_gan2, hour_zhi2 = self.calculator._calculate_hour_ganzhi(test_time2, day_gan)

        assert hour_zhi2 == "午", f"12点应为午时，实际为{hour_zhi2}时"

        print(f"✅ 时干支计算测试通过")

    def test_yuan_determination(self):
        """测试元（上中下元）确定"""
        # 测试符头确定元
        # 甲子为上元符头
        yuan = self.calculator._determine_yuan_by_futou("甲子", 0)
        assert yuan == "上元", f"甲子应为上元，实际为{yuan}"

        # 甲申为中元符头
        yuan2 = self.calculator._determine_yuan_by_futou("甲申", 0)
        assert yuan2 == "中元", f"甲申应为中元，实际为{yuan2}"

        # 甲戌为下元符头
        yuan3 = self.calculator._determine_yuan_by_futou("甲戌", 0)
        assert yuan3 == "下元", f"甲戌应为下元，实际为{yuan3}"

        print(f"✅ 元确定测试通过")

    def test_zhifu_zhishi_location(self):
        """测试值符值使定位"""
        test_time = datetime(2026, 1, 4, 15, 0, 0)

        result = self.calculator.calculate_qimen(
            query_time=test_time,
            use_true_solar_time=False
        )

        # 验证值符值使宫位存在
        assert result["值符宫"] in ["坎", "坤", "震", "巽", "中", "乾", "兑", "艮", "离"]
        assert result["值使宫"] in ["坎", "坤", "震", "巽", "中", "乾", "兑", "艮", "离"]

        print(f"✅ 值符值使定位测试通过")
        print(f"值符落宫: {result['值符宫']}")
        print(f"值使落宫: {result['值使宫']}")

    def test_pattern_detection(self):
        """测试格局检测"""
        test_time = datetime(2026, 1, 4, 15, 0, 0)

        result = self.calculator.calculate_qimen(
            query_time=test_time,
            use_true_solar_time=False
        )

        # 验证格局列表存在
        assert "格局" in result
        assert isinstance(result["格局"], list)

        # 如果有格局，验证格局结构
        for pattern in result["格局"]:
            assert "格局" in pattern
            assert "吉凶" in pattern
            assert "说明" in pattern
            assert "宫位" in pattern

        print(f"✅ 格局检测测试通过")
        print(f"检测到{len(result['格局'])}个格局")
        for pattern in result["格局"]:
            print(f"  - {pattern['格局']} ({pattern['吉凶']}): {pattern['说明']}")

    def test_directions_analysis(self):
        """测试方位分析"""
        test_time = datetime(2026, 1, 4, 15, 0, 0)

        result = self.calculator.calculate_qimen(
            query_time=test_time,
            use_true_solar_time=False
        )

        # 验证方位信息存在
        assert "吉利方位" in result
        assert "不利方位" in result
        assert isinstance(result["吉利方位"], list)
        assert isinstance(result["不利方位"], list)

        print(f"✅ 方位分析测试通过")
        print(f"吉利方位: {result['吉利方位']}")
        print(f"不利方位: {result['不利方位']}")

    def test_overall_score(self):
        """测试综合评分"""
        test_time = datetime(2026, 1, 4, 15, 0, 0)

        result = self.calculator.calculate_qimen(
            query_time=test_time,
            use_true_solar_time=False
        )

        # 验证评分在合理范围内
        assert "综合评分" in result
        score = result["综合评分"]
        assert 0.0 <= score <= 1.0, f"综合评分应在0-1之间，实际为{score}"

        print(f"✅ 综合评分测试通过")
        print(f"综合评分: {score:.2f}")

    def test_true_solar_time_conversion(self):
        """测试真太阳时转换"""
        test_time = datetime(2026, 1, 4, 15, 0, 0)

        # 测试不同经度
        result1 = self.calculator.calculate_qimen(
            query_time=test_time,
            use_true_solar_time=True,
            longitude=120.0  # 东经120度（北京时区基准）
        )

        result2 = self.calculator.calculate_qimen(
            query_time=test_time,
            use_true_solar_time=True,
            longitude=90.0  # 西部地区
        )

        # 不同经度可能导致不同的时干支
        # 这里只验证计算能正常完成
        assert result1 is not None
        assert result2 is not None

        print(f"✅ 真太阳时转换测试通过")
        print(f"经度120°时干支: {result1['时干支']}")
        print(f"经度90°时干支: {result2['时干支']}")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])
