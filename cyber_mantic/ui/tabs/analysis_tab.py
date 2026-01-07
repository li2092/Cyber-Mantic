"""
分析标签页 - 向后兼容模块

此模块已重构为子包 ui.tabs.analysis
保留此文件以兼容直接导入 analysis_tab.py 的代码
"""
from .analysis import (
    AnalysisTab,
    AnalysisWorker,
    GeocodeWorker,
    InputPanel,
    ProgressPanel,
    ResultPanel,
)

__all__ = [
    'AnalysisTab',
    'AnalysisWorker',
    'GeocodeWorker',
    'InputPanel',
    'ProgressPanel',
    'ResultPanel',
]
