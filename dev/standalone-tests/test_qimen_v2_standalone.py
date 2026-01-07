"""
奇门遁甲计算器V2 - 独立测试脚本

直接测试calculator_v2的功能，无需完整的模块导入链
"""
import sys
import os

# 添加路径
sys.path.insert(0, '/home/user/-')
sys.path.insert(0, '/home/user/-/cyber_mantic')

from datetime import datetime

# 直接导入calculator_v2模块，避免触发theories的__init__
import importlib.util
spec = importlib.util.spec_from_file_location(
    "calculator_v2",
    "/home/user/-/cyber_mantic/theories/qimen/calculator_v2.py"
)
calculator_v2_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(calculator_v2_module)

QiMenCalculatorV2 = calculator_v2_module.QiMenCalculatorV2


def test_basic_calculation():
    """测试基本排盘计算"""
    print("\n=== 测试1: 基本排盘计算 ===")

    calculator = QiMenCalculatorV2()

    # 测试日期：2026年1月4日 下午3点
    test_time = datetime(2026, 1, 4, 15, 0, 0)

    result = calculator.calculate_qimen(
        query_time=test_time,
        use_true_solar_time=False,
        longitude=120.0
    )

    # 验证基本字段存在
    assert result is not None, "计算结果不能为空"
    assert "起局时间" in result
    assert "阴阳遁" in result
    assert "日干支" in result
    assert "时干支" in result
    assert "元" in result
    assert "局数" in result
    assert "九宫" in result
    assert "值符宫" in result
    assert "值使宫" in result

    # 验证九宫数量
    assert len(result["九宫"]) == 9, f"九宫应有9个，实际{len(result['九宫'])}个"

    print(f"✅ 基本计算测试通过")
    print(f"起局时间: {result['起局时间']}")
    print(f"阴阳遁: {result['阴阳遁']}")
    print(f"日干支: {result['日干支']}")
    print(f"时干支: {result['时干支']}")
    print(f"元: {result['元']}")
    print(f"局数: {result['局数']}")
    print(f"值符宫: {result['值符宫']}")
    print(f"值使宫: {result['值使宫']}")
    print(f"综合评分: {result['综合评分']:.2f}")

    # 打印九宫信息
    print("\n九宫详情:")
    for palace in result["九宫"]:
        print(f"  {palace['宫位']}宫 ({palace['方位']}): "
              f"九星={palace['九星_天盘']}, 八门={palace['八门_天盘']}")

    # 打印格局
    print(f"\n检测到{len(result['格局'])}个格局:")
    for pattern in result["格局"]:
        print(f"  - {pattern['格局']} ({pattern['吉凶']}): {pattern['说明']}")

    return result


def test_day_ganzhi_calculation():
    """测试日干支计算准确性"""
    print("\n=== 测试2: 日干支计算 ===")

    calculator = QiMenCalculatorV2()

    # 已知：2000-01-01 为 庚辰日
    test_date = datetime(2000, 1, 1)
    gan, zhi = calculator._calculate_day_ganzhi(test_date)

    assert gan == "庚", f"2000-01-01应为庚日，实际为{gan}日"
    assert zhi == "辰", f"2000-01-01应为辰日，实际为{zhi}日"
    print(f"✅ 2000-01-01 = {gan}{zhi}日 (正确)")

    # 测试另一个日期：2000-01-02 应为 辛巳日
    test_date2 = datetime(2000, 1, 2)
    gan2, zhi2 = calculator._calculate_day_ganzhi(test_date2)

    assert gan2 == "辛", f"2000-01-02应为辛日，实际为{gan2}日"
    assert zhi2 == "巳", f"2000-01-02应为巳日，实际为{zhi2}日"
    print(f"✅ 2000-01-02 = {gan2}{zhi2}日 (正确)")

    # 测试当前日期
    today = datetime(2026, 1, 4)
    gan3, zhi3 = calculator._calculate_day_ganzhi(today)
    print(f"✅ 2026-01-04 = {gan3}{zhi3}日")


def test_hour_ganzhi_calculation():
    """测试时干支计算"""
    print("\n=== 测试3: 时干支计算 ===")

    calculator = QiMenCalculatorV2()

    # 子时（23点）应为子时
    test_time = datetime(2026, 1, 4, 23, 0, 0)
    day_gan, _ = calculator._calculate_day_ganzhi(test_time)
    hour_gan, hour_zhi = calculator._calculate_hour_ganzhi(test_time, day_gan)

    assert hour_zhi == "子", f"23点应为子时，实际为{hour_zhi}时"
    print(f"✅ 23:00 = {hour_gan}{hour_zhi}时 (子时)")

    # 午时（12点）应为午时
    test_time2 = datetime(2026, 1, 4, 12, 0, 0)
    hour_gan2, hour_zhi2 = calculator._calculate_hour_ganzhi(test_time2, day_gan)

    assert hour_zhi2 == "午", f"12点应为午时，实际为{hour_zhi2}时"
    print(f"✅ 12:00 = {hour_gan2}{hour_zhi2}时 (午时)")


def test_yuan_determination():
    """测试元（上中下元）确定"""
    print("\n=== 测试4: 元确定 ===")

    calculator = QiMenCalculatorV2()

    # 测试符头确定元
    # 甲子为上元符头
    yuan = calculator._determine_yuan_by_futou("甲子", 0)
    assert yuan == "上元", f"甲子应为上元，实际为{yuan}"
    print(f"✅ 甲子日 = {yuan}")

    # 甲申为中元符头
    yuan2 = calculator._determine_yuan_by_futou("甲申", 0)
    assert yuan2 == "中元", f"甲申应为中元，实际为{yuan2}"
    print(f"✅ 甲申日 = {yuan2}")

    # 甲戌为下元符头
    yuan3 = calculator._determine_yuan_by_futou("甲戌", 0)
    assert yuan3 == "下元", f"甲戌应为下元，实际为{yuan3}"
    print(f"✅ 甲戌日 = {yuan3}")


def test_complete_paiPan():
    """测试完整排盘流程"""
    print("\n=== 测试5: 完整排盘流程 ===")

    calculator = QiMenCalculatorV2()

    # 测试多个时间点
    test_times = [
        datetime(2026, 1, 4, 15, 0, 0),  # 下午3点
        datetime(2026, 1, 4, 9, 0, 0),   # 上午9点
        datetime(2026, 1, 4, 21, 0, 0),  # 晚上9点
    ]

    for idx, test_time in enumerate(test_times, 1):
        print(f"\n时间点{idx}: {test_time}")
        result = calculator.calculate_qimen(
            query_time=test_time,
            use_true_solar_time=False
        )

        print(f"  阴阳遁: {result['阴阳遁']}")
        print(f"  局数: {result['局数']}")
        print(f"  日干支: {result['日干支']}")
        print(f"  时干支: {result['时干支']}")
        print(f"  值符宫: {result['值符宫']}")
        print(f"  值使宫: {result['值使宫']}")
        print(f"  格局数: {len(result['格局'])}")
        print(f"  综合评分: {result['综合评分']:.2f}")

    print("\n✅ 完整排盘流程测试通过")


def main():
    """运行所有测试"""
    print("=" * 60)
    print("奇门遁甲计算器V2 - 独立测试")
    print("=" * 60)

    try:
        test_basic_calculation()
        test_day_ganzhi_calculation()
        test_hour_ganzhi_calculation()
        test_yuan_determination()
        test_complete_paiPan()

        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
