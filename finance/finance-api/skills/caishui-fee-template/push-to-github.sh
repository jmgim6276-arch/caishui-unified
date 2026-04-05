#!/bin/bash
# GitHub 推送脚本
# 将 Skill 推送到 GitHub 仓库

echo "🚀 推送 Skill 到 GitHub"
echo "========================"

# 检查 git
echo "📦 检查 Git..."
if ! command -v git &> /dev/null; then
    echo "❌ 请先安装 Git"
    exit 1
fi

# 进入 Skill 目录
cd ~/Desktop/自动添加员工项目/caishui-fee-template-skill

echo "📁 当前目录: $(pwd)"

# 初始化 git（如果不存在）
if [ ! -d ".git" ]; then
    echo "🔧 初始化 Git 仓库..."
    git init
    git branch -m main
fi

# 检查远程仓库
echo "🔗 检查远程仓库..."
if ! git remote get-url origin &> /dev/null; then
    echo "⚠️  未设置远程仓库"
    echo ""
    echo "请先在 GitHub 创建仓库，然后运行："
    echo "  git remote add origin https://github.com/USERNAME/caishui-fee-template-skill.git"
    echo ""
    read -p "是否现在添加远程仓库? (y/n): " add_remote
    
    if [ "$add_remote" = "y" ]; then
        read -p "请输入 GitHub 仓库 URL: " repo_url
        git remote add origin "$repo_url"
        echo "✅ 远程仓库已添加"
    else
        echo "❌ 取消推送"
        exit 1
    fi
fi

# 添加所有文件
echo "📥 添加文件到 Git..."
git add -A

# 检查是否有变更
if git diff --cached --quiet; then
    echo "⚠️  没有新的变更需要提交"
    exit 0
fi

# 提交
echo "💾 提交变更..."
git commit -m "Initial commit: 财税通费用模板批量添加 Skill v1.0.0

功能:
- 自动从浏览器获取认证信息
- 查询一级科目并获取完整配置
- 读取 Excel 并批量添加二级科目
- 自动继承 applyJson 和 feeJson 字段
- 完整错误处理和验证

文档:
- 详细的 README.md (小白教程)
- 快速开始指南
- 示例 Excel 文件
- API 详解和排错指南"

# 推送
echo "📤 推送到 GitHub..."
if git push -u origin main; then
    echo ""
    echo "✅ 推送成功！"
    echo ""
    echo "📎 仓库地址:"
    git remote get-url origin
    echo ""
    echo "🎉 Skill 已成功上传到 GitHub！"
else
    echo "❌ 推送失败"
    exit 1
fi
