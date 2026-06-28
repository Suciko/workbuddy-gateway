# -*- coding: utf-8 -*-
"""
一键整合：把一个 ck_ 开头的 CodeBuddy bearer token 写进 one-api.db 的 channels 表。

用法：
    python upsert_channel.py <key> [name_override]

逻辑：
- 按 key 前 8 位（ck_xxxxx）查现有渠道，完整 key 命中则只更新 base_url/status，不新建。
- 否则新建渠道：type=1、name=Tencent-CodeBuddy-N（N 自动顺延）、base_url=http://127.0.0.1:8000、
  models=9 个模型、group=default、status=1、priority=0/weight=1（优先级交给 get_credits.py 重算）。
- 同时往 abilities 表补 9 行模型能力（new-api 渠道生效靠这张表）。

输出：单行 JSON，形如 {"ok": true, "action": "created|updated", "channel_id": N, "name": "..."}
"""
import sqlite3
import json
import sys
import os
import re
import time

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'one-api.db')
BASE_URL = 'http://127.0.0.1:8000'
MODELS = 'hy3-preview,glm-5.2,glm-5.1,glm-5v-turbo,minimax-m3,kimi-k2.7-code,kimi-k2.6,deepseek-v4-flash,deepseek-v4-pro'


def upsert(key, name_override=''):
    if not key or not key.startswith('ck_'):
        return {"ok": False, "error": "key 必须以 ck_ 开头"}

    now = int(time.time())

    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # 1. 优先按照指定的渠道名称进行覆盖更新（如果存在该名称的渠道，直接更新其 Key 和状态，防止产生重复渠道）
        if name_override:
            name_match = c.execute("SELECT id FROM channels WHERE name = ?", (name_override,)).fetchone()
            if name_match:
                cid = name_match[0]
                c.execute("UPDATE channels SET key=?, base_url=?, status=1 WHERE id=?", (key, BASE_URL, cid))
                # 补齐 abilities 表能力支持
                for m in MODELS.split(','):
                    c.execute(
                        'INSERT OR IGNORE INTO abilities ("group", model, channel_id, '
                        'enabled, priority, weight) VALUES (\'default\', ?, ?, 1, 0, 1)',
                        (m, cid))
                conn.commit()
                conn.close()
                return {"ok": True, "action": "updated", "channel_id": cid, "name": name_override}

        # 2. 如果没有指定名称，或者该名称渠道不存在，则查 key 精确匹配防止完全重复
        key_prefix = key[:8]
        rows = c.execute("SELECT id, name, key FROM channels WHERE key LIKE ?",
                         (key_prefix + '%',)).fetchall()
        exact = [r for r in rows if r[2] == key]

        if exact:
            cid, cname, _ = exact[0]
            c.execute("UPDATE channels SET base_url=?, status=1 WHERE id=?", (BASE_URL, cid))
            conn.commit()
            conn.close()
            return {"ok": True, "action": "updated", "channel_id": cid,
                    "name": cname, "duplicated": True}

        # 新建：name 自动顺延（现有渠道叫 Anthropic-CodeBuddy-N）
        name_rows = c.execute(
            "SELECT name FROM channels WHERE name LIKE 'Tencent-CodeBuddy-%'").fetchall()
        max_n = 0
        for r in name_rows:
            m = re.search(r'Tencent-CodeBuddy-(\d+)', r[0] or '')
            if m:
                max_n = max(max_n, int(m.group(1)))
        name = name_override or 'Tencent-CodeBuddy-%d' % (max_n + 1)

        c.execute(
            'INSERT INTO channels (type, key, status, name, weight, created_time, '
            'base_url, models, "group", priority, auto_ban) '
            'VALUES (1, ?, 1, ?, 1, ?, ?, ?, \'default\', 0, 1)',
            (key, name, now, BASE_URL, MODELS))
        cid = c.lastrowid

        for m in MODELS.split(','):
            c.execute(
                'INSERT OR IGNORE INTO abilities ("group", model, channel_id, '
                'enabled, priority, weight) VALUES (\'default\', ?, ?, 1, 0, 1)',
                (m, cid))

        conn.commit()
        conn.close()
        return {"ok": True, "action": "created", "channel_id": cid, "name": name}
    except Exception as e:
        try:
            conn.close()
        except Exception:
            pass
        return {"ok": False, "error": str(e)}


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(json.dumps({"ok": False, "error": "缺少参数：key"}, ensure_ascii=False))
        sys.exit(1)
    key = sys.argv[1].strip()
    name_override = sys.argv[2].strip() if len(sys.argv) > 2 else ''
    print(json.dumps(upsert(key, name_override), ensure_ascii=False))
