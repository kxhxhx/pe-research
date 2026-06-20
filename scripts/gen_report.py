#!/usr/bin/env python3
"""
Generate daily research report from multiple arXiv feeds, GitHub API, and npm registry.
Optimized v2: multi-source arXiv, deduplication, structured LLM summary.
"""
import json, os, sys, urllib.request, urllib.error
from datetime import date
from xml.etree import ElementTree

today = sys.argv[1] if len(sys.argv) > 1 else str(date.today())
REPORT_DIR = "daily_reports"
api_key = os.environ.get("LLM_API_KEY", "")
os.makedirs(REPORT_DIR, exist_ok=True)

# ============================================================
# 1. Parse all arXiv XML feeds
# ============================================================
arxiv_files = [
    "/tmp/arxiv_title.xml",
    "/tmp/arxiv_pe.xml",
    "/tmp/arxiv_motor.xml",
    "/tmp/arxiv_embedded.xml",
]
papers = []
seen_titles = set()

for fpath in arxiv_files:
    try:
        xml_text = open(fpath, encoding="utf-8").read()
        if not xml_text.strip():
            continue
        root = ElementTree.fromstring(xml_text)
        ns = {"a": "http://www.w3.org/2005/Atom"}
        for entry in root.findall("a:entry", ns):
            # Title
            title_el = entry.find("a:title", ns)
            title = title_el.text.strip().replace("\n", " ") if title_el is not None else ""
            if not title or title.lower() in seen_titles:
                continue
            seen_titles.add(title.lower())

            # URL
            id_el = entry.find("a:id", ns)
            url = id_el.text.strip() if id_el is not None else ""

            # Authors
            authors = []
            for a in entry.findall("a:author", ns):
                n = a.find("a:name", ns)
                if n is not None:
                    authors.append(n.text)

            # Published date
            pub_el = entry.find("a:published", ns)
            published = pub_el.text[:10] if pub_el is not None else ""

            # Summary (first 250 chars)
            sum_el = entry.find("a:summary", ns)
            summary = sum_el.text.strip().replace("\n", " ")[:250] if sum_el is not None else ""

            papers.append({
                "title": title,
                "url": url,
                "authors": ", ".join(authors[:5]),
                "published": published,
                "summary": summary,
            })
    except Exception as e:
        print(f"  arXiv skip {fpath}: {e}")

# Sort by date (newest first)
papers.sort(key=lambda p: p["published"], reverse=True)
papers = papers[:12]

print(f"  arXiv: {len(papers)} papers")

# ============================================================
# 2. Parse GitHub results
# ============================================================
repos = []
try:
    gh = json.load(open("/tmp/gh.json"))
    for item in gh.get("items", [])[:6]:
        repos.append({
            "name": item.get("full_name", ""),
            "url": item.get("html_url", ""),
            "desc": (item.get("description") or "").strip(),
            "stars": item.get("stargazers_count", 0),
            "updated": (item.get("updated_at") or "")[:10],
            "language": item.get("language", ""),
        })
except Exception as e:
    print(f"  GitHub parse: {e}")

print(f"  GitHub: {len(repos)} repos")

