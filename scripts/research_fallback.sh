#!/bin/bash
# ============================================================
# 电力电子×智能体 每日研究 - 备用脚本
# 当 opencode run 在 CI 环境不可用时使用
# 使用 arXiv/GitHub API + LLM API 直接生成报告
# ============================================================
set -euo pipefail

DATE="${1:-$(date +%Y-%m-%d)}"
LLM_API_KEY="${2:-}"

REPORT_DIR="daily_reports"
mkdir -p "${REPORT_DIR}"

echo "🔍 备用研究模式 - ${DATE}"

# --------------------------------------------------
# 1. 搜索 arXiv 最新论文
# --------------------------------------------------
echo "  → 搜索 arXiv..."
ARXIV_RESULTS=$(curl -s "http://export.arxiv.org/api/query?search_query=all:%22power+electronics%22+AND+all:%22large+language+model%7Cagent%22&sortBy=submittedDate&sortOrder=descending&max_results=5" 2>/dev/null || echo "")

# --------------------------------------------------
# 2. 搜索 GitHub 新项目
# --------------------------------------------------
echo "  → 搜索 GitHub..."
GITHUB_RESULTS=$(curl -s "https://api.github.com/search/repositories?q=power+electronics+AI+agent&sort=updated&per_page=5" 2>/dev/null || echo "")

# --------------------------------------------------
# 3. 搜索 npm 包版本
# --------------------------------------------------
echo "  → 检查工具版本..."
OH_MY_EMBEDDED_VER=$(curl -s "https://registry.npmjs.org/oh-my-embedded/latest" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('version','unknown'))" 2>/dev/null || echo "unknown")

# --------------------------------------------------
# 4. 用 LLM 生成汇总报告
# --------------------------------------------------
REPORT_FILE="${REPORT_DIR}/${DATE}.md"

# 构建报告内容（基础模板）
cat > "${REPORT_FILE}" << EOF
# 📡 电力电子 × 智能体 每日研究

**日期**: ${DATE}

---

## 📄 今日新论文

$(if [ -n "${ARXIV_RESULTS}" ]; then
  echo "${ARXIV_RESULTS}" | python3 -c "
import sys, xml.etree.ElementTree as ET
try:
    root = ET.fromstring(sys.stdin.read())
    ns = {'a': 'http://www.w3.org/2005/Atom'}
    entries = root.findall('a:entry', ns)
    for i, entry in enumerate(entries[:5]):
        title = entry.find('a:title', ns).text.strip().replace('\n', ' ') if entry.find('a:title', ns) is not None else 'No title'
        url = entry.find('a:id', ns).text.strip() if entry.find('a:id', ns) is not None else ''
        summary = entry.find('a:summary', ns).text.strip().replace('\n', ' ')[:200] if entry.find('a:summary', ns) is not None else ''
        print(f'### {title}')
        print(f'- **链接**: {url}')
        print(f'- **摘要**: {summary}...')
        print()
" 2>/dev/null || echo '  arXiv API 暂不可用，请手动访问 https://arxiv.org/search/?searchtype=all&query=power+electronics+agent'
else
  echo '  arXiv API 暂不可用，请手动访问 https://arxiv.org/search/?searchtype=all&query=power+electronics+agent'
fi
)

---

## 🔧 工具版本状态

| 工具 | 当前最新版本 |
|------|------------|
| oh-my-embedded | ${OH_MY_EMBEDDED_VER} |
| Simulink Agentic Toolkit | [查看发布](https://github.com/matlab/simulink-agentic-toolkit/releases) |
| MATLAB MCP Server | [查看安装](https://github.com/matlab/matlab-mcp-server) |
| kicad-mcp | [查看发布](https://github.com/blwfish/kicad-mcp/releases) |

---

## 🏭 GitHub 新项目

$(if [ -n "${GITHUB_RESULTS}" ]; then
  echo "${GITHUB_RESULTS}" | python3 -c "
import sys, json
try:
    data = json.loads(sys.stdin.read())
    for item in data.get('items', [])[:5]:
        name = item.get('full_name', 'unknown')
        desc = item.get('description', '') or '无描述'
        url = item.get('html_url', '')
        stars = item.get('stargazers_count', 0)
        updated = item.get('updated_at', '')[:10]
        print(f'- [{name}]({url}) ⭐{stars} | 更新:{updated}')
        print(f'  {desc}')
        print()
except:
    print('  GitHub API 暂不可用')
" 2>/dev/null || echo '  GitHub API 暂不可用'
else
  echo '  GitHub API 暂不可用'
fi
)

---

## 📰 技术动态

- **Simulink Agentic Toolkit** 已发布，支持 Claude Code/Copilot/Codex/Amp/Gemini CLI \
  [GitHub](https://github.com/matlab/simulink-agentic-toolkit)
- **oh-my-embedded** v${OH_MY_EMBEDDED_VER} 可用 \
  [npm](https://www.npmjs.com/package/oh-my-embedded)

---

## ⭐ 推荐关注

> 此报告由 GitHub Actions 自动生成，基于 arXiv/GitHub/npm API。
> 完整的 AI 深度分析需要使用 LLM_API_KEY 配置。

---

EOF

echo "✅ 报告已生成: ${REPORT_FILE}"
echo "report_date=${DATE}"
