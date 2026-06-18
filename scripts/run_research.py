#!/usr/bin/env python3
"""
每日电力电子研究脚本
用于 GitHub Actions，不依赖 OpenCode TUI
"""
import json
import os
import subprocess
import urllib.request
import urllib.error
from datetime import date
from xml.etree import ElementTree

REPORT_DIR = "daily_reports"
TODAY = str(date.today())


def fetch_arxiv():
    """搜索 arXiv 最新论文"""
    url = ("http://export.arxiv.org/api/query?"
           "search_query=all:power+electronics+AND+all:(agent+LLM)"
           "&sortBy=submittedDate&sortOrder=descending&max_results=8")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        resp = urllib.request.urlopen(req, timeout=30)
        return resp.read().decode("utf-8")
    except Exception as e:
        return f"<!-- arXiv error: {e} -->"


def fetch_github():
    """搜索 GitHub 新项目"""
    url = ("https://api.github.com/search/repositories?"
           "q=power+electronics+AI+agent&sort=updated&per_page=5")
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "PE-Research-Bot",
            "Accept": "application/vnd.github.v3+json"
        })
        resp = urllib.request.urlopen(req, timeout=30)
        return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e)}


def fetch_npm_version(pkg="oh-my-embedded"):
    """查询 npm 包最新版本"""
    try:
        req = urllib.request.Request(
            f"https://registry.npmjs.org/{pkg}/latest",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())
        return data.get("version", "?")
    except Exception:
        return "?"


def parse_arxiv(xml_data):
    """解析 arXiv XML，提取论文信息"""
    papers = []
    try:
        root = ElementTree.fromstring(xml_data)
        ns = {"a": "http://www.w3.org/2005/Atom"}
        for entry in root.findall("a:entry", ns)[:6]:
            title_el = entry.find("a:title", ns)
            title = title_el.text.strip().replace("\n", " ") if title_el is not None else "No title"
            url_el = entry.find("a:id", ns)
            url = url_el.text.strip() if url_el is not None else ""
            summary_el = entry.find("a:summary", ns)
            summary = summary_el.text.strip().replace("\n", " ")[:200] if summary_el is not None else ""
            authors = []
            for author in entry.findall("a:author", ns):
                name = author.find("a:name", ns)
                if name is not None:
                    authors.append(name.text)
            papers.append({
                "title": title,
                "url": url,
                "summary": summary,
                "authors": ", ".join(authors[:4]),
            })
    except Exception:
        pass
    return papers


def parse_github(data):
    """解析 GitHub API 返回"""
    repos = []
    if "error" in data:
        return repos
    for item in data.get("items", [])[:5]:
        repos.append({
            "name": item.get("full_name", ""),
            "url": item.get("html_url", ""),
            "desc": item.get("description") or "",
            "stars": item.get("stargazers_count", 0),
            "updated": item.get("updated_at", "")[:10],
        })
    return repos


def call_llm(prompt, api_key):
    """调用 LLM API 生成报告"""
    if not api_key:
        return None

    # 检测 API Key 类型选择端点
    if api_key.startswith("sk-"):
        # OpenAI / DeepSeek 兼容格式
        if api_key.startswith("sk-ant"):
            # Anthropic
            return _call_anthropic(prompt, api_key)
        else:
            return _call_openai_compat(prompt, api_key)
    else:
        return _call_openai_compat(prompt, api_key)


def _call_openai_compat(prompt, api_key):
    """调用 OpenAI 兼容 API"""
    payload = json.dumps({
        "model": os.environ.get("LLM_MODEL", "deepseek-chat"),
        "messages": [
            {"role": "system", "content": "你是电力电子领域的AI研究助理，用中文输出Markdown报告。"},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 4096,
        "temperature": 0.3
    }).encode("utf-8")

    base_url = os.environ.get("LLM_BASE_URL", "https://api.deepseek.com")
    req = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        },
        method="POST"
    )
    try:
        resp = urllib.request.urlopen(req, timeout=120)
        result = json.loads(resp.read())
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        return f"<!-- LLM API error: {e} -->"


def _call_anthropic(prompt, api_key):
    """调用 Anthropic API"""
    payload = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}]
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        },
        method="POST"
    )
    try:
        resp = urllib.request.urlopen(req, timeout=120)
        result = json.loads(resp.read())
        return result["content"][0]["text"]
    except Exception as e:
        return f"<!-- Anthropic API error: {e} -->"


