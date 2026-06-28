import ctypes
import time
import os
import sys
import shutil
import subprocess
import json
from datetime import datetime, timezone
import cv2
import numpy as np
from PIL import ImageGrab

# 强制 Python 标准输出为 UTF-8 编码，防止 Windows 控制台下出现中文乱码
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# 初始化 DPI 适配，防止 Windows 缩放导致截图与窗口坐标不匹配
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2) # PROCESS_PER_MONITOR_DPI_AWARE
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# ==========================================
# 1. 路径与核心参数配置
# ==========================================
USER_PROFILE = os.path.expanduser("~")
WORKBUDDY_DATA_DIR = os.path.join(USER_PROFILE, ".workbuddy")
ACCOUNTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "accounts")
APPDATA_AUTH_INFO = os.path.join(os.environ.get("LOCALAPPDATA", ""), "CodeBuddyExtension", "Data", "Public", "auth", "workbuddy-desktop.info")

# 微信会话关键凭据文件（只交换这几个小文件夹/文件，无需备份数百MB的插件包）
SESSION_ITEMS = ["local_storage", "sessions", "workbuddy.db", "workbuddy.db-shm", "workbuddy.db-wal", "user-state.json", "settings.json"]

# 查找 WorkBuddy.exe 路径列表
WORKBUDDY_EXE_PATHS = [
    "D:\\Program Files\\WorkBuddy\\WorkBuddy.exe",  # 优先检测 D 盘安装路径
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "WorkBuddy", "WorkBuddy.exe"),
    os.path.join(os.environ.get("APPDATA", ""), "Tencent", "WorkBuddy", "WorkBuddy.exe"),
    "C:\\Program Files\\WorkBuddy\\WorkBuddy.exe",
]

# Windows API 鼠标及键盘控制定义
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
SWP_SHOWWINDOW = 0x0040
SW_RESTORE = 9
VK_ESCAPE = 0x1B
KEYEVENTF_KEYUP = 0x0002
user32 = ctypes.windll.user32

# 签到历史日志文件路径
CHECKIN_HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "checkin_history.json")

def log_checkin_result(account_name, success, message=""):
    """将签到结果追加写入 JSON 历史记录文件"""
    log_dir = os.path.dirname(CHECKIN_HISTORY_FILE)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    history = []
    if os.path.exists(CHECKIN_HISTORY_FILE):
        try:
            with open(CHECKIN_HISTORY_FILE, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except (json.JSONDecodeError, IOError):
            history = []

    record = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "account": account_name,
        "success": success,
        "message": message or ("签到成功" if success else "签到失败")
    }
    history.append(record)

    # 只保留最近 500 条记录，防止文件无限增长
    if len(history) > 500:
        history = history[-500:]

    try:
        with open(CHECKIN_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except IOError as e:
        print(f"[Warning] 无法写入签到历史日志: {e}")

# ==========================================
# 2. 辅助工具函数
# ==========================================
def kill_workbuddy():
    """强制关闭 WorkBuddy 客户端进程并确保其窗口彻底消失"""
    print("[Process] 正在强制退出 WorkBuddy 进程...")
    taskkill_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 'taskkill.exe')
    
    # 循环执行以防单次执行因权限或系统缓存延迟而没杀干净
    for attempt in range(5):
        if os.path.exists(taskkill_path):
            os.system(f'"{taskkill_path}" /f /im WorkBuddy.exe >nul 2>&1')
        else:
            os.system("taskkill /f /im WorkBuddy.exe >nul 2>&1")
        
        time.sleep(0.6)
        # 检查是否还有残留窗口句柄
        hwnd = find_workbuddy_window()
        if not hwnd:
            print("[Process] WorkBuddy 进程及窗口句柄已彻底杀干净。")
            break
        print(f"[Process] 残留句柄 {hwnd} 依然存在，等待系统注销中 (尝试 {attempt+1}/5)...")
    else:
        print("[Process] 警告: 残留句柄未能完全注销，可能影响后续拉起。")

def get_workbuddy_path():
    """寻找本地 WorkBuddy 可执行文件"""
    for path in WORKBUDDY_EXE_PATHS:
        if os.path.exists(path):
            return path
    return None

def get_process_name_by_pid(pid):
    """根据进程 PID 获取进程的可执行文件名"""
    import ctypes.wintypes
    kernel32 = ctypes.windll.kernel32
    h_process = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
    if h_process:
        buf = ctypes.create_unicode_buffer(260)
        size = ctypes.wintypes.DWORD(260)
        if kernel32.QueryFullProcessImageNameW(h_process, 0, buf, ctypes.byref(size)):
            name = os.path.basename(buf.value)
            kernel32.CloseHandle(h_process)
            return name
        kernel32.CloseHandle(h_process)
    return ""

