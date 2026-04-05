#!/usr/bin/env python3
"""
财税通三步闭环自动化工具
============================

功能：根据Excel配置表自动完成财税通系统的三步闭环配置
      1. 添加二级科目（继承一级科目字段）
      2. 创建角色组和子角色
      3. 配置费用类型和人员关系

作者: AI Assistant
版本: v1.0
日期: 2026-03-11
"""

import json
import pandas as pd
import requests
import websocket
import time
import sys
from pathlib import Path

# 配置
BASE_URL = "https://cst.uf-tree.com"
CDP_PORT = "9223"

# 禁用SSL警告
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def print_header(title):
    """打印标题"""
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)


def print_step(step_num, description):
    """打印步骤信息"""
    print(f"\n【步骤 {step_num}】{description}")
    print("-" * 70)


def get_auth_from_browser():
    """
    从浏览器获取认证信息
    
    通过Edge浏览器的远程调试接口获取Token和Company ID
    
    Returns:
        dict: {
            "token": "xxx",
            "company_id": xxx,
            "user_id": xxx
        }
    """
    print("  🔌 连接 Edge 浏览器...")
    
    # 获取页面列表
    resp = requests.get(f"http://localhost:{CDP_PORT}/json/list", timeout=10)
    pages = resp.json()
    
    # 找到财税通页面
    ws_url = None
    for page in pages:
        if "cst.uf-tree.com" in page.get("url", ""):
            ws_url = page["webSocketDebuggerUrl"]
            break
    
    if not ws_url:
        raise Exception("❌ 未找到财税通页面，请确认已登录并打开费用模板页面")
    
    print("  ✅ 已连接到浏览器")
    
    # 连接 WebSocket 获取 Token
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
    
    if not token:
        raise Exception("❌ 获取 Token 失败，请确认已登录")
    
    print(f"  ✅ Token: {token[:30]}...")
    print(f"  ✅ Company ID: {company_id}")
    print(f"  ✅ User ID: {user_id}")
    
    return {
        "token": token,
        "company_id": company_id,
        "user_id": user_id
    }


