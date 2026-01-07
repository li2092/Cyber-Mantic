# 工具脚本

本目录包含用于项目维护和管理的工具脚本。

## 脚本列表

### 1. clear_data.py - 数据清理工具

**功能**：
- 清理对话历史记录
- 清理分析记录
- 清理缓存数据
- 优化数据库（回收空间）
- 显示数据库信息

**使用方法**：

```bash
# 查看数据库信息
python tools/clear_data.py --info

# 清理对话历史
python tools/clear_data.py --clear-conversations

# 清理缓存
python tools/clear_data.py --clear-cache

# 清理分析记录（需要确认）
python tools/clear_data.py --clear-records --confirm

# 清理所有数据（需要确认）
python tools/clear_data.py --clear-all --confirm

# 优化数据库
python tools/clear_data.py --vacuum

# 指定数据库路径
python tools/clear_data.py --db-path custom/path/database.db --info
```

**使用场景**：

1. **测试前清理数据**
   ```bash
   # 清理对话和缓存，保留分析记录
   python tools/clear_data.py --clear-conversations --clear-cache
   ```

2. **完全重置数据**
   ```bash
   # 清理所有数据并优化数据库
   python tools/clear_data.py --clear-all --confirm --vacuum
   ```

3. **释放磁盘空间**
   ```bash
   # 优化数据库以回收删除数据占用的空间
   python tools/clear_data.py --vacuum
   ```

4. **检查数据状态**
   ```bash
   # 查看各表的记录数和文件大小
   python tools/clear_data.py --info
   ```

**安全提示**：
- ⚠️ 清理分析记录需要 `--confirm` 参数（防止误删）
- ✅ 清理对话历史和缓存无需确认（数据可重新生成）
- 💡 建议在清理前先使用 `--info` 查看数据状态

## 开发新工具

如需添加新的工具脚本，请遵循以下规范：

1. **命名规范**：使用小写字母和下划线（如 `tool_name.py`）
2. **文档注释**：脚本开头包含功能说明和使用示例
3. **参数解析**：使用 `argparse` 模块
4. **错误处理**：捕获异常并提供友好的错误信息
5. **更新README**：在本文件中添加工具说明

## 许可证

这些工具脚本遵循项目主许可证。

---

**创建时间**：2026-01-03
**维护者**：开发团队