def find_workbuddy_window():
    """寻找可见的 WorkBuddy 窗口句柄，并确保其属于 WorkBuddy.exe 进程"""
    import ctypes.wintypes
    for title in ["WorkBuddy", "Tencent WorkBuddy", "腾讯 WorkBuddy"]:
        hwnd = user32.FindWindowW(None, title)
        if hwnd and user32.IsWindowVisible(hwnd):
            rect = RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(rect))
            # 宽和高必须大于 100 像素，防止捕获到托盘隐藏图标或残留的无效缩略窗口
            if rect.right - rect.left > 100 and rect.bottom - rect.top > 100:
                # 校验进程名称，防止误匹配同名的 Windows 资源管理器文件夹或浏览器窗口
                pid = ctypes.wintypes.DWORD()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                pname = get_process_name_by_pid(pid.value)
                if pname.lower() == "workbuddy.exe":
                    return hwnd
                else:
                    print(f"[UI] 发现同名窗口 {title!r} (句柄: {hwnd})，但其所属进程为 {pname!r}，判定为误匹配，跳过。")
    return 0

def click(x, y):
    """点击窗口指定坐标"""
    user32.SetCursorPos(int(x), int(y))
    time.sleep(0.2)
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.1)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

def press_esc():
    """向当前活动窗口发送 Escape 键以关闭可能打开的菜单/弹窗"""
    print("[UI] 发送 Escape 键清理 UI 状态 (关闭可能已打开的上下文菜单或面板)...")
    user32.keybd_event(VK_ESCAPE, 0, 0, 0)
    time.sleep(0.05)
    user32.keybd_event(VK_ESCAPE, 0, KEYEVENTF_KEYUP, 0)

class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long),
                ("top", ctypes.c_long),
                ("right", ctypes.c_long),
                ("bottom", ctypes.c_long)]

