#!/usr/bin/env python3
"""
财税通费用模板批量添加工具
作者: AI Assistant
功能: 自动将 Excel 中的费用科目批量添加到财税通系统
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


def print_step(step_num, description):
    """打印步骤信息"""
    print(f"\n{'='*70}")
    print(f"STEP {step_num}: {description}")
    print(f"{'='*70}")


def get_token_and_company():
    """
    STEP 1: 从浏览器获取认证信息
    
    返回: {
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
    
    return {"token": token, "company_id": company_id, "user_id": user_id}


def get_primary_templates(token, company_id):
    """
    STEP 2-3: 获取一级科目列表及详细信息
    
    返回: [{
        "id": xxx,
        "name": "xxx",
        "applyJson": [...],
        "feeJson": [...],
        ...
    }]
    """
    print("  📋 查询一级科目列表...")
    
    # 2.1 获取列表
    resp = requests.get(
        f"{BASE_URL}/api/bill/feeTemplate/queryFeeTemplate",
        headers={"x-token": token},
        params={"companyId": company_id, "status": 0},
        timeout=10
    )
    
    if resp.status_code != 200:
        raise Exception(f"❌ 查询失败: {resp.status_code}")
    
    result = resp.json()
    if result.get("code") != 200:
        raise Exception(f"❌ API错误: {result.get('msg')}")
    
    templates = result.get("result", [])
    primary_list = [t for t in templates if t.get("parentId") == -1]
    
    print(f"  ✅ 找到 {len(primary_list)} 个一级科目")
    
    # 2.2 获取每个一级科目的详细信息（关键！）
    print("  🔍 获取详细信息（含 applyJson/feeJson）...")
    
    detailed_templates = []
    for template in primary_list:
        template_id = template.get("id")
        
        detail_resp = requests.get(
            f"{BASE_URL}/api/bill/feeTemplate/getFeeTemplateById",
            headers={"x-token": token},
            params={"id": template_id, "companyId": company_id},
            timeout=10
        )
        
        if detail_resp.status_code == 200:
            detail_result = detail_resp.json()
            if detail_result.get("code") == 200:
                detailed_templates.append(detail_result.get("result", template))
            else:
                detailed_templates.append(template)
        else:
            detailed_templates.append(template)
    
    print(f"  ✅ 获取到 {len(detailed_templates)} 个一级科目的完整配置")
    
    # 显示列表
    for t in detailed_templates:
        apply_count = len(t.get("applyJson", []))
        fee_count = len(t.get("feeJson", []))
        print(f"     • {t.get('name')} (applyJson: {apply_count}, feeJson: {fee_count})")
    
    return detailed_templates


def read_excel(excel_file):
    """
    STEP 4: 读取 Excel 文件
    
    返回: DataFrame
    """
    print(f"  📊 读取 Excel: {excel_file}")
    
    if not Path(excel_file).exists():
        raise Exception(f"❌ 文件不存在: {excel_file}")
    
    df = pd.read_excel(excel_file)
    
    # 数据清洗
    df = df.dropna(subset=["一级科目", "二级科目"])
    df["一级科目"] = df["一级科目"].astype(str).str.strip()
    df["二级科目"] = df["二级科目"].astype(str).str.strip()
    
    print(f"  ✅ 共 {len(df)} 条记录")
    print(f"\n  预览数据:")
    print(df.to_string(index=False))
    
    return df


def add_secondary_template(token, user_id, company_id, parent_template, name):
    """
    STEP 6-7: 添加二级科目
    
    参数:
        token: 认证Token
        user_id: 用户ID
        company_id: 公司ID
        parent_template: 父级模板完整数据
        name: 二级科目名称
    
    返回: {"success": True/False, "message": "...", "id": xxx}
    """
    # 构建请求（平铺结构！）
    request_data = {
        "userId": user_id,
        "companyId": company_id,
        "name": name,
        "parentId": parent_template.get("id"),
        "icon": parent_template.get("icon", "md-plane"),
        "iconColor": parent_template.get("iconColor", "#4c7cc3"),
        "status": "1",
        "parentFlag": "0",
        "defaultFlag": False,
        "forceShare": parent_template.get("forceShare", 0),
        "shareDepPermission": parent_template.get("shareDepPermission", 2),
        # 关键：继承单据字段配置
        "applyJson": parent_template.get("applyJson", []),
        "feeJson": parent_template.get("feeJson", [])
    }
    
    # 调用创建API
    resp = requests.post(
        f"{BASE_URL}/api/bill/feeTemplate/addFeeTemplate",
        headers={"x-token": token, "Content-Type": "application/json"},
        json=request_data,
        timeout=10
    )
    
    if resp.status_code != 200:
        return {"success": False, "message": f"HTTP错误: {resp.status_code}"}
    
    result = resp.json()
    
    if result.get("success") or result.get("code") == 200:
        return {
            "success": True,
            "message": "创建成功",
            "id": result.get("result", {}).get("id")
        }
    else:
        return {
            "success": False,
            "message": result.get("message", "未知错误")
        }


def verify_result(token, company_id, parent_id, secondary_name):
    """
    STEP 8: 验证结果
    
    查询新创建的科目，确认字段已正确继承
    """
    resp = requests.get(
        f"{BASE_URL}/api/bill/feeTemplate/getFeeTemplateById",
        headers={"x-token": token},
        params={"id": parent_id, "companyId": company_id},
        timeout=10
    )
    
    if resp.status_code != 200:
        return False
    
    result = resp.json()
    if result.get("code") != 200:
        return False
    
    parent = result.get("result", {})
    children = parent.get("children", [])
    
    for child in children:
        if child.get("name") == secondary_name:
            has_apply = bool(child.get("applyJson"))
            has_fee = bool(child.get("feeJson"))
            return has_apply and has_fee
    
    return False


def batch_add_fee_templates(excel_file):
    """
    主函数：批量添加费用模板二级科目
    
    完整流程：
    1. 获取认证信息
    2. 获取一级科目列表
    3. 获取一级科目详细信息
    4. 读取Excel
    5. 匹配并批量添加
    6. 验证结果
    """
    print("\n" + "🚀"*35)
    print("🚀  财税通费用模板二级科目批量添加工具  🚀")
    print("🚀"*35)
    
    try:
        # STEP 1: 获取认证信息
        print_step(1, "获取认证信息")
        auth = get_token_and_company()
        token = auth["token"]
        company_id = auth["company_id"]
        user_id = auth["user_id"]
        
        # STEP 2-3: 获取一级科目（含详细信息）
        print_step(2, "获取一级科目及详细信息")
        primary_templates = get_primary_templates(token, company_id)
        
        # 创建名称映射
        primary_map = {t.get("name"): t for t in primary_templates}
        
        # STEP 4: 读取Excel
        print_step(3, "读取Excel数据")
        df = read_excel(excel_file)
        
        # STEP 5-7: 批量添加
        print_step(4, "批量添加二级科目")
        
        success_count = 0
        fail_count = 0
        
        for idx, row in df.iterrows():
            primary_name = row["一级科目"]
            secondary_name = row["二级科目"]
            
            print(f"\n  [{idx+1}/{len(df)}] {primary_name} → {secondary_name}")
            
            # 查找父级
            parent = primary_map.get(primary_name)
            if not parent:
                print(f"     ❌ 未找到一级科目: {primary_name}")
                fail_count += 1
                continue
            
            # 添加
            result = add_secondary_template(
                token, user_id, company_id,
                parent, secondary_name
            )
            
            if result["success"]:
                print(f"     ✅ 创建成功 (ID: {result.get('id')})")
                success_count += 1
            else:
                print(f"     ❌ 创建失败: {result['message']}")
                fail_count += 1
            
            # 小延迟，避免请求过快
            time.sleep(0.5)
        
        # STEP 8: 总结
        print_step(5, "完成总结")
        print(f"  ✅ 成功: {success_count} 个")
        print(f"  ❌ 失败: {fail_count} 个")
        print(f"  📊 总计: {len(df)} 个")
        
        if success_count == len(df):
            print(f"\n  🎉 全部成功！")
        elif success_count > 0:
            print(f"\n  ⚠️  部分成功，请检查失败项目")
        else:
            print(f"\n  ❌ 全部失败，请检查错误信息")
        
        return success_count, fail_count
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 0, 0


if __name__ == "__main__":
    # 默认Excel文件路径
    DEFAULT_EXCEL = "/Users/tang/Desktop/费用模板.xlsx"
    
    # 支持命令行参数
    if len(sys.argv) > 1:
        excel_file = sys.argv[1]
    else:
        excel_file = DEFAULT_EXCEL
    
    # 执行
    batch_add_fee_templates(excel_file)
