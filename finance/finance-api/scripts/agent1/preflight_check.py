#!/usr/bin/env python3
"""
Preflight check for Agent1 skill portability.
Checks:
1) CDP port reachable (9223)
2) cst.uf-tree.com page attached
3) token/companyId readable from localStorage
4) key APIs reachable and minimally valid

Exit code 0 = pass, 1 = fail
"""

import json
import sys
import time
import requests
import websocket
import subprocess
import os

BASE_URL = "https://cst.uf-tree.com"

# 支持的浏览器 CDP 端口
BROWSERS = [
    {"name": "Edge", "port": 9223, "url": "http://localhost:9223/json", "path": "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"},
    {"name": "Chrome", "port": 18800, "url": "http://localhost:18800/json", "path": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"},
]


def launch_browser(browser):
    """启动浏览器并启用调试模式"""
    try:
        if os.path.exists(browser["path"]):
            print(f"正在启动 {browser['name']} 浏览器...")
            subprocess.Popen([
                browser["path"],
                f"--remote-debugging-port={browser['port']}",
                "--remote-allow-origins=*",
                "https://cst.uf-tree.com"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"⏳ 等待 {browser['name']} 启动...")
            time.sleep(3)
            return True
    except Exception as e:
        print(f"启动 {browser['name']} 失败: {e}")
    return False


def find_browser():
    """自动检测可用的浏览器，优先返回包含财税通页面的浏览器"""
    available = []
    for browser in BROWSERS:
        try:
            pages = requests.get(browser["url"], timeout=6).json()
            # 检查是否有财税通页面
            has_cst = any("cst.uf-tree.com" in p.get("url", "") for p in pages)
            available.append({**browser, "has_cst": has_cst, "page_count": len(pages)})
        except Exception:
            continue

    if not available:
        return None

    # 优先返回有财税通页面的浏览器
    for b in available:
        if b["has_cst"]:
            return b

    # 如果都没有财税通页面，返回第一个可用的
    return available[0]


def fail(msg):
    print(f"❌ {msg}")
    return False


def ok(msg):
    print(f"✅ {msg}")
    return True


def get_auth(browser):
    pages = requests.get(browser["url"], timeout=6).json()
    ws_url = None
    for p in pages:
        if "cst.uf-tree.com" in p.get("url", ""):
            ws_url = p.get("webSocketDebuggerUrl")
            break
    if not ws_url:
        raise RuntimeError(f"未在 {browser['name']} 中发现 cst.uf-tree.com 页面")

    ws = websocket.create_connection(ws_url, timeout=10, suppress_origin=True)
    ws.send(json.dumps({
        "id": 1,
        "method": "Runtime.evaluate",
        "params": {
            "expression": "(function(){const v=localStorage.getItem('vuex');if(!v)return null;const d=JSON.parse(v);return {token:d.user?.token, companyId:d.user?.company?.id, companyName:d.user?.company?.name};})()",
            "returnByValue": True,
        },
    }))
    raw = ws.recv()
    ws.close()

    value = json.loads(raw).get("result", {}).get("result", {}).get("value")
    if not value or not value.get("token") or not value.get("companyId"):
        raise RuntimeError("读取 token/companyId 失败（请确认已登录）")
    return value


def api_get(token, endpoint, params):
    return requests.get(
        f"{BASE_URL}{endpoint}",
        headers={"x-token": token, "Content-Type": "application/json"},
        params=params,
        timeout=15,
    ).json()


def api_post(token, endpoint, payload):
    return requests.post(
        f"{BASE_URL}{endpoint}",
        headers={"x-token": token, "Content-Type": "application/json"},
        json=payload,
        timeout=15,
    ).json()


def main():
    all_ok = True

    # 0) 浏览器检测
    print("---- 浏览器检测 ----")
    browser = find_browser()
    
    if not browser:
        print("未检测到可用的浏览器，尝试自动启动...")
        for b in BROWSERS:
            if launch_browser(b):
                browser = find_browser()
                if browser:
                    break
        time.sleep(2)  # 再给点时间启动
        browser = find_browser()
    
    if not browser:
        fail("未检测到可用的浏览器")
        print("\n请手动启动浏览器:")
        print("1. Edge:")
        print("   /Applications/Microsoft\\ Edge.app/Contents/MacOS/Microsoft\\ Edge --remote-debugging-port=9223 --remote-allow-origins='*'")
        print("2. Chrome:")
        print("   /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=18800 --remote-allow-origins='*'")
        print("3. 登录 https://cst.uf-tree.com")
        return 1

    print(f"✅ 检测到 {browser['name']} 浏览器 (端口 {browser['port']})")
    if browser["has_cst"]:
        print(f"✅ 已发现财税通页面")
    else:
        print(f"⚠️  {browser['name']} 中未发现财税通页面，请先登录 https://cst.uf-tree.com")
        return 1

    print()

    # 1) CDP reachable
    try:
        pages = requests.get(browser["url"], timeout=6).json()
        all_ok &= ok(f"CDP 可用，页面数: {len(pages)}")
    except Exception as e:
        fail(f"无法访问 CDP {browser['port']}: {e}")
        return 1

    # 2-3) auth
    try:
        auth = get_auth(browser)
        token = auth["token"]
        cid = auth["companyId"]
        cname = auth.get("companyName", "")
        all_ok &= ok(f"登录态可读: companyId={cid}, companyName={cname}")
    except Exception as e:
        fail(str(e))
        return 1

    # 4) APIs
    checks = []
    try:
        r = api_post(token, "/api/member/department/queryCompany", {"companyId": cid})
        users = (r.get("result", {}) or {}).get("users", []) or []
        checks.append((len(users) > 0, f"queryCompany 用户数={len(users)}"))
    except Exception as e:
        checks.append((False, f"queryCompany 异常: {e}"))

    try:
        r = api_get(token, "/api/member/department/queryDepartments", {"companyId": cid})
        deps = r.get("result", []) or []
        checks.append((len(deps) > 0, f"queryDepartments 部门数={len(deps)}"))
    except Exception as e:
        checks.append((False, f"queryDepartments 异常: {e}"))

    try:
        r = api_get(token, "/api/member/role/get/tree", {"companyId": cid})
        tree = r.get("result", []) or []
        role_count = sum(len(x.get("children") or []) for x in tree)
        checks.append((role_count > 0, f"role/get/tree 角色数={role_count}"))
    except Exception as e:
        checks.append((False, f"role/get/tree 异常: {e}"))

    try:
        r = api_get(token, "/api/bill/feeTemplate/queryFeeTemplate", {"companyId": cid, "status": 1, "pageSize": 5000})
        rows = r.get("result", []) or []
        pcount = len([x for x in rows if x.get("parentId") == -1])
        checks.append((pcount > 0, f"queryFeeTemplate 一级科目数={pcount}"))
    except Exception as e:
        checks.append((False, f"queryFeeTemplate 异常: {e}"))

    try:
        r = api_get(token, "/api/bpm/workflow/queryWorkFlow", {"companyId": cid, "t": int(time.time() * 1000)})
        wfs = r.get("result", []) or []
        checks.append((True, f"queryWorkFlow 可用，返回 {len(wfs)} 条"))
    except Exception as e:
        checks.append((False, f"queryWorkFlow 异常: {e}"))

    for passed, msg in checks:
        if passed:
            ok(msg)
        else:
            fail(msg)
            all_ok = False

    print("\n---- PRECHECK RESULT ----")
    if all_ok:
        ok("全部通过，可执行生成脚本")
        return 0
    else:
        fail("存在失败项，请先修复环境再生成")
        return 1


if __name__ == "__main__":
    sys.exit(main())