def grab_window_win32(hwnd):
    """
    通过 Windows API 直接截取特定窗口的图像，避开多显示器负坐标等 BitBlt 限制，并且支持遮挡窗口的截图。
    """
    import win32gui, win32ui, win32con
    from PIL import Image
    
    rect = RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    width = rect.right - rect.left
    height = rect.bottom - rect.top
    
    hwindc = win32gui.GetWindowDC(hwnd)
    hdcMem = win32gui.CreateCompatibleDC(hwindc)
    
    memdc = win32ui.CreateDCFromHandle(hdcMem)
    bmp = win32ui.CreateBitmap()
    bmp.CreateCompatibleBitmap(memdc, width, height)
    memdc.SelectObject(bmp)
    
    # 优先使用 PrintWindow(hwnd, hdcMem, 2) 截取渲染缓冲（支持被遮挡窗口以及硬件加速 Electron）
    success = False
    try:
        success = win32gui.PrintWindow(hwnd, hdcMem, 2)
    except Exception as pe:
        print(f"[UI] PrintWindow 尝试失败: {pe}，将使用 BitBlt 兜底...")
        
    if not success:
        # 使用原生 win32gui.BitBlt 兜底，局部坐标 (0,0) 拷贝，避开 win32ui 对 GetWindowDC 进行 DeleteDC 带来的 GDI 报错
        try:
            win32gui.BitBlt(hdcMem, 0, 0, width, height, hwindc, 0, 0, win32con.SRCCOPY)
            success = True
        except Exception as be:
            print(f"[UI] BitBlt 兜底也失败: {be}")
            
    if not success:
        raise Exception("PrintWindow and BitBlt both failed")
        
    bmpinfo = bmp.GetInfo()
    bmpstr = bmp.GetBitmapBits(True)
    
    im = Image.frombuffer(
        'RGB',
        (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
        bmpstr, 'raw', 'BGRX', 0, 1
    )
    
    # 释放与清理所有 GDI 资源，防止句柄泄露
    memdc.DeleteDC()
    win32gui.DeleteObject(bmp.GetHandle())
    win32gui.ReleaseDC(hwnd, hwindc)
    
    return im

def robust_screenshot(hwnd, bbox=None):
    try:
        return grab_window_win32(hwnd)
    except Exception as e:
        print(f"[UI] win32 窗口截图失败: {e}，尝试使用 ImageGrab 兜底...")
        return ImageGrab.grab(bbox=bbox)

def find_claim_button_by_template(hwnd, state="closed"):
    """
    通过多尺度模板匹配寻找“立即领取”按钮的绝对屏幕坐标。
    如果匹配成功，返回 (screen_x, screen_y)；否则返回 None。
    """
    template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "template_claim.png")
    if not os.path.exists(template_path):
        print("[Template] 警告: 未找到 template_claim.png，跳过图像识别。")
        return None

    try:
        # 获取窗口位置
        rect = RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        
        # 校验窗口位置和尺寸是否合法，防止坐标为负（如最小化状态）导致截图失败
        width = rect.right - rect.left
        height = rect.bottom - rect.top
        if width <= 100 or height <= 100 or rect.left < -1000 or rect.top < -1000:
            print(f"[Template] 窗口坐标或尺寸无效: ({rect.left}, {rect.top}, {rect.right}, {rect.bottom})，跳过屏幕匹配。")
            return None
            
        # 截取整个窗口区域图像
        bbox = (rect.left, rect.top, rect.right, rect.bottom)
        screenshot = robust_screenshot(hwnd, bbox=bbox)
        
        # 转换为 OpenCV 格式 (RGBA/RGB -> BGR)
        img_np = np.array(screenshot)
        if len(img_np.shape) == 3:
            if img_np.shape[2] == 4:
                img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGBA2BGR)
            else:
                img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        else:
            print("[Template] 截图通道格式异常。")
            return None
            
        # 裁剪 ROI 限制识别范围，防止其他区域干扰（如右侧和下方的其他界面按钮）
        h_img, w_img = img_bgr.shape[0], img_bgr.shape[1]
        if state == "closed":
            # 闭合状态：只搜寻左下角绿色卡片区域 (x ∈ [0, 30%], y ∈ [60%, 100%])
            y_start, y_end = int(h_img * 0.6), h_img
            x_start, x_end = 0, int(w_img * 0.3)
        else:
            # 展开状态：只搜寻左侧个人面板中间区域 (x ∈ [0, 30%], y ∈ [15%, 70%])
            y_start, y_end = int(h_img * 0.15), int(h_img * 0.7)
            x_start, x_end = 0, int(w_img * 0.3)
            
        roi = img_bgr[y_start:y_end, x_start:x_end]
            
        # 读取模板 (使用 numpy 以支持中文/Unicode 路径)
        template = cv2.imdecode(np.fromfile(template_path, dtype=np.uint8), -1)
        if template is None:
            print("[Template] 读取 template_claim.png 失败。")
            return None
            
        if template.shape[2] == 4:
            template_bgr = cv2.cvtColor(template, cv2.COLOR_BGRA2BGR)
        else:
            template_bgr = template.copy()
            
        # 多尺度模板匹配 (适配 100%, 125%, 150% 等各种系统分辨率和 DPI 缩放)
        best_max_val = -1
        best_loc = None
        best_scale = 1.0
        
        # 匹配比例：从 0.6 到 1.5 步长为 0.05
        scales = [x / 100.0 for x in range(60, 155, 5)]
        
        for scale in scales:
            w = int(template_bgr.shape[1] * scale)
            h = int(template_bgr.shape[0] * scale)
            if w <= 0 or h <= 0:
                continue
            if roi.shape[0] < h or roi.shape[1] < w:
                continue
                
            resized_template = cv2.resize(template_bgr, (w, h), interpolation=cv2.INTER_AREA)
            res = cv2.matchTemplate(roi, resized_template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(res)
            
            if max_val > best_max_val:
                best_max_val = max_val
                best_loc = max_loc
                best_scale = scale
                
        print(f"[Template] {state}状态最佳匹配比例: {best_scale}, 最高置信度: {best_max_val:.4f}")
        # 置信度阈值设为 0.75 以适配边缘像素差异
        if best_max_val >= 0.75:
            h = int(template_bgr.shape[0] * best_scale)
            w = int(template_bgr.shape[1] * best_scale)
            relative_x = x_start + best_loc[0] + w // 2
            relative_y = y_start + best_loc[1] + h // 2
            screen_x = rect.left + relative_x
            screen_y = rect.top + relative_y
            print(f"[Template] 成功识别按钮，相对窗口位置: ({relative_x}, {relative_y})，屏幕绝对坐标: ({screen_x}, {screen_y})")
            return (screen_x, screen_y)
            
    except Exception as e:
        print(f"[Template] 模板匹配执行异常: {e}")
        
    return None

def swap_session(account_folder, to_app=True):
    """
    会话交换函数。
    to_app=True  表示将备份文件夹中的凭据覆盖到运行目录 (还原登录态)
    to_app=False 表示将当前运行目录中的凭据备份到备份文件夹 (保存登录态)
    """
    if not to_app:
        # 备份时进行安全校验：如果备份目标文件夹已存在 workbuddy-desktop.info，且里面有 uid，
        # 则当前运行的 APPDATA_AUTH_INFO 中的 uid 必须与之匹配，否则拒绝回存，防止因切换失败而覆盖错账号。
        target_auth = os.path.join(account_folder, "workbuddy-desktop.info")
        if os.path.exists(target_auth) and os.path.exists(APPDATA_AUTH_INFO):
            try:
                with open(target_auth, 'r', encoding='utf-8') as f:
                    target_data = json.load(f)
                with open(APPDATA_AUTH_INFO, 'r', encoding='utf-8') as f:
                    current_data = json.load(f)
                
                target_uid = target_data.get("account", {}).get("uid")
                current_uid = current_data.get("account", {}).get("uid")
                
                if target_uid and current_uid and target_uid != current_uid:
                    target_name = target_data.get("account", {}).get("nickname", "未知")
                    current_name = current_data.get("account", {}).get("nickname", "未知")
                    print(f"[Backup] [Warning] 拒绝备份！当前运行账号是【{current_name}】(UID: {current_uid})，但备份目标是【{target_name}】(UID: {target_uid})。已跳过回存，防止覆盖破坏账号！")
                    return False
            except Exception as e:
                print(f"[Backup] [Warning] 备份安全校验时发生异常: {e}，为安全起见已终止回存。")
                return False

    src_dir = account_folder if to_app else WORKBUDDY_DATA_DIR
    dst_dir = WORKBUDDY_DATA_DIR if to_app else account_folder

    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)

    # 如果是还原登录态 (to_app=True)，在覆盖前必须把运行目录下的 SQLite WAL 日志缓冲文件删干净，
    # 防止前一个账号的残留 WAL 缓冲日志前滚恢复覆盖并污染刚拷贝进去的 workbuddy.db
    if to_app:
        for suffix in ["-shm", "-wal"]:
            wal_file = os.path.join(WORKBUDDY_DATA_DIR, "workbuddy.db" + suffix)
            if os.path.exists(wal_file):
                try:
                    os.remove(wal_file)
                    print(f"[Restore] 清理残留 SQLite WAL 日志: {wal_file}")
                except Exception as e:
                    print(f"[Restore] [Warning] 清理 WAL 失败: {e}")

    for item in SESSION_ITEMS:
        src_path = os.path.join(src_dir, item)
        dst_path = os.path.join(dst_dir, item)

        if not os.path.exists(src_path):
            continue

        if os.path.isdir(src_path):
            if os.path.exists(dst_path):
                shutil.rmtree(dst_path)
            shutil.copytree(src_path, dst_path)
        else:
            shutil.copy2(src_path, dst_path)

    # 额外交换 AppData 下的核心账号凭证
    src_auth = os.path.join(account_folder, "workbuddy-desktop.info") if to_app else APPDATA_AUTH_INFO
    dst_auth = APPDATA_AUTH_INFO if to_app else os.path.join(account_folder, "workbuddy-desktop.info")

    if to_app:
        if os.path.exists(src_auth):
            auth_dir = os.path.dirname(APPDATA_AUTH_INFO)
            if not os.path.exists(auth_dir):
                os.makedirs(auth_dir)
            shutil.copy2(src_auth, dst_auth)
            print(f"[Restore] 已恢复 AppData 微信账号登录凭证: {dst_auth}")
        else:
            print(f"[Restore] [Warning] 未在备份目录中发现 workbuddy-desktop.info: {src_auth}")
    else:
        if os.path.exists(src_auth):
            shutil.copy2(src_auth, dst_auth)
            print(f"[Backup] 已备份 AppData 微信账号登录凭证: {dst_auth}")
        else:
            print(f"[Backup] [Warning] 运行时未在 AppData 中发现 workbuddy-desktop.info: {src_auth}")

