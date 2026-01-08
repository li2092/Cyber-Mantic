"""
ErrorHandler - 统一错误处理工具

提供友好的错误提示和操作建议，避免软件卡死
"""

# 条件导入PyQt6，支持CLI模式和非GUI环境
try:
    from PyQt6.QtWidgets import QMessageBox, QWidget
    from PyQt6.QtCore import QTimer, Qt
    HAS_PYQT6 = True
except ImportError:
    HAS_PYQT6 = False
    QMessageBox = None
    QWidget = None
    QTimer = None
    Qt = None

from typing import Optional, Callable
import traceback
import sys
from pathlib import Path

from utils.logger import get_logger


class ErrorHandler:
    """统一错误处理器"""

    def __init__(self, parent: Optional['QWidget'] = None):
        self.parent = parent if HAS_PYQT6 else None
        self.logger = get_logger(__name__)
        self.contact_info = "GitHub Issues: https://github.com/cyber-mantic/cyber-mantic/issues"

    def handle_error(
        self,
        error: Exception,
        context: str = "操作",
        show_dialog: bool = True,
        suggestion: Optional[str] = None
    ) -> None:
        """
        处理错误

        Args:
            error: 异常对象
            context: 错误发生的上下文（例如："AI分析"、"报告导出"）
            show_dialog: 是否显示错误对话框
            suggestion: 自定义的操作建议
        """
        error_type = type(error).__name__
        error_msg = str(error)

        # 记录详细错误日志
        self.logger.error(f"{context}失败: {error_type}: {error_msg}")
        self.logger.error(f"堆栈跟踪:\n{traceback.format_exc()}")

        if show_dialog and HAS_PYQT6:
            # 根据错误类型生成建议
            if suggestion is None:
                suggestion = self._generate_suggestion(error_type, error_msg, context)

            self.show_error_dialog(
                title=f"{context}失败",
                message=error_msg,
                suggestion=suggestion,
                error_type=error_type
            )
        elif show_dialog and not HAS_PYQT6:
            # CLI模式：打印错误信息
            print(f"\n{'='*60}")
            print(f"❌ {context}失败")
            print(f"{'='*60}")
            print(f"错误类型：{error_type}")
            print(f"错误详情：{error_msg}")
            if suggestion:
                print(f"\n💡 建议：")
                # 移除HTML标签
                clean_suggestion = suggestion.replace('<br>', '\n').replace('<code>', '').replace('</code>', '')
                print(clean_suggestion)
            print(f"{'='*60}\n")

    def show_error_dialog(
        self,
        title: str,
        message: str,
        suggestion: str,
        error_type: str = "Error"
    ) -> None:
        """
        显示错误对话框

        Args:
            title: 对话框标题
            message: 错误消息
            suggestion: 操作建议
            error_type: 错误类型
        """
        if not HAS_PYQT6:
            self.logger.warning("PyQt6不可用，无法显示错误对话框")
            return

        msg_box = QMessageBox(self.parent)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle(f"❌ {title}")

        # 主要消息
        msg_box.setText(f"<b>发生了一个错误</b>")

        # 详细信息
        detailed_text = f"""
<p><b>错误类型：</b>{error_type}</p>
<p><b>错误详情：</b>{message}</p>

<hr>

<p><b>🔧 操作建议：</b></p>
<p>{suggestion}</p>

<hr>

<p><b>📞 需要帮助？</b></p>
<p>如果问题持续存在，请联系开发者：</p>
<p>{self.contact_info}</p>
<p>请附上错误日志文件：<code>logs/cyber_mantic.log</code></p>
"""
        msg_box.setInformativeText(detailed_text)
        msg_box.setTextFormat(Qt.TextFormat.RichText)

        # 添加按钮
        msg_box.setStandardButtons(
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Help
        )
        msg_box.setDefaultButton(QMessageBox.StandardButton.Ok)

        # 点击Help按钮时显示完整堆栈
        if msg_box.exec() == QMessageBox.StandardButton.Help:
            self._show_detailed_error()

    def _generate_suggestion(
        self,
        error_type: str,
        error_msg: str,
        context: str
    ) -> str:
        """
        根据错误类型生成操作建议

        Args:
            error_type: 错误类型
            error_msg: 错误消息
            context: 错误上下文

        Returns:
            操作建议文本
        """
        # API相关错误
        if "API" in error_msg or "api" in error_msg.lower():
            return """
• 检查网络连接是否正常<br>
• 前往【设置】标签页验证API密钥是否正确<br>
• 确认API账户有足够的额度<br>
• 尝试切换到其他API（在设置中更改主API）<br>
• 如果所有API都失败，请稍后再试
"""

        # 网络相关错误
        if any(keyword in error_msg.lower() for keyword in ["timeout", "connection", "network", "refused"]):
            return """
• 检查您的网络连接<br>
• 关闭VPN或代理后重试<br>
• 检查防火墙设置<br>
• 尝试切换到其他网络环境<br>
• 稍后再试（服务器可能暂时不可用）
"""

        # 文件操作错误
        if any(keyword in error_msg.lower() for keyword in ["file", "permission", "denied", "not found"]):
            return """
• 确保程序有读写文件的权限<br>
• 检查磁盘空间是否充足<br>
• 尝试以管理员身份运行程序<br>
• 检查文件路径是否正确<br>
• 关闭其他可能占用文件的程序
"""

        # 内存/资源错误
        if any(keyword in error_msg.lower() for keyword in ["memory", "resource"]):
            return """
• 关闭其他占用内存的程序<br>
• 重启应用程序<br>
• 如果问题持续，请重启计算机<br>
• 考虑升级系统内存
"""

        # JSON/数据格式错误
        if any(keyword in error_msg.lower() for keyword in ["json", "decode", "parse"]):
            return """
• 数据格式可能损坏，请重新生成<br>
• 如果是导入的数据，请检查文件格式<br>
• 尝试删除缓存文件后重试<br>
• 联系开发者报告此问题
"""

        # AI分析相关错误
        if "分析" in context or "AI" in context:
            return """
• 检查输入信息是否完整<br>
• 确认API配置正确（前往【设置】标签页）<br>
• 尝试简化问题描述后重试<br>
• 切换到其他AI模型<br>
• 如果问题持续，请联系开发者
"""

        # 导出相关错误
        if "导出" in context or "export" in context.lower():
            return """
• 确保有足够的磁盘空间<br>
• 检查导出路径是否有写入权限<br>
• 尝试导出到其他位置<br>
• 关闭可能占用文件的其他程序<br>
• 尝试使用不同的导出格式
"""

        # 默认建议
        return f"""
• 尝试重新执行该操作<br>
• 检查输入信息是否正确<br>
• 重启应用程序后再试<br>
• 查看日志文件获取更多信息：<code>logs/cyber_mantic.log</code><br>
• 如果问题持续，请联系开发者并提供错误信息
"""

    def _show_detailed_error(self) -> None:
        """显示详细的错误堆栈信息"""
        if not HAS_PYQT6:
            return

        detail_box = QMessageBox(self.parent)
        detail_box.setIcon(QMessageBox.Icon.Information)
        detail_box.setWindowTitle("详细错误信息")
        detail_box.setText("完整的错误堆栈跟踪：")

        # 获取最后的堆栈跟踪
        exc_info = sys.exc_info()
        if exc_info[0] is not None:
            stack_trace = ''.join(traceback.format_exception(*exc_info))
        else:
            stack_trace = "无可用的堆栈跟踪信息"

        detail_box.setDetailedText(stack_trace)
        detail_box.exec()

    @staticmethod
    def with_timeout(
        func: Callable,
        timeout_ms: int = 120000,  # 默认2分钟
        timeout_callback: Optional[Callable] = None
    ) -> None:
        """
        为函数添加超时提醒（仅提醒，不中断）

        ⚠️ 重要限制：
        此方法仅用于"超时提醒"，而非"超时中断"。
        - QTimer触发后会显示超时对话框，提醒用户操作时间过长
        - 但无法中断正在执行的函数（Python无法强制终止同步函数）
        - 函数仍会继续执行直到完成或抛出异常

        使用场景：
        - 提醒用户网络请求可能较慢
        - 提醒用户AI分析耗时较长
        - 给用户心理预期，减少焦虑

        不适用场景：
        - 需要真正中断执行的操作（请使用QThread + 取消机制）
        - 对时间有严格要求的操作
        - 可能无限阻塞的操作

        Args:
            func: 要执行的函数（同步函数）
            timeout_ms: 超时提醒时间（毫秒），默认120000ms (2分钟)
            timeout_callback: 超时时的回调函数（可选）

        Example:
            >>> def slow_operation():
            ...     time.sleep(10)  # 模拟耗时操作
            >>> ErrorHandler.with_timeout(slow_operation, timeout_ms=5000)
            # 5秒后弹出超时提醒对话框，但slow_operation仍会继续执行
        """
        if not HAS_PYQT6:
            # PyQt6不可用时，直接执行函数
            func()
            return

        timer = QTimer()
        timer.setSingleShot(True)

        def on_timeout():
            if timeout_callback:
                timeout_callback()
            else:
                # 默认超时处理
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Icon.Warning)
                msg.setWindowTitle("操作超时")
                msg.setText("操作执行时间过长")
                msg.setInformativeText(
                    f"操作已超过 {timeout_ms/1000:.0f} 秒。\n\n"
                    "可能的原因：\n"
                    "• 网络连接缓慢\n"
                    "• AI服务响应延迟\n"
                    "• 数据量过大\n\n"
                    "建议：\n"
                    "• 检查网络连接\n"
                    "• 稍后再试\n"
                    "• 简化输入内容"
                )
                msg.exec()

        timer.timeout.connect(on_timeout)
        timer.start(timeout_ms)

        # 执行函数
        try:
            func()
        finally:
            timer.stop()


