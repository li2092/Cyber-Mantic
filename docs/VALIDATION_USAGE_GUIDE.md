# 数据验证使用指南

## 概述

为了确保前后端数据一致性和类型安全，项目引入了基于 Pydantic 的数据验证层。

## 核心模块

### 1. `core/validation.py` - 验证Schema定义

包含所有数据模型的 Pydantic Schema：
- `PersonBirthInfoSchema` - 个人出生信息
- `UserInputSchema` - 用户输入
- `TheoryAnalysisResultSchema` - 理论分析结果
- `ConflictInfoSchema` - 冲突信息
- `ComprehensiveReportSchema` - 综合报告

### 2. `core/validation_helpers.py` - 验证辅助函数

提供便捷的验证和转换函数。

---

## 使用场景

### 场景1: API接口数据验证

#### 前端发送用户输入
```python
from core.validation_helpers import validate_user_input
from core.exceptions import ValidationError

# 前端传来的JSON数据
user_data = {
    "question_type": "事业",
    "question_description": "最近是否适合跳槽？",
    "birth_year": 1990,
    "birth_month": 6,
    "birth_day": 15,
    "birth_hour": 10,
    "gender": "male",
    "mbti_type": "INTJ"
}

try:
    # 验证并创建UserInput对象
    user_input = validate_user_input(user_data)

    # 验证成功，继续处理
    print(f"验证成功: {user_input.question_type}")

except ValidationError as e:
    # 验证失败，返回错误信息给前端
    print(f"验证失败: {e.message}")
    # 示例错误: "birth_year: 出生年份必须在1900-2100之间"
```

---

### 场景2: 数据完整性检查

#### 检查出生信息完整性
```python
from core.validation import UserInputSchema
from core.validation_helpers import get_validation_errors

# 不完整的出生信息
incomplete_data = {
    "question_type": "事业",
    "question_description": "问题描述",
    "birth_year": 1990,
    # 缺少 birth_month 和 birth_day
}

# 获取验证错误（不抛出异常）
errors = get_validation_errors(UserInputSchema, incomplete_data)

if errors:
    print("数据不完整:")
    for field, error in errors.items():
        print(f"  - {field}: {error}")
    # 输出: birth_month, birth_day: 如果提供出生信息，年、月、日必须完整
```

---

### 场景3: 批量数据验证

#### 验证多个理论结果
```python
from core.validation_helpers import safe_validate
from core.validation import TheoryAnalysisResultSchema

theory_results_data = [
    {
        "theory_name": "八字",
        "calculation_data": {"四柱": "..."},
        "interpretation": "命主五行平衡...",
        "judgment": "吉",
        "judgment_level": 0.75,
        "confidence": 0.85
    },
    {
        "theory_name": "紫微斗数",
        "calculation_data": {},
        "interpretation": "命宫主星...",
        "judgment": "平",
        "judgment_level": 0.5,
        "confidence": 0.8
    }
]

# 批量验证（失败的返回None）
validated_results = []
for data in theory_results_data:
    schema = safe_validate(TheoryAnalysisResultSchema, data, "theory_result")
    if schema:
        validated_results.append(schema)
    else:
        print(f"理论 {data.get('theory_name')} 验证失败")

print(f"成功验证 {len(validated_results)}/{len(theory_results_data)} 个结果")
```

---

### 场景4: 数据范围验证

#### 验证数字范围
```python
from core.validation import UserInputSchema
from pydantic import ValidationError

# 测试无效数据
invalid_data = {
    "question_type": "事业",
    "question_description": "问题",
    "birth_year": 1800,  # ❌ 超出范围（1900-2100）
    "birth_month": 13,   # ❌ 超出范围（1-12）
    "xiaoliu_numbers": [1, 2, 15]  # ❌ 第3个数字超出范围（1-9）
}

try:
    UserInputSchema(**invalid_data)
except ValidationError as e:
    print("验证失败:")
    for error in e.errors():
        field = '.'.join(str(x) for x in error['loc'])
        print(f"  - {field}: {error['msg']}")

# 输出:
#   - birth_year: 出生年份必须在1900-2100之间，当前值：1800
#   - birth_month: 月份必须在1-12之间，当前值：13
#   - xiaoliu_numbers: 小六壬数字必须在1-9之间
```

