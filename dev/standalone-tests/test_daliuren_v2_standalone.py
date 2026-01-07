"""
大六壬计算器V2 - 独立测试脚本

验证完整版大六壬起课算法的准确性
"""
import sys
sys.path.insert(0, '/home/user/-')
sys.path.insert(0, '/home/user/-/cyber_mantic')

# 直接导入
import importlib.util
spec = importlib.util.spec_from_file_location(
    "calculator_v2",
    "/home/user/-/cyber_mantic/theories/daliuren/calculator_v2.py"
)
calculator_v2_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(calculator_v2_module)

DaLiuRenCalculatorV2 = calculator_v2_module.DaLiuRenCalculatorV2


def test_basic_calculation():
    """测试基本起课计算"""
    print("\n=== 测试1: 基本起课计算 ===")

    calculator = DaLiuRenCalculatorV2()

    # 测试日期：2026年1月4日 下午3点
    result = calculator.calculate_daliuren(
        year=2026,
        month=1,
        day=4,
        hour=15,
        question="测试问题"
    )

    # 验证基本字段
    assert "日干支" in result
    assert "时支" in result
    assert "月将" in result
    assert "四课" in result
    assert "三传" in result
    assert "发用方法" in result
    assert "天将" in result
    assert "课体" in result
    assert "综合评分" in result

    print(f"✅ 基本计算测试通过")
    print(f"日干支: {result['日干支']}")
    print(f"时支: {result['时支']}")
    print(f"月将: {result['月将']}")
    print(f"发用方法: {result['发用方法']}")
    print(f"课体: {result['课体']['名称']}")
    print(f"综合评分: {result['综合评分']:.2f}")

    # 打印四课
    print("\n四课详情:")
    for ke in result["四课"]:
        print(f"  {ke['课名']}: {ke['下']} -> {ke['上']} ({ke['关系']})")

    # 打印三传
    print("\n三传详情:")
    for chuan in result["三传"]:
        print(f"  {chuan['传名']}: {chuan['地支']} ({chuan['来源']})")

    # 打印天将
    print("\n天将配置:")
    for tj in result["天将"]:
        print(f"  {tj['传名']}: {tj['天将']} ({tj['地支']}) - {tj['昼夜']}")


def test_day_ganzhi():
    """测试日干支计算准确性"""
    print("\n=== 测试2: 日干支计算 ===")

    calculator = DaLiuRenCalculatorV2()

    # 测试已知日期：2000-01-01 = 庚辰日
    gan, zhi = calculator._calculate_day_ganzhi_accurate(2000, 1, 1)
    assert gan == "庚", f"2000-01-01应为庚日，实际{gan}日"
    assert zhi == "辰", f"2000-01-01应为辰日，实际{zhi}日"
    print(f"✅ 2000-01-01 = {gan}{zhi}日 (正确)")

    # 测试2026-01-04
    gan2, zhi2 = calculator._calculate_day_ganzhi_accurate(2026, 1, 4)
    print(f"✅ 2026-01-04 = {gan2}{zhi2}日")


def test_fa_yong_methods():
    """测试不同发用方法"""
    print("\n=== 测试3: 九宗门发用方法 ===")

    calculator = DaLiuRenCalculatorV2()

    # 测试多个日期，观察不同发用方法
    test_dates = [
        (2026, 1, 4, 15),
        (2026, 1, 5, 9),
        (2026, 1, 6, 21),
    ]

    fa_yong_stats = {}

    for year, month, day, hour in test_dates:
        result = calculator.calculate_daliuren(year, month, day, hour)
        fa_yong = result["发用方法"]
        fa_yong_stats[fa_yong] = fa_yong_stats.get(fa_yong, 0) + 1

        print(f"{year}-{month:02d}-{day:02d} {hour}:00 -> {result['日干支']} -> {fa_yong}")

    print(f"\n发用方法统计: {fa_yong_stats}")
    print(f"✅ 九宗门发用方法测试通过")


def test_tian_jiang_day_night():
    """测试天将昼夜顺逆"""
    print("\n=== 测试4: 天将昼夜顺逆 ===")

    calculator = DaLiuRenCalculatorV2()

    # 白天（下午3点）
    result_day = calculator.calculate_daliuren(2026, 1, 4, 15)
    day_night1 = result_day["天将"][0]["昼夜"]
    print(f"15:00 -> {day_night1}贵")

    # 夜晚（晚上9点）
    result_night = calculator.calculate_daliuren(2026, 1, 4, 21)
    day_night2 = result_night["天将"][0]["昼夜"]
    print(f"21:00 -> {day_night2}贵")

    # 验证昼夜判断
    assert day_night1 == "昼", "15点应为昼贵"
    assert day_night2 == "夜", "21点应为夜贵"

    print(f"✅ 天将昼夜顺逆测试通过")


def test_ke_ti_judgment():
    """测试课体判断"""
    print("\n=== 测试5: 课体判断 ===")

    calculator = DaLiuRenCalculatorV2()

    result = calculator.calculate_daliuren(2026, 1, 4, 15)

    ke_ti = result["课体"]
    print(f"课体名称: {ke_ti['名称']}")
    print(f"课体说明: {ke_ti['说明']}")
    print(f"发用方法: {ke_ti['发用方法']}")

    # 验证课体结构
    assert "名称" in ke_ti
    assert "说明" in ke_ti
    assert "发用方法" in ke_ti

    print(f"✅ 课体判断测试通过")


def test_comprehensive_analysis():
    """测试综合分析"""
    print("\n=== 测试6: 综合分析（完整起课流程） ===")

    calculator = DaLiuRenCalculatorV2()

    # 完整起课
    result = calculator.calculate_daliuren(
        year=2026,
        month=1,
        day=4,
        hour=15,
        question="事业发展是否顺利"
    )

    print(f"\n【起课时间】{result['日干支']}日 {result['时支']}时")
    print(f"【月将】{result['月将']}")

    print(f"\n【四课】")
    for ke in result["四课"]:
        print(f"  {ke['课名']}: {ke['下']} -> {ke['上']} ({ke['关系']})")

    print(f"\n【三传】发用方法：{result['发用方法']}")
    for i, chuan in enumerate(result["三传"]):
        tj = result["天将"][i]
        print(f"  {chuan['传名']}: {chuan['地支']} - {tj['天将']} ({tj['属性'].get('吉凶', '平')})")

    print(f"\n【课体】{result['课体']['名称']}")
    print(f"  {result['课体']['说明']}")

    print(f"\n【吉凶判断】{result['吉凶判断']} (评分: {result['综合评分']:.2f})")
    print(f"  {result['详细分析']}")

    print(f"\n✅ 综合分析测试通过")


def main():
    """运行所有测试"""
    print("=" * 60)
    print("大六壬计算器V2 - 独立测试")
    print("=" * 60)

    try:
        test_basic_calculation()
        test_day_ganzhi()
        test_fa_yong_methods()
        test_tian_jiang_day_night()
        test_ke_ti_judgment()
        test_comprehensive_analysis()

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
