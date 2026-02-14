import win32gui
import win32con
import ctypes

def inspect_kakao_controls():
    chat_hwnd = win32gui.FindWindow(None, "강화")
    if not chat_hwnd:
        print("Chat window not found")
        return

    def callback(hwnd, results):
        cls = win32gui.GetClassName(hwnd)
        title = win32gui.GetWindowText(hwnd)
        results.append("H:" + str(hwnd) + " | C:" + cls + " | T:" + title)

    controls = []
    win32gui.EnumChildWindows(chat_hwnd, callback, controls)
    for c in controls:
        print(c)

if __name__ == "__main__":
    inspect_kakao_controls()
