import time
import win32gui
import win32con
import win32clipboard
import win32api
import pyautogui
import re
import hashlib
from PyQt6.QtCore import QThread, pyqtSignal
from pynput import keyboard

class BotEngine(QThread):
    log_signal = pyqtSignal(str)
    data_signal = pyqtSignal(dict)
    status_signal = pyqtSignal(bool)
    handshake_signal = pyqtSignal(bool)

    def __init__(self, hwnd, config_data):
        super().__init__()
        self.hwnd = hwnd
        self.config = config_data
        self.running = True
        self.is_automating = False
        self.last_msg_id = "" 
        
        self.game_data = {
            "weapon": "검 감지 중...",
            "current_gold": "0",
            "start_gold": "0",
            "gold_diff": "0"
        }
        
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()
        pyautogui.FAILSAFE = True

    def on_press(self, key):
        try:
            if key == keyboard.Key.f12:
                self.log_signal.emit("<b>[SYSTEM]</b> 긴급 정지 (F12)")
                self.stop()
        except: pass

    def find_sub_window(self, parent_hwnd, class_name):
        found_hwnd = [None]
        def callback(hwnd, extra):
            if win32gui.GetClassName(hwnd) == class_name:
                found_hwnd[0] = hwnd
                return False
            return True
        try: win32gui.EnumChildWindows(parent_hwnd, callback, None)
        except: pass
        return found_hwnd[0]

    def bring_to_front(self):
        try:
            if win32gui.IsIconic(self.hwnd): win32gui.ShowWindow(self.hwnd, win32con.SW_RESTORE)
            win32gui.ShowWindow(self.hwnd, win32con.SW_SHOW)
            win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)
            win32gui.SetForegroundWindow(self.hwnd)
            win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)
            time.sleep(0.4)
        except: pass

    def safe_get_clipboard(self):
        for _ in range(5):
            try:
                win32clipboard.OpenClipboard()
                if win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
                    data = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
                    win32clipboard.CloseClipboard()
                    return data
                win32clipboard.CloseClipboard()
            except: time.sleep(0.1)
        return ""

    def capture_chat_raw(self):
        if not self.running: return ""
        try:
            win32clipboard.OpenClipboard(); win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText("WAIT_SYNC", win32con.CF_UNICODETEXT); win32clipboard.CloseClipboard()
            self.bring_to_front()
            sub_hwnd = self.find_sub_window(self.hwnd, "EVA_VH_ListControl_Dblclk")
            rect = win32gui.GetWindowRect(sub_hwnd) if sub_hwnd else win32gui.GetWindowRect(self.hwnd)
            pyautogui.click((rect[0]+rect[2])//2, (rect[1]+rect[3])//2)
            pyautogui.press('end'); time.sleep(0.1); pyautogui.hotkey('ctrl', 'a'); time.sleep(0.1); pyautogui.hotkey('ctrl', 'c'); time.sleep(0.5)
            return self.safe_get_clipboard()
        except: return ""

    def get_structured_messages(self, raw_text):
        if not raw_text: return []
        header_pattern = r'(\[?[^\]\n\r]+?\]?)\s*\[(오[전후]\s*\d+:\d+)\]'
        parts = re.split(header_pattern, raw_text)
        messages = []
        for i in range(1, len(parts), 3):
            if i + 2 < len(parts):
                sender = parts[i].strip("[] ")
                time_str = parts[i+1].strip()
                content = parts[i+2].strip()
                if content or sender:
                    messages.append({"sender": sender, "time": time_str, "content": content})
        return messages

    def parse_game_info(self, messages):
        """과거 기록(최고 기록)을 배제하고 현재 보유 무기를 정확히 추출"""
        if not messages: return False
        
        bot_msgs = [m for m in messages if "플레이봇" in m["sender"]]
        if not bot_msgs: return False
        
        # 최신 메시지 최대 2개 병합
        combined_content = "\n".join([m["content"] for m in bot_msgs[-2:]])
        latest_bot_msg = bot_msgs[-1]

        # [FIX] '최고 기록'이 포함된 라인을 제거하여 현재 무기와 혼동 방지
        filtered_content = "\n".join([line for line in combined_content.splitlines() if "최고 기록" not in line])

        # 1. 골드 추출
        gold_match = re.search(r"(?:골드|남은)\s*[:：]\s*([\d,]+)", filtered_content)
        if gold_match:
            val = gold_match.group(1).replace(",", "")
            self.game_data["current_gold"] = val
            if self.game_data["start_gold"] == "0": self.game_data["start_gold"] = val
            diff = int(self.game_data["current_gold"]) - int(self.game_data["start_gold"])
            self.game_data["gold_diff"] = f"{diff:,}"

        # 2. 무기 추출
        weapon_name = ""
        # 『 』 기호 (파괴/지급/유지) - 최우선
        brackets = re.findall(r"『([^』]+)』", filtered_content)
        if brackets:
            weapon_name = brackets[-1].strip()
        else:
            # 명시적 키워드 탐색 (보유 검, 획득 검, 새로운 검 획득)
            std_match = re.search(r"(?:보유\s*검|획득\s*검|새로운\s*검\s*획득)\s*[:：]\s*([^\n\r]+)", filtered_content)
            if std_match:
                weapon_name = std_match.group(1).strip()
            else:
                # 최후의 수단: [+숫자] 패턴
                lvl_name_match = re.search(r"(\[\+\d+\].+)", filtered_content)
                if lvl_name_match: weapon_name = lvl_name_match.group(1).strip()

        if weapon_name: self.game_data["weapon"] = weapon_name
        self.data_signal.emit(self.game_data)
        
        msg_id = hashlib.md5(f"{latest_bot_msg['time']}{latest_bot_msg['content'][-50:]}".encode()).hexdigest()
        if msg_id != self.last_msg_id:
            self.last_msg_id = msg_id
            log_line = self.get_meaningful_line(latest_bot_msg["content"].split('\n'))
            self.log_signal.emit(f"<b>[PlayBot]</b> {log_line}")
            return True
        return False

    def get_meaningful_line(self, lines):
        for line in reversed(lines):
            if any(k in line for k in ["〖", "『", "골드", "성공", "실패", "지급"]): return line
        return lines[0] if lines else "새로운 응답"

    def send_cmd(self, text, handshake=False):
        if not self.running: return False
        try:
            self.bring_to_front()
            edit_pos = self.find_sub_window(self.hwnd, "RICHEDIT50W")
            if edit_pos:
                r = win32gui.GetWindowRect(edit_pos)
                pyautogui.click((r[0]+r[2])//2, (r[1]+r[3])//2)
            win32clipboard.OpenClipboard(); win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(f"/{text}", win32con.CF_UNICODETEXT); win32clipboard.CloseClipboard()
            pyautogui.hotkey('ctrl', 'a'); pyautogui.press('backspace'); pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.1); pyautogui.press('enter'); time.sleep(0.1); pyautogui.press('enter')
            return self.wait_for_new_response(handshake=handshake)
        except: return False

    def wait_for_new_response(self, handshake=False):
        start_wait = time.time()
        timeout = 15.0 if handshake else 10.0
        while time.time() - start_wait < timeout:
            if not self.running: break
            raw = self.capture_chat_raw()
            if raw:
                msgs = self.get_structured_messages(raw)
                if msgs and self.parse_game_info(msgs): return True
            time.sleep(1.2)
        return False

    def get_weapon_status(self):
        raw = self.game_data["weapon"]
        if not raw or "감지" in raw: return -1, "없음"
        level = 0
        lvl_match = re.search(r'\+?(\d+)', raw)
        if lvl_match: level = int(lvl_match.group(1))
        clean_name = re.sub(r'[\[\]\+\d+\s]', '', raw).strip()
        normal_suffixes = ["검", "막대", "몽둥이", "도끼", "망치"]
        grade = "일반" if any(clean_name.endswith(s) for s in normal_suffixes) else "희귀"
        return level, grade

    def run(self):
        self.status_signal.emit(True)
        self.log_signal.emit("<b>[SYSTEM]</b> 엔진 가동...")
        msgs = self.get_structured_messages(self.capture_chat_raw())
        self.parse_game_info(msgs)
        if not self.send_cmd("프로필", handshake=True):
            self.log_signal.emit("<font color='red'>초기 연결 실패.</font>"); self.stop(); return
        self.handshake_signal.emit(True); self.is_automating = True
        while self.running and self.is_automating:
            try:
                curr_gold = int(self.game_data["current_gold"])
                if curr_gold >= self.config['target_gold']:
                    self.log_signal.emit("<b>[GOAL]</b> 목표 달성."); break
                level, grade = self.get_weapon_status()
                if level == -1: self.send_cmd("프로필"); continue
                if level > 0:
                    if grade == "일반": self.send_cmd("판매")
                    else:
                        if level >= self.config['sale_threshold']: self.send_cmd("판매")
                        else: self.send_cmd("강화")
                else: self.send_cmd("강화")
                time.sleep(1.5)
            except: time.sleep(1.0)
        self.is_automating = False; self.status_signal.emit(False)

    def stop(self):
        self.running = False; self.is_automating = False
        if self.listener: self.listener.stop()
