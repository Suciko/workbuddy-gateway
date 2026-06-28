import sqlite3
import json
import os

def get_channels():
    db_path = 'one-api.db'
    if not os.path.exists(db_path):
        print(json.dumps({"error": "one-api.db not found"}))
        return

    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        # Query channels
        c.execute("SELECT id, name, type, key, base_url, status FROM channels")
        rows = c.fetchall()
        
        channels = []
        for r in rows:
            key = r[3]
            is_tencent = False
            if key and key.startswith('ck_'):
                is_tencent = True
            elif r[4] and ('8000' in r[4] or 'localhost:8000' in r[4] or '127.0.0.1:8000' in r[4]):
                is_tencent = True
                
            if is_tencent:
                key_masked = key
                if key and len(key) > 15:
                    key_masked = f"{key[:8]}...{key[-8:]}"
                channels.append({
                    "id": r[0],
                    "name": r[1],
                    "type": r[2],
                    "key_masked": key_masked,
                    "key": key,
                    "base_url": r[4],
                    "status": r[5]
                })
        conn.close()
        print(json.dumps(channels, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"error": str(e)}))

if __name__ == '__main__':
    get_channels()
