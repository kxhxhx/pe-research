#!/bin/bash
# ============================================================
# 每日研究入口脚本
# 调用 Python 研究脚本
# ============================================================
set -euo pipefail

DATE=$(date +%Y-%m-%d)
echo "[$(date '+%H:%M:%S')] Starting research for ${DATE}"

# 检查 Python3
if ! command -v python3 &>/dev/null; then
  echo "Python3 not found, installing..."
  apt-get update -qq && apt-get install -y -qq python3 2>/dev/null || {
    echo "Cannot install python3, using minimal report"
    mkdir -p daily_reports
    cat > "daily_reports/${DATE}.md" << EOF
# 电力电子 × 智能体 每日研究

日期: ${DATE}

Python3 未安装，无法运行研究脚本。
请检查 GitHub Actions 运行环境。
EOF
    exit 0
  }
fi

# 运行 Python 研究脚本
python3 scripts/run_research.py

echo "[$(date '+%H:%M:%S')] Done"
