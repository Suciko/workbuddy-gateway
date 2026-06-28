"""
只更新云端 NewAPI 的系统公告（console_setting.announcements）。
不动 api_info / faq（上一轮已改好，保留）。
不动 Footer（inject.js 侧边栏依赖）。

每条公告独立成元素，不合并 —— 用户要求"一条一条来"。
内容来自 .agents/wiki/LocalProxy.md 更新日志，面向好友用户措辞。
"""
import sqlite3
import json
import os

DB_PATH = os.environ.get('ONE_API_DB', 'one-api.db')

announcements = [
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
        # 回读校验
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
