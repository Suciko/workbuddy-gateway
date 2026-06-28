import sqlite3
import json
import os
import sys

# Ensure UTF-8 stdout encoding for Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def get_stats():
    # Use absolute or relative path to database
    db_path = 'one-api.db'
    if not os.path.exists(db_path):
        print(json.dumps({"error": "one-api.db not found"}))
        return

    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()

        # 1. Global summary (successful calls where type = 2)
        c.execute("""
            SELECT 
                COUNT(*),
                COALESCE(SUM(prompt_tokens), 0),
                COALESCE(SUM(completion_tokens), 0),
                COALESCE(SUM(quota), 0),
                COALESCE(AVG(use_time), 0),
                COALESCE(SUM(CAST(json_extract(other, '$.cache_tokens') AS INT)), 0)
            FROM logs
            WHERE type = 2
        """)
        glob = c.fetchone()
        
        # 2. By model breakdown
        c.execute("""
            SELECT 
                model_name,
                COUNT(*),
                COALESCE(SUM(prompt_tokens), 0),
                COALESCE(SUM(completion_tokens), 0),
                COALESCE(SUM(quota), 0),
                COALESCE(SUM(CAST(json_extract(other, '$.cache_tokens') AS INT)), 0)
            FROM logs
            WHERE type = 2
            GROUP BY model_name
            ORDER BY COUNT(*) DESC
        """)
        models_raw = c.fetchall()
        by_model = {}
        for r in models_raw:
            by_model[r[0]] = {
                "requests": r[1],
                "prompt_tokens": r[2],
                "completion_tokens": r[3],
                "quota": r[4],
                "cache_tokens": r[5]
            }

        # 3. By user breakdown
        c.execute("""
            SELECT 
                u.id, 
                u.username, 
                u.display_name, 
                u.quota, 
                u.used_quota, 
                u.request_count,
                COALESCE(SUM(l.prompt_tokens), 0) as log_prompt_tokens,
                COALESCE(SUM(l.completion_tokens), 0) as log_completion_tokens,
                COALESCE(SUM(l.quota), 0) as log_quota,
                COUNT(l.id) as log_requests,
                COALESCE(AVG(l.use_time), 0) as avg_latency,
                COALESCE(SUM(CAST(json_extract(l.other, '$.cache_tokens') AS INT)), 0) as log_cache_tokens
            FROM users u
            LEFT JOIN logs l ON u.id = l.user_id AND l.type = 2
            GROUP BY u.id
            ORDER BY u.used_quota DESC
        """)
        users_raw = c.fetchall()
        users = []
        for r in users_raw:
            users.append({
                "id": r[0],
                "username": r[1],
                "display_name": r[2] or r[1],
                "remaining_quota": r[3],
                "used_quota": r[4],
                "request_count": r[5],
                "prompt_tokens": r[6],
                "completion_tokens": r[7],
                "total_tokens": r[6] + r[7] + r[11],
                "quota_consumed": r[8],
                "log_requests": r[9],
                "avg_latency": round(r[10], 2),
                "cache_tokens": r[11]
            })

        result = {
            "global": {
                "total_requests": glob[0],
                "prompt_tokens": glob[1],
                "completion_tokens": glob[2],
                "total_tokens": glob[1] + glob[2] + glob[5],
                "total_quota": glob[3],
                "avg_response_ms": int(glob[4] * 1000),
                "cache_tokens": glob[5]
            },
            "by_model": by_model,
            "users": users
        }
        print(json.dumps(result, ensure_ascii=False))
        conn.close()
    except Exception as e:
        print(json.dumps({"error": str(e)}))

if __name__ == '__main__':
    get_stats()
