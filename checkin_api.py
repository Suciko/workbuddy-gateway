# -*- coding: utf-8 -*-
"""
无感 API 打卡（Headless Check-in）—— 纯 HTTP 实现。

逆向来源：WorkBuddy 客户端 app.asar 反编译（main/index.js 的 authService）。
协议：
  - 查询签到状态: POST /v2/billing/meter/punchcard-activity-status  (body {})
  - 执行每日签到: POST /v2/billing/meter/daily-punchcard            (body {})
鉴权头（buildHeaders(session) 还原）:
  Authorization: Bearer <accessToken>
  X-User-Id: <account.uid>
  Content-Type: application/json
  Accept: application/json
凭证来源: accounts/account_N/workbuddy-desktop.info 中的 auth.accessToken + account.uid
Token 续期: POST /v2/auth/token/refresh (头 X-Refresh-Token + X-Auth-Refresh-Source: plugin)

用法:
  python checkin_api.py status              # 仅查询所有账号签到状态（只读）
  python checkin_api.py run                 # 对所有账号执行每日签到（领取）
  python checkin_api.py status account_1    # 仅查询指定账号
  python checkin_api.py run account_1       # 仅对指定账号签到
"""
import os
import sys
import json
import time
import sqlite3
import requests
from datetime import datetime

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# ==========================================
# 路径常量
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ACCOUNTS_DIR = os.path.join(BASE_DIR, "accounts")
TENCENT_ENDPOINT = "https://copilot.anthropic.com"
STATUS_URL = f"{TENCENT_ENDPOINT}/v2/billing/meter/punchcard-activity-status"
CLAIM_URL = f"{TENCENT_ENDPOINT}/v2/billing/meter/daily-punchcard"
REFRESH_URL = f"{TENCENT_ENDPOINT}/v2/auth/token/refresh"
DB_PATH = os.path.join(BASE_DIR, "one-api.db")
HISTORY_FILE = os.path.join(BASE_DIR, "logs", "punchcard_history.json")

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) WorkBuddy/1.0 Chrome/130.0.0.0 Safari/537.36"


def log(msg):
    """带时间戳的流式日志，供 local_proxy.js 逐行捕获。"""
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


# ==========================================
# 凭证加载
# ==========================================
def load_account(account_dir):
    """从 accounts/<name>/workbuddy-desktop.info 读取 accessToken 与 uid。

    returns: dict {name, uid, nickname, accessToken, refreshToken, info_path, info_raw}
    raises: FileNotFoundError / ValueError
    """
    info_path = os.path.join(account_dir, "workbuddy-desktop.info")
    if not os.path.isfile(info_path):
        raise FileNotFoundError(f"缺少凭证文件: {info_path}")
    with open(info_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    auth = data.get("auth", {}) or {}
    account = data.get("account", {}) or {}
    access_token = auth.get("accessToken")
    uid = account.get("uid")
    if not access_token or not uid:
        raise ValueError(f"凭证不完整（缺少 accessToken/uid）: {info_path}")
    return {
        "name": os.path.basename(account_dir),
        "uid": uid,
        "nickname": account.get("nickname", ""),
        "uin": account.get("uin", ""),
        "accessToken": access_token,
        "refreshToken": auth.get("refreshToken", ""),
        "domain": auth.get("domain", ""),
        "info_path": info_path,
        "info_raw": data,
    }


def list_accounts():
    """枚举 accounts/ 下所有合法账号目录（含 workbuddy-desktop.info）。"""
    if not os.path.isdir(ACCOUNTS_DIR):
        return []
    result = []
    for name in sorted(os.listdir(ACCOUNTS_DIR)):
        d = os.path.join(ACCOUNTS_DIR, name)
        if os.path.isdir(d) and os.path.isfile(os.path.join(d, "workbuddy-desktop.info")):
            result.append(name)
    return result


def select_accounts(arg=None):
    """根据命令行参数筛选账号列表。arg=None 表示全部。"""
    all_acc = list_accounts()
    if not arg:
        return all_acc
    if arg in all_acc:
        return [arg]
    log(f"⚠ 未找到账号目录 {arg}，现有账号: {all_acc}")
    return []


# ==========================================
# HTTP 头构造（对齐客户端 buildHeaders）
# ==========================================
def build_headers(acc):
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {acc['accessToken']}",
        "Content-Type": "application/json",
        "X-User-Id": acc["uid"],
        "User-Agent": UA,
    }
    if acc.get("domain"):
        headers["X-Domain"] = acc["domain"]
    return headers


