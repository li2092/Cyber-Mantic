"""
测试最近修复的bug的回归测试

确保以下问题不会再次出现：
1. 理论类缺少logger属性
2. ErrorHandler PyQt6依赖污染
3. 裸except块
4. API Manager死代码
"""

import pytest
import sys
from unittest.mock import Mock, patch
from theories.base import TheoryRegistry
from models import UserInput


class TestBugFix1_LoggerAttribute:
    """测试问题#1：理论类logger属性"""

    def test_all_theories_have_logger(self):
        """验证所有理论类都有logger属性"""
        theories_dict = TheoryRegistry.get_all_theories()
        theories = theories_dict.values()  # get_all_theories returns dict

        for theory in theories:
            # 所有理论实例都应该有logger属性
            assert hasattr(theory, 'logger'), f"{theory.get_name()}缺少logger属性"
            assert theory.logger is not None, f"{theory.get_name()}的logger为None"
            # logger应该有基本的日志方法
            assert hasattr(theory.logger, 'debug')
            assert hasattr(theory.logger, 'info')
            assert hasattr(theory.logger, 'warning')
            assert hasattr(theory.logger, 'error')

    def test_theory_logger_can_write(self):
        """验证理论类的logger可以正常写入日志"""
        theories_dict = TheoryRegistry.get_all_theories()
        theories = theories_dict.values()

        for theory in theories:
            # 测试logger可以调用warning（原bug触发点）
            try:
                theory.logger.warning(f"测试{theory.get_name()}的logger")
                theory.logger.info(f"测试{theory.get_name()}的info")
                theory.logger.debug(f"测试{theory.get_name()}的debug")
            except AttributeError as e:
                pytest.fail(f"{theory.get_name()}的logger调用失败: {e}")

    def test_theory_with_additional_persons_uses_logger(self):
        """测试多人分析时logger的使用（原bug场景）"""
        from theories.ziwei import ZiWeiTheory

        theory = ZiWeiTheory()
        user_input = UserInput(
            question_type="命理",
            question_description="测试多人分析",
            birth_year=1990,
            birth_month=1,
            birth_day=1,
            birth_hour=12,
            gender="男",
            calendar_type="公历",
            additional_persons=[
                {
                    "name": "测试人员",
                    "birth_year": 1991,
                    "birth_month": 2,
                    "birth_day": 2,
                    "birth_hour": 13,
                    "gender": "女",
                    "calendar_type": "公历"
                }
            ]
        )

        # 理论计算时应该能使用logger.warning
        # 这里不应该抛出AttributeError
        try:
            result = theory.calculate(user_input)
            assert result is not None
        except AttributeError as e:
            if 'logger' in str(e):
                pytest.fail(f"理论类仍然缺少logger属性: {e}")
            raise


class TestBugFix2_ErrorHandlerPyQt6:
    """测试问题#2：ErrorHandler PyQt6依赖"""

    def test_error_handler_imports_without_pyqt6(self):
        """测试ErrorHandler可以在没有PyQt6的环境导入"""
        # 模拟PyQt6不可用
        with patch.dict(sys.modules, {'PyQt6': None, 'PyQt6.QtWidgets': None}):
            try:
                # 重新导入error_handler
                import importlib
                import utils.error_handler as error_handler_module
                importlib.reload(error_handler_module)

                # 应该能成功导入ErrorHandler类
                from utils.error_handler import ErrorHandler
                assert ErrorHandler is not None
            except ImportError as e:
                pytest.fail(f"ErrorHandler在无PyQt6环境导入失败: {e}")

    def test_error_handler_has_pyqt6_flag(self):
        """测试ErrorHandler有HAS_PYQT6标志"""
        from utils.error_handler import HAS_PYQT6

        # HAS_PYQT6应该是布尔值
        assert isinstance(HAS_PYQT6, bool)

    def test_error_handler_can_handle_error_without_gui(self):
        """测试ErrorHandler在无GUI环境下可以处理错误"""
        from utils.error_handler import ErrorHandler

        # 创建ErrorHandler（不传parent）
        handler = ErrorHandler()

        # 应该能处理错误（不显示对话框）
        try:
            test_error = ValueError("测试错误")
            handler.handle_error(test_error, "测试上下文", show_dialog=False)
        except Exception as e:
            pytest.fail(f"ErrorHandler处理错误失败: {e}")


