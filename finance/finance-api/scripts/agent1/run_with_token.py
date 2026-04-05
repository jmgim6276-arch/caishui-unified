#!/usr/bin/env python3
"""
使用已有的 token 直接运行三表生成
"""

import json
import sys
import time
import requests

# 直接设置认证信息
TOKEN = "2vERT8zu1Qem0vLtZ8Vre9a8pvY"
COMPANY_ID = 7792
COMPANY_NAME = "凯旋创智测试集团"
BASE_URL = "https://cst.uf-tree.com"

def api_get(endpoint, params):
    return requests.get(
        f"{BASE_URL}{endpoint}",
        headers={"x-token": TOKEN, "Content-Type": "application/json"},
        params=params,
        timeout=15,
    ).json()

def api_post(endpoint, payload):
    return requests.post(
        f"{BASE_URL}{endpoint}",
        headers={"x-token": TOKEN, "Content-Type": "application/json"},
        json=payload,
        timeout=15,
    ).json()

def main():
    print(f"=== 财税通三表生成器 ===")
    print(f"企业: {COMPANY_NAME} (ID: {COMPANY_ID})")
    print()
    
    # 1. 获取用户列表
    print("1. 获取用户列表...")
    r = api_post("/api/member/department/queryCompany", {"companyId": COMPANY_ID})
    users = (r.get("result", {}) or {}).get("users", []) or []
    print(f"   用户数: {len(users)}")
    
    # 2. 获取部门列表
    print("2. 获取部门列表...")
    r = api_get("/api/member/department/queryDepartments", {"companyId": COMPANY_ID})
    depts = r.get("result", []) or []
    print(f"   部门数: {len(depts)}")
    
    # 3. 获取费用科目
    print("3. 获取费用科目...")
    r = api_get("/api/bill/feeTemplate/queryFeeTemplate", {"companyId": COMPANY_ID, "status": 1, "pageSize": 5000})
    fees = r.get("result", []) or []
    print(f"   科目数: {len(fees)}")
    
    # 4. 输出摘要
    print()
    print("=== 数据摘要 ===")
    print(f"用户: {len(users)}")
    print(f"部门: {len(depts)}")
    print(f"科目: {len(fees)}")
    
    # 保存数据到文件
    data = {
        "company": {
            "id": COMPANY_ID,
            "name": COMPANY_NAME
        },
        "users": users,
        "departments": depts,
        "fee_templates": fees,
        "export_time": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    output_file = f"/Users/mac/.openclaw/workspace/finance/Agent-1/output_{COMPANY_ID}_{int(time.time())}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n数据已保存到: {output_file}")

if __name__ == "__main__":
    main()