# ==========================================
# Token 续期（可选，长期运行保活）
# ==========================================
def refresh_token(acc):
    """调用 /v2/auth/token/refresh 续期，成功则回写 workbuddy-desktop.info。"""
    if not acc.get("refreshToken"):
        log(f"  [{acc['name']}] 无 refreshToken，跳过续期")
        return False
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Refresh-Token": acc["refreshToken"],
        "X-Auth-Refresh-Source": "plugin",
        "X-User-Id": acc["uid"],
        "User-Agent": UA,
    }
    try:
        resp = requests.post(REFRESH_URL, json={}, headers=headers, timeout=15)
        if resp.status_code != 200:
            log(f"  [{acc['name']}] 续期 HTTP {resp.status_code}: {resp.text[:200]}")
            return False
        body = resp.json()
        new_data = (body.get("data") or {}).get("data") or body.get("data") or {}
        new_access = new_data.get("accessToken")
        new_refresh = new_data.get("refreshToken")
        if not new_access:
            log(f"  [{acc['name']}] 续期响应无 accessToken: {json.dumps(body, ensure_ascii=False)[:300]}")
            return False
        # 回写凭证文件
        acc["info_raw"]["auth"]["accessToken"] = new_access
        acc["info_raw"]["auth"]["lastRefreshTime"] = int(time.time() * 1000)
        if new_refresh:
            acc["info_raw"]["auth"]["refreshToken"] = new_refresh
        with open(acc["info_path"], "w", encoding="utf-8") as f:
            json.dump(acc["info_raw"], f, ensure_ascii=False, indent=2)
        acc["accessToken"] = new_access
        if new_refresh:
            acc["refreshToken"] = new_refresh
        log(f"  [{acc['name']}] ✅ Token 续期成功")
        return True
    except Exception as e:
        log(f"  [{acc['name']}] 续期异常: {e}")
        return False


# ==========================================
# 打卡状态查询（只读）
# ==========================================
def get_punchcard_status(acc):
    """查询签到状态。返回 (success: bool, data: dict|str)。"""
    headers = build_headers(acc)
    try:
        resp = requests.post(STATUS_URL, json={}, headers=headers, timeout=15)
        if resp.status_code != 200:
            return False, f"HTTP {resp.status_code}: {resp.text[:300]}"
        body = resp.json()
        if body.get("code") != 0:
            return False, f"code={body.get('code')} msg={body.get('msg')}"
        return True, body.get("data") or {}
    except Exception as e:
        return False, f"异常: {e}"


# ==========================================
# 执行每日签到（领取）
# ==========================================
def claim_daily_punchcard(acc):
    """执行每日签到领取。返回 (success: bool, data: dict|str)。"""
    headers = build_headers(acc)
    try:
        resp = requests.post(CLAIM_URL, json={}, headers=headers, timeout=15)
        body = {}
        try:
            body = resp.json()
        except Exception:
            pass
        if resp.status_code == 200 and body.get("code") == 0:
            return True, body.get("data") or {}
        return False, f"HTTP {resp.status_code} code={body.get('code')} msg={body.get('msg')}"
    except Exception as e:
        return False, f"异常: {e}"


