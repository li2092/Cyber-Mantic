"""
赛博玄数 - 主程序入口
"""
import sys
import asyncio
import yaml
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# 导入模块
from models import UserInput
from core import DecisionEngine
from utils.startup import initialize_application
from utils.logger import get_logger


def load_config(config_path: str = "config.yaml") -> dict:
    """
    加载配置文件

    注意：环境变量的加载由 initialize_application() 统一处理，
    此函数仅用于交互模式的简化配置加载。

    Args:
        config_path: 配置文件路径

    Returns:
        配置字典
    """
    # 环境变量由 startup.py 统一加载，这里检查是否需要加载
    from utils.startup import _env_loaded
    if not _env_loaded:
        load_dotenv()

    # 加载YAML配置
    config_file = Path(config_path)
    if not config_file.exists():
        print(f"警告：配置文件 {config_path} 不存在，使用默认配置")
        return {}

    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # 替换环境变量
    import os
    if 'api' in config:
        for key in ['claude_api_key', 'deepseek_api_key', 'gemini_api_key', 'kimi_api_key']:
            if key in config['api']:
                value = config['api'][key]
                if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                    env_var = value[2:-1]
                    config['api'][key] = os.getenv(env_var, '')

    return config


async def run_example():
    """运行示例分析"""
    # 使用新的初始化系统
    config = initialize_application()
    logger = get_logger()

    logger.info("开始示例分析")

    # 创建决策引擎
    engine = DecisionEngine(config)

    # 创建示例用户输入
    user_input = UserInput(
        question_type="事业",
        question_description="我想知道2025年的事业运势如何，是否适合换工作",
        birth_year=1990,
        birth_month=6,
        birth_day=15,
        birth_hour=10,
        gender="male",
        numbers=[3, 7, 5],
        current_time=datetime.now()
    )

    print("\n用户问题：")
    print(f"  类别：{user_input.question_type}")
    print(f"  描述：{user_input.question_description}")
    print(f"  出生：{user_input.birth_year}年{user_input.birth_month}月{user_input.birth_day}日 {user_input.birth_hour}时")
    print(f"  性别：{user_input.gender}")
    print(f"  随机数：{user_input.numbers}")

    # 执行分析
    try:
        report = await engine.analyze(user_input)

        # 显示报告
        print("\n" + "=" * 70)
        print("分析报告")
        print("=" * 70)

        print(f"\n报告ID: {report.report_id}")
        print(f"创建时间: {report.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"选用理论: {', '.join(report.selected_theories)}")
        print(f"综合置信度: {report.overall_confidence:.2%}")

        print("\n" + "-" * 70)
        print("执行摘要")
        print("-" * 70)
        print(report.executive_summary)

        print("\n" + "-" * 70)
        print("各理论分析结果")
        print("-" * 70)
        for result in report.theory_results:
            print(f"\n【{result.theory_name}】")
            print(f"判断：{result.judgment}（程度：{result.judgment_level:.2f}，置信度：{result.confidence:.2%}）")
            print(f"解读：")
            print(result.interpretation[:200] + "..." if len(result.interpretation) > 200 else result.interpretation)

        if report.conflict_info.has_conflict:
            print("\n" + "-" * 70)
            print("冲突检测")
            print("-" * 70)
            for conflict in report.conflict_info.conflicts:
                print(f"- {conflict['type']}: {conflict['details']}")

        if report.limitations:
            print("\n" + "-" * 70)
            print("局限性说明")
            print("-" * 70)
            for limitation in report.limitations:
                print(f"- {limitation}")

        # 保存报告（可选）
        save_report = input("\n是否保存报告到文件？(y/n): ")
        if save_report.lower() == 'y':
            output_file = f"report_{report.report_id[:8]}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report.to_json())
            print(f"报告已保存到: {output_file}")

    except Exception as e:
        print(f"\n错误：分析过程中发生异常")
        print(f"详细信息：{e}")
        import traceback
        traceback.print_exc()


def interactive_mode():
    """交互模式"""
    print("=" * 70)
    print(" " * 20 + "赛博玄数 - 交互模式")
    print("=" * 70)

    # 加载配置
    config = load_config()

    # 收集用户输入
    print("\n请输入您的信息：")

    question_types = ["事业", "财运", "感情", "婚姻", "健康", "学业", "人际", "择时", "决策", "性格"]
    print(f"\n问题类别：{', '.join([f'{i+1}.{t}' for i, t in enumerate(question_types)])}")
    type_index = int(input("请选择（输入数字）: ")) - 1
    question_type = question_types[type_index]

    question_description = input("请描述您的问题: ")

    # 出生信息
    print("\n出生信息（可选，直接回车跳过）:")
    birth_year = input("出生年份: ")
    birth_month = input("出生月份: ")
    birth_day = input("出生日期: ")
    birth_hour = input("出生时辰（0-23）: ")

    # 随机数
    numbers_input = input("\n请输入3个随机数字（用空格分隔，如：3 7 5）: ")

    # 创建用户输入对象
    user_input = UserInput(
        question_type=question_type,
        question_description=question_description,
        current_time=datetime.now()
    )

    if birth_year and birth_month and birth_day:
        user_input.birth_year = int(birth_year)
        user_input.birth_month = int(birth_month)
        user_input.birth_day = int(birth_day)

    if birth_hour:
        user_input.birth_hour = int(birth_hour)

    if numbers_input:
        user_input.numbers = [int(n) for n in numbers_input.split()]

    # 执行分析
    engine = DecisionEngine(config)
    report = asyncio.run(engine.analyze(user_input))

    # 显示简化结果
    print("\n" + "=" * 70)
    print("分析完成")
    print("=" * 70)
    print(f"\n选用理论: {', '.join(report.selected_theories)}")
    print(f"综合置信度: {report.overall_confidence:.2%}")
    print(f"\n{report.executive_summary}")


def main():
    """主函数"""
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        # 交互模式
        interactive_mode()
    else:
        # 示例模式
        print("\n提示：使用 --interactive 参数启动交互模式")
        print("当前运行示例分析...\n")
        asyncio.run(run_example())


if __name__ == "__main__":
    main()
