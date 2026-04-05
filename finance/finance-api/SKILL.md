---
name: finance-api
description: 财税通财务系统三表生成与导入一体化工具。包含Agent1.1（生成三表）和Agent2.2（导入财税通），支持"生成三表→导入系统"全流程自动化。
---

# 财税通财务系统一体化工具

## 概述

此技能整合了 **Agent1.1（三表生成）** 和 **Agent2.2（系统导入）**，实现：
1. **生成三表**：01添加员工、02费用科目配置、03单据表
2. **自动导入**：直接导入财税通系统

## 快速开始

### 一键生成并导入（推荐）

```bash
# 完整流程：生成三表 + 导入系统
python ~/.openclaw/skills/finance-api/scripts/generate_and_import.py
```

### 分步执行

```bash
# 仅生成三表
python ~/.openclaw/skills/finance-api/scripts/generate_and_import.py --skip-import

# 仅导入（使用已生成的三表）
python ~/.openclaw/skills/finance-api/scripts/generate_and_import.py --skip-generate

# 环境检查
python ~/.openclaw/skills/finance-api/scripts/generate_and_import.py --preflight-only
```

### 指定公司ID

```bash
python ~/.openclaw/skills/finance-api/scripts/generate_and_import.py --company-id 7792
```

## 目录结构

```
finance-api/
├── scripts/
│   ├── generate_and_import.py      # 统一入口（一键全流程）
│   ├── agent1/                      # Agent1.1 - 生成三表
│   │   ├── generate_three_sheets_from_customer_template.py
│   │   ├── preflight_check.py
│   │   └── generate_unique_names.py
│   ├── agent2/                      # Agent2.2 - 导入系统
│   │   └── import_from_agent1.py
│   └── batch_add_api.py             # 基础API工具
├── assets/
│   └── 客户模板.xlsx                # 三表生成模板
└── references/                      # API文档
```

## 使用场景

### 场景1：完整流程（生成+导入）
```
用户：生成三表并导入
AI：运行 generate_and_import.py（全自动）
```

### 场景2：仅生成表格
```
用户：生成三表，先不导入
AI：运行 generate_and_import.py --skip-import
```

### 场景3：仅导入已有表格
```
用户：导入之前生成的三表
AI：运行 generate_and_import.py --skip-generate
```

### 场景4：环境检查
```
用户：检查财税通环境
AI：运行 generate_and_import.py --preflight-only
```

## 前置要求

1. **浏览器已启动调试模式**
   ```bash
   /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
     --remote-debugging-port=9222 \
     --remote-allow-origins='*'
   ```

2. **已登录财税通**
   - 访问 https://cst.uf-tree.com
   - 确保有权限访问目标公司

3. **Python依赖**
   ```bash
   pip install openpyxl requests websocket-client pandas
   ```

## 三表说明

| 表名 | 内容 | 生成方式 |
|------|------|----------|
| 01_添加员工 | 姓名、手机号、部门 | 自动生成 |
| 02_费用科目配置 | 一/二/三/四级科目、单据映射 | 自动生成 |
| 03_单据表 | 单据模板、审批流、费用限制 | 自动生成 |

## 更新日志

### 2026-04-05
- 整合 Agent1.1 + Agent2.2
- 新增统一入口 `generate_and_import.py`
- 支持一键全流程或分步执行

### 2026-04-04
- Agent2.2: 完善费用角色自动创建与绑定

### 2026-04-02
- Agent1.1: 优化三表生成逻辑，新增四级科目

## 注意事项

1. **公司ID**：脚本会自动从浏览器获取，也可手动指定 `--company-id`
2. **Token**：从浏览器 localStorage 自动读取
3. **模板**：确保 `assets/客户模板.xlsx` 存在
4. **输出**：生成的三表保存在 `assets/` 目录

---
**提示**：如遇到问题，先运行 `--preflight-only` 检查环境。