# ============================================================
# 3. Check tool versions
# ============================================================
tools = {}
for pkg in ["oh-my-embedded", "opencode-ai"]:
    try:
        req = urllib.request.Request(
            f"https://registry.npmjs.org/{pkg}/latest",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        tools[pkg] = json.loads(urllib.request.urlopen(req, timeout=10).read()).get("version", "?")
    except:
        tools[pkg] = "?"

# ============================================================
# 4. Build report
# ============================================================
lines = [
    f"# 电力电子 × AI 智能体 每日研究",
    f"",
    f"> **日期**: {today} | 由 GitHub Actions 自动生成",
    f"",
    f"---",
]

# --- Papers ---
lines += ["", "## 📄 今日新论文", ""]
if papers:
    for p in papers:
        lines.append(f"### [{p['title']}]({p['url']})")
        lines.append(f"- **作者**: {p['authors']}")
        lines.append(f"- **发表**: {p['published']}")
        if p['summary']:
            lines.append(f"- **摘要**: {p['summary']}...")
        lines.append("")
else:
    lines.append("今日无新增论文（arXiv API 可能暂时不可用，手动访问：[arXiv 搜索](http://export.arxiv.org/api/query?search_query=all:power+electronics+AND+all:agent)）")
    lines.append("")

# --- GitHub ---
lines += ["---", "", "## 🏭 GitHub 新项目", ""]
if repos:
    for r in repos:
        lang_tag = f" `{r['language']}`" if r['language'] else ""
        lines.append(f"### [{r['name']}]({r['url']}) ⭐{r['stars']}")
        lines.append(f"- 更新: {r['updated']}{lang_tag}")
        if r['desc']:
            lines.append(f"- {r['desc']}")
        lines.append("")
else:
    lines.append("GitHub API 暂不可用。")
    lines.append("")

# --- Tools ---
lines += ["---", "", "## 🔧 工具版本", ""]
lines.append("| 工具 | 版本 | 链接 |")
lines.append("|------|------|------|")
lines.append(f"| oh-my-embedded | {tools.get('oh-my-embedded','?')} | [npm](https://www.npmjs.com/package/oh-my-embedded) |")
lines.append(f"| opencode-ai | {tools.get('opencode-ai','?')} | [npm](https://www.npmjs.com/package/opencode-ai) |")
lines.append(f"| Simulink Agentic Toolkit | latest | [GitHub](https://github.com/matlab/simulink-agentic-toolkit) |")
lines.append(f"| MATLAB MCP Server | latest | [GitHub](https://github.com/matlab/matlab-mcp-server) |")
lines.append(f"| kicad-mcp | latest | [GitHub](https://github.com/blwfish/kicad-mcp) |")
lines.append(f"| embedded-agent | latest | [GitHub](https://github.com/zhaozhede/embedded-agent) |")
lines.append("")

# --- LLM Summary ---
if api_key and (papers or repos):
    lines += ["---", "", "## 🤖 AI 深度分析", ""]
    try:
        # Build structured prompt
        paper_text = "\n".join(
            f"{i+1}. {p['title']} ({p['published']}) | {p['authors']} | {p['summary'][:150]}"
            for i, p in enumerate(papers[:8])
        ) or "No papers today"

        repo_text = "\n".join(
            f"{i+1}. {r['name']} ⭐{r['stars']} | {r['desc'][:150]}"
            for i, r in enumerate(repos)
        ) or "No repos today"

        prompt = f"""你是电力电子与嵌入式AI交叉领域的研究分析师。请分析今日的学术与工程动态。

## 今日学术论文
{paper_text}

## 今日开源项目
{repo_text}

## 工具版本
oh-my-embedded: v{tools.get('oh-my-embedded','?')}
opencode-ai: v{tools.get('opencode-ai','?')}

## 任务
请按以下四个维度输出分析（每个2-3句）：

### 1. 研究趋势
（从论文中提炼技术方向，如：多智能体控制、LLM驱动设计、物理信息学习等）

### 2. 工具生态动态
（新的开源工具、插件发布对工程师的影响）

### 3. 值得关注的项目
（从GitHub中挑1-2个最有价值的，说明理由）

### 4. 明日推荐追踪方向
（基于今日发现，建议明天重点搜索什么）

请用中文，保持简洁。"""

        payload = json.dumps({
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "你是电力电子AI研究分析师，用中文输出结构化分析。"},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1500,
            "temperature": 0.3
        }).encode()

        req = urllib.request.Request(
            "https://api.deepseek.com/chat/completions",
            data=payload,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
            method="POST"
        )
        resp = urllib.request.urlopen(req, timeout=60)
        result = json.loads(resp.read())
        summary = result["choices"][0]["message"]["content"]
        lines.append(summary)
        lines.append("")
    except Exception as e:
        lines.append(f"_AI 分析暂不可用 ({type(e).__name__})_")
        lines.append("")

# --- Footer ---
lines += [
    "---",
    "",
    "> 📌 **说明**",
    "> - 数据来源：arXiv API + GitHub API + npm Registry",
    "> - AI 摘要：DeepSeek Chat",
    "> - 每天北京时间 09:00 自动更新",
    "> - 完整搜索关键词：power electronics, converter, inverter, motor control, AI agent, LLM, embedded firmware",
    "> - 系统配置与维护：[README](https://github.com/kxhxhx/pe-research)",
    "",
    f"*Generated {today} by [GitHub Actions](https://github.com/kxhxhx/pe-research/actions)*",
]

# ============================================================
# 5. Write report
# ============================================================
path = os.path.join(REPORT_DIR, f"{today}.md")
with open(path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"Report: {path} ({len(lines)} lines)")
