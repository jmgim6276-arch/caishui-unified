#!/usr/bin/env python3
"""
财税通配置自动获取工具
自动从浏览器中提取：
1. x-token (认证令牌)
2. companyId (企业ID)
3. 部门列表 (部门名称和ID映射)

使用方法:
    python auto_config_helper.py

前提条件:
    1. 浏览器已启动调试模式 (--remote-debugging-port=9222)
    2. 已登录财税通系统
    3. 已进入企业（不要在"选择企业"页面）
"""

from playwright.sync_api import sync_playwright
import json
import time
import re


def extract_token_from_page(page):
    """从页面中提取 x-token"""
    print("🔍 正在查找 x-token...")
    
    # 方法1: 从 localStorage 获取
    token = page.evaluate('''() => {
        // 尝试从 localStorage 获取
        const token = localStorage.getItem('x-token') || 
                     localStorage.getItem('token') ||
                     localStorage.getItem('auth_token');
        if (token) return {source: 'localStorage', token: token};
        
        // 尝试从 sessionStorage 获取
        const sessionToken = sessionStorage.getItem('x-token') || 
                            sessionStorage.getItem('token');
        if (sessionToken) return {source: 'sessionStorage', token: sessionToken};
        
        return null;
    }''')
    
    if token:
        print(f"  ✅ 从 {token['source']} 找到 token")
        return token['token']
    
    # 方法2: 从 Cookie 获取
    cookies = page.context.cookies()
    for cookie in cookies:
        if 'token' in cookie.get('name', '').lower() or cookie.get('name') == 'x-token':
            print(f"  ✅ 从 Cookie 找到 token: {cookie['name']}")
            return cookie['value']
    
    # 方法3: 从页面变量获取（Vue/React 存储）
    token = page.evaluate('''() => {
        // 尝试从 Vuex/Redux store 获取
        if (window.__VUE__ && window.__VUE__.$store) {
            const state = window.__VUE__.$store.state;
            if (state.token) return {source: 'Vuex', token: state.token};
            if (state.auth && state.auth.token) return {source: 'Vuex auth', token: state.auth.token};
        }
        
        // 尝试从全局变量获取
        if (window.token) return {source: 'window.token', token: window.token};
        if (window.xToken) return {source: 'window.xToken', token: window.xToken};
        if (window.USER_TOKEN) return {source: 'window.USER_TOKEN', token: window.USER_TOKEN};
        
        return null;
    }''')
    
    if token:
        print(f"  ✅ 从页面变量找到 token")
        return token['token']
    
    return None


def extract_company_id(page):
    """从URL或页面数据中提取 companyId"""
    print("🔍 正在查找企业ID (companyId)...")
    
    # 方法1: 从 URL 获取
    url = page.url
    company_match = re.search(r'company[/=](\d+)', url)
    if company_match:
        company_id = company_match.group(1)
        print(f"  ✅ 从 URL 找到: {company_id}")
        return company_id
    
    # 方法2: 从页面JS变量获取
    company_id = page.evaluate('''() => {
        // 尝试从全局变量获取
        if (window.companyId) return window.companyId;
        if (window.COMPANY_ID) return window.COMPANY_ID;
        if (window.currentCompany && window.currentCompany.id) return window.currentCompany.id;
        
        // 尝试从 Vuex store 获取
        if (window.__VUE__ && window.__VUE__.$store) {
            const state = window.__VUE__.$store.state;
            if (state.companyId) return state.companyId;
            if (state.company && state.company.id) return state.company.id;
            if (state.user && state.user.companyId) return state.user.companyId;
        }
        
        return null;
    }''')
    
    if company_id:
        print(f"  ✅ 从页面变量找到: {company_id}")
        return str(company_id)
    
    # 方法3: 询问用户
    print("  ⚠️ 自动查找失败")
    print("  请手动获取：在浏览器开发者工具中查看网络请求的参数")
    company_id = input("  请输入企业ID (companyId): ").strip()
    return company_id if company_id else None