---

### 场景5: 类型安全验证

#### 验证枚举类型
```python
from core.validation import PersonBirthInfoSchema
from pydantic import ValidationError

# 测试无效的枚举值
invalid_person = {
    "label": "本人",
    "birth_year": 1990,
    "gender": "unknown",  # ❌ 无效值（只能是 "male" 或 "female"）
    "calendar_type": "gregorian",  # ❌ 无效值（只能是 "solar" 或 "lunar"）
    "mbti_type": "ABCD"  # ❌ 无效格式（必须是 [IE][NS][TF][JP]）
}

try:
    PersonBirthInfoSchema(**invalid_person)
except ValidationError as e:
    print("类型验证失败:")
    for error in e.errors():
        field = '.'.join(str(x) for x in error['loc'])
        print(f"  - {field}: {error['msg']}")

# 输出:
#   - gender: Input should be 'male' or 'female'
#   - calendar_type: Input should be 'solar' or 'lunar'
#   - mbti_type: String should match pattern '^[IE][NS][TF][JP]$'
```

---

## 验证规则详解

### UserInputSchema 验证规则

| 字段 | 类型 | 必填 | 验证规则 |
|------|------|------|---------|
| question_type | str | ✅ | 非空字符串 |
| question_description | str | ✅ | 非空字符串 |
| birth_year | int | ❌ | 1900-2100 |
| birth_month | int | ❌ | 1-12 |
| birth_day | int | ❌ | 1-31 |
| birth_hour | int | ❌ | 0-23 |
| birth_minute | int | ❌ | 0-59 |
| gender | str | ❌ | "male" 或 "female" |
| calendar_type | str | ❌ | "solar" 或 "lunar" |
| birth_time_certainty | str | ❌ | "certain", "uncertain", "unknown" |
| mbti_type | str | ❌ | 正则: `^[IE][NS][TF][JP]$` |
| xiaoliu_numbers | List[int] | ❌ | 长度3，值1-9 |
| liuyao_numbers | List[int] | ❌ | 长度6，值6-9 |
| cezi_character | str | ❌ | 单字符 |

**特殊规则**:
- 如果提供出生信息，年、月、日必须完整
- 坐标范围：经度 -180 到 180

---

### TheoryAnalysisResultSchema 验证规则

| 字段 | 类型 | 必填 | 验证规则 |
|------|------|------|---------|
| theory_name | str | ✅ | 非空字符串 |
| calculation_data | dict | ✅ | 任意字典 |
| interpretation | str | ✅ | 非空字符串 |
| judgment | str | ✅ | "大吉", "吉", "平", "凶", "大凶" |
| judgment_level | float | ✅ | 0.0-1.0 |
| confidence | float | ❌ | 0.0-1.0，默认0.8 |

---

### ComprehensiveReportSchema 验证规则

| 字段 | 类型 | 必填 | 验证规则 |
|------|------|------|---------|
| report_id | str | ✅ | 非空字符串 |
| selected_theories | List[str] | ✅ | 至少1个理论 |
| theory_results | List | ✅ | 至少1个结果 |
| executive_summary | str | ✅ | 至少50字 |
| detailed_analysis | str | ✅ | 至少100字 |
| overall_confidence | float | ✅ | 0.0-1.0 |

**特殊规则**:
- `selected_theories` 中的理论必须在 `theory_results` 中都有对应结果

---

## 错误处理最佳实践

### 1. 捕获并转换验证错误
```python
from core.validation_helpers import validate_user_input
from core.exceptions import ValidationError

def process_user_input(data: dict):
    try:
        user_input = validate_user_input(data)
        return {"success": True, "data": user_input.to_dict()}

    except ValidationError as e:
        return {
            "success": False,
            "error": e.message,
            "field": e.field
        }
```

---

