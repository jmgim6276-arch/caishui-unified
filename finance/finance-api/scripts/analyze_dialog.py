#!/usr/bin/env python3
"""
分析弹窗 DOM 结构
"""

from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    
    for ctx in browser.contexts:
        for page in ctx.pages:
            if "uf-tree.com" in page.url and "staff" in page.url:
                page.bring_to_front()
                
                # 点击添加员工按钮
                add_btn = page.query_selector('button:has-text("添加员工")')
                if add_btn:
                    add_btn.click()
                    print("✅ 点击'添加员工'按钮")
                    time.sleep(2)
                
                # 截图
                page.screenshot(path='/tmp/dialog_analysis.png')
                print("📸 截图已保存")
                
                # 分析弹窗
                print("\n" + "="*60)
                print("🔍 分析弹窗结构")
                print("="*60)
                
                # 找所有 dialog
                dialogs = page.query_selector_all('.el-dialog, [role="dialog"], .dialog, .modal')
                print(f"\n找到 {len(dialogs)} 个 dialog 元素")
                
                for i, dialog in enumerate(dialogs):
                    try:
                        if dialog.is_visible():
                            print(f"\n  Dialog [{i}]:")
                            
                            # 找所有 input
                            inputs = dialog.query_selector_all('input')
                            print(f"    输入框数量: {len(inputs)}")
                            
                            for j, inp in enumerate(inputs):
                                try:
                                    if inp.is_visible():
                                        ph = inp.get_attribute('placeholder') or ''
                                        typ = inp.get_attribute('type') or 'text'
                                        name = inp.get_attribute('name') or ''
                                        cls = inp.get_attribute('class') or ''
                                        print(f"      [{j}] placeholder='{ph}', type={typ}, name={name}")
                                        print(f"           class={cls[:60]}")
                                except:
                                    pass
                            
                            # 找所有 button
                            buttons = dialog.query_selector_all('button')
                            print(f"    按钮数量: {len(buttons)}")
                            
                            for j, btn in enumerate(buttons):
                                try:
                                    if btn.is_visible():
                                        text = btn.inner_text().strip()
                                        cls = btn.get_attribute('class') or ''
                                        print(f"      [{j}] '{text}' - {cls[:50]}")
                                except:
                                    pass
                    except:
                        pass
                
                # 如果没有找到 dialog，直接搜索整个页面的 input
                if not dialogs:
                    print("\n  未找到 dialog，搜索整个页面...")
                    all_inputs = page.query_selector_all('input')
                    print(f"  页面总共 {len(all_inputs)} 个 input")
                    
                    for i, inp in enumerate(all_inputs):
                        try:
                            if inp.is_visible():
                                ph = inp.get_attribute('placeholder') or ''
                                print(f"    [{i}] placeholder='{ph}'")
                        except:
                            pass
    
    browser.close()
    print("\n✅ 分析完成")