def step1_add_secondary_templates(auth, excel_file):
    """
    第一步：添加二级科目（继承一级科目字段）
    
    根据Excel中的"一级科目类型"和"二级科目类型"列，
    自动创建二级科目，并继承对应一级科目的字段配置。
    
    Args:
        auth: 认证信息字典
        excel_file: Excel配置文件路径
    
    Returns:
        int: 成功创建的二级科目数量
    """
    print_step(1, "添加二级科目（继承一级科目字段）")
    
    # 读取Excel
    print(f"  📊 读取Excel: {excel_file}")
    df = pd.read_excel(excel_file)
    # 清理列名（去除特殊字符）
    df.columns = [col.strip().replace('\xa0', '').replace('\n', '') for col in df.columns]
    print(f"  ✅ 共 {len(df)} 条配置")
    
    # 获取一级科目列表
    print("  📋 查询一级科目列表...")
    resp = requests.get(
        f"{BASE_URL}/api/bill/feeTemplate/queryFeeTemplate",
        headers={"x-token": auth["token"]},
        params={"companyId": auth["company_id"], "status": 0, "pageSize": 1000},
        timeout=10,
        verify=False
    )
    
    if resp.status_code != 200:
        raise Exception(f"❌ 查询失败: {resp.status_code}")
    
    result = resp.json()
    if result.get("code") != 200:
        raise Exception(f"❌ API错误: {result.get('msg')}")
    
    templates = result.get("result", [])
    primary_map = {t["name"]: t for t in templates if t.get("parentId") == -1}
    
    print(f"  ✅ 找到 {len(primary_map)} 个一级科目")
    
    # 批量添加二级科目
    print("  🚀 开始添加二级科目...")
    success_count = 0
    
    # 适配不同的列名格式
    primary_col = "一级科目类型" if "一级科目类型" in df.columns else "一级科目"
    secondary_col = "二级科目类型" if "二级科目类型" in df.columns else "二级科目"
    
    for idx, row in df.iterrows():
        primary_name = row.get(primary_col)
        secondary_name = row.get(secondary_col)
        
        if pd.isna(primary_name) or pd.isna(secondary_name):
            continue
        
        primary_name = str(primary_name).strip()
        secondary_name = str(secondary_name).strip()
        
        print(f"\n  [{idx+1}/{len(df)}] {primary_name} → {secondary_name}")
        
        # 查找父级
        parent = primary_map.get(primary_name)
        if not parent:
            print(f"     ❌ 未找到一级科目: {primary_name}")
            continue
        
        # 获取父级详细信息（关键！）
        detail_resp = requests.get(
            f"{BASE_URL}/api/bill/feeTemplate/getFeeTemplateById",
            headers={"x-token": auth["token"]},
            params={"id": parent["id"], "companyId": auth["company_id"]},
            timeout=10,
            verify=False
        )
        
        if detail_resp.status_code != 200:
            print(f"     ❌ 获取父级详情失败")
            continue
        
        detail_result = detail_resp.json()
        if detail_result.get("code") != 200:
            print(f"     ❌ 获取父级详情失败: {detail_result.get('msg')}")
            continue
        
        parent_detail = detail_result.get("result", {})
        
        # 构建请求（平铺结构，继承字段！）
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
            # 关键：继承单据字段配置
            "applyJson": parent_detail.get("applyJson", []),
            "feeJson": parent_detail.get("feeJson", [])
        }
        
        # 调用创建API
        add_resp = requests.post(
            f"{BASE_URL}/api/bill/feeTemplate/addFeeTemplate",
            headers={"x-token": auth["token"], "Content-Type": "application/json"},
            json=request_data,
            timeout=10,
            verify=False
        )
        
        if add_resp.status_code == 200:
            add_result = add_resp.json()
            if add_result.get("code") == 200 or add_result.get("success"):
                new_id = add_result.get('result', {}).get('id', 'N/A')
                print(f"     ✅ 创建成功 (ID: {new_id})")
                success_count += 1
            else:
                msg = str(add_result.get('message', ''))
                if "已存在" in msg or "重复" in msg:
                    print(f"     ⚠️  已存在，跳过")
                    success_count += 1
                else:
                    print(f"     ❌ 失败: {add_result.get('message', '未知错误')}")
        else:
            print(f"     ❌ HTTP错误: {add_resp.status_code}")
        
        # 小延迟，避免请求过快
        time.sleep(0.5)
    
    print(f"\n  📊 第一步完成: {success_count}/{len(df)} 个二级科目")
    return success_count


def step2_create_roles(auth, document_types):
    """
    第二步：创建角色组和子角色
    
    根据单据类型列表创建角色组（父节点）和子角色。
    
    Args:
        auth: 认证信息字典
        document_types: 单据类型列表（去重后的角色名称）
    
    Returns:
        dict: 角色名称到ID的映射表
    """
    print_step(2, "创建角色组和子角色")
    
    # 2.1 创建父节点（角色组）
    print("  1️⃣ 创建父节点：费用角色组")
    
    group_payload = {
        "companyId": auth["company_id"],
        "name": "费用角色组"
    }
    
    group_resp = requests.post(
        f"{BASE_URL}/api/member/role/add/group",
        headers={"x-token": auth["token"], "Content-Type": "application/json"},
        json=group_payload,
        timeout=10,
        verify=False
    )
    
    group_result = group_resp.json()
    if group_result.get("code") == 200:
        group_id = group_result["result"]
        print(f"     ✅ 父节点创建成功，ID: {group_id}")
    else:
        print(f"     ⚠️  父节点可能已存在，尝试查询现有角色组...")
        # 查询现有的角色组
        role_resp = requests.post(
            f"{BASE_URL}/api/member/role/query",
            headers={"x-token": auth["token"], "Content-Type": "application/json"},
            json={"companyId": auth["company_id"], "pageSize": 1000},
            timeout=10,
            verify=False
        )
        roles = role_resp.json().get("result", {}).get("records", [])
        parent_roles = [r for r in roles if r.get("parentId") == -1 or r.get("parentId") is None]
        if parent_roles:
            group_id = parent_roles[0].get("id")
            print(f"     ✅ 使用现有角色组: {parent_roles[0].get('name')} (ID: {group_id})")
        else:
            print(f"     ❌ 没有可用的角色组")
            return {}
    
    # 2.2 创建子角色
    print(f"\n  2️⃣ 创建子角色（父节点ID: {group_id}）")
    
    role_map = {}
    for role_name in document_types:
        print(f"\n     创建角色: {role_name}")
        
        role_payload = {
            "companyId": auth["company_id"],
            "name": role_name,
            "_parentId": group_id,
            "parentId": group_id,
            "dataType": "FEE_TYPE"
        }
        
        role_resp = requests.post(
            f"{BASE_URL}/api/member/role/add",
            headers={"x-token": auth["token"], "Content-Type": "application/json"},
            json=role_payload,
            timeout=10,
            verify=False
        )
        
        if role_resp.status_code == 200:
            role_result = role_resp.json()
            print(f"        响应: {role_result}")
            if role_result.get("code") == 200:
                role_id = role_result["result"]
                role_map[role_name] = role_id
                print(f"        ✅ 成功! ID: {role_id}")
            elif "已存在" in str(role_result.get('msg', '')) or "已存在" in str(role_result.get('message', '')):
                print(f"        ⚠️  已存在")
            else:
                print(f"        ❌ 失败: {role_result.get('msg', role_result.get('message', '未知错误'))}")
        else:
            print(f"        ❌ HTTP错误: {role_resp.status_code}")
            try:
                print(f"        错误详情: {role_resp.text}")
            except:
                pass
        
        time.sleep(0.3)
    
    print(f"\n  📊 第二步完成: {len(role_map)}/{len(document_types)} 个角色")
    return role_map


