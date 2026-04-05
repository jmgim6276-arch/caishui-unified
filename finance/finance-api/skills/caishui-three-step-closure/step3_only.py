#!/usr/bin/env python3
"""
财税通三步闭环 - 第三步：配置费用类型和人员关系

假设：
- 第一步（二级科目）已完成
- 第二步（角色）已手动创建
- 只需要执行第三步：绑定关系
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


def get_auth_from_browser():
    """从浏览器获取认证信息"""
    print("🔌 连接 Edge 浏览器...")
    
    resp = requests.get(f"http://localhost:{CDP_PORT}/json/list", timeout=10)
    pages = resp.json()
    
    ws_url = None
    for page in pages:
        if "cst.uf-tree.com" in page.get("url", ""):
            ws_url = page["webSocketDebuggerUrl"]
            break
    
    if not ws_url:
        raise Exception("❌ 未找到财税通页面")
    
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
        raise Exception("❌ 获取 Token 失败")
    
    print(f"✅ Token: {token[:30]}...")
    print(f"✅ Company ID: {company_id}")
    print(f"✅ User ID: {user_id}")
    
    return {"token": token, "company_id": company_id, "user_id": user_id}


def configure_role_relations(auth, excel_file):
    """
    第三步：配置费用类型和人员关系
    """
    print("\n" + "=" * 70)
    print("【第三步】配置费用类型和人员关系")
    print("=" * 70)
    
    # 1. 获取员工ID映射表
    print("\n1️⃣ 获取员工ID映射表...")
    
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
    
    print(f"   ✅ 获取到 {len(staff_map)} 个员工映射")
    print(f"   示例: {list(staff_map.items())[:3]}")
    
    # 2. 获取费用模板ID映射表
    print("\n2️⃣ 获取费用模板ID映射表...")
    
    # 使用已知的二级科目ID（因为queryFeeTemplate API不返回二级科目）
    known_secondary = {
        "财务": 28073,
        "城市": 28074,
        "增值": 28075
    }
    
    # 验证这些ID是否有效
    fee_map = {}
    for name, tid in known_secondary.items():
        resp = requests.get(
            f"{BASE_URL}/api/bill/feeTemplate/getFeeTemplateById",
            headers={"x-token": auth["token"]},
            params={"id": tid, "companyId": auth["company_id"]},
            timeout=10,
            verify=False
        )
        if resp.status_code == 200 and resp.json().get("code") == 200:
            fee_map[name] = tid
            print(f"   ✅ {name}: ID {tid}")
        else:
            print(f"   ❌ {name}: ID {tid} 无效")
    
    print(f"   ✅ 共 {len(fee_map)} 个有效费用模板映射")
    
    # 3. 读取Excel
    print("\n3️⃣ 读取Excel配置...")
    df = pd.read_excel(excel_file)
    # 清理列名
    df.columns = [col.strip().replace('\xa0', '').replace('\n', '') for col in df.columns]
    
    # 确定列名
    doc_type_col = "归属单据类型" if "归属单据类型" in df.columns else "单据类型"
    secondary_col = "二级科目类型" if "二级科目类型" in df.columns else "二级科目"
    persons_col = "单据适配人员" if "单据适配人员" in df.columns else "人员"
    
    print(f"   使用列名: {doc_type_col}, {secondary_col}, {persons_col}")
    print(f"   共 {len(df)} 条配置")
    
    # 4. 按单据类型分组整理
    print("\n4️⃣ 整理配置数据...")
    
    role_config = {}
    for _, row in df.iterrows():
        doc_type = str(row.get(doc_type_col, "")).strip()
        secondary = str(row.get(secondary_col, "")).strip()
        persons_str = row.get(persons_col, "")
        
        if not doc_type or not secondary:
            continue
        
        fee_id = fee_map.get(secondary)
        if not fee_id:
            print(f"   ⚠️  未找到费用模板: {secondary}")
            continue
        
        # 解析人员
        person_ids = []
        if pd.notna(persons_str):
            for name in str(persons_str).replace('、', ',').split(','):
                name = name.strip()
                pid = staff_map.get(name)
                if pid:
                    person_ids.append(pid)
                else:
                    print(f"   ⚠️  未找到员工: {name}")
        
        # 按单据类型分组
        if doc_type not in role_config:
            role_config[doc_type] = {
                "fee_ids": set(),
                "person_ids": set()
            }
        
        role_config[doc_type]["fee_ids"].add(fee_id)
        role_config[doc_type]["person_ids"].update(person_ids)
    
    print(f"   ✅ 整理出 {len(role_config)} 个单据类型配置")
    for doc_type, config in role_config.items():
        print(f"      • {doc_type}: {len(config['fee_ids'])} 个费用类型, {len(config['person_ids'])} 个人员")
    
    # 5. 输出配置摘要（因为无法自动创建角色，需要手动配置）
    print("\n" + "=" * 70)
    print("配置摘要（请手动在财税通中配置）")
    print("=" * 70)
    
    for doc_type, config in role_config.items():
        print(f"\n📋 单据类型: {doc_type}")
        print(f"   费用类型: {', '.join([k for k, v in fee_map.items() if v in config['fee_ids']])}")
        print(f"   人员: {', '.join([k for k, v in staff_map.items() if v in config['person_ids']])}")
        print(f"   操作步骤:")
        print(f"      1. 进入财税通 → 系统设置 → 角色管理")
        print(f"      2. 找到或创建角色: {doc_type}")
        print(f"      3. 绑定上述费用类型和人员")
    
    print("\n" + "=" * 70)
    print("✅ 配置整理完成！")
    print("=" * 70)
    print("\n由于当前账号没有角色管理权限，请手动完成上述配置。")
    print("或者联系管理员分配角色管理权限后，再次运行完整脚本。")
    
    return role_config


def main(excel_file):
    """主函数"""
    print("=" * 70)
    print("财税通三步闭环 - 第三步：配置费用类型和人员关系")
    print("=" * 70)
    print("\n假设：")
    print("  ✅ 第一步（二级科目）已完成")
    print("  ✅ 第二步（角色）已手动创建")
    print("  🔄 执行第三步：绑定关系")
    
    try:
        # 获取认证
        auth = get_auth_from_browser()
        
        # 执行第三步
        configure_role_relations(auth, excel_file)
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        excel_file = sys.argv[1]
    else:
        excel_file = "/Users/mac/Desktop/二步.xlsx"
    
    main(excel_file)