# ==========================================
# 3. 单账号执行签到模拟
# ==========================================
def run_ui_checkin(exe_path):
    # 1. 启动 WorkBuddy
    print("[UI] 正在启动 WorkBuddy...")
    
    # 如果当前已经有可见的 WorkBuddy 窗口，则不重复启动
    hwnd = find_workbuddy_window()
    if not hwnd:
        print(f"[UI] 窗口未找到，在前台启动 WorkBuddy: {exe_path}")
        cwd = os.path.dirname(exe_path)
        try:
            # 优先使用 os.startfile 以确保通过 Windows Shell 启动，能够彻底脱离 VBS 隐藏父进程的影响并显示窗口
            print(f"[UI] 优先使用 os.startfile 在前台拉起 WorkBuddy...")
            old_cwd = os.getcwd()
            os.chdir(cwd)
            try:
                os.startfile(exe_path)
                print("[UI] os.startfile 启动命令发送成功。")
            finally:
                os.chdir(old_cwd)
        except Exception as e:
            print(f"[UI] os.startfile 启动失败: {e}，尝试使用 subprocess.Popen...")
            try:
                startupinfo = None
                if sys.platform == "win32":
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = 1  # SW_SHOWNORMAL
                subprocess.Popen([exe_path], cwd=cwd, startupinfo=startupinfo)
                print("[UI] subprocess.Popen 启动命令发送成功。")
            except Exception as e2:
                print(f"[UI] subprocess.Popen 启动也失败: {e2}")
            
        # 等待窗口出现并可见
        for i in range(15):
            time.sleep(1)
            hwnd = find_workbuddy_window()
            if hwnd:
                print(f"[UI] 成功捕获到可见窗口，句柄: {hwnd}")
                break
    else:
        print(f"[UI] 检测到已存在运行中的可见窗口，句柄: {hwnd}")

    if not hwnd:
        print("[Error] 未能在 15 秒内捕获到有效的可见 WorkBuddy 窗口。跳过当前账号点击。")
        return False

    # 2. 激活并规范窗口位置大小
    print("[UI] 正在激活并重置 WorkBuddy 窗口位置尺寸...")
    
    # 强制窗口恢复（防止最小化状态）
    user32.ShowWindow(hwnd, SW_RESTORE)
    time.sleep(0.5)
    
    # 【窗口提权激活：Alt 键 Hack + AttachThreadInput 劫持】
    # Windows 为了防止弹窗骚扰限制非活动窗口将其他窗口带到前台。此处通过附加线程输入和发送 Alt 键强制带到最前。
    try:
        # A. 模拟 Alt 键按下与释放以移交焦点所有权
        user32.keybd_event(0x12, 0, 0, 0) # Alt Down
        time.sleep(0.05)
        user32.keybd_event(0x12, 0, 2, 0) # Alt Up
        
        # B. 绑定线程输入，劫持前台特权
        fore_hwnd = user32.GetForegroundWindow()
        fore_thread = user32.GetWindowThreadProcessId(fore_hwnd, None)
        curr_thread = ctypes.windll.kernel32.GetCurrentThreadId()
        
        if fore_thread != 0 and curr_thread != 0 and fore_thread != curr_thread:
            user32.AttachThreadInput(curr_thread, fore_thread, True)
            user32.SetForegroundWindow(hwnd)
            user32.SetFocus(hwnd)
            user32.AttachThreadInput(curr_thread, fore_thread, False)
        else:
            user32.SetForegroundWindow(hwnd)
            user32.SetFocus(hwnd)
    except Exception as e:
        print(f"[UI] 前台激活提权发生异常 (将使用传统激活方式): {e}")
        user32.SetForegroundWindow(hwnd)
        
    time.sleep(0.4)
    # 将窗口移至 (0,0) 并设定为 1024x768 
    user32.SetWindowPos(hwnd, 0, 0, 0, 1024, 768, SWP_SHOWWINDOW)
    time.sleep(1.0)

    # 获取当前实时的窗口位置
    rect = RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))

    # 3. 模拟点击流程 (纯图像匹配识别，无盲点兜底坐标)
    clicked = False
    
    # 在点击头像前先按 ESC 键以确保面板收起
    press_esc()
    time.sleep(0.5)

    # 尝试 1：在面板闭合状态下进行图像匹配（重试 3 次，给界面加载的时间）
    for attempt in range(3):
        coords = find_claim_button_by_template(hwnd, state="closed")
        if coords:
            print(f"[UI] 成功在面板闭合状态图像识别到按钮 (尝试 {attempt+1}/3)，执行点击！")
            click(coords[0], coords[1])
            clicked = True
            time.sleep(1.5)
            break
        else:
            print(f"[UI] 闭合状态第 {attempt+1}/3 次未匹配到按钮，等待重试...")
            time.sleep(0.8)
        
    if not clicked:
        # 尝试 2：如果闭合状态没找到，点击头像展开个人面板（使用当前窗口的相对偏移绝对坐标）
        print("[UI] 未能在闭合状态识别到按钮。点击头像展开个人面板...")
        click(rect.left + 30, rect.top + 730)
        time.sleep(1.0)
        
        # 在面板展开状态下进行图像匹配（重试 3 次，每次间隔 0.8s）
        for attempt in range(3):
            coords = find_claim_button_by_template(hwnd, state="open")
            if coords:
                print(f"[UI] 成功在面板展开状态图像识别到按钮 (尝试 {attempt+1}/3)，执行点击！")
                click(coords[0], coords[1])
                clicked = True
                time.sleep(1.5)
                break
            else:
                print(f"[UI] 展开状态第 {attempt+1}/3 次未匹配到按钮，等待重试...")
                time.sleep(0.8)

    if not clicked:
        print("[UI] 图像识别未匹配到“立即领取”按钮。该账号可能今日已领过，或界面未加载。直接跳过该账号，不做任何盲点操作。")

    # 签到后再次按 ESC 键，把面板恢复为关闭状态，防止干扰下一次运行
    press_esc()
    time.sleep(0.5)
    
    # 4. 最小化并结束
    user32.ShowWindow(hwnd, 6) # 最小化
    return True

