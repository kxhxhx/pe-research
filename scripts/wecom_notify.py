#!/usr/bin/env python3
"""
Send daily research report to WeCom bot with rich content preview.
"""
import json, os, urllib.request

wecom_key = os.environ.get("WECOM_KEY", "")
if not wecom_key:
    print("No WECOM_KEY, skip")
    exit(0)

today = os.environ.get("DATE", "")
report_file = os.environ.get("REPORT_FILE", "")
if not report_file or not os.path.exists(report_file):
    print(f"Report not found: {report_file}")
    exit(1)

report = open(report_file, encoding="utf-8").read()
repo = os.environ.get("GITHUB_REPOSITORY", "kxhxhx/pe-research")
report_url = f"https://github.com/{repo}/blob/main/{report_file}"

# ============================================================
# Extract structured content
# ============================================================
def extract_section(text, header):
    """Extract content between a ## header and the next ## header or ---"""
    start = text.find(header)
    if start == -1:
        return ""
    start += len(header)
    end = len(text)
    for marker in ["\n---", "\n## "]:
        pos = text.find(marker, start)
        if pos != -1 and pos < end:
            end = pos
    return text[start:end].strip()

# Extract key sections
papers = extract_section(report, "## 📄 今日新论文")
ai_summary = extract_section(report, "## 🤖 AI 深度分析")
projects = extract_section(report, "## 🏭 GitHub 新项目")

# ============================================================
# Build WeCom markdown message
# ============================================================
# WeCom markdown has strict limitations:
# - Max 4096 chars
# - Limited markdown syntax (bold, links, quotes, code)
# - No color/size support

lines = [f"# 📡 PE Research {today}", ""]

# Papers preview (titles only for brevity)
if papers:
    paper_count = papers.count("###")
    lines.append(f"> **今日论文 ({paper_count}篇)**")
    for p in papers.split("### ")[:5]:
        p = p.strip()
        if not p:
            continue
        # Extract title (first line before \n)
        title_line = p.split("\n")[0]
        # Clean up markdown link
        title_line = title_line.replace("[", "").replace("]", "")
        if len(title_line) > 80:
            title_line = title_line[:80] + "..."
        lines.append(f"- {title_line}")
    if paper_count > 5:
        lines.append(f"- ... 等 {paper_count} 篇")
    lines.append("")

# AI summary (most valuable)
if ai_summary:
    lines.append(f"> **AI 分析**")
    # Take first 4 lines
    summary_lines = ai_summary.strip().split("\n")[:8]
    for sl in summary_lines:
        sl = sl.strip()
        if sl and not sl.startswith("---"):
            # Clean markdown headers to bold
            if sl.startswith("### "):
                sl = f"**{sl[4:]}**"
            if len(sl) > 120:
                sl = sl[:120] + "..."
            lines.append(sl)
    lines.append("")

# Projects
if projects:
    project_list = projects.strip().split("\n")
    names = [l for l in project_list if l.startswith("### [")]
    if names:
        lines.append(f"> **新项目 ({len(names)}个)**")
        for n in names[:3]:
            # Extract repo name from ### [org/repo](url)
            n = n.replace("### [", "").split("](")[0]
            lines.append(f"- {n}")
        lines.append("")

lines.append("")
lines.append(f"[📖 查看完整报告]({report_url})")

# Truncate to 3800 chars (WeCom limit ~4096)
content = "\n".join(lines)
if len(content) > 3800:
    content = content[:3800] + "..."

# ============================================================
# Send to WeCom
# ============================================================
payload = json.dumps({
    "msgtype": "markdown",
    "markdown": {"content": content}
}, ensure_ascii=False).encode("utf-8")

url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={wecom_key}"
try:
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST"
    )
    resp = json.loads(urllib.request.urlopen(req, timeout=10).read())
    if resp.get("errcode") == 0:
        print("WeCom sent OK")
    else:
        print(f"WeCom error: {resp}")
except Exception as e:
    print(f"WeCom send failed: {e}")