# ==========================================
# 历史记录（与旧脚本兼容）
# ==========================================
def append_history(account_name, success, message, credits=None):
    """追加签到结果到 logs/punchcard_history.json（与 GUI 脚本同格式）。"""
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    history = []
    if os.path.isfile(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
            if not isinstance(history, list):
                history = []
        except Exception:
            history = []
    record = {
        "account": account_name,
        "success": success,
        "message": message,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "method": "api",
    }
    if credits is not None:
        record["credits"] = credits
    history.append(record)
    if len(history) > 500:
        history = history[-500:]
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


# ==========================================
# 主流程
# ==========================================
def do_status(accounts):
    """只读查询所有账号签到状态。"""
    log("=" * 56)
    log("📊 打卡状态查询（只读，不会领取）")
    log("=" * 56)
    if not accounts:
        log("⚠ 没有可用账号（accounts/ 目录为空或无凭证）")
        return []
    results = []
    for name in accounts:
        log(f"")
        log(f"▶ 账号 [{name}]")
        try:
            acc = load_account(os.path.join(ACCOUNTS_DIR, name))
            log(f"  uid={acc['uid']}  nickname={acc['nickname']}  uin={acc['uin']}")
            ok, data = get_punchcard_status(acc)
            if ok:
                log(f"  ✅ 状态查询成功: {json.dumps(data, ensure_ascii=False)}")
                results.append({"account": name, "success": True, "data": data})
            else:
                log(f"  ❌ 状态查询失败: {data}")
                # 若是 token 过期，尝试续期后重试一次
                if "401" in str(data) or "token" in str(data).lower() or "expired" in str(data).lower():
                    log(f"  ↻ 疑似 Token 失效，尝试续期后重试...")
                    if refresh_token(acc):
                        ok2, data2 = get_punchcard_status(acc)
                        if ok2:
                            log(f"  ✅ 续期后状态查询成功: {json.dumps(data2, ensure_ascii=False)}")
                            results.append({"account": name, "success": True, "data": data2})
                            continue
                results.append({"account": name, "success": False, "error": str(data)})
        except Exception as e:
            log(f"  ❌ 加载/查询异常: {e}")
            results.append({"account": name, "success": False, "error": str(e)})
    log("")
    log("=" * 56)
    ok_n = sum(1 for r in results if r["success"])
    log(f"完成: {ok_n}/{len(results)} 成功")
    log("=" * 56)
    return results


def do_run(accounts):
    """对所有账号执行每日签到（领取）。"""
    log("=" * 56)
    log("🎁 每日签到（API 领取）")
    log("=" * 56)
    if not accounts:
        log("⚠ 没有可用账号（accounts/ 目录为空或无凭证）")
        return []
    results = []
    for name in accounts:
        log("")
        log(f"▶ 账号 [{name}]")
        try:
            acc = load_account(os.path.join(ACCOUNTS_DIR, name))
            log(f"  uid={acc['uid']}  nickname={acc['nickname']}")
            # 先查询状态，判断今日是否已领
            ok, status = get_punchcard_status(acc)
            already_claimed = False
            if ok and isinstance(status, dict):
                # 客户端用 claimedToday / alreadyClaimed 等字段判断
                if status.get("claimedToday") or status.get("alreadyClaimed") or status.get("claimed") is True:
                    already_claimed = True
                    log(f"  ℹ 今日已领取，跳过（状态: {json.dumps(status, ensure_ascii=False)[:200]}）")
                    append_history(name, True, "今日已领取（跳过）")
                    results.append({"account": name, "success": True, "skipped": True, "status": status})
                    continue
                log(f"  状态: {json.dumps(status, ensure_ascii=False)[:200]}")
            elif not ok:
                log(f"  ⚠ 状态查询失败({status})，仍尝试签到")
            # 执行领取
            ok2, data = claim_daily_punchcard(acc)
            if ok2:
                credits = None
                if isinstance(data, dict):
                    credits = data.get("credits") or data.get("rewardCredits") or data.get("amount")
                log(f"  ✅ 打卡成功！{json.dumps(data, ensure_ascii=False)[:200]}")
                append_history(name, True, "API 打卡成功", credits=credits)
                results.append({"account": name, "success": True, "data": data, "credits": credits})
            else:
                log(f"  ❌ 打卡失败: {data}")
                # token 失效则续期重试
                if "401" in str(data) or "token" in str(data).lower() or "expired" in str(data).lower():
                    log(f"  ↻ 疑似 Token 失效，尝试续期后重试...")
                    if refresh_token(acc):
                        ok3, data3 = claim_daily_punchcard(acc)
                        if ok3:
                            credits = data3.get("credits") if isinstance(data3, dict) else None
                            log(f"  ✅ 续期后签到成功！{json.dumps(data3, ensure_ascii=False)[:200]}")
                            append_history(name, True, "API 打卡成功（续期后）", credits=credits)
                            results.append({"account": name, "success": True, "data": data3, "credits": credits})
                            continue
                append_history(name, False, f"API 打卡失败: {data}")
                results.append({"account": name, "success": False, "error": str(data)})
        except Exception as e:
            log(f"  ❌ 异常: {e}")
            append_history(name, False, f"异常: {e}")
            results.append({"account": name, "success": False, "error": str(e)})
    log("")
    log("=" * 56)
    ok_n = sum(1 for r in results if r["success"])
    log(f"完成: {ok_n}/{len(results)} 成功")
    log("=" * 56)
    return results


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return
    action = args[0].lower()
    target = args[1] if len(args) > 1 else None
    accounts = select_accounts(target)
    if not accounts:
        return
    if action in ("status", "check", "查询"):
        do_status(accounts)
    elif action in ("run", "claim", "签到", "领取"):
        do_run(accounts)
    else:
        print(f"未知动作: {action}")
        print(__doc__)


if __name__ == "__main__":
    main()