def extract_departments(page):
    """提取部门列表"""
    print("🔍 正在查找部门列表...")
    
    # 导航到员工管理页面
    page.goto("https://cst.uf-tree.com/company/staff")
    time.sleep(3)
    
    # 点击添加员工按钮
    try:
        page.click('button:has-text("添加员工")')
        time.sleep(1)
        page.click('.el-dropdown-menu__item:has-text("直接添加")')
        time.sleep(3)
    except:
        print("  ⚠️ 无法打开添加员工表单")
        return {}
    
    # 点击部门选择，触发加载
    try:
        page.click('.vue-treeselect__control')
        time.sleep(2)
    except:
        print("  ⚠️ 无法打开部门选择")
        return {}
    
    # 从页面提取部门数据
    departments = page.evaluate('''() => {
        const result = {};
        
        // 方法1: 从 vue-treeselect 选项中提取
        const options = document.querySelectorAll('.vue-treeselect__option');
        options.forEach(opt => {
            const text = opt.innerText.trim();
            // 尝试从 id 属性提取数字ID
            const idMatch = opt.id.match(/-(\d+)$/);
            if (idMatch && text) {
                const id = parseInt(idMatch[1]);
                result[text] = id;
            }
        });
        
        // 方法2: 如果没有找到，尝试其他选择器
        if (Object.keys(result).length === 0) {
            const items = document.querySelectorAll('.el-tree-node, .department-item, [class*="dept"]');
            items.forEach((item, index) => {
                const text = item.innerText.trim();
                const dataId = item.getAttribute('data-id') || item.getAttribute('data-key');
                if (text && dataId) {
                    result[text] = parseInt(dataId);
                }
            });
        }
        
        return result;
    }''')
    
    if departments and len(departments) > 0:
        print(f"  ✅ 找到 {len(departments)} 个部门")
        return departments
    
    # 如果自动提取失败，引导用户手动获取
    print("  ⚠️ 自动提取部门列表失败")
    print("\n  手动获取方法：")
    print("  1. 在浏览器中按 F12 打开开发者工具")
    print("  2. 切换到 Network（网络）标签")
    print("  3. 点击「添加员工」→「直接添加」")
    print("  4. 点击「部门选择」下拉框")
    print("  5. 在 Network 中找到 department/list 或类似的请求")
    print("  6. 查看 Response，找到部门名称和对应的 id")
    print("\n  示例格式：")
    print('  {')
    print('    "测试门店1": 9151,')
    print('    "测试门店2": 9152,')
    print('    "测试门店3": 9153')
    print('  }')
    
    return {}


def generate_config_file(token, company_id, departments):
    """生成配置文件"""
    config = {
        "token": token,
        "company_id": company_id,
        "department_map": departments,
        "base_url": "https://cst.uf-tree.com",
        "api_endpoint": "/api/member/userInfo/add"
    }
    
    # 保存到文件
    config_file = "config.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    return config_file


def main():
    """主函数"""
    print("="*60)
    print("🔧 财税通配置自动获取工具")
    print("="*60)
    print("\n本工具将自动从浏览器中提取：")
    print("  1. x-token (认证令牌)")
    print("  2. companyId (企业ID)")
    print("  3. 部门列表 (名称和ID映射)")
    print("\n前提条件：")
    print("  • 浏览器已启动调试模式 (port 9222)")
    print("  • 已登录财税通系统")
    print("  • 已进入企业（不在'选择企业'页面）")
    print("\n" + "="*60)
    
    print("\n自动继续...")
    time.sleep(1)
    
    try:
        with sync_playwright() as p:
            print("\n🔗 连接浏览器...")
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            
            # 获取页面
            page = None
            for ctx in browser.contexts:
                for pg in ctx.pages:
                    if "uf-tree.com" in pg.url:
                        page = pg
                        break
                if page:
                    break
            
            if not page:
                print("\n❌ 未找到财税通页面")
                print("请确保：")
                print("  1. 浏览器已启动调试模式")
                print("  2. 已打开 https://cst.uf-tree.com")
                return
            
            print("✅ 已连接到页面")
            print(f"   URL: {page.url[:60]}...")
            
            # 提取各项配置
            print("\n" + "="*60)
            
            # 1. 获取 Token
            token = extract_token_from_page(page)
            if not token:
                print("\n❌ 无法自动获取 Token")
                token = input("请手动输入 x-token: ").strip()
            if token:
                print(f"   Token: {token[:20]}...")
            
            # 2. 获取 CompanyId
            print("\n" + "-"*60)
            company_id = extract_company_id(page)
            if company_id:
                print(f"   CompanyId: {company_id}")
            
            # 3. 获取部门列表
            print("\n" + "-"*60)
            departments = extract_departments(page)
            
            browser.close()
            
            # 生成配置文件
            print("\n" + "="*60)
            if token and company_id:
                config_file = generate_config_file(token, company_id, departments)
                print(f"✅ 配置已保存到: {config_file}")
                
                print("\n📋 配置内容预览：")
                print("-"*60)
                with open(config_file, "r", encoding="utf-8") as f:
                    print(f.read())
                
                print("\n" + "="*60)
                print("🎉 配置获取完成！")
                print("="*60)
                print(f"\n现在可以运行：")
                print(f"  python caishui_add_staff_api.py your_employees.xlsx")
                print(f"\n脚本会自动读取 {config_file} 中的配置")
            else:
                print("❌ 配置不完整，请手动检查")
                
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        print("\n可能原因：")
        print("  • 浏览器未启动调试模式")
        print("  • 调试端口不是 9222")
        print("  • 未登录财税通系统")
        print("\n解决方法：")
        print("  1. 确保浏览器以调试模式启动:")
        print("     chrome --remote-debugging-port=9222")
        print("  2. 登录财税通系统")
        print("  3. 重新运行本脚本")


if __name__ == "__main__":
    main()
