#!/usr/bin/env python3
"""
统一入口：生成三表 + 导入财税通
整合 Agent1.1 (生成) + Agent2.2 (导入)

用法：
    python generate_and_import.py [--skip-generate] [--skip-import] [--company-id ID]

步骤：
    1. 生成三表 (01_添加员工, 02_费用科目配置, 03_单据表)
    2. 自动导入到财税通系统
"""

import argparse
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
AGENT1_DIR = BASE_DIR / "scripts" / "agent1"
AGENT2_DIR = BASE_DIR / "scripts" / "agent2"
ASSETS_DIR = BASE_DIR / "assets"


def run_generate():
    """Step 1: 生成三表"""
    print("=" * 60)
    print("步骤 1/2: 生成三表 (Agent1.1)")
    print("=" * 60)

    template = ASSETS_DIR / "客户模板.xlsx"
    if not template.exists():
        print(f"错误: 模板文件不存在: {template}")
        print("请确保 assets/客户模板.xlsx 存在")
        return False

    script = AGENT1_DIR / "generate_three_sheets_from_customer_template.py"
    output = ASSETS_DIR / f"三表生成结果_{subprocess.check_output(['date', '+%Y%m%d_%H%M%S']).decode().strip()}.xlsx"

    cmd = [
        sys.executable, str(script),
        "--template", str(template),
        "--output", str(output)
    ]

    print(f"运行: {' '.join(cmd)}")
    result = subprocess.run(cmd)

    if result.returncode != 0:
        print("生成三表失败")
        return False

    print(f"✅ 三表已生成: {output}")
    return True


def run_import(company_id=None):
    """Step 2: 导入财税通"""
    print("\n" + "=" * 60)
    print("步骤 2/2: 导入财税通 (Agent2.2)")
    print("=" * 60)

    script = AGENT2_DIR / "import_from_agent1.py"

    cmd = [sys.executable, str(script)]
    if company_id:
        cmd.extend(["--company-id", str(company_id)])

    print(f"运行: {' '.join(cmd)}")
    result = subprocess.run(cmd)

    if result.returncode != 0:
        print("导入失败")
        return False

    print("✅ 导入完成")
    return True


def main():
    parser = argparse.ArgumentParser(description="生成三表并导入财税通")
    parser.add_argument("--skip-generate", action="store_true", help="跳过生成步骤")
    parser.add_argument("--skip-import", action="store_true", help="跳过导入步骤")
    parser.add_argument("--company-id", type=int, help="指定公司ID")
    parser.add_argument("--preflight-only", action="store_true", help="仅运行环境检查")
    args = parser.parse_args()

    if args.preflight_only:
        script = AGENT1_DIR / "preflight_check.py"
        subprocess.run([sys.executable, str(script)])
        return

    success = True

    if not args.skip_generate:
        success = run_generate() and success

    if not args.skip_import and success:
        success = run_import(args.company_id) and success

    if success:
        print("\n" + "=" * 60)
        print("✅ 全部完成!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ 部分步骤失败")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
