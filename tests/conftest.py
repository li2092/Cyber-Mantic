"""
Pytest配置文件

配置测试环境，包括mock PyQt6组件以支持无头环境测试
"""
import sys
from unittest.mock import MagicMock


# Mock PyQt6模块以支持无头环境测试
class MockQtModule:
    """Mock Qt模块基类"""
    def __getattr__(self, name):
        return MagicMock()


# 在导入任何模块之前mock PyQt6
sys.modules['PyQt6'] = MockQtModule()
sys.modules['PyQt6.QtWidgets'] = MockQtModule()
sys.modules['PyQt6.QtCore'] = MockQtModule()
sys.modules['PyQt6.QtGui'] = MockQtModule()


# Pytest配置
def pytest_configure(config):
    """Pytest启动配置"""
    import os
    # 设置Qt平台为offscreen
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    # 禁用Qt插件警告
    os.environ['QT_LOGGING_RULES'] = '*.debug=false;qt.qpa.*=false'


def pytest_collection_modifyitems(items):
    """修改测试收集项"""
    pass