def step3_configure_role_relations(auth, excel_file, role_map):
    """
    第三步：配置费用类型和人员关系
    
    为每个角色绑定对应的费用类型和人员。
    
    Args:
        auth: 认证信息字典
        excel_file: Excel配置文件路径
        role_map: 角色名称到ID的映射表
    
    Returns:
        int: 成功配置的角色数量
    """
    print_step(3, "配置费用类型和人员关系")
    
    # 3.1 获取员工ID映射表
    print("  1️⃣ 获取员工ID映射表...")
    
    staff_resp = requests.post(
        f"{BASE_URL}/api/member/department/queryCompany",
        headers={"x-token": auth["token"], "Content-Type": "application/json"},
        json={"companyId": auth["company_id"]},
        timeout=10,
        verify=False
    )
    
    staff_map = {}
    if staff_resp.status_code == 200:
        staff_result = staff_resp.json()
        if staff_result.get("code") == 200:
            for user in staff_result.get("result", {}).get("users", []):
                nick_name = user.get("nickName", "")
                user_id = user.get("id")
                if nick_name and user_id:
                    staff_map[nick_name] = user_id
    
    print(f"     ✅ 获取到 {len(staff_map)} 个员工映射")
    
    # 3.2 获取费用模板ID映射表
    print("\n  2️⃣ 获取费用模板ID映射表...")
    
    fee_resp = requests.get(
        f"{BASE_URL}/api/bill/feeTemplate/queryFeeTemplate",
        headers={"x-token": auth["token"]},
        params={"companyId": auth["company_id"], "status": 0, "pageSize": 1000},
        timeout=10,
        verify=False
    )
    
    fee_map = {}
    if fee_resp.status_code == 200:
        fee_result = fee_resp.json()
        if fee_result.get("code") == 200:
            for template in fee_result.get("result", []):
                if template.get("parentId") != -1:  # 只取二级科目
                    fee_map[template["name"]] = template["id"]
    
    print(f"     ✅ 获取到 {len(fee_map)} 个费用模板映射")
    
    # 3.3 读取Excel并整理配置
    print("\n  3️⃣ 整理配置数据...")
    
    df = pd.read_excel(excel_file)
    # 清理列名（去除特殊字符）
    df.columns = [col.strip().replace('\xa0', '').replace('\n', '') for col in df.columns]
    
    # 按角色分组整理数据
    role_config = {}
    
    # 适配不同的列名格式
    doc_type_col = "归属单据类型" if "归属单据类型" in df.columns else ("单据类型" if "单据类型" in df.columns else "单据类型 ")
    secondary_col = "二级科目类型" if "二级科目类型" in df.columns else "二级科目"
    persons_col = "单据适配人员" if "单据适配人员" in df.columns else "人员"
    
    for _, row in df.iterrows():
        doc_type = row.get(doc_type_col)
        secondary = row.get(secondary_col)
        persons_str = row.get(persons_col)
        
        if pd.isna(doc_type) or pd.isna(secondary):
            continue
        
        doc_type = str(doc_type).strip()
        secondary = str(secondary).strip()
        
        role_id = role_map.get(doc_type)
        fee_id = fee_map.get(secondary)
        
        if not role_id:
            print(f"     ⚠️  未找到角色: {doc_type}")
            continue
        if not fee_id:
            print(f"     ⚠️  未找到费用模板: {secondary}")
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
    
    print(f"     ✅ 整理出 {len(role_config)} 个角色配置")
    
    # 3.4 批量保存绑定关系
    print("\n  4️⃣ 保存绑定关系...")
    
    success_count = 0
    for role_id, config in role_config.items():
        print(f"\n     保存: {config['name']} (ID: {role_id})")
        
        payload = {
            "roleId": role_id,
            "userIds": list(config["person_ids"]),
            "feeTemplateIds": config["fee_ids"],
            "companyId": auth["company_id"]
        }
        
        save_resp = requests.post(
            f"{BASE_URL}/api/member/role/add/relation",
            headers={"x-token": auth["token"], "Content-Type": "application/json"},
            json=payload,
            timeout=10,
            verify=False
        )
        
        if save_resp.status_code == 200:
            save_result = save_resp.json()
            if save_result.get("code") == 200:
                print(f"        ✅ 成功!")
                success_count += 1
            else:
                print(f"        ❌ 失败: {save_result.get('msg', '未知错误')}")
        else:
            print(f"        ❌ HTTP错误: {save_resp.status_code}")
        
        time.sleep(0.3)
    
    print(f"\n  📊 第三步完成: {success_count}/{len(role_config)} 个角色")
    return success_count


