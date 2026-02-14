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
from core.database import Database

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
        self.is_recovering_gold = False 
        
        # [NEW] 강화 시도 직전 레벨 기억용
        self.last_attempt_level = 0
        self.last_attempt_grade = "일반"
        
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
                sender = parts[i].strip("[] "); time_str = parts[i+1].strip(); content = parts[i+2].strip()
                if content or sender: messages.append({"sender": sender, "time": time_str, "content": content})
        return messages

    def parse_game_info(self, messages):
        if not messages: return False
        bot_msgs = [m for m in messages if "플레이봇" in m["sender"]]
        if not bot_msgs: return False
        
        combined_content = "\n".join([m["content"] for m in bot_msgs[-2:]])
        latest_bot_msg = bot_msgs[-1]
        filtered_content = "\n".join([line for line in combined_content.splitlines() if "최고 기록" not in line])

        # 1. 골드 추출
        gold_match = re.search(r"(?:골드|남은|현재\s*보유)\s*[:：]\s*([\d,]+)", filtered_content)
        if gold_match:
            val = gold_match.group(1).replace(",", "")
            self.game_data["current_gold"] = val
            if self.game_data["start_gold"] == "0": self.game_data["start_gold"] = val
            diff = int(self.game_data["current_gold"]) - int(self.game_data["start_gold"])
            self.game_data["gold_diff"] = f"{diff:,}"

        # 2. 무기 추출
        weapon_name = ""
        brackets = re.findall(r"『([^』]+)』", filtered_content)
        if brackets: weapon_name = brackets[-1].strip()
        else:
            std_match = re.search(r"(?:보유\s*검|획득\s*검|새로운\s*검\s*획득)\s*[:：]\s*([^\n\r]+)", filtered_content)
            if std_match: weapon_name = std_match.group(1).strip()
            elif re.search(r"(\[\+\d+\].+)", filtered_content): 
                weapon_name = re.search(r"(\[\+\d+\].+)", filtered_content).group(1).strip()

        if weapon_name: self.game_data["weapon"] = weapon_name
        self.data_signal.emit(self.game_data)
        
        # 3. 강화 결과 분석 기록
        self.record_analytics(combined_content)

        msg_id = hashlib.md5(f"{latest_bot_msg['time']}{latest_bot_msg['content'][-50:]}".encode()).hexdigest()
        if msg_id != self.last_msg_id:
            self.last_msg_id = msg_id
            log_line = self.get_meaningful_line(latest_bot_msg["content"].split('\n'))
            self.log_signal.emit(f"<b>[PlayBot]</b> {log_line}")
            return True
        return False

    def record_analytics(self, text):
        """강화 결과와 비용을 '시도 시점 레벨' 기준으로 기록"""
        result = None
        if "강화 성공" in text: result = "성공"
        elif "강화 유지" in text: result = "유지"
        elif "산산조각" in text: result = "파괴"
        
        if result:
            # 비용 추출
            cost_match = re.search(r"사용\s*골드\s*[:：]\s*-?([\d,]+)", text)
            cost = int(cost_match.group(1).replace(",", "")) if cost_match else 0
            
            # [FIX] 시도 시점의 정보를 사용하여 정확히 기록
            Database.record_attempt(self.last_attempt_grade, self.last_attempt_level, result, cost)
            
            # 기록 후 시도 데이터 초기화 (중복 기록 방지용이나, 실제로는 해시에서 걸러짐)
            # 여기서는 다음 시도를 위해 유지

    def get_meaningful_line(self, lines):
        for line in reversed(lines):
            if any(k in line for k in ["〖", "『", "골드", "성공", "실패", "지급"]): return line
        return lines[0] if lines else "새로운 응답"

    def send_cmd(self, text, handshake=False):
        if not self.running: return False
        try:
            # [FIX] 강화 명령어 전송 직전에 현재 레벨과 등급을 스냅샷으로 저장
            if text == "강화":
                lvl, grade, _ = self.get_weapon_status()
                if lvl != -1:
                    self.last_attempt_level = lvl
                    self.last_attempt_grade = grade

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
        start_wait = time.time(); timeout = 15.0 if handshake else 10.0
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
        if not raw or "감지" in raw or "없음" in raw: return -1, "없음", ""
        level = 0
        match = re.search(r'\+?(\d+)', raw)
        if match: level = int(match.group(1))
        name = re.sub(r'[\[\]\+\d+\s]', '', raw).strip()
        sfx = ["검", "막대", "몽둥이", "도끼", "망치"]
        grade = "일반" if any(name.endswith(s) for s in sfx) else "희귀"
        return level, grade, name

    def run(self):
        self.status_signal.emit(True)
        self.log_signal.emit(f"<b>[SYSTEM]</b> 엔진 가동 시작")
        msgs = self.get_structured_messages(self.capture_chat_raw())
        self.parse_game_info(msgs)
        if not self.send_cmd("프로필", handshake=True):
            self.log_signal.emit("<font color='red'>연결 실패.</font>"); self.stop(); return
        self.handshake_signal.emit(True); self.is_automating = True

        while self.running and self.is_automating:
            try:
                curr_gold = int(self.game_data["current_gold"])
                level, grade, name = self.get_weapon_status()

                if self.config['mode'] == 0: # 골드 수급
                    if curr_gold >= self.config['target_gold']: break
                    if level == -1: self.send_cmd("프로필"); continue
                    if level > 0:
                        if grade == "일반" or level >= self.config['sale_threshold']: self.send_cmd("판매")
                        else: self.send_cmd("강화")
                    else: self.send_cmd("강화")
                else: # 자동 강화
                    if self.is_recovering_gold:
                        if curr_gold >= self.config['start_fund']:
                            self.log_signal.emit(f"자금 복구 완료. 강화로 복귀합니다.")
                            self.is_recovering_gold = False
                        else:
                            if level == -1: self.send_cmd("프로필"); continue
                            if level == 0: self.send_cmd("강화")
                            elif grade == "일반" or level >= self.config['sale_threshold']: self.send_cmd("판매")
                            else: self.send_cmd("강화")
                            time.sleep(1.5); continue
                    if level >= self.config['target_level']:
                        self.log_signal.emit("<b>[GOAL]</b> 목표 레벨 달성!"); break
                    if level == -1: 
                        if curr_gold < self.config['min_fund']:
                            self.log_signal.emit("자금 부족으로 수급 모드 전환.")
                            self.is_recovering_gold = True; continue
                        self.send_cmd("프로필"); continue
                    target_g_idx = self.config['target_grade']
                    is_correct = True
                    if target_g_idx == 1 and grade != "일반": is_correct = False
                    if target_g_idx == 2 and grade != "희귀": is_correct = False
                    is_comp = self.config['exclude_collection'] and level >= 1 and name in self.config['completed_routes']
                    if not is_correct or is_comp:
                        if level == 0: self.send_cmd("강화")
                        else: self.send_cmd("판매")
                        continue
                    self.send_cmd("강화")
                time.sleep(1.5)
            except: time.sleep(1.0)
        self.is_automating = False; self.status_signal.emit(False)

    def stop(self):
        self.running = False; self.is_automating = False
        if self.listener: self.listener.stop()
