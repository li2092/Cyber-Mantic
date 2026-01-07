"""
分析标签页模块

将原本1600+行的AnalysisTab拆分为以下模块：
- analysis_tab.py: 主控制器 (~200行)
- input_panel.py: 输入面板组件 (~600行)
- progress_panel.py: 进度面板组件 (~80行)
- result_panel.py: 结果面板组件 (~400行)
- workers.py: 工作线程 (~60行)
"""

from .analysis_tab import AnalysisTab
from .input_panel import InputPanel
from .progress_panel import ProgressPanel
from .result_panel import ResultPanel
from .workers import AnalysisWorker, GeocodeWorker

__all__ = [
    'AnalysisTab',
    'InputPanel',
    'ProgressPanel',
    'ResultPanel',
    'AnalysisWorker',
    'GeocodeWorker',
]