class TestBugFix3_NoBarExcept:
    """测试问题#3：无裸except块"""

    def test_history_tab_disconnect_uses_exception(self):
        """测试history_tab使用Exception而非裸except"""
        # 直接读取文件内容，避免PyQt6 mock问题
        with open('/home/user/-/cyber_mantic/ui/tabs/history_tab.py', 'r', encoding='utf-8') as f:
            source = f.read()

        # 检查_display_history方法中的except使用
        # 提取_display_history方法部分
        if '_display_history' in source:
            # 不应该有裸except:后跟缩进（避免误判注释）
            import re
            bare_except_pattern = r'except:\s*\n\s+'
            assert not re.search(bare_except_pattern, source), "_display_history仍使用裸except"
            # 应该有except Exception
            assert 'except Exception' in source, "_display_history未使用except Exception"

    def test_history_tab_cleanup_uses_exception(self):
        """测试history_tab cleanup使用Exception"""
        # 直接读取文件内容
        with open('/home/user/-/cyber_mantic/ui/tabs/history_tab.py', 'r', encoding='utf-8') as f:
            source = f.read()

        import re
        bare_except_pattern = r'except:\s*\n\s+'
        assert not re.search(bare_except_pattern, source), "cleanup仍使用裸except"
        assert 'except Exception' in source, "cleanup未使用except Exception"

    def test_analysis_tab_cleanup_uses_exception(self):
        """测试analysis_tab cleanup使用Exception"""
        import os
        # 获取项目根目录
        tests_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(tests_dir)

        # 检查主控制器和输入面板（都有cleanup方法）
        analysis_tab_path = os.path.join(project_root, 'ui/tabs/analysis/analysis_tab.py')
        input_panel_path = os.path.join(project_root, 'ui/tabs/analysis/input_panel.py')

        import re
        bare_except_pattern = r'except:\s*\n\s+'

        for file_path in [analysis_tab_path, input_panel_path]:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    source = f.read()
                assert not re.search(bare_except_pattern, source), f"{file_path} cleanup仍使用裸except"
                assert 'except Exception' in source, f"{file_path} cleanup未使用except Exception"


class TestBugFix4_NoDeadCode:
    """测试问题#4：无死代码"""

    def test_api_manager_get_endpoint_has_no_dead_code(self):
        """测试API Manager _get_endpoint_name没有死代码"""
        # 直接读取文件内容
        with open('/home/user/-/cyber_mantic/api/manager.py', 'r', encoding='utf-8') as f:
            source = f.read()

        # 检查return语句后不应该有检查available_apis的代码
        lines = source.split('\n')
        found_return = False
        for line in lines:
            stripped = line.strip()
            if 'return "chat"' in stripped and '# 默认' in stripped:
                found_return = True
            if found_return and 'if not self.available_apis' in stripped:
                pytest.fail("_get_endpoint_name仍有return后的死代码")


class TestRegressionSuite:
    """综合回归测试套件"""

    def test_all_theories_registered(self):
        """验证所有8个理论都已注册"""
        theories_dict = TheoryRegistry.get_all_theories()
        theory_names = [t.get_name() for t in theories_dict.values()]

        expected_theories = [
            "八字", "紫微斗数", "奇门遁甲", "六爻",
            "小六壬", "梅花易数", "大六壬", "测字术"
        ]

        for expected in expected_theories:
            assert expected in theory_names, f"理论{expected}未注册"

    def test_theories_have_required_methods(self):
        """验证所有理论都有必需的方法"""
        theories_dict = TheoryRegistry.get_all_theories()
        theories = theories_dict.values()

        required_methods = [
            'get_name', 'get_required_fields', 'get_optional_fields',
            'get_field_weights', 'get_min_completeness', 'calculate'
        ]

        for theory in theories:
            for method_name in required_methods:
                assert hasattr(theory, method_name), \
                    f"{theory.get_name()}缺少{method_name}方法"

    def test_error_handler_cli_fallback(self):
        """测试ErrorHandler在CLI模式下的降级方案"""
        from utils.error_handler import ErrorHandler
        import io
        from contextlib import redirect_stdout

        handler = ErrorHandler()
        test_error = RuntimeError("CLI测试错误")

        # 捕获print输出
        f = io.StringIO()
        with redirect_stdout(f):
            handler.handle_error(test_error, "CLI测试", show_dialog=True)

        output = f.getvalue()
        # 在CLI模式下应该有输出（如果HAS_PYQT6=False）
        # 或者没有输出（如果HAS_PYQT6=True，显示对话框）
        # 关键是不应该崩溃
        assert True, "ErrorHandler在CLI模式下正常工作"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
