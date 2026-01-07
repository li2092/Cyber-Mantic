"""
UI标签页模块

标签页架构（v4.0）：
1. 问道 (AIConversationTab) - 对话式渐进预测
2. 推演 (AnalysisTab) - 快速排盘分析
3. 典籍 (LibraryTab) - 术数资料阅读与学习
4. 洞察 (InsightTab) - 用户画像与状态评估
5. 历史记录 (HistoryTab) - 问道+推演历史管理
6. 设置 (SettingsTab) - 配置管理
"""
from .analysis import AnalysisTab
from .ai_conversation_tab import AIConversationTab
from .settings_tab import SettingsTab
from .history_tab import HistoryTab
from .library_tab import LibraryTab
from .insight_tab import InsightTab

__all__ = [
    'AnalysisTab',
    'AIConversationTab',
    'SettingsTab',
    'HistoryTab',
    'LibraryTab',
    'InsightTab',
]
