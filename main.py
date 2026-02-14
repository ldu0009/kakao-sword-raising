import sys
import os
import ctypes # 윈도우 시스템 설정을 위해 추가
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from ui.dashboard import KaBlackSmithDashboard

def main():
    # [FIX] 윈도우 작업표시줄 아이콘 활성화를 위한 AppUserModelID 설정
    try:
        myappid = 'mycompany.myproduct.subproduct.version' # 고유 ID
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except:
        pass

    # 고해상도 DPI 지원 설정
    if sys.platform == 'win32':
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass

    app = QApplication(sys.argv)
    
    # 앱 전체 아이콘 설정 (assets/icons/icon.ico)
    icon_path = os.path.join(os.path.dirname(__file__), "assets", "icons", "icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    window = KaBlackSmithDashboard()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
