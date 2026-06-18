# 🧪 电力电子 × 智能体 每日研究

> 每天自动搜索电力电子与 AI 智能体交叉领域的最新学术论文、开源工具、工业案例，
> 生成结构化报告并通过企业微信 Bot 推送到手机。

---

## 目录

- [系统架构](#系统架构)
- [前置准备](#前置准备)
- [快速搭建（3分钟）](#快速搭建3分钟)
  - [第1步：创建 GitHub 私有仓库](#第1步创建-github-私有仓库)
  - [第2步：推送代码](#第2步推送代码)
  - [第3步：配置企业微信 Bot](#第3步配置企业微信-bot)
  - [第4步：添加 GitHub Secrets](#第4步添加-github-secrets)
  - [第5步：启用 Actions](#第5步启用-actions)
- [效果验证](#效果验证)
- [自定义指南](#自定义指南)
- [故障排查](#故障排查)

---

## 系统架构

```
[GitHub Actions] 每天 UTC 01:00 (= 北京时间 09:00)
       │
       ▼
  ┌─ 安装 OpenCode CLI + API 密钥 ──────────────────┐
  │   opencode run -p "搜索+汇总研究提示词"           │
  │   ↓                                              │
  │   生成 daily_reports/YYYY-MM-DD.md               │
  └──────────────────────────────────────────────────┘
       │
       ▼
  ┌─ 提交到 Git 仓库 ────────┐
  │  自动归档30天前的旧报告    │
  └──────────────────────────┘
       │
       ▼
  ┌─ 推送企业微信 Bot ───────┐
  │  手机收到 Markdown 通知    │
  └──────────────────────────┘
```

### 文件结构

```
pe-research/
├── .github/
│   └── workflows/
│       └── daily-research.yml    # GitHub Actions 工作流（核心）
├── scripts/
│   ├── research_fallback.sh      # 备用研究脚本（OpenCode不可用时）
│   └── send_wecom.sh             # 企业微信推送脚本
├── daily_reports/                # 每日报告（自动生成）
│   ├── YYYY-MM-DD.md
│   └── archive/                  # 超过30天的报告
├── README.md                     # 本文件
└── .gitignore
```

---

## 前置准备

| 项目 | 说明 |
|------|------|
| GitHub 账号 | 免费，用于托管代码和运行 Actions |
| LLM API Key | 推荐 Anthropic (Claude) 或 OpenAI，用于研究生成 |
| 企业微信 | 免费，用于接收手机推送 |

---

## 快速搭建（3分钟）

### 第1步：创建 GitHub 私有仓库

浏览器打开 GitHub → New repository：

```
Repository name: pe-research
Description: 电力电子×智能体 每日研究
Visibility: Private（私有）
勾选: Add a README file ❌（不勾选，我们用已有的）
```

或直接在终端：

<｜｜DSML｜｜tool_calls>
<｜｜DSML｜｜invoke name="bash">
<｜｜DSML｜｜parameter name="command" string="true">curl -s -u "kxhxhx" -X POST "https://api.github.com/user/repos" -H "Accept: application/vnd.github.v3+json" -d "{\"name\":\"pe-research\",\"description\":\"电力电子×智能体 每日研究\",\"private\":true}" 2>&1 | python3 -c "import sys,json; d=json.load(sys.stdin); print('✅ 创建成功:', d.get('html_url','')); print('Clone URL:', d.get('clone_url',''))" 2>&1 | findstr /v "^full_name$"