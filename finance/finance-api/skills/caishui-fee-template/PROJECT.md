# 项目说明

## 📦 caishui-fee-template-skill

财税通费用模板批量添加 Skill - 教小白 AI 从零开始自动化添加费用科目

---

## 🎯 项目目标

让任何 AI（即使是零基础）都能学会：
1. ✅ 连接浏览器获取认证
2. ✅ 调用 API 查询数据
3. ✅ 读取 Excel 并批量导入
4. ✅ 处理错误和验证结果

---

## 📁 文件说明

```
caishui-fee-template-skill/
├── README.md                      # 📚 完整教程（11583字，小白必读）
├── config.json                    # ⚙️ Skill 配置文件
├── docs/
│   └── QUICKSTART.md             # 🚀 5分钟快速开始
├── examples/
│   └── 费用模板示例.xlsx          # 📊 Excel 示例文件
├── scripts/
│   └── add_fee_templates.py      # 🐍 主要脚本（300行，详细注释）
└── push-to-github.sh             # 📤 GitHub 推送脚本
```

---

## ✨ 核心功能

| 功能 | 说明 |
|------|------|
| 🔐 自动认证 | 连接 Edge 浏览器，从 localStorage 获取 Token |
| 📋 获取父级 | 查询一级科目并获取完整字段配置（applyJson/feeJson）|
| 📊 读取 Excel | 解析 Excel，匹配父级科目 |
| ➕ 批量添加 | 自动创建二级科目，继承所有字段 |
| ✅ 结果验证 | 验证字段是否正确继承 |

---

## 🚀 快速开始

```bash
# 1. 安装依赖
pip install pandas requests websocket-client openpyxl

# 2. 启动 Edge（调试模式）
/Applications/Microsoft\ Edge.app/Contents/MacOS/Microsoft\ Edge \
  --remote-debugging-port=9223

# 3. 登录财税通并打开费用模板页面

# 4. 运行脚本
python3 scripts/add_fee_templates.py examples/费用模板示例.xlsx
```

详细步骤见 [docs/QUICKSTART.md](docs/QUICKSTART.md)

---

## 📖 学习路径

### 小白路径（推荐）
1. 阅读 [docs/QUICKSTART.md](docs/QUICKSTART.md) - 5分钟上手
2. 运行示例脚本，看效果
3. 遇到问题查看 README.md 的"常见问题排错"
4. 想深入了解再阅读完整 README.md

### 进阶路径
1. 直接阅读 [README.md](README.md) - 完整教程
2. 学习 API 详解和进阶技巧
3. 修改脚本满足自定义需求

---

## 🔑 关键技术点

### 1. API 区别（重要！）

```python
# ❌ queryFeeTemplate - 返回简化数据（不含 applyJson/feeJson）
resp = requests.get("/api/bill/feeTemplate/queryFeeTemplate")

# ✅ getFeeTemplateById - 返回完整数据（含所有字段）
resp = requests.get("/api/bill/feeTemplate/getFeeTemplateById", 
                    params={"id": xxx, "companyId": xxx})
```

### 2. 请求结构（重要！）

```python
# ❌ 错误：嵌套结构
{"feeTemplate": {"name": "xxx"}}

# ✅ 正确：平铺结构
{"name": "xxx", "parentId": xxx, "applyJson": [...]}
```

### 3. 字段继承（关键！）

```python
request_data = {
    # ... 基础字段 ...
    "applyJson": parent.get("applyJson", []),  # 必须继承！
    "feeJson": parent.get("feeJson", [])      # 必须继承！
}
```

---

## 📚 文档详情

### README.md（11583字）
- 零基础概念解释
- 8步详细操作流程
- 常见问题排错（6个问题）
- API 详解（3个API）
- 进阶技巧

### QUICKSTART.md
- 5分钟快速上手
- 最简单的使用方式
- 预期输出示例
- 常见问题速查

### 代码注释
- 300行详细注释
- 每个函数都有文档字符串
- 关键步骤都有中文说明

---

## 🎓 学习价值

通过这个 Skill，小白 AI 可以学会：

1. **浏览器自动化**
   - WebSocket 连接浏览器
   - 从 localStorage 获取数据
   - CDP 协议基础

2. **API 调用**
   - HTTP GET/POST 请求
   - 请求头和参数
   - 响应处理

3. **数据处理**
   - Excel 读取（pandas）
   - 数据清洗和匹配
   - JSON 构建

4. **错误处理**
   - 异常捕获
   - 错误重试
   - 日志输出

5. **工程化思维**
   - 模块化设计
   - 步骤分解
   - 验证机制

---

## 🔄 更新记录

### v1.0.0 (2026-03-10)
- ✅ 初始版本
- ✅ 完整功能实现
- ✅ 详细文档
- ✅ 示例文件

---

## 📞 支持

遇到问题？
1. 查看 README.md 的"常见问题排错"章节
2. 检查 examples/ 目录的示例
3. 查看 scripts/ 的详细注释

---

## 📄 许可证

MIT License

---

**Made with ❤️ by AI Assistant**

**For 泽龙 - AI时代的推动者、革命者 🚀**
