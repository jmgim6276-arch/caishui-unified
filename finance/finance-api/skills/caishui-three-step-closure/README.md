# 财税通三步闭环自动化 Skill

> **版本**: v1.0  
> **创建日期**: 2026-03-11  
> **目标**: 教AI从零到一学会财税通费用科目-角色-人员完整配置闭环

---

## 📚 目录

1. [什么是三步闭环](#什么是三步闭环)
2. [核心概念](#核心概念)
3. [完整API文档](#完整api文档)
4. [从零教AI学会三步闭环](#从零教ai学会三步闭环)
5. [完整代码示例](#完整代码示例)
6. [常见问题与解决方案](#常见问题与解决方案)
7. [附录：数据映射表](#附录数据映射表)

---

## 什么是三步闭环

### 概念定义

**三步闭环**是指在财税通系统中，将**费用科目**、**角色**、**人员**三个核心要素通过标准化流程关联起来，形成完整的权限控制体系。

```
┌─────────────────────────────────────────────────────────────┐
│                    三步闭环架构图                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   第一步          第二步              第三步                │
│   费用科目  ──→  角色体系  ──→  人员配置                   │
│      ↓              ↓                  ↓                   │
│   二级科目       角色组/角色        费用类型+人员           │
│   (继承字段)     (单据类型)         (权限绑定)              │
│                                                             │
│   示例：          示例：            示例：                  │
│   机器设备  ──→  采购付款单  ──→  张总、韩老师             │
│   原材料    ──→  采购付款单  ──→  张总、韩老师             │
│   办公费    ──→  员工报销单  ──→  OpenClaw               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 为什么叫"闭环"

因为这三个步骤形成了完整的权限控制链条：
1. **人员**能看到什么**单据类型**（角色）
2. **角色**能使用什么**费用类型**（二级科目）
3. **费用类型**属于哪个**一级科目**（财务科目体系）

最终实现了：**人员 → 角色 → 费用类型 → 财务科目** 的完整映射。

---

## 核心概念

### 1. 费用模板（FeeTemplate）

财税通系统中所有费用科目的基础数据结构：

```javascript
{
  "id": 22062,                          // 唯一标识
  "name": "固定资产",                    // 科目名称
  "parentId": -1,                       // -1=一级科目, 其他=二级科目
  "parentFlag": "1",                    // "1"=父级, "0"=子级
  "status": "1",                        // "1"=启用, "0"=停用
  "applyJson": [...],                   // 申请单字段配置
  "feeJson": [...],                     // 费用明细字段配置
  "icon": "md-plane",                   // 图标
  "iconColor": "#4c7cc3"               // 图标颜色
}
```

**关键原则**：二级科目必须继承一级科目的 `applyJson` 和 `feeJson`。

### 2. 角色体系（Role System）

采用 **"角色组 → 角色"** 的层级结构：

```
费用角色组（父节点）
    ├── 采购付款单（子角色）
    │       ├── 费用类型：原材料、机器设备...
    │       └── 人员：张总、韩老师...
    ├── 员工报销单（子角色）
    │       ├── 费用类型：办公费、差旅费...
    │       └── 人员：OpenClaw...
    └── ...
```

### 3. 人员映射

通过 `nickName` 关联系统用户：

```javascript
{
  "id": 13961,          // 员工ID（系统唯一）
  "nickName": "韩老师"   // 显示名称
}
```

---

## 完整API文档

### 第一步：添加二级科目

#### API端点
```http
POST /api/bill/feeTemplate/addFeeTemplate
Headers:
  x-token: {从浏览器获取的token}
  Content-Type: application/json
```

#### 请求参数
```json
{
  "userId": 14939,                                    // 当前用户ID
  "companyId": 7792,                                  // 公司ID
  "name": "机器设备",                                  // 二级科目名称
  "parentId": 22062,                                  // 父级（一级科目）ID
  "icon": "md-plane",                                 // 继承父级
  "iconColor": "#4c7cc3",                            // 继承父级
  "status": "1",                                      // 启用状态
  "parentFlag": "0",                                  // "0"表示二级科目
  "defaultFlag": false,
  "forceShare": 0,                                    // 继承父级
  "shareDepPermission": 2,                           // 继承父级
  "applyJson": [...父级applyJson...],                // ⚠️ 必须继承！
  "feeJson": [...父级feeJson...]                     // ⚠️ 必须继承！
}
```

#### 响应示例
```json
{
  "success": true,
  "result": {
    "id": 28042                                       // 新创建的二级科目ID
  }
}
```

#### 关键步骤
1. **获取父级详情**：调用 `/api/bill/feeTemplate/getFeeTemplateById` 获取 `applyJson` 和 `feeJson`
2. **构建请求**：将父级字段完整复制到子级
3. **设置 parentFlag**：必须为 "0"
4. **调用API**：创建二级科目

---

### 第二步：创建角色组和子角色

#### 2.1 创建父节点（角色组）

**API端点**
```http
POST /api/member/role/add/group
```

**请求参数**
```json
{
  "companyId": 7792,
  "name": "费用角色组"
}
```

**响应示例**
```json
{
  "code": 200,
  "message": "成功",
  "result": 22164                          // 父节点ID，后续创建子角色需要用到
}
```

#### 2.2 创建子角色

**API端点**
```http
POST /api/member/role/add
```

**请求参数**
```json
{
  "companyId": 7792,
  "name": "采购付款单",                     // 角色名称（单据类型）
  "_parentId": 22164,                     // 父节点ID（带下划线）
  "parentId": 22164,                      // 父节点ID（不带下划线）
  "dataType": "FEE_TYPE"                  // 固定值：费用类型角色
}
```

**关键字段说明**
| 字段 | 类型 | 说明 |
|------|------|------|
| `_parentId` | Integer | 父节点ID（必须带下划线） |
| `parentId` | Integer | 父节点ID（不带下划线） |
| `dataType` | String | 固定值 `"FEE_TYPE"` |

**响应示例**
```json
{
  "code": 200,
  "message": "成功",
  "result": 22165                          // 子角色ID
}
```

---

### 第三步：配置费用类型和人员

#### 3.1 获取员工ID映射表

**API端点**
```http
POST /api/member/department/queryCompany
```

**请求参数**
```json
{
  "companyId": 7792
}
```

**响应数据结构**
```json
{
  "code": 200,
  "result": {
    "users": [
      {
        "id": 13961,                      // 员工ID（用于绑定）
        "nickName": "韩老师"               // 显示名称
      },
      {
        "id": 14824,
        "nickName": "张总"
      }
    ]
  }
}
```

**映射规则**
- 使用 `nickName` 作为匹配键
- 使用 `id` 作为员工ID

#### 3.2 获取费用模板ID映射表

**API端点**
```http
GET /api/bill/feeTemplate/queryFeeTemplate
Params:
  companyId: 7792
  status: 1
  pageSize: 1000
```

**响应数据结构**
```json
{
  "code": 200,
  "result": [
    {
      "id": 28042,                       // 费用模板ID
      "name": "测试项目A",                // 费用名称
      "parentId": 28041                   // 不为-1表示二级科目
    }
  ]
}
```

**映射规则**
- 过滤 `parentId != -1` 的项（只取二级科目）
- 使用 `name` 作为匹配键
- 使用 `id` 作为费用模板ID

#### 3.3 保存绑定关系

**API端点**
```http
POST /api/member/role/add/relation
```

**请求参数**
```json
{
  "roleId": 22165,                       // 角色ID
  "userIds": [13961, 14824],            // 员工ID列表（可多个）
  "feeTemplateIds": [28042, 28043],     // 费用模板ID列表（可多个）
  "companyId": 7792
}
```

**关键说明**
- 一个角色可以绑定**多个费用类型**
- 一个角色可以绑定**多个人员**
- 建议在Excel中整理好后，批量绑定

**响应示例**
```json
{
  "code": 200,
  "message": "成功"
}
```

---

## 从零教AI学会三步闭环

### 教学模式：五步法

```
┌─────────────────────────────────────────────────────────────┐
│                    教AI学会三步闭环                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  第1步: 理解概念                                            │
│  └── 解释什么是三步闭环                                     │
│  └── 解释每个步骤的作用                                     │
│                                                             │
│  第2步: 掌握API                                             │
│  └── 教AI每个API的端点、参数、响应                          │
│  └── 强调关键字段和注意事项                                 │
│                                                             │
│  第3步: 获取认证                                            │
│  └── 教AI从浏览器获取Token                                  │
│  └── 教AI获取Company ID                                     │
│                                                             │
│  第4步: 数据映射                                            │
│  └── 教AI如何获取ID映射表                                   │
│  └── 教AI如何匹配Excel数据                                  │
│                                                             │
│  第5步: 执行操作                                            │
│  └── 按顺序执行三步                                         │
│  └── 验证结果                                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 教学要点

#### 要点1：强调继承机制
必须让AI理解：**二级科目必须继承一级科目的字段**

```python
# 正确做法
request_data = {
    "applyJson": parent_template.get("applyJson", []),  # ✅ 继承
    "feeJson": parent_template.get("feeJson", [])       # ✅ 继承
}
```

#### 要点2：强调ID映射
必须让AI理解：**不能猜测ID，必须通过API查询**

```python
# 正确做法：通过API获取映射表
staff_map = {}  # nickName -> id
fee_map = {}    # name -> id
role_map = {}   # name -> id
```

#### 要点3：强调数据准备
必须让AI理解：**先整理数据，再批量执行**

```python
# 按角色分组整理数据
role_config = {
    role_id: {
        "fee_ids": [...],      # 该角色的所有费用类型ID
        "person_ids": [...]    # 该角色的所有人员ID
    }
}
```

---

## 完整代码示例

### 主程序：三步闭环自动化

```python
#!/usr/bin/env python3
"""
财税通三步闭环自动化工具
功能：根据Excel配置表自动完成费用科目-角色-人员配置
"""

import json
import pandas as pd
import requests
import websocket

# 配置
BASE_URL = "https://cst.uf-tree.com"
CDP_PORT = "9223"


def get_auth_from_browser():
    """从浏览器获取认证信息"""
    resp = requests.get(f"http://localhost:{CDP_PORT}/json/list", timeout=10)
    pages = resp.json()
    
    # 找到财税通页面
    ws_url = None
    for page in pages:
        if "cst.uf-tree.com" in page.get("url", ""):
            ws_url = page["webSocketDebuggerUrl"]
            break
    
    # 连接WebSocket获取Token
    ws = websocket.create_connection(ws_url, timeout=10, suppress_origin=True)
    
    ws.send(json.dumps({
        "id": 1,
        "method": "Runtime.evaluate",
        "params": {"expression": "localStorage.getItem('vuex')", "returnByValue": True}
    }))
    
    token = None
    company_id = None
    user_id = None
    
    for _ in range(10):
        resp = ws.recv()
        data = json.loads(resp)
        if data.get("id") == 1:
            value = data.get("result", {}).get("result", {}).get("value")
            if value:
                parsed = json.loads(value)
                token = parsed["user"]["token"]
                company_id = parsed["user"]["company"]["id"]
                user_id = parsed["user"].get("id", 14939)
            break
    
    ws.close()
    
    return {
        "token": token,
        "company_id": company_id,
        "user_id": user_id
    }


def step1_add_secondary_templates(auth, excel_file):
    """
    第一步：添加二级科目（继承一级科目字段）
    """
    print("=" * 70)
    print("【第一步】添加二级科目")
    print("=" * 70)
    
    # 读取Excel
    df = pd.read_excel(excel_file)
    
    # 获取一级科目列表
    resp = requests.get(
        f"{BASE_URL}/api/bill/feeTemplate/queryFeeTemplate",
        headers={"x-token": auth["token"]},
        params={"companyId": auth["company_id"], "status": 1, "pageSize": 1000}
    )
    
    templates = resp.json().get("result", [])
    primary_map = {t["name"]: t for t in templates if t["parentId"] == -1}
    
    # 批量添加二级科目
    success_count = 0
    for _, row in df.iterrows():
        primary_name = row["一级科目类型"]
        secondary_name = row["二级科目类型"]
        
        parent = primary_map.get(primary_name)
        if not parent:
            continue
        
        # 获取父级详情
        detail_resp = requests.get(
            f"{BASE_URL}/api/bill/feeTemplate/getFeeTemplateById",
            headers={"x-token": auth["token"]},
            params={"id": parent["id"], "companyId": auth["company_id"]}
        )
        
        parent_detail = detail_resp.json().get("result", {})
        
        # 创建二级科目（继承字段）
        request_data = {
            "userId": auth["user_id"],
            "companyId": auth["company_id"],
            "name": secondary_name,
            "parentId": parent["id"],
            "icon": parent_detail.get("icon", "md-plane"),
            "iconColor": parent_detail.get("iconColor", "#4c7cc3"),
            "status": "1",
            "parentFlag": "0",
            "defaultFlag": False,
            "forceShare": parent_detail.get("forceShare", 0),
            "shareDepPermission": parent_detail.get("shareDepPermission", 2),
            "applyJson": parent_detail.get("applyJson", []),
            "feeJson": parent_detail.get("feeJson", [])
        }
        
        add_resp = requests.post(
            f"{BASE_URL}/api/bill/feeTemplate/addFeeTemplate",
            headers={"x-token": auth["token"], "Content-Type": "application/json"},
            json=request_data
        )
        
        if add_resp.json().get("code") == 200:
            success_count += 1
    
    print(f"✅ 成功添加 {success_count} 个二级科目")
    return success_count


def step2_create_roles(auth, document_types):
    """
    第二步：创建角色组和子角色
    """
    print("\n" + "=" * 70)
    print("【第二步】创建角色组和子角色")
    print("=" * 70)
    
    # 2.1 创建父节点（角色组）
    group_resp = requests.post(
        f"{BASE_URL}/api/member/role/add/group",
        headers={"x-token": auth["token"], "Content-Type": "application/json"},
        json={"companyId": auth["company_id"], "name": "费用角色组"}
    )
    
    group_result = group_resp.json()
    if group_result.get("code") == 200:
        group_id = group_result["result"]
        print(f"✅ 父节点创建成功，ID: {group_id}")
    else:
        print(f"⚠️  父节点可能已存在，使用已知ID: 22164")
        group_id = 22164
    
    # 2.2 创建子角色
    role_map = {}
    for role_name in document_types:
        role_resp = requests.post(
            f"{BASE_URL}/api/member/role/add",
            headers={"x-token": auth["token"], "Content-Type": "application/json"},
            json={
                "companyId": auth["company_id"],
                "name": role_name,
                "_parentId": group_id,
                "parentId": group_id,
                "dataType": "FEE_TYPE"
            }
        )
        
        role_result = role_resp.json()
        if role_result.get("code") == 200:
            role_id = role_result["result"]
            role_map[role_name] = role_id
            print(f"✅ 角色 '{role_name}' 创建成功，ID: {role_id}")
    
    return role_map


def step3_configure_role_relations(auth, excel_file, role_map):
    """
    第三步：配置费用类型和人员关系
    """
    print("\n" + "=" * 70)
    print("【第三步】配置费用类型和人员关系")
    print("=" * 70)
    
    # 3.1 获取员工ID映射表
    staff_resp = requests.post(
        f"{BASE_URL}/api/member/department/queryCompany",
        headers={"x-token": auth["token"], "Content-Type": "application/json"},
        json={"companyId": auth["company_id"]}
    )
    
    staff_map = {}
    for user in staff_resp.json().get("result", {}).get("users", []):
        staff_map[user["nickName"]] = user["id"]
    
    print(f"✅ 获取到 {len(staff_map)} 个员工映射")
    
    # 3.2 获取费用模板ID映射表
    fee_resp = requests.get(
        f"{BASE_URL}/api/bill/feeTemplate/queryFeeTemplate",
        headers={"x-token": auth["token"]},
        params={"companyId": auth["company_id"], "status": 1, "pageSize": 1000}
    )
    
    fee_map = {}
    for template in fee_resp.json().get("result", []):
        if template["parentId"] != -1:  # 只取二级科目
            fee_map[template["name"]] = template["id"]
    
    print(f"✅ 获取到 {len(fee_map)} 个费用模板映射")
    
    # 3.3 读取Excel并整理配置
    df = pd.read_excel(excel_file)
    
    role_config = {}
    for _, row in df.iterrows():
        doc_type = row["归属单据类型"]
        secondary = row["二级科目类型"]
        persons_str = row["单据适配人员"]
        
        role_id = role_map.get(doc_type)
        fee_id = fee_map.get(secondary)
        
        if not role_id or not fee_id:
            continue
        
        # 解析人员
        person_ids = []
        if pd.notna(persons_str):
            for name in str(persons_str).replace('、', ',').split(','):
                pid = staff_map.get(name.strip())
                if pid:
                    person_ids.append(pid)
        
        # 按角色分组
        if role_id not in role_config:
            role_config[role_id] = {
                "name": doc_type,
                "fee_ids": [],
                "person_ids": set()
            }
        
        role_config[role_id]["fee_ids"].append(fee_id)
        role_config[role_id]["person_ids"].update(person_ids)
    
    # 3.4 批量保存绑定关系
    success_count = 0
    for role_id, config in role_config.items():
        save_resp = requests.post(
            f"{BASE_URL}/api/member/role/add/relation",
            headers={"x-token": auth["token"], "Content-Type": "application/json"},
            json={
                "roleId": role_id,
                "userIds": list(config["person_ids"]),
                "feeTemplateIds": config["fee_ids"],
                "companyId": auth["company_id"]
            }
        )
        
        if save_resp.json().get("code") == 200:
            success_count += 1
            print(f"✅ 角色 '{config['name']}' 配置成功")
    
    return success_count


def main(excel_file):
    """
    主函数：执行完整的三步闭环
    """
    print("🚀 财税通三步闭环自动化工具")
    print("=" * 70)
    
    # 获取认证
    auth = get_auth_from_browser()
    
    # 读取Excel获取单据类型列表
    df = pd.read_excel(excel_file)
    document_types = df["归属单据类型"].unique().tolist()
    
    # 执行三步
    step1_add_secondary_templates(auth, excel_file)
    role_map = step2_create_roles(auth, document_types)
    step3_configure_role_relations(auth, excel_file, role_map)
    
    print("\n" + "=" * 70)
    print("🎉 三步闭环执行完成！")
    print("=" * 70)


if __name__ == "__main__":
    excel_file = "/path/to/your/config.xlsx"
    main(excel_file)
```

---

## 常见问题与解决方案

### Q1: API返回403错误
**原因**：当前账号没有该API的权限  
**解决**：检查账号权限，或联系管理员分配权限

### Q2: 二级科目创建成功但字段未继承
**原因**：未正确传递 `applyJson` 和 `feeJson`  
**解决**：确保从父级获取并完整复制这两个字段

### Q3: 找不到人员ID
**原因**：员工姓名匹配失败  
**解决**：使用 `nickName` 字段匹配，而不是 `name` 字段

### Q4: 角色创建成功但无法配置
**原因**：角色ID不正确  
**解决**：通过API查询或页面确认真实角色ID，不要猜测

---

## 附录：数据映射表

### 员工ID映射表示例

| 显示名称 | 员工ID |
|---------|--------|
| 韩老师 | 13961 |
| 张总 | 14824 |
| OpenClaw | 14843 |
| 李君英 | 10749 |
| 邱工 | 14785 |

### 费用模板ID映射表示例

| 费用名称 | 模板ID |
|---------|--------|
| 测试项目A | 28042 |
| 测试项目B | 28043 |
| 测试项目C | 28044 |
| ... | ... |

### 角色ID映射表示例

| 角色名称 | 角色ID |
|---------|--------|
| 其他付款单 | 22167 |
| 员工报销单/批量付款单 | 22166 |
| 采购付款单 | 22165 |
| 计提单 | 22168 |

---

## 总结

通过本文档，AI可以：
1. ✅ 理解三步闭环的概念和意义
2. ✅ 掌握所有API的调用方法
3. ✅ 学会从浏览器获取认证信息
4. ✅ 学会获取和使用ID映射表
5. ✅ 独立完成完整的三步闭环配置

**记住核心口诀**：
- 先父后子，继承字段
- 查询映射，不要猜测
- 分组整理，批量执行

---

**文档版本**: v1.0  
**最后更新**: 2026-03-11  
**作者**: AI Assistant
