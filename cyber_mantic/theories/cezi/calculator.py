"""
测字术计算器
"""
from typing import Dict, Any, List, Tuple, Optional
from .constants import *
from .stroke_data import get_stroke_count, has_stroke_data
from .ai_validator import get_cezi_validator


class CeZiCalculator:
    """测字术计算器"""

    def __init__(self, use_ai_validation: bool = True):
        """
        初始化计算器

        Args:
            use_ai_validation: 是否使用AI验证（默认True）
        """
        self.use_ai_validation = use_ai_validation
        self.validator = get_cezi_validator() if use_ai_validation else None

    def analyze_character(
        self,
        character: str,
        question: str = "",
        context: str = ""
    ) -> Dict[str, Any]:
        """
        分析汉字

        Args:
            character: 要分析的汉字
            question: 问题描述
            context: 上下文背景

        Returns:
            测字分析结果
        """
        if not character or len(character) == 0:
            return self._empty_result()

        # 取第一个字符进行分析
        char = character[0]

        # 基本信息（代码初步分析）
        basic_info = self._analyze_basic_info(char)
        code_stroke_count = basic_info["笔画数"]
        code_structure = self._guess_structure(char)

        # AI验证（如果启用）
        validation_result = None
        if self.use_ai_validation and self.validator:
            try:
                validation_result = self.validator.validate_character(
                    char,
                    code_stroke_count,
                    code_structure
                )

                # 使用验证后的结果
                if validation_result.get("validation_success"):
                    final_stroke_count = validation_result["final_stroke_count"]
                    final_structure = validation_result["final_structure"]

                    # 更新基本信息
                    basic_info["笔画数"] = final_stroke_count
                    basic_info["AI验证"] = True
                    basic_info["验证置信度"] = validation_result.get("confidence", 0.8)

                    if not validation_result.get("is_consistent"):
                        basic_info["验证说明"] = validation_result.get("unified_reason", "")
                else:
                    final_stroke_count = code_stroke_count
                    final_structure = code_structure
                    basic_info["AI验证"] = False
                    basic_info["验证失败原因"] = validation_result.get("error", "")
            except Exception as e:
                # AI验证失败，使用代码结果
                final_stroke_count = code_stroke_count
                final_structure = code_structure
                basic_info["AI验证"] = False
                basic_info["验证异常"] = str(e)
        else:
            final_stroke_count = code_stroke_count
            final_structure = code_structure
            basic_info["AI验证"] = False

        # 笔画分析（使用验证后的笔画数）
        stroke_analysis = self._analyze_strokes(final_stroke_count)

        # 结构分析（使用验证后的结构）
        structure_analysis = self._analyze_structure_with_type(char, final_structure)

        # 部首分析
        radical_analysis = self._analyze_radical(char)

        # 五行分析
        wuxing_analysis = self._analyze_wuxing(basic_info["笔画数"], radical_analysis)

        # 拆字分析（可能包含AI提供的拆字部件）
        ai_split_parts = None
        if validation_result and validation_result.get("validation_success"):
            ai_split_parts = validation_result.get("final_split_parts") or \
                           validation_result.get("ai_split_parts")

        split_analysis = self._analyze_split(char, ai_split_parts)

        # 字义分析
        meaning_analysis = self._analyze_meaning(char, question)

        # 综合判断
        judgment = self._make_judgment(
            stroke_analysis,
            structure_analysis,
            radical_analysis,
            wuxing_analysis,
            meaning_analysis
        )

        # 生成基础拆字摘要（供专业人士参考）
        paipan_summary = self._generate_paipan_summary(
            char, basic_info, structure_analysis, radical_analysis, wuxing_analysis, split_analysis
        )

        return {
            "测字": char,
            "原文": character,
            "基本信息": basic_info,
            "笔画分析": stroke_analysis,
            "结构分析": structure_analysis,
            "部首分析": radical_analysis,
            "五行分析": wuxing_analysis,
            "拆字分析": split_analysis,
            "字义分析": meaning_analysis,
            "吉凶判断": judgment["judgment"],
            "综合评分": judgment["score"],
            "详细分析": judgment["analysis"],
            "基础排盘信息": paipan_summary,  # 新增：拆字摘要
            "置信度": 0.65  # 测字术主观性较强
        }

    def _empty_result(self) -> Dict[str, Any]:
        """空结果"""
        return {
            "测字": "",
            "错误": "未提供汉字",
            "吉凶判断": "平",
            "综合评分": 0.5,
            "详细分析": "请提供要测的汉字",
            "置信度": 0.0
        }

    def _analyze_basic_info(self, char: str) -> Dict[str, Any]:
        """分析基本信息（简化：使用固定数据）"""
        # 实际应用中应该使用汉字数据库或API
        # 这里使用简化的估算方法
        stroke_count = self._estimate_stroke_count(char)

        return {
            "汉字": char,
            "笔画数": stroke_count,
            "Unicode": hex(ord(char))
        }

    def _estimate_stroke_count(self, char: str) -> int:
        """
        获取/估算笔画数

        优先使用准确的笔画数数据，如果找不到则使用估算方法
        """
        # 优先使用准确的笔画数数据
        if has_stroke_data(char):
            return get_stroke_count(char)

        # 如果没有准确数据，使用估算方法
        # 根据Unicode范围和字形复杂度估算
        unicode_val = ord(char)

        # 常用字范围：0x4E00-0x9FFF
        if 0x4E00 <= unicode_val <= 0x9FFF:
            # 简化估算：根据字符编码位置粗略估计
            relative_pos = (unicode_val - 0x4E00) / (0x9FFF - 0x4E00)
            # 笔画数通常在1-30之间，编码靠后的字相对复杂
            estimated = int(5 + relative_pos * 15)
            return max(1, min(30, estimated))

        return 10  # 默认值

    def _analyze_strokes(self, stroke_count: int) -> Dict[str, Any]:
        """分析笔画数"""
        # 使用81数理（取模）
        key = stroke_count % 20 if stroke_count > 20 else stroke_count
        if key == 0:
            key = 20

        judgment_data = STROKE_JUDGMENT.get(key, {"吉凶": "平", "说明": "一般之数"})

        return {
            "笔画数": stroke_count,
            "数理": key,
            "吉凶": judgment_data["吉凶"],
            "说明": judgment_data["说明"]
        }

    def _analyze_structure_with_type(self, char: str, structure_type: str) -> Dict[str, Any]:
        """
        分析字体结构（使用指定的结构类型）

        Args:
            char: 汉字
            structure_type: 结构类型

        Returns:
            结构分析结果
        """
        structure_info = STRUCTURE_TYPES.get(structure_type, STRUCTURE_TYPES["独体"])

        return {
            "结构类型": structure_type,
            "吉凶": structure_info["吉凶"],
            "说明": structure_info["说明"]
        }

    def _analyze_structure(self, char: str) -> Dict[str, Any]:
        """分析字体结构（简化，仅用于向后兼容）"""
        structure_type = self._guess_structure(char)
        return self._analyze_structure_with_type(char, structure_type)

    def _guess_structure(self, char: str) -> str:
        """猜测字体结构（简化）"""
        # 实际需要字形分析
        # 这里返回常见结构
        common_structures = ["左右", "上下", "包围", "半包围", "独体"]
        # 根据字符哈希选择（保持一致性）
        hash_val = hash(char) % len(common_structures)
        return common_structures[hash_val]

    def _analyze_radical(self, char: str) -> Dict[str, Any]:
        """分析部首（简化）"""
        # 实际需要部首数据库
        # 这里检测常见部首
        detected_radicals = []

        for radical, properties in RADICAL_PROPERTIES.items():
            if radical in char or self._contains_radical_variant(char, radical):
                detected_radicals.append({
                    "部首": radical,
                    "吉凶": properties["吉凶"],
                    "主事": properties["主事"],
                    "五行": properties["五行"]
                })

        if not detected_radicals:
            detected_radicals.append({
                "部首": "未识别",
                "吉凶": "平",
                "主事": "一般含义",
                "五行": "土"
            })

        return {
            "部首列表": detected_radicals,
            "主部首": detected_radicals[0]
        }

    def _contains_radical_variant(self, char: str, radical: str) -> bool:
        """检测部首变体（简化）"""
        # 部首变体映射
        variants = {
            "水": ["氵", "冫"],
            "火": ["灬", "火"],
            "人": ["亻", "人"],
            "手": ["扌", "手"],
            "心": ["忄", "心"],
            "刀": ["刂", "刀"]
        }

        if radical in variants:
            for variant in variants[radical]:
                if variant in char:
                    return True

        return False

    def _analyze_wuxing(
        self,
        stroke_count: int,
        radical_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """分析五行"""
        # 笔画数五行
        stroke_tail = stroke_count % 10
        stroke_wuxing = WUXING_BY_STROKE[stroke_tail]

        # 部首五行
        radical_wuxing = radical_analysis["主部首"]["五行"]

        # 检查生克关系
        relationship = self._check_wuxing_relationship(stroke_wuxing, radical_wuxing)

        return {
            "笔画五行": stroke_wuxing,
            "部首五行": radical_wuxing,
            "生克关系": relationship["关系"],
            "说明": relationship["说明"]
        }

    def _check_wuxing_relationship(self, wuxing1: str, wuxing2: str) -> Dict[str, str]:
        """检查五行生克关系"""
        if wuxing1 == wuxing2:
            return {"关系": "比和", "说明": "五行相同，力量增强"}

        if WUXING_SHENG.get(wuxing1) == wuxing2:
            return {"关系": "相生", "说明": f"{wuxing1}生{wuxing2}，有助益"}

        if WUXING_KE.get(wuxing1) == wuxing2:
            return {"关系": "相克", "说明": f"{wuxing1}克{wuxing2}，有制约"}

        if WUXING_SHENG.get(wuxing2) == wuxing1:
            return {"关系": "被生", "说明": f"{wuxing2}生{wuxing1}，受助力"}

        if WUXING_KE.get(wuxing2) == wuxing1:
            return {"关系": "被克", "说明": f"{wuxing2}克{wuxing1}，受制约"}

        return {"关系": "无关", "说明": "五行关系较弱"}

    def _analyze_split(
        self,
        char: str,
        ai_split_parts: Optional[List[str]] = None
    ) -> List[Dict[str, str]]:
        """
        拆字分析

        Args:
            char: 汉字
            ai_split_parts: AI提供的拆字部件

        Returns:
            拆字分析结果列表
        """
        splits = []

        # 如果有AI提供的拆字部件
        if ai_split_parts and len(ai_split_parts) > 0:
            splits.append({
                "方法": "AI拆字",
                "部件": ", ".join(ai_split_parts),
                "说明": f"字'{char}'可拆为：{' + '.join(ai_split_parts)}"
            })
        else:
            # 简化：提供几种常见拆字方法
            splits.append({
                "方法": "观形",
                "说明": f"此字形体观之，结构特征明显"
            })

            splits.append({
                "方法": "取象",
                "说明": f"字形象征一定事物，可引申解读"
            })

        return splits

    def _analyze_meaning(self, char: str, question: str) -> Dict[str, Any]:
        """分析字义"""
        # 检查字义中的吉凶关键词
        ji_count = 0
        xiong_count = 0

        # 简化：检查字符是否包含吉凶字
        for keyword in MEANING_KEYWORDS["吉"]:
            if keyword == char:
                ji_count += 1

        for keyword in MEANING_KEYWORDS["凶"]:
            if keyword == char:
                xiong_count += 1

        if ji_count > 0:
            tendency = "吉"
            tendency_desc = "字义吉祥"
        elif xiong_count > 0:
            tendency = "凶"
            tendency_desc = "字义不吉"
        else:
            tendency = "平"
            tendency_desc = "字义中性"

        return {
            "字义倾向": tendency,
            "说明": tendency_desc,
            "应用": f"结合问题'{question}'理解字义"
        }

    def _make_judgment(
        self,
        stroke_analysis: Dict[str, Any],
        structure_analysis: Dict[str, Any],
        radical_analysis: Dict[str, Any],
        wuxing_analysis: Dict[str, Any],
        meaning_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """综合判断"""
        # 统计吉凶
        ji_score = 0
        xiong_score = 0

        # 笔画吉凶
        if stroke_analysis["吉凶"] == "吉":
            ji_score += 1
        elif stroke_analysis["吉凶"] == "凶":
            xiong_score += 1

        # 结构吉凶
        if structure_analysis["吉凶"] == "吉":
            ji_score += 1
        elif structure_analysis["吉凶"] == "凶":
            xiong_score += 1

        # 部首吉凶
        radical_jx = radical_analysis["主部首"]["吉凶"]
        if radical_jx == "吉":
            ji_score += 1.5  # 部首权重较大
        elif radical_jx == "凶":
            xiong_score += 1.5

        # 字义吉凶
        if meaning_analysis["字义倾向"] == "吉":
            ji_score += 1
        elif meaning_analysis["字义倾向"] == "凶":
            xiong_score += 1

        # 五行关系
        wuxing_rel = wuxing_analysis["生克关系"]
        if wuxing_rel in ["相生", "被生", "比和"]:
            ji_score += 0.5
        elif wuxing_rel in ["相克", "被克"]:
            xiong_score += 0.5

        # 计算评分
        total = ji_score + xiong_score
        if total > 0:
            score = 0.5 + (ji_score - xiong_score) / total * 0.4
        else:
            score = 0.5

        score = max(0.2, min(1.0, score))

        # 判断吉凶
        if score >= 0.7:
            judgment = "吉"
            desc = "字象吉祥，多有喜庆"
        elif score >= 0.5:
            judgment = "平"
            desc = "字象平和，吉凶参半"
        else:
            judgment = "凶"
            desc = "字象欠佳，需多谨慎"

        analysis = (
            f"{desc}。"
            f"笔画{stroke_analysis['笔画数']}画为{stroke_analysis['吉凶']}，"
            f"结构为{structure_analysis['结构类型']}，"
            f"部首{radical_analysis['主部首']['部首']}主{radical_analysis['主部首']['主事']}。"
        )

        return {
            "judgment": judgment,
            "score": score,
            "analysis": analysis
        }

    def _generate_paipan_summary(
        self,
        char: str,
        basic_info: Dict[str, Any],
        structure_analysis: Dict[str, Any],
        radical_analysis: Dict[str, Any],
        wuxing_analysis: Dict[str, Any],
        split_analysis: List[Dict[str, str]]
    ) -> str:
        """
        生成简化的拆字信息摘要（供专业人士参考）

        Args:
            char: 汉字
            basic_info: 基本信息
            structure_analysis: 结构分析
            radical_analysis: 部首分析
            wuxing_analysis: 五行分析
            split_analysis: 拆字分析

        Returns:
            拆字摘要文本
        """
        summary = f"【测字术拆字】'{char}'\n\n"

        # 基本信息
        stroke_count = basic_info.get("笔画数", 0)
        unicode_val = basic_info.get("Unicode", "")
        summary += f"笔画: {stroke_count}画 | {unicode_val}\n"

        # 结构
        structure = structure_analysis.get("结构类型", "")
        summary += f"结构: {structure}\n"

        # 部首
        main_radical = radical_analysis.get("主部首", {})
        radical_name = main_radical.get("部首", "")
        radical_wuxing = main_radical.get("五行", "")
        summary += f"部首: {radical_name}({radical_wuxing})\n"

        # 五行
        stroke_wuxing = wuxing_analysis.get("笔画五行", "")
        wuxing_relation = wuxing_analysis.get("生克关系", "")
        summary += f"五行: 笔画{stroke_wuxing} 部首{radical_wuxing} {wuxing_relation}\n"

        # 拆字部件
        if split_analysis and len(split_analysis) > 0:
            first_split = split_analysis[0]
            parts = first_split.get("部件", "")
            if parts:
                summary += f"拆字: {parts}\n"

        # AI验证状态
        ai_verified = basic_info.get("AI验证", False)
        if ai_verified:
            confidence = basic_info.get("验证置信度", 0.0)
            summary += f"AI验证: ✓ (置信度{confidence:.1%})"
        else:
            summary += "AI验证: - (未启用)"

        return summary.strip()
