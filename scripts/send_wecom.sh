#!/bin/bash
# ============================================================
# 推送每日研究报告到企业微信 Bot
# 使用方式:
#   bash scripts/send_wecom.sh "2026-06-18" "YOUR_WEBHOOK_KEY"
#
# 获取 Webhook:
#   企业微信 → 群聊 → 群机器人 → 添加 → 复制 Webhook URL
#   URL 中的 key 部分即 WECOM_WEBHOOK_KEY
# ============================================================
set -euo pipefail

DATE="${1:-$(date +%Y-%m-%d)}"
WECOM_WEBHOOK_KEY="${2:-}"

REPORT_DIR="daily_reports"
REPORT_FILE="${REPORT_DIR}/${DATE}.md"
REPO_URL="https://github.com/${GITHUB_REPOSITORY:-your-username/pe-research}"

if [ -z "${WECOM_WEBHOOK_KEY}" ]; then
  echo "⚠️ 未配置 WECOM_WEBHOOK_KEY，跳过推送"
  exit 0
fi

if [ ! -f "${REPORT_FILE}" ]; then
  echo "⚠️ 报告文件不存在: ${REPORT_FILE}"
  # 发送简单通知告知研究失败
  WEBHOOK_URL="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=${WECOM_WEBHOOK_KEY}"
  curl -s -X POST "${WEBHOOK_URL}" \
    -H "Content-Type: application/json" \
    -d "{
      \"msgtype\": \"text\",
      \"text\": {
        \"content\": \"⚠️ 电力电子×智能体 每日研究 - ${DATE}\n\n今日研究未生成报告，请手动检查。\n\"
      }
    }"
  exit 1
fi

# 读取报告内容（取前1500字符作为摘要）
SUMMARY=$(head -c 1500 "${REPORT_FILE}" 2>/dev/null || echo "报告读取失败")

# 构建 Markdown 消息（企业微信 Markdown 有长度限制，约4096字符）
WEBHOOK_URL="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=${WECOM_WEBHOOK_KEY}"

# 构建更精简的推送内容
# 从报告中提取关键部分
TITLE_LINE=$(grep "^# 📡" "${REPORT_FILE}" | head -1)
PAPERS=$(sed -n '/^## 📄/,/^## 🔧/p' "${REPORT_FILE}" | grep -E '^###' | head -5 | sed 's/###/- /g')
TOOLS=$(sed -n '/^## 🔧/,/^## /p' "${REPORT_FILE}" | grep -E '^\|' | head -1)
STARS=$(sed -n '/^## ⭐/,/---/p' "${REPORT_FILE}" | head -10)

# 构建推送内容（企业微信 Markdown 格式）
MSG_CONTENT="# 📡 电力电子 × 智能体 每日研究
**${DATE}**

---

## 📄 今日新论文

${PAPERS:-今日无新增论文}

## 🔧 工具版本

详见完整报告

---

## ⭐ 重点关注

${STARS:-详见完整报告}

---

[📖 查看完整报告](${REPO_URL}/blob/main/${REPORT_FILE})
"

# 发送到企微
RESPONSE=$(curl -s -X POST "${WEBHOOK_URL}" \
  -H "Content-Type: application/json" \
  -d "$(python3 -c "
import json, sys
content = sys.stdin.read()
payload = {
    'msgtype': 'markdown',
    'markdown': {
        'content': content.strip()
    }
}
print(json.dumps(payload, ensure_ascii=False))
" <<< "${MSG_CONTENT}")" 2>/dev/null || {
  echo "⚠️ 推送失败，尝试使用 text 模式"
  # 如果 Markdown 格式失败，用 text 兜底
  SHORT_MSG="📡 电力电子×智能体 每日研究 - ${DATE}\n\n报告已生成，请查看完整报告:\n${REPO_URL}/blob/main/${REPORT_FILE}"
  curl -s -X POST "${WEBHOOK_URL}" \
    -H "Content-Type: application/json" \
    -d "{
      \"msgtype\": \"text\",
      \"text\": {
        \"content\": \"${SHORT_MSG}\n\"
      }
    }"
  exit 0
}

echo "✅ 企业微信推送成功"
