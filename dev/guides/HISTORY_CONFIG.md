# 历史记录保存路径配置指南

本文档说明如何自定义历史记录的保存位置。

## 📁 默认保存路径

默认情况下，历史记录保存在项目目录下：

```
cyber_mantic/
├── data/
│   └── user/
│       ├── history.db          # 历史记录数据库
│       └── exports/            # 导出文件夹（PDF、JSON等）
```

## ⚙️ 自定义保存路径

### 方法一：使用 user_config.yaml（推荐）

1. **复制示例文件**

```bash
cp user_config.yaml.example user_config.yaml
```

2. **编辑 user_config.yaml**

```yaml
data:
  history:
    # 历史记录数据库保存路径
    db_path: "D:/我的文档/玄数历史记录/history.db"

    # 历史记录导出文件夹
    export_folder: "D:/我的文档/玄数历史记录/导出"
```

3. **重启应用**

配置会在下次启动时生效。

### 方法二：直接修改 config.yaml

**不推荐**，因为 config.yaml 会被git追踪，可能导致配置冲突。

```yaml
data:
  history:
    db_path: "D:/我的文档/玄数历史记录/history.db"
    export_folder: "D:/我的文档/玄数历史记录/导出"
```

## 📝 路径格式说明

### Windows 路径

```yaml
# 方式1：使用正斜杠 /（推荐）
db_path: "D:/我的文档/玄数历史记录/history.db"

# 方式2：使用双反斜杠 \\
db_path: "D:\\我的文档\\玄数历史记录\\history.db"
```

### Linux/macOS 路径

```yaml
# 绝对路径
db_path: "/home/user/Documents/cyber_mantic_history/history.db"

# 使用 ~ 表示用户目录
db_path: "~/Documents/cyber_mantic_history/history.db"
```

### 相对路径

```yaml
# 相对于项目根目录
db_path: "data/user/history.db"

# 相对路径（向上一级）
db_path: "../cyber_mantic_data/history.db"
```

## 🔐 权限要求

确保配置的路径：
- ✅ 目录存在或程序有权限创建
- ✅ 有读写权限
- ✅ 磁盘空间充足（建议至少预留 100MB）

## 🔄 迁移现有历史记录

如果你想将已有的历史记录迁移到新位置：

### Windows

```bash
# 1. 停止应用
# 2. 复制数据库文件
copy "data\user\history.db" "D:\我的文档\玄数历史记录\history.db"
# 3. 修改配置
# 4. 重启应用
```

### Linux/macOS

```bash
# 1. 停止应用
# 2. 复制数据库文件
cp data/user/history.db ~/Documents/cyber_mantic_history/history.db
# 3. 修改配置
# 4. 重启应用
```

## 🗄️ 历史记录数据库结构

历史记录使用 SQLite 数据库存储，包含：

- **analysis_history 表**：分析报告主表
  - report_id：报告唯一ID
  - created_at：创建时间
  - question_type：问题类型
  - question_desc：问题描述
  - selected_theories：使用的术数理论
  - executive_summary：执行摘要
  - report_data：完整报告JSON数据
  - user_input_summary：用户输入摘要

## 📊 导出文件夹

导出文件夹用于保存：
- 📄 PDF格式报告
- 📋 JSON格式数据
- 📈 Markdown格式文档
- 🖼️ 图表和可视化

配置示例：

```yaml
data:
  history:
    export_folder: "D:/我的文档/玄数历史记录/导出"
```

导出文件会按日期组织：

```
导出/
├── 2025-01-01/
│   ├── 报告_八字分析_001.pdf
│   └── 报告_八字分析_001.json
├── 2025-01-02/
│   └── 报告_奇门遁甲_002.pdf
```

## ⚠️ 注意事项

1. **路径中包含中文**
   - 完全支持，但建议使用引号包裹路径
   - 示例：`db_path: "D:/我的文档/玄数/history.db"`

2. **网络驱动器**
   - 支持，但可能影响性能
   - 示例：`db_path: "Z:/Network/cyber_mantic/history.db"`

3. **云同步文件夹**
   - 可以保存到 OneDrive、Dropbox 等
   - 但**不建议同时在多台设备运行**，可能导致数据库冲突

4. **备份建议**
   - 定期备份 history.db 文件
   - 可以使用文件版本控制或自动备份工具

## 🔧 故障排除

### 问题：启动时提示"无法创建历史记录数据库"

**解决方案**：
1. 检查路径是否正确
2. 检查目录权限
3. 检查磁盘空间
4. 尝试使用默认路径

### 问题：历史记录丢失

**解决方案**：
1. 检查 user_config.yaml 中的路径配置
2. 查找旧的 data/user/history.db 文件
3. 恢复备份文件

### 问题：配置不生效

**解决方案**：
1. 确认文件名为 `user_config.yaml`（不是 .example）
2. 检查 YAML 格式是否正确（缩进、冒号等）
3. 重启应用
4. 查看日志文件确认配置是否被读取

## 📚 相关文档

- [配置文件说明](CONFIG.md)
- [数据备份指南](BACKUP.md)
- [常见问题解答](FAQ.md)
