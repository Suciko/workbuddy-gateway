"""
更新云端 NewAPI 系统公告（console_setting.announcements）。
保留已有 4 条（1-4，上一轮已上线，不动），追加 2 条新公告对应
LocalProxy.md 第 22、23 节用户改动：
  id=5  第22节 Claude Code 缓存命中模拟
  id=6  第23节 Claude Code 系统提示词定向清洗
不动 api_info / faq / Footer。
"""
import sqlite3
import json
import os

DB_PATH = os.environ.get('ONE_API_DB', 'one-api.db')

announcements = [
    # --- 以下 4 条为上一轮已上线内容，原样保留（"之前改过的不用弄"）---
    {
        "id": 1,
        "publishDate": "2026-06-27",
        "type": "success",
        "content": "### 🚀 敏感词过滤大幅放宽\n\n之前部分正常对话（含 \"Claude\"、\"OpenAI\"、\"签到\" 等常见词）会被误判拦截。现已大幅精简过滤规则，**只保留极少数真正触发风控的词**。\n\n日常对话和代码请求基本不再被误伤，可放心使用。"
    },
    {
        "id": 2,
        "publishDate": "2026-06-27",
        "type": "info",
        "content": "### ✨ 长对话不再受限\n\n之前当单个会话消息过多时会触发 \"聊天历史过长\" 错误导致无法继续。\n\n现已**解除条数限制**，超长历史不再被截断，可放心进行长会话。"
    },
    {
        "id": 3,
        "publishDate": "2026-06-27",
        "type": "info",
        "content": "### 🔧 账号额度显示优化\n\n修复了 \"保存当前账号\" 后额度明细不刷新、云端账号名对不上等问题。\n\n现在保存 / 同步账号后，**额度套餐明细会立即更新**，账号名称也能正确显示昵称和手机号。"
    },
    {
        "id": 4,
        "publishDate": "2026-06-27",
        "type": "warning",
        "content": "### 🐛 打卡面板加载异常修复\n\n修复了打卡面板偶发 \"加载账号发生异常\"、账号列表空白的问题。如仍遇到加载失败，请强制刷新浏览器（Ctrl+F5）后再试。"
    },
    # --- 以下 2 条为本次新增，对应 LocalProxy.md 第 22、23 节 ---
    {
        "id": 5,
        "publishDate": "2026-06-27",
        "type": "success",
        "content": "### ⚡ Claude Code 缓存命中模拟上线\n\n之前 Claude Code / VSCode 插件在本站显示 **0% 缓存命中**，无法估算上下文预算，也不会自动压缩历史。\n\n现已实现**前缀匹配缓存模拟**：代理会比对会话历史的前缀，估算并返回缓存读取 / 写入 token 数。Claude Code 现在能正常显示缓存命中状态，并在上下文超限时自动触发压缩。"
    },
    {
        "id": 6,
        "publishDate": "2026-06-27",
        "type": "info",
        "content": "### 🛡️ Claude Code 系统提示词适配\n\nClaude Code 自带的系统提示词含有模拟 HTTP 头和高风险安全术语，会被国内合规系统误判拦截（连发\"你好\"都报敏感）。\n\n现已做**定向清洗**：剥离模拟 HTTP 头、替换品牌伪装短语、移除高风险安全条款段落。Claude Code 现可 100% 正常使用，不再误触发敏感拦截，同时保留标准编码指引。"
    }
]


def main():
    if not os.path.exists(DB_PATH):
        print(f"Error: {DB_PATH} 不存在")
        raise SystemExit(1)
    conn = sqlite3.connect(DB_PATH)
    try:
        val = json.dumps(announcements, ensure_ascii=False)
        conn.execute("INSERT OR REPLACE INTO options (key, value) VALUES (?, ?)",
                     ("console_setting.announcements", val))
        conn.commit()
        print(f"[OK] console_setting.announcements <- {len(announcements)} 条, {len(val)} 字节")
        row = conn.execute("SELECT value FROM options WHERE key='console_setting.announcements'").fetchone()
        obj = json.loads(row[0])
        print(f"\n== 回读校验：{len(obj)} 条 ==")
        for a in obj:
            print(f"\n[id={a['id']} type={a['type']} date={a['publishDate']}]")
            print(a['content'])
    finally:
        conn.close()


if __name__ == "__main__":
    main()
