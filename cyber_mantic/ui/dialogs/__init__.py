"""
UI Dialogs - 对话框组件
"""

from .term_explain_sidebar import TermExplainSidebar
from .report_qa_dialog import ReportQADialog
from .report_custom_dialog import ReportCustomDialog
from .report_compare_dialog import ReportCompareDialog
from .disclaimer_dialog import (
    FirstLaunchDisclaimerDialog,
    SimpleDisclaimerDialog,
    MinorDetectionDialog,
    MinorExtraConfirmDialog,
    DisclaimerManager,
    get_disclaimer_manager
)
from .onboarding_dialog import OnboardingDialog
from .rag_qa_dialog import RAGQADialog

__all__ = [
    'TermExplainSidebar',
    'ReportQADialog',
    'ReportCustomDialog',
    'ReportCompareDialog',
    # 免责声明相关
    'FirstLaunchDisclaimerDialog',
    'SimpleDisclaimerDialog',
    'MinorDetectionDialog',
    'MinorExtraConfirmDialog',
    'DisclaimerManager',
    'get_disclaimer_manager',
    # 引导相关
    'OnboardingDialog',
    # RAG问答
    'RAGQADialog',
]
