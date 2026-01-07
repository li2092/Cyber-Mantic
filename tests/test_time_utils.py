"""
时间工具测试
"""
import pytest
from datetime import datetime, timedelta
from utils.time_utils import TimeUtils


class TestTimeUtils:
    """时间工具测试"""

    def test_china_standard_longitude(self):
        """测试中国标准时区经度"""
        assert TimeUtils.CHINA_STANDARD_LONGITUDE == 120.0

    def test_minutes_per_degree(self):
        """测试每度对应分钟数"""
        assert TimeUtils.MINUTES_PER_DEGREE == 4.0

    def test_calculate_true_solar_time_beijing(self):
        """测试北京(东经116度)真太阳时计算"""
        beijing_time = datetime(2024, 6, 15, 12, 0, 0)
        beijing_longitude = 116.4

        true_time = TimeUtils.calculate_true_solar_time(
            beijing_time,
            beijing_longitude
        )

        # 北京在东经116度，应该比120度慢
        # 时差约为 (116.4 - 120) × 4 = -14.4分钟
        assert true_time < beijing_time
        time_diff = (beijing_time - true_time).total_seconds() / 60
        # 考虑时差修正，应该在10-20分钟范围内
        assert 10 <= time_diff <= 20

    def test_calculate_true_solar_time_shanghai(self):
        """测试上海(东经121度)真太阳时计算"""
        shanghai_time = datetime(2024, 6, 15, 12, 0, 0)
        shanghai_longitude = 121.5

        true_time = TimeUtils.calculate_true_solar_time(
            shanghai_time,
            shanghai_longitude
        )

        # 上海在东经121度，应该比120度快
        # 时差约为 (121.5 - 120) × 4 = 6分钟
        assert true_time > shanghai_time

    def test_calculate_true_solar_time_exactly_120(self):
        """测试东经120度真太阳时"""
        time = datetime(2024, 6, 15, 12, 0, 0)
        longitude = 120.0

        true_time = TimeUtils.calculate_true_solar_time(time, longitude)

        # 东经120度，经度修正为0，只有时差修正
        # 时间差应该较小
        time_diff = abs((true_time - time).total_seconds())
        assert time_diff < 900  # 小于15分钟

    def test_calculate_true_solar_time_west_china(self):
        """测试中国西部(东经100度)真太阳时"""
        time = datetime(2024, 6, 15, 12, 0, 0)
        west_longitude = 100.0

        true_time = TimeUtils.calculate_true_solar_time(time, west_longitude)

        # 东经100度，比120度慢
        # 时差约为 (100 - 120) × 4 = -80分钟
        assert true_time < time
        time_diff = (time - true_time).total_seconds() / 60
        assert 70 <= time_diff <= 90

    def test_equation_of_time_calculation(self):
        """测试时差修正计算"""
        # 测试一年中的不同日期
        dates = [
            datetime(2024, 1, 1),   # 冬至附近
            datetime(2024, 4, 1),   # 春分附近
            datetime(2024, 7, 1),   # 夏至附近
            datetime(2024, 10, 1),  # 秋分附近
        ]

        for date in dates:
            equation_of_time = TimeUtils._calculate_equation_of_time(date)
            # 时差修正应该在-20到+20分钟之间
            assert -20 <= equation_of_time <= 20

    def test_validate_qimen_timestamp_valid(self):
        """测试有效的起卦时间戳"""
        server_time = datetime(2024, 6, 15, 14, 30, 0)
        user_time = datetime(2024, 6, 15, 14, 29, 30)  # 30秒前

        is_valid, message = TimeUtils.validate_qimen_timestamp(
            user_time,
            server_time
        )

        assert is_valid is True
        assert "验证通过" in message

    def test_validate_qimen_timestamp_just_within_limit(self):
        """测试刚好在限制内的时间戳"""
        server_time = datetime(2024, 6, 15, 14, 30, 0)
        user_time = datetime(2024, 6, 15, 14, 25, 0)  # 5分钟前

        is_valid, message = TimeUtils.validate_qimen_timestamp(
            user_time,
            server_time,
            max_diff_seconds=300
        )

        assert is_valid is True

    def test_validate_qimen_timestamp_invalid(self):
        """测试无效的起卦时间戳"""
        server_time = datetime(2024, 6, 15, 14, 30, 0)
        user_time = datetime(2024, 6, 15, 14, 20, 0)  # 10分钟前

        is_valid, message = TimeUtils.validate_qimen_timestamp(
            user_time,
            server_time,
            max_diff_seconds=300
        )

        assert is_valid is False
        assert "时间差过大" in message

    def test_validate_qimen_timestamp_future_time(self):
        """测试未来时间戳"""
        server_time = datetime(2024, 6, 15, 14, 30, 0)
        user_time = datetime(2024, 6, 15, 14, 40, 0)  # 10分钟后

        is_valid, message = TimeUtils.validate_qimen_timestamp(
            user_time,
            server_time,
            max_diff_seconds=300
        )

        assert is_valid is False

    def test_validate_qimen_timestamp_custom_limit(self):
        """测试自定义时间限制"""
        server_time = datetime(2024, 6, 15, 14, 30, 0)
        user_time = datetime(2024, 6, 15, 14, 29, 0)  # 1分钟前

        # 限制30秒，应该无效
        is_valid, message = TimeUtils.validate_qimen_timestamp(
            user_time,
            server_time,
            max_diff_seconds=30
        )

        assert is_valid is False

        # 限制120秒，应该有效
        is_valid, message = TimeUtils.validate_qimen_timestamp(
            user_time,
            server_time,
            max_diff_seconds=120
        )

        assert is_valid is True

    def test_get_solar_term(self):
        """测试节气查询"""
        # 春分附近
        spring_date = datetime(2024, 3, 20)
        term_name, term_time = TimeUtils.get_solar_term(spring_date)

        assert term_name is not None
        assert term_time is not None

    def test_different_dates_solar_time(self):
        """测试不同日期的真太阳时计算"""
        longitude = 116.4

        # 测试一年中的不同日期
        dates = [
            datetime(2024, 1, 15, 12, 0, 0),
            datetime(2024, 4, 15, 12, 0, 0),
            datetime(2024, 7, 15, 12, 0, 0),
            datetime(2024, 10, 15, 12, 0, 0),
        ]

        for date in dates:
            true_time = TimeUtils.calculate_true_solar_time(date, longitude)
            # 应该都能正常计算
            assert true_time is not None
            assert isinstance(true_time, datetime)

    def test_extreme_longitudes(self):
        """测试极端经度值"""
        time = datetime(2024, 6, 15, 12, 0, 0)

        # 东经135度（日本）
        east_time = TimeUtils.calculate_true_solar_time(time, 135.0)
        assert east_time > time

        # 东经75度（新疆）
        west_time = TimeUtils.calculate_true_solar_time(time, 75.0)
        assert west_time < time

    def test_time_validation_same_time(self):
        """测试相同时间的验证"""
        time = datetime(2024, 6, 15, 14, 30, 0)

        is_valid, message = TimeUtils.validate_qimen_timestamp(
            time,
            time
        )

        assert is_valid is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