# ==========================================
# 4. 主程序入口 (遍历多账号)
# ==========================================
def main():
    exe_path = get_workbuddy_path()
    if not exe_path:
        print("[Error] 未在电脑中找到 WorkBuddy.exe，请确保其已正确安装。")
        sys.exit(1)

    # 如果 accounts 目录不存在，初始化创建
    if not os.path.exists(ACCOUNTS_DIR):
        os.makedirs(ACCOUNTS_DIR)
        print(f"==================================================")
        print(f"[Create] 首次运行，已自动创建多账号凭证目录：")
        print(f"  {ACCOUNTS_DIR}")
        print(f"==================================================")
        print(f"请在此目录下创建账号子文件夹进行登录态备份，例如：")
        print(f"  accounts/account_1")
        print(f"  accounts/account_2")
        print(f"备份方法：在此账户登录状态下，将以下文件/夹复制到子文件夹即可：")
        print(f"  {', '.join(SESSION_ITEMS)}")
        print(f"==================================================")
        sys.exit(0)

    # 遍历所有子账号文件夹
    subfolders = [os.path.join(ACCOUNTS_DIR, d) for d in os.listdir(ACCOUNTS_DIR) if os.path.isdir(os.path.join(ACCOUNTS_DIR, d))]
    
    if len(subfolders) == 0:
        print(f"[Warning] 暂未在 accounts/ 目录下检测到备份账户。执行当前默认登录账号签到。")
        kill_workbuddy()
        run_ui_checkin(exe_path)
        kill_workbuddy()
        print("[Success] 默认账号签到流程结束。")
        sys.exit(0)

    print(f"[Info] 检测到已配置 {len(subfolders)} 个账号，开始多账号自动轮巡签到流程...")

    for i, folder in enumerate(subfolders):
        acc_name = os.path.basename(folder)
        print(f"\n--------------------------------------------------")
        print(f"【开始执行】 账号 {i+1}/{len(subfolders)}: {acc_name}")
        print(f"--------------------------------------------------")
        
        # 1. 确保旧进程退干净
        kill_workbuddy()
        
        # 2. 覆盖写入该账户的微信登录会话
        print(f"[Restore] 正在装载 {acc_name} 的登录会话...")
        swap_session(folder, to_app=True)
        
        # 3. 启动并签到
        success = run_ui_checkin(exe_path)
        
        if success:
            # 4. 签到完毕，为了保存最新的积分数据和签到连续性，回写备份数据
            print(f"[Backup] 正在回存最新会话数据...")
            swap_session(folder, to_app=False)
            print(f"[Success] 账号 {acc_name} 自动签到成功！")
            log_checkin_result(acc_name, True, "签到成功")
        else:
            print(f"[Error] 账号 {acc_name} 执行失败。")
            log_checkin_result(acc_name, False, "未能在 12 秒内捕获到 WorkBuddy 窗口")

    # 执行完毕退出进程
    kill_workbuddy()
    print("\n==================================================")
    print("[Success] 所有账号签到执行完毕！已恢复正常后台模式。")
    print("==================================================")

if __name__ == "__main__":
    main()
