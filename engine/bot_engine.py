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
        self.last_msg_hash = "" 
        
        self.game_data = {
            "weapon": "검 감지 중...",
            "current_gold": "0",
            "start_gold": "0",
            "gold_diff": "0"
        }
        
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1

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

    def capture_chat_active(self):
        if not self.running: return None
        backup = self.safe_get_clipboard()
        try:
            self.bring_to_front()
            sub_hwnd = self.find_sub_window(self.hwnd, "EVA_VH_ListControl_Dblclk")
            if sub_hwnd:
                r = win32gui.GetWindowRect(sub_hwnd)
                pyautogui.click((r[0]+r[2])//2, (r[1]+r[3])//2)
            else:
                r = win32gui.GetWindowRect(self.hwnd)
                pyautogui.click((r[0]+r[2])//2, r[1] + 200)
            
            time.sleep(0.2)
            pyautogui.hotkey('ctrl', 'a'); time.sleep(0.1); pyautogui.hotkey('ctrl', 'c'); time.sleep(0.5) 
            chat = self.safe_get_clipboard()
            
            # 백업 복구
            if backup:
                try:
                    win32clipboard.OpenClipboard(); win32clipboard.EmptyClipboard()
                    win32clipboard.SetClipboardText(backup, win32con.CF_UNICODETEXT); win32clipboard.CloseClipboard()
                except: pass
            return chat
        except: return None

    def parse_game_info(self, text):
        if not text: return self.game_data
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        reversed_text = "\n".join(reversed(lines))

        gold_match = re.search(r"(?:보유|남은|현재\s*보유)\s*골드\s*[:：]\s*([\d,]+)\s*G", reversed_text)
        if gold_match:
            raw_gold = gold_match.group(1).replace(",", "")
            if self.game_data["start_gold"] == "0": self.game_data["start_gold"] = raw_gold
            self.game_data["current_gold"] = raw_gold
            diff = int(self.game_data["current_gold"]) - int(self.game_data["start_gold"])
            self.game_data["gold_diff"] = f"{diff:,}"

        bracket_matches = re.findall(r"『([^』]+)』", reversed_text)
        standard_match = re.search(r"(?:보유\s*검|획득\s*검|새로운\s*검\s*획득)\s*[:：]\s*([^\n]+)", reversed_text)

        if bracket_matches: self.game_data["weapon"] = bracket_matches[0].strip()
        elif standard_match: self.game_data["weapon"] = standard_match.group(1).strip()

        self.data_signal.emit(self.game_data)
        return self.game_data

    def get_meaningful_line(self, lines):
        for line in reversed(lines[-5:]):
            if any(k in line for k in ["〖", "『", "골드"]): return line
        return lines[-1]

    def send_cmd(self, text, handshake=False):
        if not self.running: return False
        try:
            self.bring_to_front()
            edit_hwnd = self.find_sub_window(self.hwnd, "RICHEDIT50W")
            if edit_hwnd:
                r = win32gui.GetWindowRect(edit_hwnd)
                pyautogui.click((r[0]+r[2])//2, (r[1]+r[3])//2)
            
            # 명령어 입력
            win32clipboard.OpenClipboard(); win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(f"/{text}", win32con.CF_UNICODETEXT); win32clipboard.CloseClipboard()
            
            pyautogui.hotkey('ctrl', 'a'); pyautogui.press('backspace'); pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.1); pyautogui.press('enter'); time.sleep(0.1); pyautogui.press('enter')
            
            # [FIX] 명령어를 보낸 직후의 상태를 즉시 캡처하여 해시 업데이트
            # 이를 통해 내가 보낸 명령어를 봇의 응답으로 착각하는 것을 방지
            time.sleep(0.5) 
            post_cmd_data = self.capture_chat_active()
            if post_cmd_data:
                lines = [l.strip() for l in post_cmd_data.splitlines() if l.strip()]
                if lines: self.last_msg_hash = hashlib.md5(lines[-1].encode()).hexdigest()
            
            # 이제 봇의 진짜 응답을 기다림
            return self.wait_for_new_response(handshake=handshake)
        except: return False

    def wait_for_new_response(self, handshake=False):
        start_wait = time.time()
        timeout = 15.0 if handshake else 10.0
        while time.time() - start_wait < timeout:
            if not self.running: break
            current_data = self.capture_chat_active()
            if current_data:
                lines = [l.strip() for l in current_data.splitlines() if l.strip()]
                if not lines: continue
                
                current_hash = hashlib.md5(lines[-1].encode()).hexdigest()
                
                # 핸드쉐이크가 아니고, 마지막 메시지가 내가 방금 보낸 명령어와 같다면 패스
                if not handshake and current_hash == self.last_msg_hash:
                    time.sleep(0.8)
                    continue

                if handshake:
                    self.parse_game_info(current_data)
                    if "감지" not in self.game_data["weapon"]:
                        self.last_msg_hash = current_hash
                        self.log_signal.emit(self.get_meaningful_line(lines))
                        return True
                else:
                    if current_hash != self.last_msg_hash:
                        # 변화 감지 시, 그것이 봇의 응답인지 내용 검증
                        new_content = "\n".join(lines[-10:])
                        # 봇 특유의 기호나 키워드가 포함되어야만 응답으로 인정
                        if any(k in new_content for k in ["〖", "『", "●", "골드", "성공", "실패", "파괴", "유지"]):
                            self.last_msg_hash = current_hash
                            self.parse_game_info(current_data)
                            self.log_signal.emit(self.get_meaningful_line(lines))
                            return True
            time.sleep(1.0)
        return False

    def get_weapon_status(self):
        raw = self.game_data["weapon"]
        if not raw or "없음" in raw or "감지" in raw: return -1, "없음"
        level = 0
        lvl_match = re.search(r'\+?(\d+)', raw)
        if lvl_match: level = int(lvl_match.group(1))
        clean_name = re.sub(r'[\[\]\+\d+\s]', '', raw).strip()
        normal_suffixes = ["검", "막대", "몽둥이", "도끼", "망치"]
        grade = "일반" if any(clean_name.endswith(s) for s in normal_suffixes) else "희귀"
        return level, grade

    def run(self):
        self.status_signal.emit(True)
        self.log_signal.emit("<b>[SYSTEM]</b> 엔진 가동 및 초기화...")
        
        # 시작 전 현재 상태 한 번 찍고 시작
        init_data = self.capture_chat_active()
        if init_data:
            ls = [l.strip() for l in init_data.splitlines() if l.strip()]
            if ls: self.last_msg_hash = hashlib.md5(ls[-1].encode()).hexdigest()

        if not self.send_cmd("프로필", handshake=True):
            self.log_signal.emit("<font color='red'>연결 실패.</font>"); self.stop(); return

        self.handshake_signal.emit(True); self.is_automating = True

        while self.running and self.is_automating:
            try:
                curr_gold = int(self.game_data["current_gold"])
                if curr_gold >= self.config['target_gold']:
                    self.log_signal.emit("<b>[GOAL]</b> 목표 달성 완료."); break
                
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
