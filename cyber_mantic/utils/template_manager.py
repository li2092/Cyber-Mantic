"""
TemplateManager - 报告模板管理器

支持用户自定义报告模板，保存5条历史记录
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from utils.logger import get_logger


class ReportTemplate:
    """报告模板数据类"""

    def __init__(
        self,
        template_id: str,
        name: str,
        user_requirements: str,
        generated_prompt: str,
        created_at: datetime,
        is_default: bool = False
    ):
        self.template_id = template_id
        self.name = name
        self.user_requirements = user_requirements  # 用户描述的需求
        self.generated_prompt = generated_prompt  # AI生成的prompt模板
        self.created_at = created_at
        self.is_default = is_default

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "template_id": self.template_id,
            "name": self.name,
            "user_requirements": self.user_requirements,
            "generated_prompt": self.generated_prompt,
            "created_at": self.created_at.isoformat(),
            "is_default": self.is_default
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReportTemplate':
        """从字典创建"""
        return cls(
            template_id=data["template_id"],
            name=data["name"],
            user_requirements=data["user_requirements"],
            generated_prompt=data["generated_prompt"],
            created_at=datetime.fromisoformat(data["created_at"]),
            is_default=data.get("is_default", False)
        )


class TemplateManager:
    """报告模板管理器"""

    MAX_CUSTOM_TEMPLATES = 5  # 最多保存5条自定义模板

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化模板管理器

        Args:
            config_path: 配置文件路径，默认为 config/report_templates.json
        """
        if config_path is None:
            # 默认配置路径
            project_root = Path(__file__).parent.parent
            config_path = project_root / "config" / "report_templates.json"

        self.config_path = Path(config_path)
        self.logger = get_logger(__name__)
        self.templates: List[ReportTemplate] = []
        self.current_template_id: Optional[str] = None
        self._load_templates()

    def _load_templates(self):
        """加载模板配置"""
        if not self.config_path.exists():
            # 创建默认模板
            self._create_default_template()
            self._save_templates()
            return

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 加载模板列表
            self.templates = [
                ReportTemplate.from_dict(t) for t in data.get("templates", [])
            ]

            # 加载当前选择的模板ID
            self.current_template_id = data.get("current_template_id")

            # 如果没有默认模板，创建一个
            if not any(t.is_default for t in self.templates):
                self._create_default_template()
                self._save_templates()

            self.logger.info(f"已加载 {len(self.templates)} 个报告模板")

        except Exception as e:
            self.logger.error(f"加载模板配置失败: {e}，使用默认配置")
            self._create_default_template()
            self._save_templates()

    def _create_default_template(self):
        """创建默认模板"""
        default_template = ReportTemplate(
            template_id="default",
            name="默认模板",
            user_requirements="标准的综合分析报告，包含执行摘要、过去三年回顾、未来两年预测、行动建议",
            generated_prompt="",  # 默认模板使用系统内置的COMPREHENSIVE_REPORT
            created_at=datetime.now(),
            is_default=True
        )
        self.templates.append(default_template)
        self.current_template_id = "default"

    def _save_templates(self):
        """保存模板配置"""
        try:
            # 确保目录存在
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "current_template_id": self.current_template_id,
                "templates": [t.to_dict() for t in self.templates]
            }

            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            self.logger.info("模板配置已保存")
            return True

        except Exception as e:
            self.logger.error(f"保存模板配置失败: {e}")
            return False

    def add_template(
        self,
        name: str,
        user_requirements: str,
        generated_prompt: str
    ) -> ReportTemplate:
        """
        添加新的自定义模板

        Args:
            name: 模板名称
            user_requirements: 用户需求描述
            generated_prompt: AI生成的prompt模板

        Returns:
            新创建的模板对象
        """
        # 检查是否超过最大数量（不包括默认模板）
        custom_templates = [t for t in self.templates if not t.is_default]
        if len(custom_templates) >= self.MAX_CUSTOM_TEMPLATES:
            # 删除最旧的自定义模板
            oldest_custom = min(custom_templates, key=lambda t: t.created_at)
            self.templates.remove(oldest_custom)
            self.logger.info(f"已删除最旧的模板: {oldest_custom.name}")

        # 创建新模板
        import uuid
        template = ReportTemplate(
            template_id=str(uuid.uuid4()),
            name=name,
            user_requirements=user_requirements,
            generated_prompt=generated_prompt,
            created_at=datetime.now(),
            is_default=False
        )

        self.templates.append(template)
        self._save_templates()

        self.logger.info(f"已添加新模板: {name}")
        return template

    def get_template(self, template_id: str) -> Optional[ReportTemplate]:
        """
        获取指定模板

        Args:
            template_id: 模板ID

        Returns:
            模板对象，如果不存在返回None
        """
        for template in self.templates:
            if template.template_id == template_id:
                return template
        return None

    def get_current_template(self) -> ReportTemplate:
        """
        获取当前选择的模板

        Returns:
            当前模板对象
        """
        if self.current_template_id:
            template = self.get_template(self.current_template_id)
            if template:
                return template

        # 如果当前模板不存在，返回默认模板
        for template in self.templates:
            if template.is_default:
                return template

        # 极端情况：没有默认模板，创建一个
        self._create_default_template()
        return self.templates[-1]

    def set_current_template(self, template_id: str) -> bool:
        """
        设置当前使用的模板

        Args:
            template_id: 模板ID

        Returns:
            是否设置成功
        """
        if self.get_template(template_id) is None:
            self.logger.error(f"模板不存在: {template_id}")
            return False

        self.current_template_id = template_id
        self._save_templates()

        self.logger.info(f"已切换到模板: {template_id}")
        return True

    def delete_template(self, template_id: str) -> bool:
        """
        删除模板

        Args:
            template_id: 模板ID

        Returns:
            是否删除成功
        """
        template = self.get_template(template_id)
        if template is None:
            self.logger.error(f"模板不存在: {template_id}")
            return False

        # 不能删除默认模板
        if template.is_default:
            self.logger.error("不能删除默认模板")
            return False

        # 如果删除的是当前模板，切换到默认模板
        if self.current_template_id == template_id:
            for t in self.templates:
                if t.is_default:
                    self.current_template_id = t.template_id
                    break

        self.templates.remove(template)
        self._save_templates()

        self.logger.info(f"已删除模板: {template.name}")
        return True

    def get_all_templates(self) -> List[ReportTemplate]:
        """获取所有模板"""
        return self.templates.copy()

    def get_custom_templates(self) -> List[ReportTemplate]:
        """获取所有自定义模板（不包括默认模板）"""
        return [t for t in self.templates if not t.is_default]

    def reset_to_default(self) -> bool:
        """重置为默认模板"""
        for template in self.templates:
            if template.is_default:
                self.current_template_id = template.template_id
                self._save_templates()
                self.logger.info("已重置为默认模板")
                return True

        # 如果没有默认模板，创建一个
        self._create_default_template()
        self._save_templates()
        return True

    def get_template_preview(self, template: ReportTemplate) -> str:
        """
        获取模板预览（用于UI显示）

        Args:
            template: 模板对象

        Returns:
            预览文本
        """
        preview = f"""**{template.name}**

📝 用户需求：
{template.user_requirements}

📅 创建时间：{template.created_at.strftime('%Y-%m-%d %H:%M')}

"""
        if template.is_default:
            preview += "🔖 默认模板\n"

        if template.generated_prompt:
            # 提取关键信息
            preview += "\n💡 报告将包含：\n"
            if "过去" in template.user_requirements or "回顾" in template.user_requirements:
                preview += "• 过去事件回顾分析\n"
            if "未来" in template.user_requirements or "预测" in template.user_requirements:
                preview += "• 未来趋势预测\n"
            if "月度" in template.user_requirements or "每月" in template.user_requirements:
                preview += "• 月度运势详解\n"
            if "通俗" in template.user_requirements or "白话" in template.user_requirements:
                preview += "• 通俗化语言解读\n"

        return preview