### 2. 预先检查数据有效性
```python
from core.validation import UserInputSchema
from core.validation_helpers import get_validation_errors

def check_data_before_processing(data: dict) -> tuple[bool, dict]:
    """
    返回 (是否有效, 错误详情)
    """
    errors = get_validation_errors(UserInputSchema, data)

    if errors:
        return False, errors
    else:
        return True, {}

# 使用
is_valid, errors = check_data_before_processing(user_data)
if not is_valid:
    print("数据无效:", errors)
else:
    # 继续处理
    pass
```

---

### 3. 在UI层显示友好错误信息
```python
from core.validation_helpers import get_validation_errors

# 中文错误消息映射
ERROR_MESSAGES_ZH = {
    "birth_year": "出生年份",
    "birth_month": "出生月份",
    "birth_day": "出生日期",
    "gender": "性别",
    "mbti_type": "MBTI类型"
}

def format_error_for_ui(errors: dict) -> list:
    """格式化错误信息供UI显示"""
    formatted_errors = []

    for field, message in errors.items():
        field_name = ERROR_MESSAGES_ZH.get(field, field)
        formatted_errors.append(f"{field_name}: {message}")

    return formatted_errors

# 使用示例
errors = get_validation_errors(UserInputSchema, invalid_data)
if errors:
    ui_errors = format_error_for_ui(errors)
    for error in ui_errors:
        print(f"⚠️ {error}")
```

---

## 性能考虑

### 1. 缓存验证结果
```python
from functools import lru_cache
from core.validation import UserInputSchema

@lru_cache(maxsize=128)
def validate_cached(data_json: str):
    """缓存验证结果（仅用于不可变数据）"""
    import json
    data = json.loads(data_json)
    return UserInputSchema(**data)
```

---

### 2. 异步验证（大批量数据）
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor
from core.validation_helpers import safe_validate
from core.validation import TheoryAnalysisResultSchema

async def validate_batch_async(data_list: list):
    """异步批量验证"""
    loop = asyncio.get_event_loop()

    with ThreadPoolExecutor() as executor:
        tasks = [
            loop.run_in_executor(
                executor,
                safe_validate,
                TheoryAnalysisResultSchema,
                data,
                f"item_{i}"
            )
            for i, data in enumerate(data_list)
        ]

        results = await asyncio.gather(*tasks)
        return [r for r in results if r is not None]

# 使用
# results = await validate_batch_async(large_data_list)
```

---

## 集成测试示例

### 完整的API端点验证流程
```python
from flask import Flask, request, jsonify
from core.validation_helpers import validate_user_input
from core.exceptions import ValidationError

app = Flask(__name__)

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """分析API端点"""
    try:
        # 1. 获取请求数据
        data = request.get_json()

        # 2. 验证数据
        user_input = validate_user_input(data)

        # 3. 执行分析
        # result = decision_engine.analyze(user_input)

        # 4. 返回结果
        return jsonify({
            "success": True,
            "data": {
                "question_type": user_input.question_type,
                # ... 其他结果
            }
        })

    except ValidationError as e:
        # 验证失败，返回400错误
        return jsonify({
            "success": False,
            "error": "数据验证失败",
            "details": e.message
        }), 400

    except Exception as e:
        # 其他错误，返回500错误
        return jsonify({
            "success": False,
            "error": "服务器内部错误"
        }), 500
```

---

## 总结

### 优势
✅ **类型安全** - 编译时检查类型错误
✅ **数据验证** - 自动验证范围、格式、必填项
✅ **一致性** - 前后端使用同一套Schema
✅ **易维护** - 集中管理验证规则
✅ **友好错误** - 详细的错误信息

### 最佳实践
1. **总是验证外部输入** - API、用户输入、文件导入
2. **使用辅助函数** - 简化验证流程
3. **捕获并处理错误** - 提供友好的错误信息
4. **编写测试** - 确保验证规则正确
5. **保持Schema同步** - 修改数据模型时更新Schema

---

**更新时间**: 2026-01-09
**维护者**: 项目团队
