#!/usr/bin/env python3
"""
完全通用版 - 自动获取任意账号的部门结构
通过多种方式尝试获取部门数据
"""

import requests
import pandas as pd
import json
import time
from playwright.sync_api import sync_playwright

BASE_URL = "https://cst.uf-tree.com"

def get_token():
    """从浏览器获取Token"""
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://localhost:9222")
        for ctx in browser.contexts:
            for pg in ctx.pages:
                if "cst.uf-tree.com" in pg.url and "login" not in pg.url:
                    token = pg.evaluate("""() => {
                        const raw = localStorage.getItem('vuex');
                        if (!raw) return null;
                        const store = JSON.parse(raw);
                        return store.user && store.user.token ? store.user.token : null;
                    }""")
                    browser.close()
                    return token
        browser.close()
    return None

def try_get_departments_method1(page):
    """方法1: 直接从Vue组件读取（需要点击触发）"""
    try:
        # 尝试点击添加员工按钮
        page.goto("https://cst.uf-tree.com/company/staff", timeout=15000)
        time.sleep(2)
        
        # 使用JavaScript点击（绕过1Password弹窗）
        page.evaluate('''() => {
            const btn = document.querySelector('button:has-text("添加员工")');
            if (btn) btn.click();
        }''')
        time.sleep(1)
        
        page.evaluate('''() => {
            const items = document.querySelectorAll('.el-dropdown-menu__item');
            for (const item of items) {
                if (item.innerText.includes('直接添加')) item.click();
            }
        }''')
        time.sleep(2)
        
        # 点击部门选择框
        page.evaluate('''() => {
            const input = document.querySelector('.vue-treeselect__input');
            if (input) input.click();
        }''')
        time.sleep(2)
        
        # 读取数据
        depts = page.evaluate('''() => {
            const el = document.querySelector('.vue-treeselect');
            return el && el.__vue__ ? el.__vue__.options : null;
        }''')
        
        return depts
    except Exception as e:
        print(f"   方法1失败: {e}")
        return None

def try_get_departments_method2(page):
    """方法2: 从页面全局变量扫描"""
    try:
        result = page.evaluate('''() => {
            // 扫描所有可能包含部门数据的全局变量
            const candidates = [];
            
            for (const key of Object.keys(window)) {
                try {
                    const val = window[key];
                    if (val && typeof val === 'object') {
                        // 检查是否是数组且包含id和name/label
                        if (Array.isArray(val) && val.length > 0 && val.length < 1000) {
                            const first = val[0];
                            if (first && (first.id !== undefined) && (first.name || first.label)) {
                                candidates.push({key: key, data: val.slice(0, 10)});
                            }
                        }
                        // 检查是否是对象且包含部门相关key
                        else if (!Array.isArray(val) && Object.keys(val).length > 0) {
                            const keys = Object.keys(val);
                            if (keys.includes('id') && (keys.includes('name') || keys.includes('label'))) {
                                candidates.push({key: key, data: [val]});
                            }
                        }
                    }
                } catch (e) {}
            }
            
            return candidates;
        }''')
        
        # 解析找到的数据
        for candidate in result:
            data = candidate.get('data', [])
            if data and len(data) > 0:
                dept_map = {}
                for item in data:
                    if isinstance(item, dict):
                        dept_id = item.get('id')
                        name = item.get('name') or item.get('label')
                        if dept_id and name and isinstance(dept_id, int):
                            dept_map[name] = dept_id
                
                if len(dept_map) > 0:
                    print(f"   从 window.{candidate['key']} 找到 {len(dept_map)} 个部门")
                    return dept_map
        
        return None
    except Exception as e:
        print(f"   方法2失败: {e}")
        return None