class WorkerErrorMixin:
    """
    Worker线程错误处理Mixin

    用法：
    class MyWorker(QThread, WorkerErrorMixin):
        error_occurred = pyqtSignal(str, str)  # (error_type, error_msg)

        def run(self):
            try:
                # ... 你的代码 ...
            except Exception as e:
                self.handle_worker_error(e, "数据处理")
    """

    def handle_worker_error(self, error: Exception, context: str = "操作"):
        """
        Worker线程中的错误处理

        Args:
            error: 异常对象
            context: 错误上下文
        """
        error_type = type(error).__name__
        error_msg = str(error)

        # 记录日志
        logger = get_logger(self.__class__.__name__)
        logger.error(f"{context}失败: {error_type}: {error_msg}")
        logger.error(f"堆栈跟踪:\n{traceback.format_exc()}")

        # 发送错误信号（如果定义了error信号）
        if hasattr(self, 'error'):
            self.error.emit(error_msg)

        # 如果定义了error_occurred信号，发送详细信息
        if hasattr(self, 'error_occurred'):
            self.error_occurred.emit(error_type, error_msg)


def setup_global_exception_handler():
    """
    设置全局异常处理器

    捕获未处理的异常，避免程序崩溃
    """
    logger = get_logger("GlobalExceptionHandler")

    def exception_hook(exctype, value, tb):
        """全局异常钩子"""
        # 记录异常
        logger.critical(
            f"未捕获的异常: {exctype.__name__}: {value}\n"
            f"{''.join(traceback.format_tb(tb))}"
        )

        # 显示错误对话框（仅在PyQt6可用时）
        if HAS_PYQT6:
            from PyQt6.QtWidgets import QApplication
            app = QApplication.instance()
        else:
            app = None

        if app and HAS_PYQT6:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("❌ 程序错误")
            msg.setText("<b>程序遇到了一个严重错误</b>")
            msg.setInformativeText(
                f"<p><b>错误类型：</b>{exctype.__name__}</p>"
                f"<p><b>错误详情：</b>{value}</p>"
                f"<hr>"
                f"<p><b>🔧 建议操作：</b></p>"
                f"<p>• 保存当前工作（如果可能）<br>"
                f"• 重启应用程序<br>"
                f"• 如果问题持续，请联系开发者<br>"
                f"• 附上日志文件：<code>logs/cyber_mantic.log</code></p>"
            )
            msg.setTextFormat(Qt.TextFormat.RichText)
            msg.setDetailedText(''.join(traceback.format_exception(exctype, value, tb)))
            msg.exec()

        # 调用原始的异常处理器
        sys.__excepthook__(exctype, value, tb)

    # 设置异常钩子
    sys.excepthook = exception_hook


# 便捷的装饰器
def handle_errors(context: str = "操作", show_dialog: bool = True):
    """
    错误处理装饰器

    用法：
    @handle_errors("加载配置")
    def load_config(self):
        # ... 你的代码 ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # 尝试获取self（如果是方法）
                if args and hasattr(args[0], 'error_handler'):
                    args[0].error_handler.handle_error(e, context, show_dialog)
                else:
                    # 创建临时错误处理器
                    handler = ErrorHandler()
                    handler.handle_error(e, context, show_dialog)
                raise
        return wrapper
    return decorator