def build_report(arxiv_papers, github_repos, npm_ver, llm_content=None):
    """构建最终报告"""
    if llm_content and not llm_content.startswith("<!--"):
        # 有 LLM 生成内容，直接使用
        return f"# 电力电子 × 智能体 每日研究\n\n**日期**: {TODAY}\n\n---\n\n{llm_content}"

    # 无 LLM，构建基础报告
    lines = [
        f"# 电力电子 × 智能体 每日研究",
        f"",
        f"**日期**: {TODAY}",
        f"",
        f"---",
        f"",
        f"## 📄 今日新论文",
        f"",
    ]

    for p in arxiv_papers:
        lines.append(f"### {p['title']}")
        lines.append(f"- **作者**: {p['authors']}")
        lines.append(f"- **摘要**: {p['summary']}...")
        lines.append(f"- **链接**: {p['url']}")
        lines.append("")

    if not arxiv_papers:
        lines.append("今日未发现新论文（arXiv API 暂不可用）。")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## 🔧 工具版本")
    lines.append("")
    lines.append(f"| 工具 | 版本 |")
    lines.append(f"|------|------|")
    lines.append(f"| oh-my-embedded | {npm_ver} |")
    lines.append(f"| Simulink Agentic Toolkit | [查看发布](https://github.com/matlab/simulink-agentic-toolkit/releases) |")
    lines.append(f"| kicad-mcp | [查看发布](https://github.com/blwfish/kicad-mcp/releases) |")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## 🏭 GitHub 新项目")
    lines.append("")
    for r in github_repos:
        lines.append(f"- [{r['name']}]({r['url']}) ⭐{r['stars']} | {r['updated']}")
        if r['desc']:
            lines.append(f"  {r['desc']}")
        lines.append("")

    if not github_repos:
        lines.append("GitHub API 暂不可用。")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## 📰 技术动态")
    lines.append("")
    lines.append("- **Simulink Agentic Toolkit** 已发布，支持 Claude Code/Copilot/Codex/Amp/Gemini CLI")
    lines.append("  https://github.com/matlab/simulink-agentic-toolkit")
    lines.append("- **oh-my-embedded** for OpenCode，嵌入式/电力电子专用插件")
    lines.append("  https://github.com/captainluzik/oh-my-embedded")
    lines.append("- **kicad-mcp** - 71 个工具的 KiCad AI 代理")
    lines.append("  https://github.com/blwfish/kicad-mcp")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*此报告由 GitHub Actions 自动生成。配置 LLM_API_KEY 可获得 AI 深度分析。*")

    return "\n".join(lines)


def main():
    print(f"[{TODAY}] Starting research...")
    os.makedirs(REPORT_DIR, exist_ok=True)

    # 1. 搜 arXiv
    print("  -> Fetching arXiv...")
    arxiv_xml = fetch_arxiv()
    arxiv_papers = parse_arxiv(arxiv_xml)
    print(f"     Found {len(arxiv_papers)} papers")

    # 2. 搜 GitHub
    print("  -> Fetching GitHub...")
    gh_data = fetch_github()
    gh_repos = parse_github(gh_data)
    print(f"     Found {len(gh_repos)} repos")

    # 3. 工具版本
    print("  -> Checking npm versions...")
    npm_ver = fetch_npm_version()
    print(f"     oh-my-embedded: v{npm_ver}")

    # 4. LLM 深度分析
    api_key = os.environ.get("LLM_API_KEY", "")
    llm_result = None
    if api_key:
        print("  -> Generating AI report...")
        # 构建 LLM prompt
        papers_text = "\n".join(
            f"- {p['title']} | {p['authors']} | {p['summary'][:100]}"
            for p in arxiv_papers[:5]
        )
        repos_text = "\n".join(
            f"- {r['name']} | {r['desc'][:100]} | ⭐{r['stars']}"
            for r in gh_repos[:5]
        )
        prompt = f"""根据以下搜索数据生成一份中文 Markdown 研究报告。

## 今日论文
{papers_text or '无新论文数据'}

## 今日 GitHub 项目
{repos_text or '无新项目数据'}

## 工具版本
oh-my-embedded: v{npm_ver}

## 要求
按以下结构输出：
1. 今日新论文（每个论文简评核心贡献）
2. 工具更新
3. GitHub 新项目
4. 技术动态
5. 重点关注（今日最有价值的 1-2 条，含推荐理由）"""
        llm_result = call_llm(prompt, api_key)
        if llm_result:
            print("     AI report generated")

    # 5. 生成报告
    report = build_report(arxiv_papers, gh_repos, npm_ver, llm_result)
    report_path = os.path.join(REPORT_DIR, f"{TODAY}.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"[{TODAY}] Report saved: {report_path}")


if __name__ == "__main__":
    main()
