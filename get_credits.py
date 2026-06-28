# -*- coding: utf-8 -*-
import sqlite3
import json
import os
import sys
import requests
from datetime import datetime, timedelta

# Force output to utf-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def format_time(val):
    if not val:
        return ""
    if isinstance(val, (int, float)):
        try:
            # Check if ms or seconds
            if val > 1e11:
                val = val / 1000.0
            dt = datetime.fromtimestamp(val)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return str(val)
    return str(val)

def get_timestamp(val):
    if not val:
        return None
    if isinstance(val, (int, float)):
        if val > 1e11:
            return val / 1000.0
        return val
    if isinstance(val, str):
        try:
            dt = datetime.strptime(val, "%Y-%m-%d %H:%M:%S")
            return dt.timestamp()
        except Exception:
            return None
    return None

def extract_account_name(name):
    if not name:
        return ""
    if name.startswith("Tencent-CodeBuddy-"):
        suffix = name[len("Tencent-CodeBuddy-"):]
        if suffix.isdigit():
            name = "account_" + suffix
        else:
            name = suffix
    if name.startswith("synced_"):
        name = name[len("synced_"):]
    return name

def get_credits():
    db_path = 'one-api.db'
    sources = []

    # Scan active credential accounts on disk
    active_accounts = set()
    accounts_dir = 'accounts'
    if os.path.isdir(accounts_dir):
        for name in os.listdir(accounts_dir):
            if os.path.isdir(os.path.join(accounts_dir, name)):
                if os.path.exists(os.path.join(accounts_dir, name, 'workbuddy-desktop.info')):
                    active_accounts.add(extract_account_name(name))
    creds_dir = '.codebuddy_creds'
    if os.path.isdir(creds_dir):
        for name in os.listdir(creds_dir):
            # 只用 synced_ 凭证来过滤废弃的测试渠道，避免旧凭证干扰
            if name.endswith('.json') and name.startswith('synced_'):
                active_accounts.add(extract_account_name(name[:-5]))

    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("SELECT id, name, key, status FROM channels")
            rows = c.fetchall()
            conn.close()
            for channel_id, name, key, status in rows:
                if key and key.startswith('ck_') and status == 1:
                    # Filter out obsolete test accounts if we have active credentials
                    acc_name = extract_account_name(name)
                    if active_accounts and acc_name not in active_accounts:
                        continue
                    sources.append({
                        "id": channel_id,
                        "name": name,
                        "key": key,
                        "source": "channel"
                    })
        except Exception as e:
            print(json.dumps({"error": f"Failed to query database: {e}"}))
            return

    creds_dir = '.codebuddy_creds'
    if os.path.isdir(creds_dir):
        for name in sorted(os.listdir(creds_dir)):
            if not name.endswith('.json'):
                continue
            # 仅扫描 synced_ 前缀的凭证文件，与云端 web.py 的 accounts/credits
            # 过滤保持一致，避免旧的非 synced_ 凭证导致“账号数对不上”。
            if not name.startswith('synced_'):
                continue
            path = os.path.join(creds_dir, name)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                token = data.get('bearer_token') or data.get('access_token')
                if not token:
                    continue
                sources.append({
                    "id": f"cred:{name}",
                    "name": name[:-5],
                    "key": token,
                    "source": "credential"
                })
            except Exception:
                continue

    if not sources:
        print(json.dumps({"error": "No active ck_ channels or .codebuddy_creds tokens found"}, ensure_ascii=False))
        return

    now = datetime.now()
    future = now + timedelta(days=365 * 10)
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")
    future_str = future.strftime("%Y-%m-%d %H:%M:%S")

    payload = {
        "PageNumber": 1,
        "PageSize": 100,
        "ProductCode": "p_tcaca",
        "Status": [0, 3],
        "PackageEndTimeRangeBegin": now_str,
        "PackageEndTimeRangeEnd": future_str
    }

    results = []
    channel_expirations = {} # channel_id -> earliest_expire_timestamp

    # Commodity code definitions
    BASIC_CODES = [
        "TCACA_code_008_cfWoLwvjU4", # freeMon (基础体验包)
        "TCACA_code_001_PqouKr6QWV", # free
        "TCACA_code_002_AkiJS3ZHF5", # proMon
        "TCACA_code_005_maRGyrHhw1", # proMonPlus
        "TCACA_code_003_FAnt7lcmRT"  # proYear
    ]
    GIFT_CODES = [
        "TCACA_code_006_DbXS0lrypC", # gift
        "TCACA_code_007_nzdH5h4Nl0"  # activity (活动赠送包)
    ]
    EXTRA_CODES = [
        "TCACA_code_009_0XmEQc2xOf"  # extra (加量包)
    ]

    for source in sources:
        channel_id = source["id"]
        name = source["name"]
        key = source["key"]
        try:
            # If domestic JWT is prefixed with ck_ for gateway compliance, strip it before forwarding
            request_key = key
            if request_key.startswith('ck_') and request_key[3:].startswith('eyJ'):
                request_key = request_key[3:]

            headers = {
                "Authorization": f"Bearer {request_key}",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            resp = requests.post(
                "https://copilot.tencent.com/v2/billing/meter/get-user-resource",
                json=payload,
                headers=headers,
                timeout=10
            )

            if resp.status_code != 200:
                results.append({
                    "channel_id": channel_id,
                    "channel_name": name,
                    "source": source.get("source"),
                    "error": f"Tencent API returned status code {resp.status_code}"
                })
                continue

            resp_json = resp.json()
            if resp_json.get("code") != 0:
                results.append({
                    "channel_id": channel_id,
                    "channel_name": name,
                    "source": source.get("source"),
                    "error": resp_json.get("msg", "Unknown error")
                })
                continue

            data_resp = resp_json.get("data", {}).get("Response", {}).get("Data", {})
            accounts = data_resp.get("Accounts") or []

            # Group containers
            groups = {
                "basic": {"total": 0.0, "left": 0.0, "used": 0.0, "refresh_time": ""},
                "gift": {"total": 0.0, "left": 0.0, "used": 0.0, "packages": []},
                "extra": {"total": 0.0, "left": 0.0, "used": 0.0, "packages": []}
            }

            expiring_timestamps = []

            for acc in accounts:
                pkg_code = acc.get("PackageCode", "")
                pkg_name = acc.get("PackageName", "")
                
                # Retrieve capacity details
                c_total = float(acc.get("CycleCapacitySizePrecise") or acc.get("CapacitySizePrecise") or 0)
                c_left = float(acc.get("CycleCapacityRemainPrecise") or acc.get("CapacityRemainPrecise") or 0)
                c_used = float(acc.get("CycleCapacityUsedPrecise") or acc.get("CapacityUsedPrecise") or 0)

                cycle_end = acc.get("CycleEndTime") or ""
                deduct_end = acc.get("DeductionEndTime") or ""

                # Determine group
                group_type = "basic"
                is_expiring_pkg = False
                if pkg_code in BASIC_CODES:
                    group_type = "basic"
                elif pkg_code in GIFT_CODES:
                    group_type = "gift"
                    is_expiring_pkg = True
                elif pkg_code in EXTRA_CODES:
                    group_type = "extra"
                    is_expiring_pkg = True
                else:
                    # Fallback classification by name search
                    lower_name = pkg_name.lower()
                    if "赠送" in lower_name or "运营" in lower_name or "gift" in lower_name or "裂变" in lower_name:
                        group_type = "gift"
                        is_expiring_pkg = True
                    elif "加量" in lower_name or "extra" in lower_name or "addon" in lower_name:
                        group_type = "extra"
                        is_expiring_pkg = True
                    else:
                        group_type = "basic"

                # Skip exhausted or expired non-basic packages (e.g. used-up activity/extra packs)
                if group_type != "basic" and c_left <= 0.01:
                    continue

                # Update group aggregates
                groups[group_type]["total"] += c_total
                groups[group_type]["left"] += c_left
                groups[group_type]["used"] += c_used

                # Format times
                expire_time_str = format_time(deduct_end) if deduct_end else cycle_end
                
                if group_type == "basic":
                    # For basic packages, the next refresh time is the cycle end
                    if cycle_end and (not groups["basic"]["refresh_time"] or cycle_end < groups["basic"]["refresh_time"]):
                        groups["basic"]["refresh_time"] = cycle_end
                else:
                    groups[group_type]["packages"].append({
                        "name": pkg_name,
                        "total": c_total,
                        "left": c_left,
                        "used": c_used,
                        "expire_time": expire_time_str
                    })

                # Expiration tracking for priority sorting
                if c_left > 0.05:
                    if group_type == "basic":
                        target_end = cycle_end
                    else:
                        target_end = deduct_end if deduct_end else cycle_end
                    ts = get_timestamp(target_end)
                    if ts:
                        expiring_timestamps.append(ts)

            # Record earliest expiration for this channel
            if expiring_timestamps:
                channel_expirations[channel_id] = min(expiring_timestamps)

            # Clean basic refresh time if it's empty
            if not groups["basic"]["refresh_time"] and len(accounts) > 0:
                groups["basic"]["refresh_time"] = "无"

            # Sort packages in gift and extra by expire time
            for gt in ["gift", "extra"]:
                groups[gt]["packages"].sort(key=lambda x: x["expire_time"])

            results.append({
                "channel_id": channel_id,
                "channel_name": name,
                "source": source.get("source"),
                "key_masked": f"{key[:8]}...{key[-8:]}" if len(key) > 15 else key,
                "groups": groups
            })

        except Exception as ex:
            results.append({
                "channel_id": channel_id,
                "channel_name": name,
                "source": source.get("source"),
                "error": str(ex)
            })

    # Update priorities in database automatically to prioritize channels with earliest expiring packages
    try:
        # Channels with expiring packages sorted by expiration time ascending (earlier first)
        expiring_channels = sorted(channel_expirations.items(), key=lambda x: x[1])

        priority_updates = {}
        for i, (chan_id, _) in enumerate(expiring_channels):
            # Expiring packages get highest priority (100, 99, 98...)
            priority_updates[chan_id] = 100 - i

        # Non-expiring active Tencent channels get priority 0 (fallback)
        for r in rows:
            chan_id, _, key, status = r
            if key and key.startswith('ck_') and status == 1:
                if chan_id not in priority_updates:
                    priority_updates[chan_id] = 0

        if priority_updates:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            # 缓存每个渠道的 models / group，用于同步 abilities 表
            channel_models = {}
            channel_group = {}
            for r in rows:
                chan_id_r, _, key, status = r
                if key and key.startswith('ck_') and status == 1 and chan_id_r in priority_updates:
                    # 读取该渠道的 models 和 group 字段
                    c.execute("SELECT models, \"group\" FROM channels WHERE id = ?", (chan_id_r,))
                    row_m = c.fetchone()
                    if row_m:
                        channel_models[chan_id_r] = row_m[0]
                        channel_group[chan_id_r] = row_m[1] or "default"

            for chan_id, priority in priority_updates.items():
                # Also set weight to force traffic towards higher priority channels
                # Weight calculation: earliest expiring = 100, each tier drops by 15
                # Non-expiring channels get weight 1 (minimal traffic)
                weight = max(100 - (100 - priority) * 15, 1) if priority > 0 else 1
                c.execute("UPDATE channels SET priority = ?, weight = ? WHERE id = ?",
                          (priority, weight, chan_id))

                # 同步更新 abilities 表 (new-api 实际从这里读取路由决策)
                # 没有 abilities 记录的 channel 永远不会被选中！
                models_str = channel_models.get(chan_id, "")
                group = channel_group.get(chan_id, "default")
                if models_str:
                    models = [m.strip() for m in models_str.split(',') if m.strip()]
                    for model in models:
                        c.execute(
                            "INSERT INTO abilities (\"group\", model, channel_id, enabled, priority, weight) "
                            "VALUES (?, ?, ?, 1, ?, ?) "
                            "ON CONFLICT(\"group\", model, channel_id) DO UPDATE SET "
                            "enabled=1, priority=excluded.priority, weight=excluded.weight",
                            (group, model, chan_id, priority, weight)
                        )
            conn.commit()
            conn.close()
    except Exception as db_err:
        sys.stderr.write(f"[DB Update Error] {str(db_err)}\n")

    # Add priority info to each result for dashboard display
    for r in results:
        cid = r.get("channel_id")
        if cid and cid in priority_updates:
            r["priority"] = priority_updates[cid]
        else:
            r["priority"] = 0

    # Deduplicate results based on normalized account name to avoid redundant cards (e.g. channel and credential source)
    # Sort results first: success first (no error), credential source first
    def get_sort_key(res_item):
        has_error = 1 if res_item.get("error") else 0
        is_credential = 0 if res_item.get("source") == "credential" else 1
        return (has_error, is_credential)

    results.sort(key=get_sort_key)

    unique_results = []
    seen_accounts = set()
    for r in results:
        acc_name = extract_account_name(r.get("channel_name", ""))
        if acc_name:
            if acc_name in seen_accounts:
                continue
            seen_accounts.add(acc_name)
        unique_results.append(r)
    results = unique_results

    print(json.dumps(results, ensure_ascii=False))

if __name__ == '__main__':
    get_credits()
