# 财税通费用模板添加 Skill

> **目标**：让任何 AI（即使是小白）都能学会自动添加费用模板二级科目
> 
> **难度**：⭐⭐ 初级（跟着步骤做就能成功）
> 
> **预计时间**：30分钟学会

---

## 📖 目录

1. [这是什么东西？](#这是什么东西)
2. [零基础入门（必看）](#零基础入门必看)
3. [一步一步跟着做](#一步一步跟着做)
4. [常见问题排错](#常见问题排错)
5. [API 详解](#api-详解)
6. [进阶技巧](#进阶技巧)

---

## 这是什么东西？

### 一句话解释

这个 Skill 可以**自动把 Excel 里的费用科目，批量添加到财税通系统的费用模板中**。

### 举个例子

你有一个 Excel 表格：

| 一级科目 | 二级科目 |
|---------|---------|
| 差旅费 | 飞机票 |
| 差旅费 | 火车票 |
| 办公费 | 文具 |

运行这个 Skill 后，系统会自动创建：
- 📁 差旅费
  - ✈️ 飞机票（继承差旅费的所有配置）
  - 🚄 火车票（继承差旅费的所有配置）
- 📁 办公费
  - ✏️ 文具（继承办公费的所有配置）

### 为什么要用 AI 来做？

❌ **人工操作**：
- 需要手动一个个点击添加
- 容易遗漏字段配置
- 100个科目要操作 100 次，耗时 2 小时

✅ **AI 自动操作**：
- 一键批量添加
- 自动继承所有字段配置
- 100个科目 2 分钟完成

---

## 零基础入门（必看）

### 你需要知道的基本概念

#### 1. 什么是费用模板？

费用模板 = 报销时可以选择的费用类型

```
财税通系统
├── 费用模板（一级科目）
│   ├── 差旅费
│   │   ├── 飞机票（二级科目）✅ 我们添加这个
│   │   └── 火车票（二级科目）✅ 我们添加这个
│   └── 办公费
│       └── 文具（二级科目）✅ 我们添加这个
```

#### 2. 什么是字段继承？

一级科目有一些配置（比如报销时要填哪些字段），二级科目需要**继承**这些配置。

```
一级科目：差旅费
├── 报销金额（必填）
├── 日期（必填）
└── 描述（选填）
    ↓ 继承给
二级科目：飞机票
├── 报销金额（必填）✅ 自动继承
├── 日期（必填）✅ 自动继承
└── 描述（选填）✅ 自动继承
```

#### 3. 什么是 API？

API = 系统提供的"操作接口"

想象 API 是一个服务员：
- 你对服务员说："我要创建一个费用科目"
- 服务员（API）帮你去厨房（系统）完成操作
- 服务员告诉你："创建成功了"

本 Skill 用到的 API：
- `queryFeeTemplate` - 查询费用模板列表
- `getFeeTemplateById` - 查询单个费用模板详情
- `addFeeTemplate` - 添加费用模板

---

## 一步一步跟着做

### 第一步：准备工作（5分钟）

#### 1.1 确认浏览器已启动

打开终端，运行：

```bash
# 检查 Edge 浏览器是否启动了调试模式
curl http://localhost:9223/json/version
```

✅ **成功标志**：返回类似以下内容
```json
{
  "Browser": "Edg/145.0.3800.97",
  "Protocol-Version": "1.3"
}
```

❌ **失败标志**：`Connection refused`

**解决方法**：
```bash
# 启动 Edge（调试模式）
/Applications/Microsoft\ Edge.app/Contents/MacOS/Microsoft\ Edge \
  --remote-debugging-port=9223
```

#### 1.2 登录财税通系统

1. 打开 Edge 浏览器
2. 访问：https://cst.uf-tree.com
3. 输入账号密码登录
4. 进入"单据设置" → "费用模板"页面
5. **保持页面打开**，不要关闭浏览器

#### 1.3 准备 Excel 文件

创建一个 Excel 文件，命名为 `费用模板.xlsx`

内容格式：

| 一级科目 | 二级科目 |
|---------|---------|
| 差旅费 | 飞机票 |
| 差旅费 | 火车票 |
| 办公费 | 文具用品 |
| 办公费 | 打印耗材 |

**注意事项**：
- ✅ 第一列必须叫"一级科目"
- ✅ 第二列必须叫"二级科目"
- ✅ 一级科目必须是系统中已存在的
- ❌ 不能有空白行

---

### 第二步：获取认证信息（5分钟）

#### 2.1 为什么要获取认证信息？

系统需要知道：
- 你是谁？（Token）
- 你在哪个公司？（Company ID）
- 你的用户ID是什么？（User ID）

这些信息存在浏览器的 `localStorage` 中。

#### 2.2 获取步骤

**方法 A：让 AI 自动获取（推荐）**

AI 会自动连接浏览器，从 `localStorage.vuex` 中提取：

```python
# 伪代码，AI 会自动执行
1. 连接浏览器 WebSocket
2. 执行 JavaScript: localStorage.getItem('vuex')
3. 解析 JSON，提取 token、companyId、userId
```

**方法 B：手动获取（备用）**

如果自动获取失败，可以手动：

1. 在费用模板页面按 `F12` 打开开发者工具
2. 切换到 Console 标签
3. 粘贴执行：
   ```javascript
   JSON.parse(localStorage.getItem('vuex')).user.token
   ```
4. 复制返回的字符串给 AI

---

### 第三步：查询一级科目（5分钟）

#### 3.1 为什么要查询一级科目？

我们需要知道：
- 系统中有哪些一级科目？
- 它们的 ID 是什么？
- 它们的完整配置是什么？（用于继承）

#### 3.2 查询步骤

**调用 API**：

```http
GET https://cst.uf-tree.com/api/bill/feeTemplate/queryFeeTemplate
Headers:
  x-token: {你的token}
Params:
  companyId: {你的companyId}
  status: 0
```

**Python 代码**：

```python
import requests

resp = requests.get(
    "https://cst.uf-tree.com/api/bill/feeTemplate/queryFeeTemplate",
    headers={"x-token": token},
    params={"companyId": company_id, "status": 0}
)

templates = resp.json()["result"]

# 筛选一级科目（parentId = -1）
primary_templates = [t for t in templates if t.get("parentId") == -1]

for t in primary_templates:
    print(f"{t['name']} (ID: {t['id']})")
```

**预期输出**：
```
1 (ID: 9085)
2 (ID: 27940)
3 (ID: 27941)
4 (ID: 27957)
5 (ID: 27960)
```

#### 3.3 ⚠️ 关键：获取完整配置

**重要！** `queryFeeTemplate` 返回的数据**不包含完整的字段配置**。

我们需要对每个一级科目，单独调用 `getFeeTemplateById`：

```python
for template in primary_templates:
    resp = requests.get(
        "https://cst.uf-tree.com/api/bill/feeTemplate/getFeeTemplateById",
        headers={"x-token": token},
        params={"id": template["id"], "companyId": company_id}
    )
    
    detail = resp.json()["result"]
    
    # 现在可以获取完整的字段配置
    applyJson = detail.get("applyJson", [])  # 申请单字段
    feeJson = detail.get("feeJson", [])      # 报销单字段
    icon = detail.get("icon")                 # 图标
    iconColor = detail.get("iconColor")       # 图标颜色
```

---

### 第四步：读取 Excel 并匹配（5分钟）

#### 4.1 读取 Excel

```python
import pandas as pd

df = pd.read_excel("/path/to/费用模板.xlsx")

# 查看数据
print(df)
```

**预期输出**：
```
   一级科目    二级科目
0    差旅费      飞机票
1    差旅费      火车票
2    办公费    文具用品
3    办公费    打印耗材
```

#### 4.2 匹配父级科目

```python
# 创建映射：名称 -> 完整配置
primary_map = {t["name"]: t for t in primary_templates}

for idx, row in df.iterrows():
    primary_name = row["一级科目"]
    secondary_name = row["二级科目"]
    
    # 查找父级配置
    parent = primary_map.get(primary_name)
    
    if parent:
        print(f"✅ 找到父级: {primary_name} (ID: {parent['id']})")
        # 继续创建...
    else:
        print(f"❌ 未找到父级: {primary_name}")
```

---

### 第五步：构建创建请求（关键！5分钟）

#### 5.1 请求结构

**重要！必须是平铺结构，不是嵌套结构！**

❌ **错误**（嵌套结构）：
```json
{
  "userId": 123,
  "companyId": 7061,
  "feeTemplate": {
    "name": "飞机票",
    "parentId": 9085
    // ...
  }
}
```

✅ **正确**（平铺结构）：
```json
{
  "userId": 123,
  "companyId": 7061,
  "name": "飞机票",
  "parentId": 9085,
  "icon": "md-plane",
  "iconColor": "#4c7cc3",
  "status": "1",
  "parentFlag": "0",
  "defaultFlag": false,
  "forceShare": 0,
  "shareDepPermission": 2,
  "applyJson": [...],
  "feeJson": [...]
}
```

#### 5.2 完整代码

```python
# 构建请求
request_data = {
    "userId": user_id,
    "companyId": company_id,
    "name": secondary_name,                    # 二级科目名称
    "parentId": parent["id"],                  # 父级ID
    "icon": parent.get("icon", "md-plane"),    # 继承图标
    "iconColor": parent.get("iconColor", "#4c7cc3"),  # 继承颜色
    "status": "1",                             # 启用
    "parentFlag": "0",                         # 标记为子级
    "defaultFlag": False,
    "forceShare": parent.get("forceShare", 0),
    "shareDepPermission": parent.get("shareDepPermission", 2),
    # 关键：继承单据字段配置
    "applyJson": parent.get("applyJson", []),
    "feeJson": parent.get("feeJson", [])
}
```

---

### 第六步：调用 API 创建（5分钟）

#### 6.1 调用创建 API

```python
resp = requests.post(
    "https://cst.uf-tree.com/api/bill/feeTemplate/addFeeTemplate",
    headers={
        "x-token": token,
        "Content-Type": "application/json"
    },
    json=request_data,
    timeout=10
)

result = resp.json()

if result.get("success") or result.get("code") == 200:
    new_id = result["result"]["id"]
    print(f"✅ 创建成功！新ID: {new_id}")
else:
    print(f"❌ 创建失败: {result.get('message')}")
```

#### 6.2 批量创建

```python
success_count = 0
fail_count = 0

for idx, row in df.iterrows():
    # ... 构建请求 ...
    
    # 调用API
    resp = requests.post(...)
    result = resp.json()
    
    if result.get("success"):
        print(f"✅ [{idx+1}/{len(df)}] {secondary_name}: 成功")
        success_count += 1
    else:
        print(f"❌ [{idx+1}/{len(df)}] {secondary_name}: {result.get('message')}")
        fail_count += 1

print(f"\n📊 完成！成功: {success_count}, 失败: {fail_count}")
```

---

### 第七步：验证结果（5分钟）

#### 7.1 为什么要验证？

确认：
- ✅ 科目是否创建成功
- ✅ 字段是否正确继承

#### 7.2 验证方法

**重要！** 必须用 `getFeeTemplateById`，不能用 `queryFeeTemplate`！

```python
# 查询新创建的科目
resp = requests.get(
    "https://cst.uf-tree.com/api/bill/feeTemplate/getFeeTemplateById",
    headers={"x-token": token},
    params={"id": parent_id, "companyId": company_id}
)

parent = resp.json()["result"]
children = parent.get("children", [])

# 查找刚创建的科目
for child in children:
    if child["name"] == secondary_name:
        has_apply = bool(child.get("applyJson"))
        has_fee = bool(child.get("feeJson"))
        
        print(f"✅ {child['name']}")
        print(f"   applyJson: {'有' if has_apply else '无'} ({len(child.get('applyJson', []))}个字段)")
        print(f"   feeJson: {'有' if has_fee else '无'} ({len(child.get('feeJson', []))}个字段)")
        break
```

---

## 常见问题排错

### 问题 1：连接浏览器失败

**错误信息**：`Connection refused`

**原因**：浏览器未启动调试模式

**解决**：
```bash
# 完全退出 Edge
pkill -f "Microsoft Edge"

# 重新启动（带调试端口）
/Applications/Microsoft\ Edge.app/Contents/MacOS/Microsoft\ Edge \
  --remote-debugging-port=9223
```

### 问题 2：未找到财税通页面

**错误信息**：`未找到 cst.uf-tree.com 页面`

**原因**：
1. 浏览器打开了，但没有访问财税通
2. 或者访问了但没有登录

**解决**：
1. 确保在 Edge 中打开了 https://cst.uf-tree.com
2. 确保已登录
3. 确保在"费用模板"页面

### 问题 3：添加失败，提示"无权限"

**错误信息**：`无操作权限`

**原因**：Token 过期，或者用户没有创建权限

**解决**：
1. 刷新财税通页面
2. 重新获取 Token
3. 确认用户有费用模板管理权限

### 问题 4：字段没有继承

**现象**：创建的科目缺少 applyJson/feeJson

**原因**：使用了 `queryFeeTemplate` 获取父级配置（它返回的数据不完整）

**解决**：
```python
# ❌ 错误：使用 queryFeeTemplate
resp = requests.get("/api/bill/feeTemplate/queryFeeTemplate")

# ✅ 正确：使用 getFeeTemplateById
resp = requests.get("/api/bill/feeTemplate/getFeeTemplateById", 
                    params={"id": parent_id, "companyId": company_id})
```

### 问题 5：请求格式错误

**错误信息**：`费用类型名称不能为空`

**原因**：请求结构错误，使用了嵌套结构

**解决**：
```python
# ❌ 错误：嵌套结构
{"feeTemplate": {"name": "xxx"}}

# ✅ 正确：平铺结构
{"name": "xxx"}
```

---

## API 详解

### API 1: queryFeeTemplate

**用途**：查询费用模板列表

**请求**：
```http
GET /api/bill/feeTemplate/queryFeeTemplate
Headers:
  x-token: {token}
Params:
  companyId: {companyId}
  status: 0
```

**响应**：
```json
{
  "code": 200,
  "result": [
    {
      "id": 9085,
      "name": "1",
      "parentId": -1,
      // ... 其他基础字段
      // ⚠️ 注意：不包含 applyJson/feeJson
    }
  ]
}
```

### API 2: getFeeTemplateById

**用途**：查询单个费用模板详情（包含完整字段）

**请求**：
```http
GET /api/bill/feeTemplate/getFeeTemplateById
Headers:
  x-token: {token}
Params:
  id: {templateId}
  companyId: {companyId}
```

**响应**：
```json
{
  "code": 200,
  "result": {
    "id": 9085,
    "name": "1",
    "applyJson": [...],  // ✅ 完整字段配置
    "feeJson": [...],    // ✅ 完整字段配置
    // ... 其他字段
    "children": [...]    // 子科目列表
  }
}
```

### API 3: addFeeTemplate

**用途**：添加费用模板

**请求**：
```http
POST /api/bill/feeTemplate/addFeeTemplate
Headers:
  x-token: {token}
  Content-Type: application/json
Body:
  {
    "userId": 123,
    "companyId": 7061,
    "name": "飞机票",
    "parentId": 9085,
    "icon": "md-plane",
    "iconColor": "#4c7cc3",
    "status": "1",
    "parentFlag": "0",
    "defaultFlag": false,
    "forceShare": 0,
    "shareDepPermission": 2,
    "applyJson": [...],
    "feeJson": [...]
  }
```

**响应**：
```json
{
  "success": true,
  "code": 200,
  "result": {
    "id": 27980,
    "name": "飞机票",
    // ...
  }
}
```

---

## 进阶技巧

### 技巧 1：处理 Excel 中的多种情况

```python
# 处理空值
df = df.dropna(subset=["一级科目", "二级科目"])

# 去除空格
df["一级科目"] = df["一级科目"].str.strip()
df["二级科目"] = df["二级科目"].str.strip()

# 模糊匹配父级
parent = None
for name, config in primary_map.items():
    if primary_name in name or name in primary_name:
        parent = config
        break
```

### 技巧 2：错误重试

```python
import time

for attempt in range(3):  # 重试3次
    try:
        resp = requests.post(..., timeout=10)
        if resp.status_code == 200:
            break
    except Exception as e:
        print(f"重试 {attempt+1}/3...")
        time.sleep(1)
```

### 技巧 3：批量处理进度显示

```python
from tqdm import tqdm  # pip install tqdm

for idx, row in tqdm(df.iterrows(), total=len(df), desc="添加进度"):
    # ... 处理逻辑 ...
```

---

## 完整代码示例

见 `scripts/add_fee_templates.py`

---

## 总结

### 核心流程图

```
开始
  ↓
连接浏览器获取 Token
  ↓
查询一级科目列表
  ↓
获取一级科目详情（含完整字段）
  ↓
读取 Excel
  ↓
匹配父级科目
  ↓
构建创建请求（继承所有字段）
  ↓
调用 addFeeTemplate API
  ↓
验证结果
  ↓
完成！
```

### 关键记忆点

1. **两个 API 要区分清楚**：
   - `queryFeeTemplate` → 查列表（不含详细字段）
   - `getFeeTemplateById` → 查详情（含完整字段）

2. **请求必须是平铺结构**：
   - ❌ 不要嵌套在 `feeTemplate` 中
   - ✅ 直接放请求体里

3. **一定要继承的字段**：
   - `applyJson`（申请单配置）
   - `feeJson`（报销单配置）
   - `icon`、`iconColor`（样式）

---

**恭喜！你现在掌握了完整的费用模板自动添加技能！** 🎉

有任何问题，查看：
- [常见问题排错](#常见问题排错)
- `examples/` 目录下的示例代码
- 或者直接问 AI
