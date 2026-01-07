"""
对话服务模块（重构版）

模块结构：
- context.py: 对话上下文数据模型（ConversationStage, ConversationContext）
- nlp_parser.py: NLP解析器（NLPParser）
- stage_handlers.py: 阶段处理器（Stage1-4Handler）
- qa_handler.py: 问答处理器（QAHandler）
- report_generator.py: 报告生成器（ReportGenerator, ConversationExporter）

向后兼容：
从原 conversation_service.py 导入的类仍可正常使用
"""
from .context import ConversationStage, ConversationContext, MAX_CONVERSATION_HISTORY
from .nlp_parser import NLPParser
from .stage_handlers import (
    BaseStageHandler,
    Stage1Handler,
    Stage2Handler,
    Stage3Handler,
    Stage4Handler
)
from .qa_handler import QAHandler, DEFAULT_QA_KEYWORDS, FALLBACK_RESPONSES
from .report_generator import ReportGenerator, ConversationExporter

__all__ = [
    # 上下文数据
    'ConversationStage',
    'ConversationContext',
    'MAX_CONVERSATION_HISTORY',
    # NLP解析
    'NLPParser',
    # 阶段处理器
    'BaseStageHandler',
    'Stage1Handler',
    'Stage2Handler',
    'Stage3Handler',
    'Stage4Handler',
    # 问答处理
    'QAHandler',
    'DEFAULT_QA_KEYWORDS',
    'FALLBACK_RESPONSES',
    # 报告生成
    'ReportGenerator',
    'ConversationExporter',
]
