"""
提示词模板加载器

统一加载和渲染提示词模板，支持变量替换。
"""

import re
from pathlib import Path
from typing import Dict, Any, Optional


# prompts目录路径
PROMPTS_DIR = Path(__file__).parent


def load_prompt(template_name: str, context: Optional[Dict[str, Any]] = None) -> str:
    """
    加载并渲染提示词模板

    Args:
        template_name: 模板名（如 "conversation/greeting.md"）
        context: 模板变量字典

    Returns:
        渲染后的提示词字符串

    Raises:
        FileNotFoundError: 模板文件不存在

    示例:
        >>> load_prompt("conversation/greeting.md", {"current_time": "2026-01-09 14:30"})
    """
    template_path = PROMPTS_DIR / template_name

    if not template_path.exists():
        raise FileNotFoundError(f"模板不存在: {template_name}")

    content = template_path.read_text(encoding='utf-8')

    if context:
        content = render_template(content, context)

    return content


def render_template(template: str, context: Dict[str, Any]) -> str:
    """
    渲染模板，替换变量

    支持两种语法：
    - {{variable}} - Jinja风格
    - $variable 或 ${variable} - Shell风格

    Args:
        template: 模板字符串
        context: 变量字典

    Returns:
        渲染后的字符串
    """
    result = template

    # 替换 {{variable}} 语法
    for key, value in context.items():
        pattern = r'\{\{\s*' + re.escape(key) + r'\s*\}\}'
        result = re.sub(pattern, str(value), result)

    # 替换 $variable 和 ${variable} 语法
    for key, value in context.items():
        # ${variable} 语法
        result = result.replace(f'${{{key}}}', str(value))
        # $variable 语法（注意边界）
        result = re.sub(r'\$' + re.escape(key) + r'(?![a-zA-Z0-9_])', str(value), result)

    return result


def get_prompt_path(template_name: str) -> Path:
    """获取模板的完整路径"""
    return PROMPTS_DIR / template_name


def prompt_exists(template_name: str) -> bool:
    """检查模板是否存在"""
    return (PROMPTS_DIR / template_name).exists()


def list_prompts(category: Optional[str] = None) -> list:
    """
    列出所有提示词模板

    Args:
        category: 可选的分类筛选（如 "conversation", "analysis"）

    Returns:
        模板文件路径列表
    """
    if category:
        search_path = PROMPTS_DIR / category
        if not search_path.exists():
            return []
        return list(search_path.glob("*.md"))
    else:
        return list(PROMPTS_DIR.glob("**/*.md"))


# 预定义的模板常量
class PromptTemplates:
    """提示词模板常量"""

    # 对话相关
    GREETING = "conversation/greeting.md"
    CLARIFICATION = "conversation/clarification.md"
    FOLLOWUP = "conversation/followup.md"
    SUMMARY = "conversation/summary.md"

    # 分析相关
    COMPREHENSIVE = "analysis/comprehensive.md"
    XIAOLIU = "analysis/xiaoliu.md"
    BAZI_DEFAULT = "analysis/bazi/default.md"
    QIMEN = "analysis/qimen.md"
    ZIWEI = "analysis/ziwei.md"

    # 增强验证
    INPUT_VALIDATE = "enhance/input_validate.md"
    SMART_UNDERSTAND = "enhance/smart_understand.md"
    TIME_EXPRESSION = "enhance/time_expression.md"
    QUESTION_TYPE = "enhance/question_type.md"

    # 验证问题
    VERIFICATION_QUESTIONS = "verification/questions_gen.md"


# 便捷函数
def load_greeting(current_time: str) -> str:
    """加载开场白模板"""
    return load_prompt(PromptTemplates.GREETING, {"current_time": current_time})


def load_clarification(missing_info: str, collected_info: str) -> str:
    """加载澄清追问模板"""
    return load_prompt(PromptTemplates.CLARIFICATION, {
        "missing_info": missing_info,
        "collected_info": collected_info
    })
