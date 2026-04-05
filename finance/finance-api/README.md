# 财税通财务系统API与自动化工具

🚀 **OpenClaw Skill** - 财税通（凯旋创智）财务系统的API接口和自动化工具集合

## 📦 安装

```bash
# 安装skill
openclaw skills install finance-api.skill

# 或复制到skills目录
cp finance-api.skill ~/.openclaw/skills/
```

## 🎯 功能特性

### 1. 批量添加员工 ⭐
- **API高速导入** - 0.8秒/人，比浏览器快10倍
- **浏览器自动化** - 无需API权限，稳定可靠
- **自动获取Token** - 从已登录浏览器实时读取
- **智能部门映射** - 自动匹配部门ID

### 2. 财务API文档
- 单据管理API
- 借款/费用管理API  
- 审批流程API
- 部门/组件管理API

### 3. 自动化脚本
- `batch_add_api.py` - API批量添加员工
- `auto_add_v10.py` - 浏览器自动化
- `auto_add_universal_v2.py` - 通用自动化
- `analyze_dialog.py` - 页面元素分析
- `auto_config_helper.py` - 配置辅助

## 🚀 快速开始

### 批量添加员工

#### 准备工作

1. **安装依赖**
```bash
cd ~/.openclaw/skills/finance-api/scripts
pip install -r requirements.txt
playwright install chromium
```

2. **启动Chrome调试模式**
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
```

3. **登录系统**
- 访问 https://cst.uf-tree.com
- 输入账号密码登录
- 选择企业进入系统
- **保持浏览器窗口打开**

4. **准备员工数据**
```bash
cp ~/.openclaw/skills/finance-api/assets/employees_template.csv ~/Desktop/employees.csv
# 编辑CSV文件，添加员工信息
```

#### 运行脚本

**方式1：API高速导入（推荐）**
```bash
python ~/.openclaw/skills/finance-api/scripts/batch_add_api.py
```

**方式2：浏览器自动化**
```bash
python ~/.openclaw/skills/finance-api/scripts/auto_add_v10.py
```

## 📊 数据格式

### employees.csv

```csv
姓名,手机号,部门
张三,13800138000,1
李四,13800138001,2
王五,13800138002,3
```

**部门编号对应：**
- 1 → 测试门店1
- 2 → 测试门店2
- 3 → 测试门店3

脚本会自动获取真实的部门ID（如9151, 9152, 9153）

## 🔧 使用示例

### 直接调用API

```python
import requests

TOKEN = "从浏览器获取的token"

headers = {
    "x-token": TOKEN,
    "Content-Type": "application/json"
}

payload = {
    "nickName": "张三",
    "mobile": "13800138000",
    "departmentIds": [9151],
    "companyId": 7792
}

response = requests.post(
    "https://cst.uf-tree.com/api/member/userInfo/add",
    headers=headers,
    json=payload
)

print(response.json())
```

## 📚 API文档

完整的API文档保存在 `references/` 目录：
- `bill.html` - 单据管理API
- `member.html` - 成员管理API

## ❓ 常见问题

### Q1: API返回403无操作权限？
**原因：** 部门ID不正确或缺少companyId
**解决：** 使用 `batch_add_api.py`，它会自动获取正确的部门ID

### Q2: 浏览器连接失败？
**原因：** Chrome未启动调试模式
**解决：** 
```bash
chrome --remote-debugging-port=9222
```

### Q3: 如何获取部门真实ID？
**解决：** 脚本会自动从页面获取并显示映射关系

## 📁 文件结构

```
finance-api/
├── SKILL.md              # 技能说明文档
├── scripts/              # 自动化脚本
│   ├── batch_add_api.py      # API批量添加
│   ├── auto_add_v10.py       # 浏览器自动化
│   ├── auto_add_universal_v2.py
│   ├── analyze_dialog.py
│   ├── auto_config_helper.py
│   └── requirements.txt      # Python依赖
├── references/           # API文档
│   ├── bill.html         # 单据API
│   ├── member.html       # 成员API
│   └── libs/             # 前端资源
└── assets/               # 模板文件
    └── employees_template.csv
```

## 🤝 分享

将 `finance-api.skill` 文件分享给其他人：

```bash
# 接收方安装
openclaw skills install finance-api.skill
```

## 📝 更新日志

### v1.0.0
- ✅ 整合API文档和自动化脚本
- ✅ 支持批量添加员工
- ✅ 自动获取Token和部门ID
- ✅ 提供CSV模板文件

## 📄 许可证

MIT License

---

**注意：** 本工具仅供学习和合法使用，请遵守相关法律法规。
