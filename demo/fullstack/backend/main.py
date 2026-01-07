"""
赛博玄数 - FastAPI 后端
Web全栈Demo
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import json
import asyncio
import random

app = FastAPI(
    title="赛博玄数 API",
    description="Cyber Mantic - 智能术数分析系统",
    version="1.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============== 数据模型 ==============

class UserInput(BaseModel):
    """用户输入"""
    question_type: str = "事业"
    question_description: str = ""
    birth_year: Optional[int] = None
    birth_month: Optional[int] = None
    birth_day: Optional[int] = None
    birth_hour: Optional[int] = None
    gender: Optional[str] = None
    numbers: Optional[List[int]] = None
    character: Optional[str] = None


class ChatMessage(BaseModel):
    """聊天消息"""
    content: str
    is_user: bool
    timestamp: str = ""
    stage: Optional[str] = None


class AnalysisRequest(BaseModel):
    """分析请求"""
    user_input: UserInput
    theories: Optional[List[str]] = None


class BaZiResult(BaseModel):
    """八字结果"""
    year_pillar: dict
    month_pillar: dict
    day_pillar: dict
    hour_pillar: dict
    wuxing: dict
    judgment: str
    interpretation: str


# ============== 模拟数据 ==============

TIANGAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
DIZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
WUXING_MAP = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
    "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水",
    "子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土",
    "巳": "火", "午": "火", "未": "土", "申": "金", "酉": "金",
    "戌": "土", "亥": "水"
}

LIUSHEN = [
    {"name": "大安", "nature": "吉", "element": "木", "score": 0.75},
    {"name": "留连", "nature": "凶", "element": "土", "score": 0.3},
    {"name": "速喜", "nature": "吉", "element": "火", "score": 0.9},
    {"name": "赤口", "nature": "凶", "element": "金", "score": 0.2},
    {"name": "小吉", "nature": "吉", "element": "水", "score": 0.65},
    {"name": "空亡", "nature": "凶", "element": "土", "score": 0.1},
]

THEORIES = [
    {"id": "bazi", "name": "八字", "icon": "🎴", "description": "四柱推命，分析命运格局"},
    {"id": "ziwei", "name": "紫微斗数", "icon": "⭐", "description": "星宫布局，解读人生轨迹"},
    {"id": "qimen", "name": "奇门遁甲", "icon": "🚪", "description": "时空布局，预测事态发展"},
    {"id": "liuren", "name": "大六壬", "icon": "🔮", "description": "课传分析，占断吉凶"},
    {"id": "liuyao", "name": "六爻", "icon": "⚔️", "description": "卦象推演，解答疑惑"},
    {"id": "meihua", "name": "梅花易数", "icon": "🌸", "description": "数理推演，感应天机"},
    {"id": "xiaoliu", "name": "小六壬", "icon": "🎲", "description": "快速占卜，即时预测"},
    {"id": "cezi", "name": "测字", "icon": "✍️", "description": "字形拆解，洞察玄机"},
]


# ============== 工具函数 ==============

def calculate_ganzhi(year: int, month: int, day: int, hour: int = 12):
    """计算干支（简化版）"""
    # 年柱
    year_gan_idx = (year - 4) % 10
    year_zhi_idx = (year - 4) % 12

    # 月柱（简化）
    month_gan_idx = (year_gan_idx * 2 + month) % 10
    month_zhi_idx = (month + 1) % 12

    # 日柱（简化）
    day_gan_idx = (year * 5 + (year // 4) + day + month * 2) % 10
    day_zhi_idx = (year * 5 + (year // 4) + day + month * 2) % 12

    # 时柱
    hour_zhi_idx = (hour + 1) // 2 % 12
    hour_gan_idx = (day_gan_idx * 2 + hour_zhi_idx) % 10

    return {
        "year": {"gan": TIANGAN[year_gan_idx], "zhi": DIZHI[year_zhi_idx]},
        "month": {"gan": TIANGAN[month_gan_idx], "zhi": DIZHI[month_zhi_idx]},
        "day": {"gan": TIANGAN[day_gan_idx], "zhi": DIZHI[day_zhi_idx]},
        "hour": {"gan": TIANGAN[hour_gan_idx], "zhi": DIZHI[hour_zhi_idx]},
    }


def calculate_wuxing(ganzhi: dict) -> dict:
    """计算五行分布"""
    wuxing_count = {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}

    for pillar in ganzhi.values():
        wuxing_count[WUXING_MAP[pillar["gan"]]] += 1
        wuxing_count[WUXING_MAP[pillar["zhi"]]] += 1

    return wuxing_count


def xiaoliu_divine(numbers: List[int]) -> dict:
    """小六壬占卜"""
    if len(numbers) >= 3:
        idx = (numbers[0] + numbers[1] + numbers[2] - 3) % 6
    else:
        idx = random.randint(0, 5)

    return LIUSHEN[idx]


# ============== API 路由 ==============

@app.get("/")
async def root():
    """根路由"""
    return {"message": "赛博玄数 API", "version": "1.0.0"}


@app.get("/api/theories")
async def get_theories():
    """获取支持的理论列表"""
    return {"theories": THEORIES}


@app.post("/api/bazi/calculate")
async def calculate_bazi(user_input: UserInput):
    """计算八字"""
    if not all([user_input.birth_year, user_input.birth_month, user_input.birth_day]):
        return {"error": "请提供完整的出生日期"}

    hour = user_input.birth_hour or 12
    ganzhi = calculate_ganzhi(
        user_input.birth_year,
        user_input.birth_month,
        user_input.birth_day,
        hour
    )

    wuxing = calculate_wuxing(ganzhi)

    # 简单判断
    max_element = max(wuxing, key=wuxing.get)
    min_element = min(wuxing, key=wuxing.get)

    judgment = "中平"
    if wuxing[max_element] >= 4:
        judgment = "偏旺"
    elif wuxing[min_element] == 0:
        judgment = "有缺"

    return {
        "pillars": ganzhi,
        "wuxing": wuxing,
        "day_master": ganzhi["day"]["gan"],
        "day_master_element": WUXING_MAP[ganzhi["day"]["gan"]],
        "judgment": judgment,
        "interpretation": f"日主{ganzhi['day']['gan']}属{WUXING_MAP[ganzhi['day']['gan']]}，命局{judgment}。{max_element}气最旺，{min_element}气较弱。"
    }


@app.post("/api/xiaoliu/divine")
async def divine_xiaoliu(user_input: UserInput):
    """小六壬占卜"""
    numbers = user_input.numbers or [random.randint(1, 9) for _ in range(3)]
    result = xiaoliu_divine(numbers)

    return {
        "numbers": numbers,
        "liushen": result["name"],
        "nature": result["nature"],
        "element": result["element"],
        "score": result["score"],
        "interpretation": f"所得{result['name']}，属{result['element']}，{result['nature']}象。"
    }


@app.post("/api/analyze")
async def analyze(request: AnalysisRequest):
    """综合分析"""
    results = []
    user_input = request.user_input
    theories = request.theories or ["xiaoliu", "bazi"]

    for theory in theories:
        if theory == "bazi" and user_input.birth_year:
            bazi_result = await calculate_bazi(user_input)
            results.append({
                "theory": "八字",
                "result": bazi_result
            })
        elif theory == "xiaoliu":
            xiaoliu_result = await divine_xiaoliu(user_input)
            results.append({
                "theory": "小六壬",
                "result": xiaoliu_result
            })

    return {
        "question": user_input.question_description,
        "question_type": user_input.question_type,
        "theories_used": [r["theory"] for r in results],
        "results": results,
        "summary": "综合多个理论分析，为您提供全面的参考意见。"
    }


# ============== WebSocket 对话 ==============

class ConversationManager:
    """对话管理器"""

    STAGES = ["greeting", "collect_info", "analysis", "qa"]

    GREETINGS = [
        "您好！我是赛博玄数智能助手。请问今天您想咨询什么事项？",
        "我可以为您提供八字、紫微斗数、奇门遁甲等多种术数分析。"
    ]

    def __init__(self):
        self.stage = "greeting"
        self.context = {}
        self.messages = []

    async def process_message(self, message: str) -> str:
        """处理用户消息"""
        self.messages.append({"role": "user", "content": message})

        # 简单的意图识别
        if self.stage == "greeting":
            self.stage = "collect_info"
            return "好的，为了给您更准确的分析，我需要了解一些信息。\n\n请问您的出生年月日是？（例如：1990年6月15日）"

        elif self.stage == "collect_info":
            # 尝试提取日期
            if any(char.isdigit() for char in message):
                self.context["birth_info_raw"] = message
                self.stage = "analysis"
                return "收到！我正在为您进行多维度分析...\n\n根据您提供的信息，八字显示您的命局整体呈现稳健发展态势。日主属土，喜用神为金水，2025年乙巳年对您的事业发展较为有利。\n\n您还有什么想了解的吗？"
            else:
                return "请告诉我您的出生日期，这样我才能为您进行准确的分析。"

        elif self.stage == "analysis" or self.stage == "qa":
            self.stage = "qa"
            # 简单的问答
            if "事业" in message:
                return "从命理角度看，您的事业运势在2025年呈上升趋势。建议把握上半年的机遇，特别是农历三、四月份。"
            elif "感情" in message or "姻缘" in message:
                return "感情方面，今年桃花运较旺，但需注意分辨真心。已有伴侣的朋友感情稳定，适合进一步发展。"
            elif "财运" in message:
                return "财运方面，正财稳定，偏财有起伏。建议以稳健投资为主，避免高风险操作。"
            else:
                return "我理解您的问题。从综合分析来看，保持积极心态，顺势而为是最好的策略。您还有其他想了解的吗？"

        return "请告诉我您想咨询的具体问题。"


# 存储活跃的对话
conversations: dict[str, ConversationManager] = {}


@app.websocket("/ws/chat/{client_id}")
async def websocket_chat(websocket: WebSocket, client_id: str):
    """WebSocket 对话接口"""
    await websocket.accept()

    # 创建对话管理器
    if client_id not in conversations:
        conversations[client_id] = ConversationManager()

    manager = conversations[client_id]

    # 发送欢迎消息
    for greeting in manager.GREETINGS:
        await websocket.send_json({
            "type": "message",
            "content": greeting,
            "is_user": False,
            "timestamp": datetime.now().isoformat()
        })
        await asyncio.sleep(0.5)

    try:
        while True:
            # 接收用户消息
            data = await websocket.receive_json()
            user_message = data.get("content", "")

            # 发送"正在输入"状态
            await websocket.send_json({
                "type": "typing",
                "is_typing": True
            })

            # 模拟思考延迟
            await asyncio.sleep(1)

            # 处理消息
            response = await manager.process_message(user_message)

            # 发送回复
            await websocket.send_json({
                "type": "typing",
                "is_typing": False
            })

            await websocket.send_json({
                "type": "message",
                "content": response,
                "is_user": False,
                "timestamp": datetime.now().isoformat(),
                "stage": manager.stage
            })

    except WebSocketDisconnect:
        if client_id in conversations:
            del conversations[client_id]


@app.get("/api/stats")
async def get_stats():
    """获取统计数据"""
    return {
        "analysis_count": 128,
        "learning_hours": 24.5,
        "notes_count": 56,
        "accuracy": 87
    }


@app.get("/api/history")
async def get_history():
    """获取历史记录"""
    return {
        "items": [
            {
                "id": "1",
                "title": "2025年事业运势分析",
                "theory": "八字",
                "time": "2小时前",
                "status": "success"
            },
            {
                "id": "2",
                "title": "感情姻缘咨询",
                "theory": "紫微斗数",
                "time": "昨天",
                "status": "info"
            },
            {
                "id": "3",
                "title": "投资决策分析",
                "theory": "奇门遁甲",
                "time": "3天前",
                "status": "warning"
            }
        ]
    }


# ============== 启动配置 ==============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
