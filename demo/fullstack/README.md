# 赛博玄数 - Web 全栈 Demo

基于 **Vue 3 + Tailwind CSS + FastAPI** 的现代化 Web 应用。

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| **前端** | Vue 3 + Vite | 响应式框架 |
| | Tailwind CSS | 原子化 CSS |
| | Pinia | 状态管理 |
| **后端** | FastAPI | 高性能 Python API |
| | WebSocket | 实时对话 |
| | Uvicorn | ASGI 服务器 |

## 快速开始

### 方式一：一键启动（推荐）

```bash
# 进入项目目录
cd demo/fullstack

# 启动后端 (终端1)
cd backend
pip install -r requirements.txt
python main.py

# 启动前端 (终端2)
cd frontend
npm install
npm run dev

# 访问 http://localhost:3000
```

### 方式二：Docker 部署

```bash
# 构建并运行
docker-compose up -d

# 访问 http://localhost:3000
```

## 项目结构

```
fullstack/
├── backend/                 # FastAPI 后端
│   ├── main.py             # 主入口 + API路由
│   ├── requirements.txt    # Python依赖
│   └── api/                # API模块（可扩展）
│
├── frontend/                # Vue 3 前端
│   ├── package.json        # 依赖配置
│   ├── vite.config.js      # Vite配置
│   ├── tailwind.config.js  # Tailwind配置
│   ├── index.html          # HTML入口
│   └── src/
│       ├── main.js         # Vue入口
│       ├── App.vue         # 根组件
│       ├── style.css       # 全局样式
│       └── components/     # 组件库
│           ├── Sidebar.vue
│           ├── TopBar.vue
│           ├── WelcomeBanner.vue
│           ├── StatsGrid.vue
│           ├── ChatSection.vue
│           ├── BaZiCard.vue
│           ├── QuickActions.vue
│           └── HistoryList.vue
│
└── README.md
```

## API 接口

### REST API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/theories` | 获取支持的理论列表 |
| POST | `/api/bazi/calculate` | 计算八字 |
| POST | `/api/xiaoliu/divine` | 小六壬占卜 |
| POST | `/api/analyze` | 综合分析 |
| GET | `/api/stats` | 获取统计数据 |
| GET | `/api/history` | 获取历史记录 |

### WebSocket

| 路径 | 说明 |
|------|------|
| `/ws/chat/{client_id}` | 实时对话 |

#### WebSocket 消息格式

```javascript
// 发送
{ "content": "用户消息" }

// 接收
{
  "type": "message" | "typing",
  "content": "AI回复",
  "is_user": false,
  "timestamp": "ISO时间",
  "stage": "greeting" | "collect_info" | "analysis" | "qa"
}
```

## 前端组件

| 组件 | 功能 |
|------|------|
| `Sidebar` | 侧边栏导航 |
| `TopBar` | 顶部栏（搜索、通知） |
| `WelcomeBanner` | 欢迎横幅 |
| `StatsGrid` | 统计卡片网格 |
| `ChatSection` | 聊天对话区 |
| `BaZiCard` | 八字命盘展示 |
| `QuickActions` | 快捷操作入口 |
| `HistoryList` | 历史记录列表 |

## 样式系统

### 颜色变量 (Tailwind)

```javascript
colors: {
  primary: '#6366f1',      // 玄青紫
  'primary-light': '#818cf8',
  'primary-dark': '#4f46e5',

  accent: '#f59e0b',       // 丹朱橙
  'accent-light': '#fbbf24',

  'dark-primary': '#0f0f1a',
  'dark-secondary': '#1a1a2e',
  'dark-tertiary': '#252542',

  wuxing: {
    wood: '#22c55e',
    fire: '#ef4444',
    earth: '#f59e0b',
    metal: '#e2e8f0',
    water: '#3b82f6',
  }
}
```

### 组件类

```css
.glass-card    /* 玻璃卡片 */
.btn-primary   /* 主按钮 */
.btn-secondary /* 次要按钮 */
.nav-btn       /* 导航按钮 */
.input-field   /* 输入框 */
.chat-bubble-ai   /* AI消息气泡 */
.chat-bubble-user /* 用户消息气泡 */
.stat-card     /* 统计卡片 */
.bazi-pillar   /* 八字柱位 */
.wuxing-circle /* 五行圆圈 */
```

## 与现有代码集成

后端可以导入现有的 `cyber_mantic` 模块：

```python
# main.py
import sys
sys.path.insert(0, '../../../cyber_mantic')

from theories.bazi.calculator import BaZiCalculator
from theories.xiaoliu.theory import XiaoLiuRenTheory
from core.decision_engine import DecisionEngine
from api.manager import APIManager

# 在API中使用
@app.post("/api/bazi/calculate")
async def calculate_bazi(user_input: UserInput):
    calculator = BaZiCalculator()
    result = calculator.calculate_full_bazi(
        user_input.birth_year,
        user_input.birth_month,
        user_input.birth_day,
        user_input.birth_hour
    )
    return result
```

## 生产部署

### 前端构建

```bash
cd frontend
npm run build
# 产物在 dist/ 目录
```

### Nginx 配置

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /var/www/cyber-mantic/dist;
        try_files $uri $uri/ /index.html;
    }

    # API代理
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }

    # WebSocket代理
    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## 扩展建议

1. **用户认证**: 添加 JWT 认证
2. **数据库**: 集成 SQLite/PostgreSQL
3. **缓存**: 添加 Redis 缓存
4. **SSE**: 流式响应 AI 回复
5. **PWA**: 离线访问支持
6. **国际化**: 多语言支持

---

*Demo 版本: v1.0*
*创建时间: 2026-01-06*
