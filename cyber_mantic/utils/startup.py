"""
启动初始化模块 - 应用启动时的初始化流程

确保环境变量只加载一次，避免重复初始化
"""
import yaml
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from .config_validator import validate_and_load_config
from .logger import setup_logger, get_logger


# 全局标志：确保环境变量只加载一次
_env_loaded = False


class StartupManager:
    """启动管理器"""

    def __init__(self, config_file: str = "config.yaml", env_file: str = ".env"):
        self.config_file = config_file
        self.env_file = env_file
        self.config: Optional[Dict[str, Any]] = None
        self.logger = None

    def initialize(self) -> bool:
        """
        初始化应用

        Returns:
            是否成功初始化
        """
        print("="*60)
        print("赛博玄数 - 多理论术数智能预测系统")
        print("="*60)
        print()

        # 1. 加载环境变量
        print("[1/4] 加载环境变量...")
        self._load_env()

        # 2. 加载配置文件
        print("[2/4] 加载配置文件...")
        if not self._load_config():
            return False

        # 3. 验证配置
        print("[3/4] 验证配置...")
        if not self._validate_config():
            return False

        # 4. 初始化日志系统
        print("[4/4] 初始化日志系统...")
        self._setup_logging()

        print()
        print("✓ 系统初始化完成")
        print("="*60)
        print()

        return True

    def _load_env(self):
        """加载环境变量（确保只加载一次）"""
        global _env_loaded

        # 如果已经加载过，跳过
        if _env_loaded:
            print(f"  ✓ 环境变量已加载（跳过重复加载）")
            return

        env_path = Path(self.env_file)

        if not env_path.exists():
            print(f"  提示: 环境变量文件 {self.env_file} 不存在")
            print(f"  可以创建 {self.env_file} 文件来存储API密钥")
            _env_loaded = True  # 标记为已处理，即使文件不存在
            return

        try:
            from dotenv import load_dotenv
            load_dotenv(env_path)
            _env_loaded = True
            print(f"  ✓ 已加载环境变量: {self.env_file}")
        except ImportError:
            print("  警告: python-dotenv 未安装，跳过 .env 文件加载")
            _env_loaded = True
        except Exception as e:
            print(f"  警告: 加载 .env 文件失败: {e}")
            _env_loaded = True

    def _load_config(self) -> bool:
        """加载配置文件"""
        config_path = Path(self.config_file)

        if not config_path.exists():
            print(f"  ✗ 配置文件不存在: {self.config_file}")
            print(f"  请创建 {self.config_file} 配置文件")
            return False

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            print(f"  ✓ 已加载配置: {self.config_file}")
            return True
        except Exception as e:
            print(f"  ✗ 加载配置文件失败: {e}")
            return False

    def _validate_config(self) -> bool:
        """验证配置"""
        if not self.config:
            print("  ✗ 配置为空")
            return False

        is_valid, validated_config, summary = validate_and_load_config(self.config)

        # 应用验证后的配置（包含默认值）
        self.config = validated_config

        # 打印验证摘要
        print()
        print(summary)
        print()

        if not is_valid:
            print("  ✗ 配置验证失败，请修正上述错误后重试")
            return False

        print("  ✓ 配置验证通过")
        return True

    def _setup_logging(self):
        """设置日志系统"""
        logging_config = self.config.get("logging", {})

        try:
            setup_logger(
                level=logging_config.get("level", "INFO"),
                log_to_file=logging_config.get("log_to_file", True),
                log_dir=logging_config.get("log_dir", "logs"),
                max_file_size=logging_config.get("max_file_size", "10MB"),
                backup_count=logging_config.get("backup_count", 5),
                log_calculations=logging_config.get("log_calculations", True)
            )

            self.logger = get_logger()
            print("  ✓ 日志系统已初始化")

            # 记录启动
            self.logger.info("="*60)
            self.logger.info("赛博玄数系统启动")
            self.logger.info("="*60)
            self.logger.info(f"配置文件: {self.config_file}")
            self.logger.info(f"日志级别: {logging_config.get('level', 'INFO')}")

        except Exception as e:
            print(f"  警告: 日志系统初始化失败: {e}")
            print("  系统将继续运行，但不会记录日志")

    def get_config(self) -> Dict[str, Any]:
        """
        获取配置

        Returns:
            配置字典
        """
        return self.config or {}

    def shutdown(self):
        """关闭系统"""
        if self.logger:
            self.logger.info("="*60)
            self.logger.info("赛博玄数系统关闭")
            self.logger.info("="*60)

        print()
        print("="*60)
        print("感谢使用赛博玄数")
        print("="*60)


def initialize_application(
    config_file: str = "config.yaml",
    env_file: str = ".env"
) -> Optional[Dict[str, Any]]:
    """
    初始化应用（便捷函数）

    Args:
        config_file: 配置文件路径
        env_file: 环境变量文件路径

    Returns:
        配置字典（如果初始化成功），否则返回None
    """
    manager = StartupManager(config_file, env_file)

    if manager.initialize():
        return manager.get_config()
    else:
        sys.exit(1)
