"""
数据可视化工具模块

提供术数分析结果的可视化功能：
- 五行雷达图
- 大运流年时间轴
- 理论适配度分布图
- 冲突解决过程图

支持导出为图片或嵌入PyQt6 UI
"""
import matplotlib
matplotlib.use('Agg')  # 无GUI后端

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.figure import Figure
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import io
from pathlib import Path


# 中文字体配置
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


class WuxingRadarChart:
    """五行雷达图"""

    WUXING_NAMES = ["木", "火", "土", "金", "水"]
    WUXING_COLORS = {
        "木": "#228B22",
        "火": "#DC143C",
        "土": "#DAA520",
        "金": "#C0C0C0",
        "水": "#1E90FF"
    }

    @classmethod
    def create(cls, wuxing_scores: Dict[str, float], title: str = "五行分布") -> Figure:
        """
        创建五行雷达图

        Args:
            wuxing_scores: 五行分数字典 {"木": 3, "火": 2, ...}
            title: 图表标题

        Returns:
            matplotlib Figure对象
        """
        # 准备数据
        values = [wuxing_scores.get(element, 0) for element in cls.WUXING_NAMES]
        values += values[:1]  # 闭合雷达图

        # 创建角度
        angles = np.linspace(0, 2 * np.pi, len(cls.WUXING_NAMES), endpoint=False)
        angles = np.concatenate((angles, [angles[0]]))

        # 创建图表
        fig = plt.figure(figsize=(8, 8))
        ax = fig.add_subplot(111, polar=True)

        # 绘制雷达图
        ax.plot(angles, values, 'o-', linewidth=2, color='#4169E1', label='五行强度')
        ax.fill(angles, values, alpha=0.25, color='#4169E1')

        # 设置刻度标签
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(cls.WUXING_NAMES, size=12, weight='bold')

        # 设置Y轴范围
        max_value = max(values) if values else 5
        ax.set_ylim(0, max_value * 1.2)
        ax.set_yticks(range(0, int(max_value * 1.2) + 1, max(1, int(max_value * 1.2) // 5)))

        # 添加网格
        ax.grid(True, linestyle='--', alpha=0.7)

        # 添加标题
        ax.set_title(title, size=16, weight='bold', pad=20)

        plt.tight_layout()
        return fig

    @classmethod
    def save_to_file(cls, wuxing_scores: Dict[str, float], filepath: str, title: str = "五行分布"):
        """保存五行雷达图到文件"""
        fig = cls.create(wuxing_scores, title)
        fig.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close(fig)

    @classmethod
    def to_bytes(cls, wuxing_scores: Dict[str, float], title: str = "五行分布") -> bytes:
        """将五行雷达图转换为字节流（用于PyQt6显示）"""
        fig = cls.create(wuxing_scores, title)
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        data = buf.read()
        plt.close(fig)
        return data


class DayunTimeline:
    """大运流年时间轴"""

    @classmethod
    def create(
        cls,
        dayun_data: List[Dict[str, Any]],
        current_year: int,
        title: str = "大运流年时间轴"
    ) -> Figure:
        """
        创建大运流年时间轴

        Args:
            dayun_data: 大运数据列表 [{"start_age": 8, "end_age": 17, "gan_zhi": "甲子", "description": "..."}, ...]
            current_year: 当前年份
            title: 图表标题

        Returns:
            matplotlib Figure对象
        """
        if not dayun_data:
            fig, ax = plt.subplots(figsize=(12, 2))
            ax.text(0.5, 0.5, '暂无大运数据', ha='center', va='center', fontsize=14)
            ax.axis('off')
            return fig

        fig, ax = plt.subplots(figsize=(14, 4))

        # 绘制时间轴
        for i, dayun in enumerate(dayun_data):
            start_age = dayun.get("start_age", 0)
            end_age = dayun.get("end_age", 0)
            gan_zhi = dayun.get("gan_zhi", "")

            # 绘制区间
            ax.barh(0, end_age - start_age, left=start_age, height=0.5,
                    color=plt.cm.tab20(i % 20), alpha=0.7, edgecolor='black')

            # 添加标签
            mid_age = (start_age + end_age) / 2
            ax.text(mid_age, 0, f'{gan_zhi}\n{start_age}-{end_age}岁',
                    ha='center', va='center', fontsize=10, weight='bold')

        # 设置坐标轴
        ax.set_xlim(0, max([d.get("end_age", 0) for d in dayun_data]) + 5)
        ax.set_ylim(-1, 1)
        ax.set_xlabel('年龄', fontsize=12)
        ax.set_yticks([])
        ax.set_title(title, fontsize=16, weight='bold', pad=15)

        # 添加网格
        ax.grid(True, axis='x', alpha=0.3, linestyle='--')

        plt.tight_layout()
        return fig

    @classmethod
    def save_to_file(cls, dayun_data: List[Dict], current_year: int, filepath: str, title: str = "大运流年时间轴"):
        """保存时间轴到文件"""
        fig = cls.create(dayun_data, current_year, title)
        fig.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close(fig)

    @classmethod
    def to_bytes(cls, dayun_data: List[Dict], current_year: int, title: str = "大运流年时间轴") -> bytes:
        """将大运时间轴转换为字节流（用于PyQt6显示）"""
        fig = cls.create(dayun_data, current_year, title)
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        data = buf.read()
        plt.close(fig)
        return data


class TheoryFitnessChart:
    """理论适配度分布图"""

    @classmethod
    def create(
        cls,
        theory_fitness: List[Dict[str, Any]],
        title: str = "理论适配度分布"
    ) -> Figure:
        """
        创建理论适配度饼图或柱状图

        Args:
            theory_fitness: 理论适配度列表 [{"theory": "八字", "fitness": 0.95, "priority": "基础"}, ...]
            title: 图表标题

        Returns:
            matplotlib Figure对象
        """
        if not theory_fitness:
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.text(0.5, 0.5, '暂无理论适配度数据', ha='center', va='center', fontsize=14)
            ax.axis('off')
            return fig

        # 准备数据
        theories = [item["theory"] for item in theory_fitness]
        fitness_scores = [item["fitness"] for item in theory_fitness]

        # 创建柱状图
        fig, ax = plt.subplots(figsize=(10, 6))

        # 绘制柱状图
        bars = ax.bar(theories, fitness_scores, color=plt.cm.Paired(np.linspace(0, 1, len(theories))),
                       edgecolor='black', linewidth=1.5)

        # 添加数值标签
        for bar, score in zip(bars, fitness_scores):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{score:.2f}',
                    ha='center', va='bottom', fontsize=10, weight='bold')

        # 设置坐标轴
        ax.set_ylabel('适配度分数', fontsize=12)
        ax.set_xlabel('理论', fontsize=12)
        ax.set_title(title, fontsize=16, weight='bold', pad=15)
        ax.set_ylim(0, 1.1)
        ax.grid(True, axis='y', alpha=0.3, linestyle='--')

        # 旋转X轴标签
        plt.xticks(rotation=45, ha='right')

        plt.tight_layout()
        return fig

    @classmethod
    def save_to_file(cls, theory_fitness: List[Dict], filepath: str, title: str = "理论适配度分布"):
        """保存适配度图到文件"""
        fig = cls.create(theory_fitness, title)
        fig.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close(fig)

    @classmethod
    def to_bytes(cls, theory_fitness: List[Dict], title: str = "理论适配度分布") -> bytes:
        """将理论适配度图转换为字节流（用于PyQt6显示）"""
        fig = cls.create(theory_fitness, title)
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        data = buf.read()
        plt.close(fig)
        return data


class ConflictResolutionFlow:
    """冲突解决流程图"""

    @classmethod
    def create(
        cls,
        conflicts: List[Dict[str, Any]],
        title: str = "冲突解决流程"
    ) -> Figure:
        """
        创建冲突解决流程图

        Args:
            conflicts: 冲突列表 [{"level": 3, "theories": ["八字", "紫微"], "resolution": "..."}, ...]
            title: 图表标题

        Returns:
            matplotlib Figure对象
        """
        if not conflicts:
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.text(0.5, 0.5, '无冲突检测', ha='center', va='center', fontsize=14, color='green')
            ax.axis('off')
            return fig

        # 统计冲突级别
        level_counts = {1: 0, 2: 0, 3: 0, 4: 0}
        for conflict in conflicts:
            level = conflict.get("level", 1)
            level_counts[level] = level_counts.get(level, 0) + 1

        # 创建堆叠柱状图
        fig, ax = plt.subplots(figsize=(10, 6))

        levels = list(level_counts.keys())
        counts = [level_counts[l] for l in levels]
        colors = ['#90EE90', '#FFD700', '#FFA500', '#DC143C']  # 绿-黄-橙-红
        level_names = ['轻微', '中等', '严重', '极严重']

        bars = ax.bar(level_names, counts, color=colors, edgecolor='black', linewidth=1.5)

        # 添加数值标签
        for bar, count in zip(bars, counts):
            if count > 0:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                        f'{count}个',
                        ha='center', va='bottom', fontsize=11, weight='bold')

        ax.set_ylabel('冲突数量', fontsize=12)
        ax.set_xlabel('冲突级别', fontsize=12)
        ax.set_title(title, fontsize=16, weight='bold', pad=15)
        ax.grid(True, axis='y', alpha=0.3, linestyle='--')

        plt.tight_layout()
        return fig

    @classmethod
    def save_to_file(cls, conflicts: List[Dict], filepath: str, title: str = "冲突解决流程"):
        """保存冲突图到文件"""
        fig = cls.create(conflicts, title)
        fig.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close(fig)

    @classmethod
    def to_bytes(cls, conflicts: List[Dict], title: str = "冲突解决流程") -> bytes:
        """将冲突解决流程图转换为字节流（用于PyQt6显示）"""
        fig = cls.create(conflicts, title)
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        data = buf.read()
        plt.close(fig)
        return data


class LifeKLineChart:
    """人生K线图 - 仿股票K线展示运势走势"""

    @classmethod
    def create(
        cls,
        fortune_data: List[Dict[str, Any]],
        title: str = "人生运势K线图"
    ) -> Figure:
        """
        创建人生K线图

        Args:
            fortune_data: 运势数据列表 [
                {"year": 2020, "open": 60, "close": 75, "high": 80, "low": 55, "event": "事业转折"},
                ...
            ]
            title: 图表标题

        Returns:
            matplotlib Figure对象
        """
        if not fortune_data:
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.text(0.5, 0.5, '暂无运势数据', ha='center', va='center', fontsize=14)
            ax.axis('off')
            return fig

        fig, ax = plt.subplots(figsize=(14, 7))

        years = [d.get("year", i) for i, d in enumerate(fortune_data)]
        x_positions = range(len(fortune_data))

        # 绘制K线
        for i, data in enumerate(fortune_data):
            open_val = data.get("open", 50)
            close_val = data.get("close", 50)
            high_val = data.get("high", max(open_val, close_val))
            low_val = data.get("low", min(open_val, close_val))

            # 颜色：收盘高于开盘为绿色（运势上升），否则为红色（运势下降）
            color = '#10b981' if close_val >= open_val else '#ef4444'
            edge_color = '#059669' if close_val >= open_val else '#dc2626'

            # 绘制影线（上下须）
            ax.plot([i, i], [low_val, high_val], color='#64748b', linewidth=1.5, zorder=1)

            # 绘制实体（蜡烛body）
            body_bottom = min(open_val, close_val)
            body_height = abs(close_val - open_val)
            if body_height < 2:
                body_height = 2  # 最小高度

            rect = plt.Rectangle((i - 0.3, body_bottom), 0.6, body_height,
                                  facecolor=color, edgecolor=edge_color,
                                  linewidth=1.5, zorder=2)
            ax.add_patch(rect)

            # 添加关键事件标记
            event = data.get("event", "")
            if event:
                ax.annotate(event, xy=(i, high_val + 3),
                           fontsize=8, ha='center', va='bottom',
                           color='#6366f1', weight='bold',
                           rotation=45)

        # 添加运势参考线
        ax.axhline(y=50, color='#94a3b8', linestyle='--', linewidth=1, label='中等运势', alpha=0.7)
        ax.axhline(y=70, color='#10b981', linestyle=':', linewidth=1, label='好运区间', alpha=0.5)
        ax.axhline(y=30, color='#ef4444', linestyle=':', linewidth=1, label='低谷区间', alpha=0.5)

        # 填充背景区域
        ax.axhspan(70, 100, alpha=0.1, color='#10b981')
        ax.axhspan(0, 30, alpha=0.1, color='#ef4444')

        # 设置坐标轴
        ax.set_xlim(-0.5, len(fortune_data) - 0.5)
        ax.set_ylim(0, 100)
        ax.set_xticks(x_positions)
        ax.set_xticklabels([str(y) for y in years], rotation=45, ha='right')
        ax.set_xlabel('年份', fontsize=12)
        ax.set_ylabel('运势指数', fontsize=12)
        ax.set_title(title, fontsize=16, weight='bold', pad=15)

        # 添加图例
        ax.legend(loc='upper left', fontsize=9)

        # 网格
        ax.grid(True, axis='y', alpha=0.3, linestyle='--')

        plt.tight_layout()
        return fig

    @classmethod
    def from_dayun_data(cls, dayun_data: List[Dict[str, Any]], birth_year: int) -> List[Dict[str, Any]]:
        """
        从大运数据生成K线数据

        Args:
            dayun_data: 大运数据
            birth_year: 出生年份

        Returns:
            K线格式的运势数据
        """
        fortune_data = []
        base_fortune = 50

        for dayun in dayun_data:
            start_age = dayun.get("start_age", 0)
            end_age = dayun.get("end_age", 0)
            gan_zhi = dayun.get("gan_zhi", "")
            description = dayun.get("description", "")

            # 简单的运势计算逻辑（实际应用中可以更复杂）
            # 这里只是示例，实际应该根据八字理论计算
            import random
            random.seed(hash(gan_zhi) % 100)  # 确保相同干支产生相同结果

            for age in range(start_age, min(end_age + 1, start_age + 10)):
                year = birth_year + age
                variation = random.randint(-15, 15)
                open_val = base_fortune + variation
                close_val = open_val + random.randint(-10, 15)
                high_val = max(open_val, close_val) + random.randint(3, 10)
                low_val = min(open_val, close_val) - random.randint(3, 10)

                # 确保在有效范围内
                open_val = max(10, min(90, open_val))
                close_val = max(10, min(90, close_val))
                high_val = max(10, min(95, high_val))
                low_val = max(5, min(85, low_val))

                fortune_data.append({
                    "year": year,
                    "open": open_val,
                    "close": close_val,
                    "high": high_val,
                    "low": low_val,
                    "event": f"{gan_zhi}" if age == start_age else ""
                })

                base_fortune = close_val  # 下一个时期的起点

        return fortune_data

    @classmethod
    def save_to_file(cls, fortune_data: List[Dict], filepath: str, title: str = "人生运势K线图"):
        """保存K线图到文件"""
        fig = cls.create(fortune_data, title)
        fig.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close(fig)

    @classmethod
    def to_bytes(cls, fortune_data: List[Dict], title: str = "人生运势K线图") -> bytes:
        """将K线图转换为字节流（用于PyQt6显示）"""
        fig = cls.create(fortune_data, title)
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        data = buf.read()
        plt.close(fig)
        return data


class VisualizationManager:
    """可视化管理器 - 统一管理所有可视化功能"""

    @staticmethod
    def generate_all_charts(
        analysis_result: Dict[str, Any],
        output_dir: str
    ) -> Dict[str, str]:
        """
        为分析结果生成所有可视化图表

        Args:
            analysis_result: 完整分析结果字典
            output_dir: 输出目录

        Returns:
            生成的图表文件路径字典
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        chart_paths = {}

        # 1. 五行雷达图
        if "wuxing_analysis" in analysis_result:
            wuxing_scores = analysis_result["wuxing_analysis"].get("scores", {})
            if wuxing_scores:
                filepath = output_path / "wuxing_radar.png"
                WuxingRadarChart.save_to_file(wuxing_scores, str(filepath))
                chart_paths["wuxing_radar"] = str(filepath)

        # 2. 大运时间轴
        if "dayun_data" in analysis_result:
            dayun_data = analysis_result["dayun_data"]
            if dayun_data:
                filepath = output_path / "dayun_timeline.png"
                DayunTimeline.save_to_file(
                    dayun_data,
                    datetime.now().year,
                    str(filepath)
                )
                chart_paths["dayun_timeline"] = str(filepath)

        # 3. 理论适配度
        if "selected_theories" in analysis_result:
            theory_fitness = analysis_result.get("theory_fitness", [])
            if theory_fitness:
                filepath = output_path / "theory_fitness.png"
                TheoryFitnessChart.save_to_file(theory_fitness, str(filepath))
                chart_paths["theory_fitness"] = str(filepath)

        # 4. 冲突解决
        if "conflicts" in analysis_result:
            conflicts = analysis_result["conflicts"]
            if conflicts:
                filepath = output_path / "conflict_resolution.png"
                ConflictResolutionFlow.save_to_file(conflicts, str(filepath))
                chart_paths["conflict_resolution"] = str(filepath)

        return chart_paths