def try_get_departments_method3(token):
    """方法3: 尝试调用API获取部门列表（可能权限不足）"""
    try:
        headers = {"x-token": token, "Content-Type": "application/json"}
        
        # 尝试多个可能的API端点
        endpoints = [
            "/api/member/department/list",
            "/api/department/list",
            "/api/company/department/list",
            "/api/organization/department/list"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(
                    f"{BASE_URL}{endpoint}",
                    headers=headers,
                    timeout=5
                )
                data = response.json()
                
                if data.get('code') == 200 and data.get('data'):
                    dept_map = {}
                    for dept in data['data']:
                        dept_id = dept.get('id')
                        name = dept.get('name') or dept.get('departmentName')
                        if dept_id and name:
                            dept_map[name] = dept_id
                            # 处理子部门
                            children = dept.get('children', [])
                            for child in children:
                                child_id = child.get('id')
                                child_name = child.get('name')
                                if child_id and child_name:
                                    dept_map[child_name] = child_id
                    
                    if dept_map:
                        print(f"   从API {endpoint} 获取成功")
                        return dept_map
            except:
                continue
        
        return None
    except Exception as e:
        print(f"   方法3失败: {e}")
        return None

def get_departments_auto(token):
    """自动尝试多种方式获取部门"""
    print("\n🔍 自动获取部门结构...")
    
    # 尝试方法3: API（最快，但可能权限不足）
    print("   尝试方法1: 调用API...")
    depts = try_get_departments_method3(token)
    if depts:
        return depts, "API"
    
    # 尝试方法1: Vue组件（最准确，但需要页面交互）
    print("   尝试方法2: 读取Vue组件...")
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://localhost:9222")
        for ctx in browser.contexts:
            for pg in ctx.pages:
                if "cst.uf-tree.com" in pg.url and "login" not in pg.url:
                    depts = try_get_departments_method1(pg)
                    browser.close()
                    if depts:
                        dept_map = {}
                        for d in depts:
                            if d.get('id') and d.get('label'):
                                dept_map[d['label']] = d['id']
                        return dept_map, "Vue组件"
        browser.close()
    
    # 尝试方法2: 全局变量扫描（备用方案）
    print("   尝试方法3: 扫描全局变量...")
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://localhost:9222")
        for ctx in browser.contexts:
            for pg in ctx.pages:
                if "cst.uf-tree.com" in pg.url and "login" not in pg.url:
                    depts = try_get_departments_method2(pg)
                    browser.close()
                    if depts:
                        return depts, "全局变量"
        browser.close()
    
    return {}, "none"

def add_employee_api(name, phone, dept_id, token):
    """调用API添加员工"""
    url = f"{BASE_URL}/api/member/userInfo/add"
    headers = {
        "x-token": token,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    payload = {
        "nickName": name,
        "mobile": phone,
        "departmentIds": [dept_id],
        "companyId": 7792
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        result = response.json()
        if result.get("code") == 200 or result.get("success"):
            return True, "添加成功"
        else:
            return False, result.get("message", "未知错误")
    except Exception as e:
        return False, str(e)

def main():
    print("="*60)
    print("🤖 完全通用版 - 自动适应任意账号")
    print("="*60)
    
    # 1. 获取Token
    print("\n🔑 获取Token...")
    TOKEN = get_token()
    if not TOKEN:
        print("❌ 未找到Token，请确保已登录")
        return
    print(f"✅ Token: {TOKEN[:20]}...")
    
    # 2. 自动获取部门结构
    dept_map, source = get_departments_auto(TOKEN)
    
    if not dept_map:
        print("\n❌ 无法自动获取部门结构")
        print("💡 请手动输入部门ID列表（格式: 部门名:ID, 部门名:ID）")
        print("   例如: 销售部:1001, 技术部:1002, 财务部:1003")
        manual_input = input("\n部门列表: ").strip()
        
        if not manual_input:
            print("❌ 未提供部门信息")
            return
        
        dept_map = {}
        for item in manual_input.split(','):
            parts = item.strip().split(':')
            if len(parts) == 2:
                name, id_str = parts
                try:
                    dept_map[name.strip()] = int(id_str.strip())
                except:
                    pass
        
        if not dept_map:
            print("❌ 格式错误")
            return
    
    print(f"\n✅ 从[{source}]获取到 {len(dept_map)} 个部门:")
    for name, dept_id in sorted(dept_map.items()):
        print(f"   - {name}: {dept_id}")
    
    # 3. 读取Excel
    import os
    excel_files = [f for f in os.listdir('/Users/tang/Desktop') 
                   if f.endswith('.xlsx') and '员工' in f and not f.startswith('.')]
    
    if not excel_files:
        print("❌ 未找到Excel文件")
        return
    
    excel_file = f"/Users/tang/Desktop/{excel_files[0]}"
    print(f"\n📊 读取: {excel_files[0]}")
    df = pd.read_excel(excel_file)
    print(f"共 {len(df)} 个员工")
    
    # 4. 智能分配部门（轮询）
    stores = list(dept_map.items())
    
    print(f"\n🎯 将员工分配到 {len(stores)} 个部门（轮询）:")
    assignments = []
    for idx, row in df.iterrows():
        store_name, store_id = stores[idx % len(stores)]
        assignments.append({
            'name': row['姓名'],
            'phone': str(row['手机号']),
            'dept_name': store_name,
            'dept_id': store_id
        })
        print(f"   {idx+1}. {row['姓名']} → {store_name}")
    
    # 5. 批量添加
    print("\n" + "="*60)
    print("🚀 开始批量添加")
    print("="*60)
    
    success = fail = 0
    for i, a in enumerate(assignments, 1):
        print(f"\n[{i}/{len(assignments)}] {a['name']} ({a['dept_name']})...", end=" ")
        
        ok, msg = add_employee_api(a['name'], a['phone'], a['dept_id'], TOKEN)
        
        if ok:
            print(f"✅ {msg}")
            success += 1
        else:
            print(f"❌ {msg}")
            fail += 1
        
        time.sleep(0.5)
    
    print("\n" + "="*60)
    print(f"📊 完成: 成功 {success}/{len(df)}")
    print("="*60)

if __name__ == "__main__":
    main()
