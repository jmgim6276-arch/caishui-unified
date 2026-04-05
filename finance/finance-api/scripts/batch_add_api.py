#!/usr/bin/env python3
"""
使用 API 批量添加员工 - 支持Edge浏览器和CSV/Excel
"""

import requests
import pandas as pd
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

# 配置
BASE_URL = "https://cst.uf-tree.com"

def get_desktop_path():
    """获取桌面路径"""
    return str(Path.home() / "Desktop")

def get_token_from_browser():
    """
    从已登录的浏览器实时获取 Token
    支持Chrome/Edge等Chromium内核浏览器
    """
    js = """
    () => {
        const raw = localStorage.getItem('vuex');
        if (!raw) return null;
        const store = JSON.parse(raw);
        return store.user && store.user.token ? store.user.token : null;
    }
    """
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            
            for ctx in browser.contexts:
                for pg in ctx.pages:
                    if "cst.uf-tree.com" in pg.url and "login" not in pg.url:
                        token = pg.evaluate(js)
                        browser.close()
                        return token
            
            browser.close()
    except Exception as e:
        print(f"❌ 连接浏览器失败: {e}")
        return None
    
    return None

def get_department_map():
    """从浏览器获取部门映射"""
    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            
            for ctx in browser.contexts:
                for pg in ctx.pages:
                    if "cst.uf-tree.com" in pg.url and "login" not in pg.url:
                        pg.bring_to_front()
                        
                        # 导航到员工管理页面
                        print("   导航到员工管理页面...")
                        pg.goto("https://cst.uf-tree.com/company/staff", timeout=15000)
                        pg.wait_for_timeout(3000)
                        
                        # 尝试点击"添加员工"按钮
                        print("   点击添加员工...")
                        try:
                            # 尝试多种选择器
                            selectors = [
                                'button:has-text("添加员工")',
                                'button:has-text("新增")',
                                '[class*="add"]',
                                '[class*="新增"]'
                            ]
                            for selector in selectors:
                                try:
                                    pg.click(selector, timeout=5000)
                                    print(f"   ✓ 使用选择器: {selector}")
                                    break
                                except:
                                    continue
                        except Exception as e:
                            print(f"   点击添加员工失败: {e}")
                        
                        pg.wait_for_timeout(2000)
                        
                        # 尝试点击"直接添加"
                        print("   点击直接添加...")
                        try:
                            pg.click('text=直接添加', timeout=5000)
                        except:
                            try:
                                pg.click('li:has-text("直接添加")', timeout=5000)
                            except:
                                print("   未找到'直接添加'，尝试其他方式...")
                        
                        pg.wait_for_timeout(3000)
                        
                        # 尝试点击部门选择器
                        print("   展开部门选择器...")
                        try:
                            pg.click('.vue-treeselect__input', timeout=5000)
                        except:
                            try:
                                pg.click('[class*="treeselect"]', timeout=5000)
                            except:
                                pass
                        
                        pg.wait_for_timeout(3000)
                        
                        # 从 Vue 组件读取部门数据（多种方式尝试）
                        print("   读取部门数据...")
                        depts = pg.evaluate('''() => {
                            // 尝试多种方式获取部门数据
                            // 方式1: vue-treeselect组件
                            const el = document.querySelector('.vue-treeselect');
                            if (el && el.__vue__) {
                                return el.__vue__.options;
                            }
                            
                            // 方式2: 从页面Vue实例获取
                            const vueEl = document.querySelector('[data-v-app]');
                            if (vueEl && vueEl.__vue_app__) {
                                const app = vueEl.__vue_app__;
                                // 尝试从全局store获取
                                if (app.config && app.config.globalProperties && app.config.globalProperties.$store) {
                                    const store = app.config.globalProperties.$store;
                                    if (store.state && store.state.department) {
                                        return store.state.department.list;
                                    }
                                }
                            }
                            
                            // 方式3: 从localStorage获取
                            const vuex = localStorage.getItem('vuex');
                            if (vuex) {
                                const store = JSON.parse(vuex);
                                if (store.department && store.department.list) {
                                    return store.department.list;
                                }
                            }
                            
                            return null;
                        }''')
                        
                        browser.close()
                        
                        if depts:
                            dept_map = {}
                            for d in depts:
                                if d.get('id') and d.get('label'):
                                    dept_map[d['label']] = d['id']
                                elif d.get('id') and d.get('name'):
                                    dept_map[d['name']] = d['id']
                            return dept_map
                        else:
                            print("   未从页面获取到部门数据，尝试使用默认配置...")
                            # 返回空，让主程序使用手动输入或默认配置
                            return {}
            
            browser.close()
    except Exception as e:
        print(f"❌ 获取部门映射失败: {e}")
        return {}
    
    return {}

def find_employee_file(desktop_path):
    """查找员工信息文件（支持CSV和Excel）"""
    files = []
    for f in os.listdir(desktop_path):
        if f.startswith('.') or f.startswith('~'):
            continue
        if '员工' in f or 'employee' in f.lower():
            if f.endswith('.csv') or f.endswith('.xlsx') or f.endswith('.xls'):
                files.append(f)
    return files