def main(excel_file):
    """
    主函数：执行完整的三步闭环
    
    Args:
        excel_file: Excel配置文件路径
        
    Excel格式要求：
        - 一级科目类型: 一级科目名称
        - 二级科目类型: 二级科目名称
        - 归属单据类型: 单据类型（将创建为角色）
        - 单据适配人员: 人员名称（多个用顿号或逗号分隔）
    """
    print_header("财税通三步闭环自动化工具")
    
    try:
        # 获取认证信息
        print("\n🔐 获取认证信息...")
        auth = get_auth_from_browser()
        
        # 读取Excel获取单据类型列表
        df = pd.read_excel(excel_file)
        # 清理列名（去除特殊字符）
        df.columns = [col.strip().replace('\xa0', '').replace('\n', '') for col in df.columns]
        doc_type_col = "归属单据类型" if "归属单据类型" in df.columns else "单据类型"
        document_types = df[doc_type_col].dropna().unique().tolist()
        
        print(f"\n📋 配置概览:")
        print(f"   总记录数: {len(df)}")
        print(f"   单据类型: {len(document_types)} 种")
        print(f"   角色列表: {', '.join(document_types)}")
        
        # 执行三步
        step1_add_secondary_templates(auth, excel_file)
        role_map = step2_create_roles(auth, document_types)
        step3_configure_role_relations(auth, excel_file, role_map)
        
        # 完成总结
        print_header("🎉 三步闭环执行完成！")
        print("\n✅ 第一步：添加二级科目（继承字段）")
        print("✅ 第二步：创建角色组和子角色")
        print("✅ 第三步：配置费用类型和人员")
        print("\n所有配置已成功保存到系统！")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # 支持命令行参数
    if len(sys.argv) > 1:
        excel_file = sys.argv[1]
    else:
        # 默认路径
        excel_file = "/Users/tang/Desktop/中转 API Claude/openclaw测试一-科目配置表.xlsx"
    
    if not Path(excel_file).exists():
        print(f"❌ 文件不存在: {excel_file}")
        print(f"用法: python {sys.argv[0]} <excel_file_path>")
        sys.exit(1)
    
    main(excel_file)
