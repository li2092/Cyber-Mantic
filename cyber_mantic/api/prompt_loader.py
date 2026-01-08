"""
Prompt加载器 - 从Markdown文件加载Prompt模板

功能：
- 从 prompts/ 目录加载Prompt模板
- 支持 {{variable}} 语法的变量替换
- 支持A/B测试变体
- 缓存机制提高性能
- 热重载支持

设计参考：docs/design/04_Prompt管理方案.md
"""
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from utils.logger import get_logger


# 默认Prompts目录路径
DEFAULT_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


class PromptLoader:
    """
    Prompt加载器

    使用方法：
        loader = PromptLoader()
        prompt = loader.get("analysis", "bazi", birth_info="...", gender="男")
    """

    def __init__(self, prompts_dir: Optional[Path] = None):
        """
        初始化Prompt加载器

        Args:
            prompts_dir: Prompt目录路径，默认使用 docs/prompts/
        """
        self.prompts_dir = Path(prompts_dir) if prompts_dir else DEFAULT_PROMPTS_DIR
        self.logger = get_logger(__name__)
        self._cache: Dict[str, str] = {}
        self._variants: Dict[str, str] = {}

        self.logger.info(f"PromptLoader初始化，目录: {self.prompts_dir}")

    def get(self, category: str, name: str, **variables) -> str:
        """
        获取Prompt，支持变体和变量替换

        Args:
            category: 类别（如 "analysis", "conversation"）
            name: 名称（如 "bazi", "greeting"）
            **variables: 要替换的变量

        Returns:
            处理后的Prompt内容

        Examples:
            >>> loader.get("analysis", "bazi", birth_info="1990年5月20日", gender="男")
            >>> loader.get("conversation", "greeting", current_time="下午好")
        """
        # 确定使用哪个变体
        key = f"{category}/{name}"
        variant = self._variants.get(key, "default")

        # 构建路径
        path = self._resolve_path(category, name, variant)

        # 读取并缓存
        content = self._load_template(str(path))

        # 变量替换
        return self._substitute_variables(content, variables)

    def load(self, name: str, **variables) -> str:
        """
        加载Prompt（兼容旧接口）

        Args:
            name: Prompt名称（如 "analysis/bazi" 或 "system"）
            **variables: 变量

        Returns:
            处理后的Prompt
        """
        # 解析 category/name 格式
        if "/" in name:
            parts = name.split("/", 1)
            return self.get(parts[0], parts[1], **variables)
        else:
            # 尝试作为文件名加载
            path = self.prompts_dir / f"{name}.md"
            if path.exists():
                content = self._load_template(str(path))
                return self._substitute_variables(content, variables)
            raise FileNotFoundError(f"Prompt not found: {name}")

    def _resolve_path(self, category: str, name: str, variant: str = "default") -> Path:
        """
        解析Prompt文件路径

        支持两种结构：
        1. 单文件：analysis/ziwei.md
        2. 多变体目录：analysis/bazi/default.md

        Args:
            category: 类别
            name: 名称
            variant: 变体名称

        Returns:
            Prompt文件路径
        """
        # 首先检查是否是目录（多变体情况）
        dir_path = self.prompts_dir / category / name
        if dir_path.is_dir():
            return dir_path / f"{variant}.md"

        # 否则是单文件
        return self.prompts_dir / category / f"{name}.md"

    def _load_template(self, path: str) -> str:
        """
        加载模板内容（带缓存）

        Args:
            path: 文件路径

        Returns:
            模板内容
        """
        if path in self._cache:
            return self._cache[path]

        try:
            file_path = Path(path)
            if not file_path.exists():
                self.logger.warning(f"Prompt文件不存在: {path}")
                return f"[Prompt文件不存在: {path}]"

            content = file_path.read_text(encoding="utf-8")
            self._cache[path] = content
            self.logger.debug(f"加载Prompt: {path}")
            return content

        except Exception as e:
            self.logger.error(f"加载Prompt失败: {path}, 错误: {e}")
            return f"[加载Prompt失败: {e}]"

    def _substitute_variables(self, template: str, variables: Dict[str, Any]) -> str:
        """
        替换模板中的变量

        使用 {{variable_name}} 语法

        Args:
            template: 模板内容
            variables: 变量字典

        Returns:
            替换后的内容
        """
        result = template
        for var_name, value in variables.items():
            pattern = r'\{\{' + re.escape(var_name) + r'\}\}'
            result = re.sub(pattern, str(value) if value is not None else '', result)
        return result

    def set_variant(self, key: str, variant: str):
        """
        设置变体

        Args:
            key: 路径键（如 "analysis/bazi"）
            variant: 变体名称（如 "variant_a"）
        """
        self._variants[key] = variant
        # 清除相关缓存
        self._clear_cache_for_key(key)
        self.logger.info(f"设置变体: {key} -> {variant}")

    def get_variant(self, key: str) -> str:
        """
        获取当前变体设置

        Args:
            key: 路径键

        Returns:
            当前变体名称，默认返回 "default"
        """
        return self._variants.get(key, "default")

    def clear_variant(self, name: str):
        """
        清除变体设置（兼容旧接口）

        Args:
            name: Prompt名称
        """
        if name in self._variants:
            del self._variants[name]
            self.logger.info(f"清除Prompt变体: {name}")

    def list_variants(self, category: str, name: str) -> List[str]:
        """
        列出可用变体

        Args:
            category: 类别
            name: 名称

        Returns:
            变体名称列表
        """
        dir_path = self.prompts_dir / category / name
        if dir_path.is_dir():
            return [p.stem for p in dir_path.glob("*.md")]
        return ["default"]

    def list_prompts(self, category: Optional[str] = None) -> Dict[str, List[str]]:
        """
        列出所有可用的Prompt

        Args:
            category: 可选，指定类别

        Returns:
            {category: [name1, name2, ...], ...}
        """
        result = {}

        if category:
            categories = [category]
        else:
            categories = [d.name for d in self.prompts_dir.iterdir()
                         if d.is_dir() and not d.name.startswith('.')]

        for cat in categories:
            cat_path = self.prompts_dir / cat
            if not cat_path.exists():
                continue

            names = []
            for item in cat_path.iterdir():
                if item.is_file() and item.suffix == ".md":
                    names.append(item.stem)
                elif item.is_dir():
                    names.append(item.name)
            result[cat] = sorted(names)

        return result

    def preview(self, category: str, name: str, variant: Optional[str] = None) -> str:
        """
        预览Prompt原始内容（不替换变量）

        Args:
            category: 类别
            name: 名称
            variant: 变体名称（可选）

        Returns:
            原始Prompt内容
        """
        if variant is None:
            variant = self.get_variant(f"{category}/{name}")

        path = self._resolve_path(category, name, variant)
        return self._load_template(str(path))

    def get_prompt_info(self, category: str, name: str) -> Dict[str, Any]:
        """
        获取Prompt元信息

        Args:
            category: 类别
            name: 名称

        Returns:
            元信息字典
        """
        variants = self.list_variants(category, name)
        path = self._resolve_path(category, name, "default")

        content = ""
        if path.exists():
            content = path.read_text(encoding="utf-8")

        # 提取变量
        variables = re.findall(r'\{\{([a-z_]+)\}\}', content)

        return {
            "category": category,
            "name": name,
            "path": str(path),
            "variants": variants,
            "variables": list(set(variables)),
            "size": len(content)
        }

    def _clear_cache_for_key(self, key: str):
        """清除指定键相关的缓存"""
        to_remove = [k for k in self._cache if key in k]
        for k in to_remove:
            del self._cache[k]

    def reload(self, name: Optional[str] = None):
        """
        热重载 - 清除缓存

        Args:
            name: 可选，指定清除的Prompt名称。不指定则清除全部
        """
        if name:
            self._clear_cache_for_key(name)
        else:
            self._cache.clear()
        self.logger.info("Prompt缓存已清除")

    def clear_cache(self):
        """清除缓存（reload的别名）"""
        self.reload()

    def load_variants_from_config(self, config: Dict[str, str]):
        """
        从配置加载变体设置

        Args:
            config: 变体配置 {"analysis/bazi": "variant_a", ...}
        """
        for key, variant in config.items():
            self._variants[key] = variant
        self.logger.info(f"加载变体配置: {len(config)}项")

    def get_system_prompt(self, include_safety: bool = True) -> str:
        """
        获取系统级Prompt（AI人设 + 安全准则）

        Args:
            include_safety: 是否包含安全准则

        Returns:
            系统级Prompt
        """
        persona = self._load_template(str(self.prompts_dir / "system" / "base_persona.md"))

        if include_safety:
            safety = self._load_template(str(self.prompts_dir / "system" / "safety_guidelines.md"))
            return f"{persona}\n\n---\n\n{safety}"

        return persona


# 全局单例
_prompt_loader: Optional[PromptLoader] = None


def get_prompt_loader() -> PromptLoader:
    """获取全局PromptLoader实例"""
    global _prompt_loader
    if _prompt_loader is None:
        _prompt_loader = PromptLoader()
    return _prompt_loader


def load_prompt(category: str, name: str, **variables) -> str:
    """
    便捷函数：加载并格式化Prompt

    Args:
        category: 类别
        name: 名称
        **variables: 变量

    Returns:
        处理后的Prompt
    """
    return get_prompt_loader().get(category, name, **variables)