def read_employee_file(file_path):
    """读取员工文件（自动识别格式）"""
    if file_path.endswith('.csv'):
        return pd.read_csv(file_path)
    else:
        return pd.read_excel(file_path)

def add_employee_api(name, phone, dept_id, token):
    """调用 API 添加员工"""
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
    print("🤖 财税通批量添加员工工具")
    print("="*60)
    print("支持: Chrome / Edge / 其他Chromium浏览器")
    
    # 1. 获取 Token（实时从浏览器读取）
    print("\n🔑 从浏览器获取 Token...")
    print("   请确保Edge已启动调试模式并登录系统")
    TOKEN = get_token_from_browser()
    
    if not TOKEN:
        print("\n❌ 未找到 Token，请确保：")
        print("   1. Edge 已启动调试模式:")
        print("      /Applications/Microsoft\\ Edge.app/Contents/MacOS/Microsoft\\ Edge --remote-debugging-port=9222")
        print("   2. 已登录财税通系统 https://cst.uf-tree.com")
        print("   3. 浏览器窗口保持打开")
        return
    
    print(f"✅ Token: {TOKEN[:20]}...")
    
    # 2. 获取部门映射
    print("\n🔍 获取部门映射...")
    dept_map = get_department_map()
    
    if not dept_map:
        print("⚠️  无法自动获取部门映射")
        print("\n请手动输入部门信息（从页面查看部门ID）:")
        print("示例格式: 测试门店1=9151,测试门店2=9152,测试门店3=9153")
        
        # 尝试使用默认配置
        use_default = input("\n是否使用默认配置？(y/n): ").strip().lower()
        
        if use_default == 'y':
            # 默认配置，用户可以根据实际情况修改
            dept_map = {
                '测试门店1': 9151,
                '测试门店2': 9152,
                '测试门店3': 9153,
                '凯旋创智测试集团': 9147
            }
            print("使用默认部门配置:")
        else:
            # 手动输入
            dept_input = input("请输入部门映射（格式: 名称=ID,名称=ID）: ").strip()
            dept_map = {}
            for item in dept_input.split(','):
                if '=' in item:
                    name, dept_id = item.split('=', 1)
                    try:
                        dept_map[name.strip()] = int(dept_id.strip())
                    except:
                        pass
        
        if not dept_map:
            print("❌ 没有有效的部门配置")
            return
    
    print(f"✅ 找到 {len(dept_map)} 个部门:")
    for name, dept_id in sorted(dept_map.items()):
        print(f"   - {name}: {dept_id}")
    
    # 3. 查找并读取员工文件
    desktop = get_desktop_path()
    employee_files = find_employee_file(desktop)
    
    if not employee_files:
        print(f"\n❌ 未找到员工信息文件")
        print(f"   请在桌面创建文件，文件名包含'员工'，如:")
        print(f"   - employees.csv")
        print(f"   - 员工信息.xlsx")
        return
    
    # 使用第一个匹配的文件
    file_name = employee_files[0]
    file_path = os.path.join(desktop, file_name)
    print(f"\n📊 读取: {file_name}")
    
    try:
        df = read_employee_file(file_path)
        print(f"✅ 共 {len(df)} 个员工")
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return
    
    # 4. 智能匹配部门
    # 获取门店列表（排除集团）
    store_list = [n for n in dept_map.keys() if '门店' in n or '部门' in n]
    store_list.sort()
    
    if not store_list:
        store_list = list(dept_map.keys())
    
    # 创建编号映射（1,2,3...）
    store_by_index = {str(i+1): dept_map[name] for i, name in enumerate(store_list)}
    
    print(f"\n📋 部门编号映射:")
    for num, dept_id in sorted(store_by_index.items()):
        name = [k for k, v in dept_map.items() if v == dept_id][0]
        print(f"   部门 {num} → {name} (ID:{dept_id})")
    
    # 5. 批量添加
    print("\n" + "="*60)
    print("🚀 开始批量添加")
    print("="*60)
    
    success = fail = 0
    
    for idx, row in df.iterrows():
        name = str(row.get('姓名', row.get('name', '')))
        phone = str(row.get('手机号', row.get('mobile', row.get('phone', ''))))
        dept_num = str(row.get('部门', row.get('department', row.get('dept', 1))))
        
        if not name or not phone:
            print(f"\n[{idx+1}/{len(df)}] 跳过: 姓名或手机号为空")
            fail += 1
            continue
        
        dept_id = store_by_index.get(dept_num)
        if not dept_id:
            print(f"\n[{idx+1}/{len(df)}] {name}... ❌ 未知部门编号: {dept_num}")
            fail += 1
            continue
        
        dept_name = [k for k, v in dept_map.items() if v == dept_id][0]
        
        print(f"\n[{idx+1}/{len(df)}] {name} ({dept_name})...", end=" ")
        
        ok, msg = add_employee_api(name, phone, dept_id, TOKEN)
        
        if ok:
            print(f"✅ {msg}")
            success += 1
        else:
            print(f"❌ {msg}")
            fail += 1
    
    print("\n" + "="*60)
    print(f"📊 完成: 成功 {success}/{len(df)}, 失败 {fail}")
    print("="*60)

if __name__ == "__main__":
    main()
