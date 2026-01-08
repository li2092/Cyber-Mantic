"""
分析工作线程模块 - 提供异步分析和地理编码功能
"""
from PyQt6.QtCore import QThread, pyqtSignal

from models import UserInput, ComprehensiveReport
from services.analysis_service import AnalysisService


class AnalysisWorker(QThread):
    """分析工作线程"""

    progress = pyqtSignal(str, str, int, str)  # 理论名, 状态, 进度, 详细信息
    quick_result = pyqtSignal(str)  # 快速结果
    finished = pyqtSignal(object)  # 完成信号，传递报告
    error = pyqtSignal(str)  # 错误信号

    def __init__(self, analysis_service: AnalysisService, user_input: UserInput):
        super().__init__()
        self.analysis_service = analysis_service
        self.user_input = user_input

    def run(self):
        """执行分析"""
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            def progress_callback(theory_name: str, message: str, progress: int, detail: str = ""):
                self.progress.emit(theory_name, message, progress, detail)

            report = loop.run_until_complete(
                self.analysis_service.analyze(self.user_input, progress_callback)
            )

            loop.close()
            self.finished.emit(report)
        except Exception as e:
            self.error.emit(str(e))


class GeocodeWorker(QThread):
    """地理编码查询线程"""

    finished = pyqtSignal(object)  # 查询成功，传递结果字典
    error = pyqtSignal(str)  # 查询失败，传递错误消息

    def __init__(self, address: str):
        super().__init__()
        self.address = address

    def run(self):
        """执行地理编码查询"""
        try:
            from utils.amap_geocoder import get_geocoder
            # 使用force_refresh=True确保读取最新的配置
            geocoder = get_geocoder(force_refresh=True)
            result = geocoder.geocode(self.address)

            if result:
                self.finished.emit(result)
            else:
                self.error.emit(f"未找到地址\"{self.address}\"的位置信息\n请检查是否已配置高德地图API密钥")
        except Exception as e:
            self.error.emit(f"查询失败: {str(e)}")
