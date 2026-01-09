# 紧急修复 - 2026-01-09 晚

## 问题描述

在完成P1修复后，运行`python gui.py`时遇到导入错误：

```
NameError: name 'ConflictInfo' is not defined
cannot import name 'JudgmentType' from 'core.constants'
```

## 根本原因

1. **命名冲突问题**: `core/arbitration_system.py` 中有多处使用了 `ConflictInfo`，但应该使用 `ArbitrationConflictInfo`（P0修复时重命名）

2. **文件覆盖问题**: 创建新的 `core/constants.py` 时完全覆盖了原文件，丢失了原有的枚举类型定义（`JudgmentType`, `QuestionCategory`, `TheoryType` 等）

## 修复内容

### 1. 修复 arbitration_system.py 中的类型引用

**问题位置**: 6处使用了 `ConflictInfo` 而不是 `ArbitrationConflictInfo`

**修复**:
```python
# 修复前
def request_arbitration(self, conflict: ConflictInfo, ...) -> Optional[str]:
def execute_arbitration(self, conflict: ConflictInfo, ...) -> ArbitrationResult:
async def _ai_arbitration(self, conflict: ConflictInfo, ...) -> ArbitrationResult:
def _rule_based_arbitration(self, conflict: ConflictInfo, ...) -> ArbitrationResult:
def should_arbitrate(self, conflict: ConflictInfo, ...) -> bool:
def create_conflict_info(...) -> ConflictInfo:

# 修复后
def request_arbitration(self, conflict: ArbitrationConflictInfo, ...) -> Optional[str]:
def execute_arbitration(self, conflict: ArbitrationConflictInfo, ...) -> ArbitrationResult:
async def _ai_arbitration(self, conflict: ArbitrationConflictInfo, ...) -> ArbitrationResult:
def _rule_based_arbitration(self, conflict: ArbitrationConflictInfo, ...) -> ArbitrationResult:
def should_arbitrate(self, conflict: ArbitrationConflictInfo, ...) -> bool:
def create_conflict_info(...) -> ArbitrationConflictInfo:
```

**影响文件**:
- `core/arbitration_system.py` - 6处修复
- `core/__init__.py` - 导出名称修复

---

### 2. 恢复 constants.py 原有内容

**问题**: 新的 `constants.py` 只包含配置常量，丢失了原有的枚举类型

**修复方案**:
1. 恢复原 `constants.py` 全部内容（261行）
2. 在文件末尾追加新的配置常量（50行）

**最终文件结构** (311行):
```python
"""
核心常量定义 - 提取魔法字符串为枚举类型
"""
from enum import Enum
from typing import Tuple

# 原有内容（261行）
class JudgmentType(Enum):
    """吉凶判断类型枚举"""
    DA_JI = ("大吉", 1.0, "极为吉利，事事顺遂")
    JI = ("吉", 0.75, "总体吉利，可以进行")
    # ... 完整的枚举定义

class QuestionCategory(Enum):
    """问题类别枚举"""
    CAREER = ("事业", "career", "职业发展、工作变动、升迁机会")
    WEALTH = ("财运", "wealth", "投资理财、收入变化、财务决策")
    # ... 完整的枚举定义

class TheoryType(Enum):
    """理论类型枚举"""
    # ... 完整的枚举定义

class ConflictLevel(Enum):
    """冲突级别枚举"""
    # ... 完整的枚举定义

# 其他枚举和常量...

# ==================== 新增：配置常量（P0/P1修复） ====================

# 理论选择数量
DEFAULT_MAX_THEORIES = 5  # 最多选择的理论数量
DEFAULT_MIN_THEORIES = 3  # 最少选择的理论数量

# 理论适配度阈值
DEFAULT_FITNESS_THRESHOLD = 0.3  # 初始适配度阈值（30%）
FALLBACK_FITNESS_THRESHOLD = 0.15  # 降级阈值

# 冲突级别阈值
JUDGMENT_THRESHOLD_MINOR = 0.2  # 小于20%差异视为微小差异
JUDGMENT_THRESHOLD_SIGNIFICANT = 0.4  # 小于40%差异视为显著差异

# 置信度权重因子
CONFIDENCE_WEIGHT_FACTOR = 1.5  # 提升高置信度理论的影响

# 超时配置
DEFAULT_THEORY_TIMEOUT = 250
DEFAULT_INTERPRETATION_TIMEOUT = 250
DEFAULT_INTERPRETATION_TIMEOUT_SECONDARY = 120
DEFAULT_REPORT_TIMEOUT = 300
DEFAULT_API_TIMEOUT = 60

# 对话流程配置
DEFAULT_VERIFICATION_YEARS = 3
CONVERSATION_STAGE_TIMEOUT = 1800

# 缓存配置
LUNAR_CONVERSION_CACHE_SIZE = 500
BAZI_CALCULATION_CACHE_SIZE = 1000
THEORY_RESULT_CACHE_SIZE = 200
DEFAULT_CACHE_TTL = 86400

# UI配置
WORKER_THREAD_WAIT_TIMEOUT = 2000
PROGRESS_UPDATE_INTERVAL = 100
```

---

## 验证结果

### 语法检查 ✅
```bash
$ python -m py_compile cyber_mantic/core/arbitration_system.py
$ python -m py_compile cyber_mantic/core/constants.py
$ python -m py_compile cyber_mantic/core/__init__.py
# 全部通过
```

### 应用启动 ✅
```bash
$ cd cyber_mantic && python gui.py
# 应用正常启动，无错误
```

---

## 修复文件清单

| 文件 | 修复类型 | 说明 |
|------|---------|------|
| `core/arbitration_system.py` | 类型注解修复 | 6处ConflictInfo改为ArbitrationConflictInfo |
| `core/__init__.py` | 导出修复 | 导出名称更新 |
| `core/constants.py` | 内容恢复+追加 | 恢复原有261行 + 追加50行新常量 |

---

## 经验教训

### 1. 创建新文件前检查是否已存在
- ❌ 错误做法：直接创建新文件覆盖
- ✅ 正确做法：先检查文件是否存在，如已存在则合并内容

### 2. 全局搜索替换要彻底
- ❌ 错误：只修复了部分引用
- ✅ 正确：使用 `grep -rn` 找出所有引用并逐一修复

### 3. 修复后务必进行端到端测试
- ❌ 错误：只做单元测试或语法检查
- ✅ 正确：运行实际应用验证修复效果

---

## 最终状态

### 修复完成 ✅
- ✅ 所有类型引用正确
- ✅ 所有导入正常
- ✅ 应用成功启动
- ✅ 无语法错误

### 文件状态
- `core/arbitration_system.py`: ✅ 已修复
- `core/__init__.py`: ✅ 已修复
- `core/constants.py`: ✅ 已恢复+扩展（261行→311行）

---

## 下一步建议

1. **测试核心功能**: 运行应用测试各功能模块
2. **添加单元测试**: 为新增的验证模块添加测试
3. **文档更新**: 更新相关文档说明新的常量

---

**修复时间**: 2026-01-09 20:40
**修复状态**: ✅ 完成
**应用状态**: ✅ 可正常启动
