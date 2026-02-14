import sys
import os
import ctypes

# [패키징 필수] 윈도우 DPI 인식을 프로세스 수준에서 강제 설정 (에러 방지 및 좌표 무결성)
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1) # Process_System_DPI_Aware
except:
    ctypes.windll.user32.SetProcessDPIAware()

# Qt 환경 변수 설정
os.environ["QT_QPA_PLATFORM"] = "windows:dpiawareness=0"
os.environ["QT_LOGGING_RULES"] = "qt.qpa.window=false"

from PyQt6.QtWidgets import QApplication
from ui.dashboard import KaBlackSmithDashboard

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = KaBlackSmithDashboard()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
