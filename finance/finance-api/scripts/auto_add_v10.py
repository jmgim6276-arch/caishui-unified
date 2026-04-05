#!/usr/bin/env python3
"""
财税通自动添加员工脚本 - v10 修复部门选择（vue-treeselect）
"""

from playwright.sync_api import sync_playwright
import csv
import time

CSV_FILE = "/Users/tang/Desktop/caishui_bot/员工数据.csv"
DEBUG_PORT = "http://localhost:9222"

def find_add_staff_page(browser):
    """查找已经打开的添加员工页面"""
    for ctx in browser.contexts:
        for page in ctx.pages:
            if "uf-tree.com" in page.url:
                title = page.query_selector(".title")
                if title and "添加新员工" in title.inner_text():
                    return page
    return None

def select_department(page, dept_name):
    """选择部门 - vue-treeselect"""
    print(f"    选择部门: {dept_name}...", end="")
    
    try:
        # vue-treeselect 的选择方式
        # 1. 点击 treeselect 输入框
        treeselect_input = page.query_selector('.vue-treeselect__input')
        
        if not treeselect_input or not treeselect_input.is_visible():
            print("⚠️ 未找到部门选择框")
            return False
        
        # 点击展开下拉
        treeselect_input.click()
        time.sleep(1)
        
        # 2. 查找部门选项
        # vue-treeselect 的选项通常有 .vue-treeselect__option 类
        option_selectors = [
            f'.vue-treeselect__option:has-text("{dept_name}")',
            f'.vue-treeselect__label:has-text("{dept_name}")',
            f'[data-test="{dept_name}"]',
            f'.vue-treeselect__list-item:has-text("{dept_name}")',
        ]
        
        for selector in option_selectors:
            try:
                option = page.query_selector(selector)
                if option and option.is_visible():
                    option.click()
                    print(f"✅")
                    time.sleep(0.5)
                    return True
            except:
                pass
        
        # 如果没找到，打印可用选项
        all_options = page.query_selector_all('.vue-treeselect__option, .vue-treeselect__label')
        if all_options:
            print(f"⚠️ 未找到'{dept_name}'")
            print(f"      可用选项({len(all_options)}个):")
            for opt in all_options[:10]:
                try:
                    if opt.is_visible():
                        text = opt.inner_text()
                        print(f"        - {text}")
                except:
                    pass
        
        # 关闭下拉（按Escape或点击空白）
        page.keyboard.press('Escape')
        return False
        
    except Exception as e:
        print(f"⚠️ {e}")
        return False

def add_employee(page, name, phone, department):
    """添加单个员工"""
    print(f"\n  添加: {name} | {phone} | {department}")
    
    try:
        # 1. 填写手机
        print("    填写手机...", end="")
        page.locator('input[placeholder="请输入员工手机"]').first.fill(phone)
        print(f"✅")
        
        # 2. 填写姓名
        print("    填写姓名...", end="")
        page.locator('input[placeholder="请输入员工姓名"]').first.fill(name)
        print(f"✅")
        
        # 3. 选择部门
        select_department(page, department)
        
        # 4. 点击保存并继续添加
        print("    点击保存...", end="")
        save_btn = page.locator('button:has-text("保存并继续添加")').first
        
        if save_btn.count() > 0 and save_btn.is_visible():
            save_btn.click()
            print("✅")
            time.sleep(2)
            
            # 检查结果
            msg = page.locator('.el-message--success, .el-message--error').first
            if msg.count() > 0 and msg.is_visible():
                msg_text = msg.inner_text()
                print(f"    📢 {msg_text}")
                if '成功' in msg_text:
                    return True
                elif '已存在' in msg_text:
                    print("    ⚠️ 用户已存在，继续")
                    return True
            else:
                print("    ✅ 操作完成")
                return True
        else:
            print("❌ 未找到保存按钮")
            return False
        
    except Exception as e:
        print(f"\n    ❌ 错误: {e}")
        return False

def main():
    print("=" * 60)
    print("🤖 财税通自动添加员工脚本 v10")
    print("=" * 60)
    
    # 读取数据
    employees = []
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            employees.append(row)
    
    print(f"\n📋 数据: {len(employees)} 人")
    for emp in employees:
        print(f"   - {emp['姓名']} -> {emp['部门']}")
    
    # 连接浏览器
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(DEBUG_PORT)
        print("\n✅ 连接浏览器")
        
        # 查找添加员工页面
        target_page = find_add_staff_page(browser)
        
        if not target_page:
            print("❌ 未找到添加员工页面")
            print("💡 请手动在Comet浏览器中打开添加员工页面")
            browser.close()
            return
        
        target_page.bring_to_front()
        print(f"✅ 找到添加员工页面\n")
        
        # 添加员工
        success = fail = 0
        
        for i, emp in enumerate(employees, 1):
            print(f"\n[{i}/{len(employees)}]", end="")
            if add_employee(target_page, emp['姓名'], emp['手机号'], emp['部门']):
                success += 1
            else:
                fail += 1
            
            if i < len(employees):
                time.sleep(1.5)
        
        print("\n" + "=" * 60)
        print(f"📊 完成: 成功 {success} / 失败 {fail}")
        print("=" * 60)
        
        browser.close()

if __name__ == "__main__":
    main()
