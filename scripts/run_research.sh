#!/bin/bash
# ============================================================
# 每日研究执行脚本
# 供 GitHub Actions 调用
# ============================================================
set -euo pipefail

DATE=$(date +%Y-%m-%d)
REPORT_DIR="daily_reports"
mkdir -p "${REPORT_DIR}"

echo "[$(date '+%H:%M:%S')] Starting daily research for ${DATE}"

# 安装 OpenCode（如果未安装）
if ! command -v opencode &>/dev/null; then
  echo "Installing opencode-ai..."
  npm install -g opencode-ai
fi

# 用 OpenCode run 模式执行研究
opencode run -p 'You are a research assistant specializing in power electronics and AI agents.

Search for the following topics using available web search tools:

1. ACADEMIC PAPERS: Search arxiv.org / IEEE for:
   - power electronics + AI agent + LLM
   - power converter + autonomous design
   - motor control + reinforcement learning + embedded
   - SiC/GaN inverter + AI optimization
   - LLM + SPICE + circuit simulation

2. GITHUB PROJECTS: Search for repos updated in last 7 days:
   - opencode plugin embedded
   - power electronics AI agent firmware
   - motor control LLM code generation

3. TOOLS: Check latest versions of:
   - oh-my-embedded (npm registry)
   - Simulink Agentic Toolkit
   - kicad-mcp
   - MATLAB MCP Server

4. INDUSTRY: Search MathWorks/ST/TI/Infineon/ABB for AI+power electronics news

Write the results to /tmp/research_report.md in this format:

# Power Electronics x AI Agent Daily Research
Date: '${DATE}'

--- New Papers ---
Title | Source | Authors | Key Contribution | URL

--- Tools ---
Name | Version | Changes | Link

--- GitHub Projects ---
Repo | Stars | Description | URL

--- Industry News ---

--- Key Takeaways ---

' 2>&1 | tail -5

echo "[$(date '+%H:%M:%S')] OpenCode finished"

# 检查报告是否生成
if [ -f /tmp/research_report.md ]; then
  cp /tmp/research_report.md "${REPORT_DIR}/${DATE}.md"
  echo "report_generated=true"
  echo "REPORT_FILE=${REPORT_DIR}/${DATE}.md"
else
  echo "OpenCode did not generate report, running fallback..."
  # 用 LLM_API_KEY 环境变量
  bash scripts/research_fallback.sh "${DATE}" "${LLM_API_KEY:-}"
  echo "report_generated=true"
  echo "REPORT_FILE=${REPORT_DIR}/${DATE}.md"
fi

echo "[$(date '+%H:%M:%S')] Research complete: ${REPORT_DIR}/${DATE}.md"
