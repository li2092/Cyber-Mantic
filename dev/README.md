# 开发文档目录

此文件夹包含所有开发相关的文档和记录，与产品代码分离。

## 目录结构

```
dev/
├── CLAUDE.md              # AI助手上下文（Claude Code使用）
├── README.md              # 本文件
│
├── guides/                # 开发指南
│   ├── TECHNICAL_README.md        # 技术说明文档
│   ├── TESTING_GUIDE.md           # 测试指南
│   ├── USER_TEST_CHECKLIST.md     # 用户测试清单
│   ├── AI_INTEGRATION_GUIDE.md    # AI集成指南
│   ├── FRONTEND_REDESIGN_PLAN.md  # 前端重构计划
│   ├── INTEGRATION_EXAMPLE.md     # 集成示例
│   ├── REPORT_OPTIMIZATION_GUIDE.md # 报告优化指南
│   ├── THEME_INTEGRATION_GUIDE.md # 主题集成指南
│   ├── HISTORY_CONFIG.md          # 历史记录配置说明
│   └── LOGO_SETUP_GUIDE.md        # Logo设置指南
│
├── records/               # 开发记录
│   ├── CODE_REVIEW_*.md           # 代码审查记录
│   ├── P2_OPTIMIZATION_SUMMARY.md # 优化总结
│   ├── THEORY_CALCULATION_AUDIT.md # 理论计算审计
│   ├── PHASE6_*.md                # 阶段开发记录
│   ├── COMPLETE_SUMMARY.md        # 完整总结
│   └── ...
│
├── test-reports/          # 测试报告
│   ├── TEST_REPORT.md             # 测试报告
│   ├── TESTING_CHECKLIST.md       # 测试清单
│   └── TESTING_REPORT_TEMPLATE.md # 测试报告模板
│
└── standalone-tests/      # 独立测试脚本
    ├── test_qimen_v2_standalone.py
    └── test_daliuren_v2_standalone.py
```

## 文件分类原则

| 类型 | 存放位置 | 说明 |
|------|----------|------|
| 产品源代码 | `cyber_mantic/` | 所有可运行的代码 |
| 单元测试 | `tests/` | pytest测试用例 |
| 产品文档 | `docs/` | 用户可见的产品文档 |
| 开发文档 | `dev/` | 仅开发者需要的文档 |
| 项目说明 | 根目录 | README、LICENSE等 |

## 与cyber_mantic的区别

- `cyber_mantic/`: 只包含产品运行所需的文件
- `dev/`: 包含开发过程中产生的文档、记录、计划等
