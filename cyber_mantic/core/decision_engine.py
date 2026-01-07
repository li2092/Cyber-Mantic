"""
决策引擎 - 核心分析流程

安全特性：
- 异步操作超时控制，防止无限等待
- 完善的错误处理和降级机制
"""
import json
import uuid
import time
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from models import UserInput, TheoryAnalysisResult, ConflictInfo, ComprehensiveReport


# 默认超时配置（秒）
DEFAULT_THEORY_TIMEOUT = 250  # 单个理论分析超时
DEFAULT_INTERPRETATION_TIMEOUT = 250  # LLM解读超时（主模型）
DEFAULT_INTERPRETATION_TIMEOUT_SECONDARY = 120  # LLM解读超时（副模型）
DEFAULT_REPORT_TIMEOUT = 300  # 综合报告生成超时
from theories import TheoryRegistry
from api import APIManager, PromptTemplates
from .theory_selector import TheorySelector
from .conflict_resolver import ConflictResolver
from utils.logger import get_logger, log_calculation, log_conflict_resolution, log_performance
from utils.mbti_analyzer import MBTIAnalyzer
from .ai_assistant import AIAssistant


class DecisionEngine:
    """决策引擎，负责整个分析流程"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化决策引擎

        Args:
            config: 配置字典
        """
        self.config = config
        self.theory_selector = TheorySelector()
        self.api_manager = APIManager(config.get("api", {}))
        self.conflict_resolver = ConflictResolver()
        self.ai_assistant = AIAssistant(self.api_manager)  # 新增AI助手
        self.logger = get_logger()

    async def analyze(self, user_input: UserInput, progress_callback=None) -> ComprehensiveReport:
        """
        执行完整分析流程

        Args:
            user_input: 用户输入
            progress_callback: 可选的进度回调函数 callback(theory_name, status, progress_percent)

        Returns:
            综合报告
        """
        start_time = time.time()

        print("=" * 60)
        print("赛博玄数 - 开始分析")
        print("=" * 60)

        self.logger.info("="*60)
        self.logger.info("开始新的分析流程")
        self.logger.info(f"问题类型: {user_input.question_type}")
        self.logger.info(f"问题描述: {user_input.question_description}")
        self.logger.info("="*60)

        # 向UI传递开始分析信息
        if progress_callback:
            progress_callback("系统", "开始分析", 0, "============================================================\n赛博玄数 - 开始分析\n============================================================")

        # 1. 选择理论
        print("\n[步骤1] 选择适合的理论...")
        if progress_callback:
            progress_callback("系统", "选择理论", 5, "[步骤1] 选择适合的理论...")
        theory_select_start = time.time()
        selected_theories, missing_info = self.theory_selector.select_theories(
            user_input,
            max_theories=self.config.get("analysis", {}).get("max_theories", 5),
            min_theories=self.config.get("analysis", {}).get("min_theories", 3)
        )

        if missing_info:
            print(f"提示：补充以下信息可提高准确性：{', '.join(missing_info)}")

        theory_names = [t["theory"] for t in selected_theories]
        print(f"选中理论：{', '.join(theory_names)}")

        theory_select_duration = time.time() - theory_select_start
        self.logger.info(f"理论选择完成，选中 {len(theory_names)} 个理论: {', '.join(theory_names)}")
        log_performance(operation="理论选择", duration=theory_select_duration)

        # 通过 progress_callback 传递选中理论信息
        if progress_callback:
            detail_msg = f"选中理论：{', '.join(theory_names)}"
            if missing_info:
                detail_msg += f"\n提示：补充以下信息可提高准确性：{', '.join(missing_info)}"
            progress_callback("系统", "理论选择完成", 8, detail_msg)

        # 2. 确定执行顺序
        execution_order = self.theory_selector.determine_execution_order(selected_theories)
        print(f"执行顺序：{' -> '.join(execution_order)}")
        self.logger.info(f"执行顺序: {' -> '.join(execution_order)}")

        # 通过 progress_callback 传递执行顺序信息
        if progress_callback:
            progress_callback("系统", "确定执行顺序", 10, f"执行顺序：{' -> '.join(execution_order)}")

        # 3. 运行各理论计算
        print("\n[步骤2] 运行理论计算...")
        if progress_callback:
            progress_callback("系统", "开始计算", 10, "[步骤2] 运行理论计算...")
        theory_results = []
        total_theories = len(execution_order)

        for idx, theory_name in enumerate(execution_order):
            # 计算当前进度（10%-70%分配给理论分析）
            base_progress = 10 + int((idx / total_theories) * 60)

            print(f"\n正在计算 {theory_name}...")
            if progress_callback:
                progress_callback(theory_name, "计算排盘", base_progress, f"正在计算 {theory_name}...")

            theory = TheoryRegistry.get_theory(theory_name)
            if theory:
                try:
                    # 计算排盘
                    calculation_data = theory.calculate(user_input)
                    print(f"{theory_name} 计算完成")
                    if progress_callback:
                        progress_callback(theory_name, "计算完成", base_progress + int(60 / total_theories / 4), f"{theory_name} 计算完成")

                    # LLM解读
                    print(f"正在解读 {theory_name}...")
                    if progress_callback:
                        progress_callback(theory_name, "AI解读中", base_progress + int(60 / total_theories / 2), f"正在解读 {theory_name}...")
                        # 如果启用了双模型验证，显示提示
                        if self.api_manager.enable_dual_verification:
                            progress_callback(theory_name, "双模型验证", base_progress + int(60 / total_theories / 2) + 1, "启用双模型验证")

                    interpretation = await self._get_interpretation(
                        theory_name,
                        calculation_data,
                        user_input
                    )

                    # 解读完成后显示验证完成提示
                    if progress_callback and self.api_manager.enable_dual_verification:
                        progress_callback(theory_name, "双模型验证", base_progress + int(60 / total_theories * 0.85), "双模型验证完成，两个模型都成功响应")

                    # 创建结果对象
                    result = TheoryAnalysisResult(
                        theory_name=theory_name,
                        calculation_data=calculation_data,
                        interpretation=interpretation,
                        judgment=calculation_data.get("judgment", "平"),
                        judgment_level=calculation_data.get("judgment_level", 0.5),
                        timing=calculation_data.get("timing"),
                        advice=calculation_data.get("advice"),
                        confidence=calculation_data.get("confidence", 0.8)
                    )

                    theory_results.append(result)
                    print(f"{theory_name} 解读完成")

                    # 通过 progress_callback 传递完成信息
                    if progress_callback:
                        progress_callback(theory_name, "解读完成", base_progress + int(60 / total_theories * 0.9), f"{theory_name} 解读完成")
                        judgment = calculation_data.get("judgment", "平")
                        confidence = calculation_data.get("confidence", 0.8)
                        detail_msg = f"✓ {theory_name} 分析完成 - 判断: {judgment}，置信度: {confidence*100:.1f}%"
                        progress_callback(theory_name, "分析完成", base_progress + int(60 / total_theories), detail_msg)

                except Exception as e:
                    print(f"{theory_name} 分析失败: {e}")
                    self.logger.error(f"{theory_name} 分析失败: {e}")
                    # 通过 progress_callback 传递失败信息
                    if progress_callback:
                        progress_callback(theory_name, "分析失败", base_progress, f"✗ {theory_name} 分析失败: {str(e)}")
                    continue

        # 检查是否有成功的理论结果
        if not theory_results:
            error_msg = "所有理论分析都失败了，请检查输入信息是否完整或稍后重试"
            self.logger.error(error_msg)
            raise Exception(error_msg)

        self.logger.info(f"成功分析 {len(theory_results)}/{len(execution_order)} 个理论")
        if progress_callback:
            progress_callback("系统", "理论分析汇总", 72, f"成功分析 {len(theory_results)}/{len(execution_order)} 个理论")

        # 4. 检测并解决冲突
        print("\n[步骤3] 检测并解决理论间冲突...")
        if progress_callback:
            progress_callback("系统", "检测冲突", 75, "[步骤3] 检测并解决理论间冲突...")
        conflict_start = time.time()
        conflict_info = self.conflict_resolver.detect_and_resolve_conflicts(theory_results)

        if conflict_info.has_conflict:
            print(f"检测到 {len(conflict_info.conflicts)} 个冲突")
            self.logger.warning(f"检测到 {len(conflict_info.conflicts)} 个理论冲突")
            if progress_callback:
                progress_callback("系统", "冲突检测", 76, f"检测到 {len(conflict_info.conflicts)} 个冲突")

            if conflict_info.resolution:
                strategy = conflict_info.resolution.get("总体策略", "")
                print(f"解决策略：{strategy}")
                # 打印冲突摘要
                summary = self.conflict_resolver.get_conflict_summary(conflict_info)
                print(f"冲突摘要：\n{summary}")

                # 通过 progress_callback 传递详细信息到 UI
                if progress_callback:
                    detail_info = f"解决策略：{strategy}\n{summary}"
                    progress_callback("系统", "冲突解决", 78, detail_info)

                # 记录冲突解决过程
                log_conflict_resolution(
                    conflicts=conflict_info.conflicts,
                    resolution=conflict_info.resolution
                )
        else:
            print("未检测到冲突")
            self.logger.info("理论结果一致，未检测到冲突")
            # 通过 progress_callback 传递信息到 UI
            if progress_callback:
                progress_callback("系统", "冲突检测", 76, "未检测到冲突")
                progress_callback("系统", "冲突检测", 78, "理论结果一致，未检测到冲突")

        conflict_duration = time.time() - conflict_start
        log_performance(operation="冲突检测与解决", duration=conflict_duration)

        # 5. 生成综合报告
        print("\n[步骤4] 生成综合报告...")
        if progress_callback:
            progress_callback("系统", "生成报告", 85, "[步骤4] 生成综合报告...")
        report = await self._generate_comprehensive_report(
            user_input,
            selected_theories,
            theory_results,
            conflict_info,
            progress_callback
        )

        # 记录总耗时
        total_duration = time.time() - start_time
        log_performance(operation="完整分析流程", duration=total_duration)

        self.logger.info("="*60)
        self.logger.info(f"分析完成，总耗时: {total_duration:.2f}秒")
        self.logger.info(f"综合置信度: {report.overall_confidence:.2%}")
        self.logger.info("="*60)

        print("\n" + "=" * 60)
        print("分析完成")
        print(f"总耗时: {total_duration:.2f}秒")
        print("=" * 60)

        # 向UI传递分析完成信息
        if progress_callback:
            completion_msg = f"============================================================\n分析完成\n总耗时: {total_duration:.2f}秒\n============================================================"
            progress_callback("系统", "分析完成", 100, completion_msg)

        return report

    async def _get_interpretation(
        self,
        theory_name: str,
        calculation_data: Dict[str, Any],
        user_input: UserInput
    ) -> str:
        """
        获取LLM解读（带超时控制和多级降级）

        降级策略：
        1. 主模型解读（250秒超时）
        2. 主模型超时 -> 尝试副模型（120秒超时）
        3. 副模型也超时 -> 返回简化解读

        Args:
            theory_name: 理论名称
            calculation_data: 计算数据
            user_input: 用户输入

        Returns:
            解读文本
        """
        # 判断是否使用快速解读
        is_quick = theory_name in TheorySelector.THEORY_PRIORITY["快速"]

        if is_quick:
            prompt = PromptTemplates.format_quick_interpretation(
                theory_name=theory_name,
                question_description=user_input.question_description,
                calculation_result=json.dumps(calculation_data, ensure_ascii=False, indent=2)
            )
            task_type = "快速解读"
            primary_timeout = DEFAULT_INTERPRETATION_TIMEOUT // 2  # 快速解读使用更短超时
            secondary_timeout = DEFAULT_INTERPRETATION_TIMEOUT_SECONDARY // 2
        else:
            prompt = PromptTemplates.format_single_theory(
                theory_name=theory_name,
                question_type=user_input.question_type,
                question_description=user_input.question_description,
                current_time=user_input.current_time.isoformat(),
                calculation_result=json.dumps(calculation_data, ensure_ascii=False, indent=2),
                initial_inquiry_time=user_input.initial_inquiry_time.isoformat() if user_input.initial_inquiry_time else user_input.current_time.isoformat(),
                mbti_type=user_input.mbti_type,
                birth_time_certainty=user_input.birth_time_certainty
            )
            task_type = "单理论解读"
            primary_timeout = DEFAULT_INTERPRETATION_TIMEOUT
            secondary_timeout = DEFAULT_INTERPRETATION_TIMEOUT_SECONDARY

        # 第一步：尝试主模型
        try:
            self.logger.info(f"{theory_name} 使用主模型解读（超时：{primary_timeout}秒）")
            interpretation = await asyncio.wait_for(
                self.api_manager.call_api(task_type, prompt, enable_dual_verification=False),
                timeout=primary_timeout
            )
            return interpretation

        except asyncio.TimeoutError:
            self.logger.warning(f"{theory_name} 主模型解读超时（{primary_timeout}秒），尝试副模型...")

        # 第二步：主模型超时，尝试副模型
        try:
            # 获取副模型
            secondary_api = self._get_secondary_api()
            if secondary_api:
                self.logger.info(f"{theory_name} 使用副模型 {secondary_api} 解读（超时：{secondary_timeout}秒）")
                interpretation = await asyncio.wait_for(
                    self.api_manager._call_api_by_name(secondary_api, prompt),
                    timeout=secondary_timeout
                )
                # 标注使用了副模型
                return f"{interpretation}\n\n【注】本解读由副模型（{secondary_api}）生成，因主模型响应超时。"
            else:
                self.logger.warning(f"没有可用的副模型")

        except asyncio.TimeoutError:
            self.logger.warning(f"{theory_name} 副模型也超时（{secondary_timeout}秒），使用简化解读")
        except Exception as e:
            self.logger.warning(f"{theory_name} 副模型调用失败: {e}，使用简化解读")

        # 第三步：都失败，返回简化解读
        return self._generate_simplified_interpretation(theory_name, calculation_data)

    def _get_secondary_api(self) -> Optional[str]:
        """
        获取副模型API名称

        Returns:
            副模型名称，如果没有可用的返回None
        """
        primary_api = self.api_manager.primary_api
        available = self.api_manager.available_apis

        # 从可用API中选择一个非主模型的
        for api in self.api_manager.API_PRIORITY:
            if api in available and api != primary_api:
                return api
        return None

    def _generate_simplified_interpretation(
        self,
        theory_name: str,
        calculation_data: Dict[str, Any]
    ) -> str:
        """
        生成简化解读（当API调用失败时的降级方案）

        Args:
            theory_name: 理论名称
            calculation_data: 计算数据

        Returns:
            简化的解读文本
        """
        judgment = calculation_data.get('judgment', '待定')
        confidence = calculation_data.get('confidence', 0.7)
        timing = calculation_data.get('timing', '')
        advice = calculation_data.get('advice', '')

        result = f"【{theory_name}分析】\n"
        result += f"基于排盘数据的简要分析（因网络原因详细解读未能生成）：\n\n"
        result += f"• 核心判断：{judgment}\n"
        result += f"• 置信度：{confidence:.0%}\n"

        if timing:
            result += f"• 时机提示：{timing}\n"

        if advice:
            result += f"• 建议：{advice}\n"

        result += f"\n提示：您可以稍后重新分析以获取详细解读。"

        return result


    async def _generate_comprehensive_report(
        self,
        user_input: UserInput,
        selected_theories: List[Dict[str, Any]],
        theory_results: List[TheoryAnalysisResult],
        conflict_info: ConflictInfo,
        progress_callback=None
    ) -> ComprehensiveReport:
        """
        生成综合报告

        Args:
            user_input: 用户输入
            selected_theories: 选中的理论
            theory_results: 理论结果
            conflict_info: 冲突信息
            progress_callback: 进度回调函数

        Returns:
            综合报告
        """
        # 格式化各理论结果
        results_text = ""
        for result in theory_results:
            results_text += f"\n### {result.theory_name}\n"
            results_text += f"核心判断：{result.judgment}（程度：{result.judgment_level:.2f}）\n"
            results_text += f"详细分析：\n{result.interpretation}\n"

        # 添加MBTI分析（如果提供了MBTI类型）
        mbti_info = ""
        if user_input.mbti_type and MBTIAnalyzer.validate_mbti_type(user_input.mbti_type):
            mbti_summary = MBTIAnalyzer.get_summary(user_input.mbti_type)
            mbti_advice = MBTIAnalyzer.get_advice_for_question_type(
                user_input.mbti_type,
                user_input.question_type
            )
            mbti_info = f"\n\n## MBTI性格分析\n{mbti_summary}\n\n### 针对{user_input.question_type}问题的个性化建议\n"
            mbti_info += "\n".join([f"- {advice}" for advice in mbti_advice])

        # 调用LLM生成综合报告
        # 将MBTI信息附加到理论结果中
        full_results_text = results_text + mbti_info

        prompt = PromptTemplates.format_comprehensive_report(
            question_type=user_input.question_type,
            question_description=user_input.question_description,
            current_time=user_input.current_time.isoformat(),
            mbti_type=user_input.mbti_type or "未提供",
            theory_results=full_results_text,
            conflict_info=json.dumps(conflict_info.to_dict(), ensure_ascii=False, indent=2),
            initial_inquiry_time=user_input.initial_inquiry_time.isoformat() if user_input.initial_inquiry_time else user_input.current_time.isoformat(),
            birth_time_certainty=user_input.birth_time_certainty
        )

        if progress_callback:
            progress_callback("系统", "AI报告生成", 86, f"正在调用AI生成综合报告解读（{len(theory_results)}个理论）...")

        report_text = await self.api_manager.call_api("综合报告解读", prompt)

        if progress_callback:
            progress_callback("系统", "综合报告", 88, f"综合报告解读生成完成（{len(report_text)}字）")

        # 计算综合置信度
        if theory_results:
            overall_confidence = sum(r.confidence for r in theory_results) / len(theory_results)
        else:
            overall_confidence = 0.5

        # ========== 使用AI智能助手生成摘要和建议（后台调用Kimi） ==========
        print("\n[步骤5] AI智能助手生成摘要和建议...")
        if progress_callback:
            progress_callback("系统", "智能摘要生成", 90, "[步骤5] AI智能助手生成摘要和建议...")

        # 智能生成执行摘要（而非硬编码提取）
        if progress_callback:
            progress_callback("系统", "生成执行摘要", 90, "正在生成执行摘要...")
        try:
            ai_summary = await self.ai_assistant.generate_executive_summary(
                full_report=report_text,
                theory_results=theory_results,
                question_type=user_input.question_type,
                user_mbti=user_input.mbti_type
            )
            self.logger.info("AI智能摘要生成成功")
            if progress_callback:
                progress_callback("系统", "执行摘要", 91, f"执行摘要生成成功（{len(ai_summary)}字）")
        except Exception as e:
            self.logger.warning(f"AI智能摘要生成失败: {e}，使用原始报告")
            ai_summary = report_text[:500]  # 降级方案
            if progress_callback:
                progress_callback("系统", "执行摘要", 91, f"执行摘要生成失败，使用降级方案")

        if progress_callback:
            progress_callback("系统", "行动建议生成", 92, "正在生成行动建议...")

        # 创建临时报告对象（用于生成建议）
        temp_report = ComprehensiveReport(
            report_id=str(uuid.uuid4()),
            created_at=datetime.now(),
            user_input_summary=user_input.to_dict(),
            selected_theories=[t["theory"] for t in selected_theories],
            selection_reason=f"基于信息完备度和问题类型匹配度选择",
            theory_results=theory_results,
            conflict_info=conflict_info,
            executive_summary=ai_summary,
            detailed_analysis="",  # 稍后生成
            retrospective_analysis="",
            predictive_analysis="",
            comprehensive_advice=[],
            overall_confidence=overall_confidence,
            limitations=self._extract_limitations(user_input, theory_results)
        )

        # 智能生成行动建议
        try:
            ai_advice = await self.ai_assistant.generate_actionable_advice(temp_report)
            self.logger.info(f"AI行动建议生成成功，共{len(ai_advice)}条")
            if progress_callback:
                progress_callback("系统", "行动建议", 93, f"行动建议生成成功，共{len(ai_advice)}条")
        except Exception as e:
            self.logger.warning(f"AI行动建议生成失败: {e}，使用默认建议")
            ai_advice = [
                {"priority": "高", "content": "仔细阅读各理论的详细分析，理解核心要点"},
                {"priority": "中", "content": "结合自身实际情况，制定具体行动计划"}
            ]
            if progress_callback:
                progress_callback("系统", "行动建议", 93, f"行动建议生成失败，使用默认建议")

        # 更新临时报告的建议字段（用于生成时间分析）
        temp_report.comprehensive_advice = ai_advice

        if progress_callback:
            progress_callback("系统", "时间维度分析", 94, "开始生成时间维度分析...")

        # 准备用户出生信息（用于时间维度分析）
        user_birth_info = None
        if user_input.birth_year and user_input.birth_month and user_input.birth_day:
            user_birth_info = {
                "birth_year": user_input.birth_year,
                "birth_month": user_input.birth_month,
                "birth_day": user_input.birth_day,
                "birth_hour": user_input.birth_hour
            }

        # 智能生成过去三年回顾分析（根据问题类型判断是否需要）
        retrospective = ""
        # 只有命理类、运势类、事业类等需要时间回顾的问题才生成回顾分析
        time_sensitive_types = ["事业", "财运", "学业", "健康", "综合运势", "职业发展"]
        if any(qtype in user_input.question_type for qtype in time_sensitive_types):
            if progress_callback:
                progress_callback("系统", "回溯分析", 95, f"正在生成过去三年回顾分析（问题类型：{user_input.question_type}）...")
            try:
                retrospective = await self.ai_assistant.generate_retrospective_analysis(
                    report=temp_report,
                    user_birth_info=user_birth_info,
                    question_type=user_input.question_type
                )
                self.logger.info("过去三年回顾分析生成成功")
                if progress_callback:
                    progress_callback("系统", "回溯分析", 95, f"过去三年回顾分析生成成功（{len(retrospective)}字）")
            except Exception as e:
                self.logger.warning(f"过去三年回顾分析生成失败: {e}")
                if progress_callback:
                    progress_callback("系统", "回溯分析", 95, f"过去三年回顾分析生成失败：{str(e)}")
        else:
            self.logger.info(f"问题类型'{user_input.question_type}'不需要时间回顾分析")
            if progress_callback:
                progress_callback("系统", "回溯分析", 95, f"问题类型'{user_input.question_type}'不需要时间回顾分析")

        # 智能生成未来两年趋势分析（根据问题类型判断是否需要）
        predictive = ""
        if any(qtype in user_input.question_type for qtype in time_sensitive_types):
            if progress_callback:
                progress_callback("系统", "预测分析", 96, f"正在生成未来两年趋势分析（问题类型：{user_input.question_type}）...")
            try:
                predictive = await self.ai_assistant.generate_predictive_analysis(
                    report=temp_report,
                    user_birth_info=user_birth_info,
                    question_type=user_input.question_type
                )
                self.logger.info("未来两年趋势分析生成成功")
                if progress_callback:
                    progress_callback("系统", "预测分析", 96, f"未来两年趋势分析生成成功（{len(predictive)}字）")
            except Exception as e:
                self.logger.warning(f"未来两年趋势分析生成失败: {e}")
                if progress_callback:
                    progress_callback("系统", "预测分析", 96, f"未来两年趋势分析生成失败：{str(e)}")
        else:
            self.logger.info(f"问题类型'{user_input.question_type}'不需要未来趋势分析")
            if progress_callback:
                progress_callback("系统", "预测分析", 96, f"问题类型'{user_input.question_type}'不需要未来趋势分析")

        # 智能生成详细问题解答（报告核心内容，直接回答用户问题）
        if progress_callback:
            progress_callback("系统", "详细问题解答", 97, f"正在生成详细问题解答（问题：{user_input.question_description[:30]}...）")

        detailed_analysis = ""
        try:
            detailed_analysis = await self.ai_assistant.generate_detailed_analysis(
                report=temp_report,
                question_type=user_input.question_type,
                question_description=user_input.question_description,
                user_mbti=user_input.mbti_type
            )
            self.logger.info("详细问题解答生成成功")
            if progress_callback:
                progress_callback("系统", "详细问题解答", 98, f"详细问题解答生成成功（{len(detailed_analysis)}字）")
        except Exception as e:
            self.logger.warning(f"详细问题解答生成失败: {e}")
            # 降级方案：使用各理论解读的简单拼接
            detailed_analysis = "## 基于术数理论的分析\n\n"
            for result in theory_results:
                detailed_analysis += f"### {result.theory_name}\n{result.interpretation}\n\n"
            if progress_callback:
                progress_callback("系统", "详细问题解答", 98, f"详细问题解答生成失败，使用降级方案")

        # 创建最终报告对象
        report = ComprehensiveReport(
            report_id=temp_report.report_id,
            created_at=temp_report.created_at,
            user_input_summary=temp_report.user_input_summary,
            selected_theories=temp_report.selected_theories,
            selection_reason=temp_report.selection_reason,
            theory_results=temp_report.theory_results,
            conflict_info=temp_report.conflict_info,
            executive_summary=ai_summary,  # AI智能生成的摘要
            detailed_analysis=detailed_analysis,  # AI智能生成的详细问题解答（报告主要内容）
            retrospective_analysis=retrospective,  # AI智能生成的过去三年回顾
            predictive_analysis=predictive,  # AI智能生成的未来两年趋势
            comprehensive_advice=ai_advice,  # AI智能生成的建议
            overall_confidence=temp_report.overall_confidence,
            limitations=temp_report.limitations
        )

        return report

    def _extract_summary(self, report_text: str) -> str:
        """从报告文本中提取执行摘要

        由于使用了灵活的提示词模板，不再依赖固定格式。
        返回完整报告文本，让UI层负责格式化显示。
        """
        # 返回完整报告，UI层的_extract_summary_content会处理摘要提取
        return report_text.strip()

    def _extract_section(self, report_text: str, section_name: str) -> str:
        """从报告文本中提取特定章节

        由于使用了灵活的提示词模板，章节名称可能不固定。
        暂时返回空字符串，这些字段在ComprehensiveReport中不是核心显示内容。
        """
        # 灵活提示词下，章节结构不固定，返回空字符串
        # 主要内容在executive_summary中
        return ""

    def _extract_advice(self, report_text: str) -> List[Dict[str, Any]]:
        """从报告文本中提取行动建议

        由于使用了灵活的提示词模板，建议内容格式不固定。
        返回空列表，建议内容已包含在完整报告文本中。
        """
        # 灵活提示词下，建议格式不固定，返回空列表
        # 建议内容已包含在executive_summary的完整文本中
        return []

    def _extract_limitations(
        self,
        user_input: UserInput,
        theory_results: List[TheoryAnalysisResult]
    ) -> List[str]:
        """提取局限性说明"""
        limitations = []

        if user_input.birth_hour is None:
            limitations.append("未提供出生时辰，八字分析准确度有所降低")

        if len(theory_results) < 3:
            limitations.append("使用理论数量较少，建议补充更多信息以获得更多理论验证")

        return limitations
