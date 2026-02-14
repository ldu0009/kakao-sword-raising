import win32gui
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QFrame, QLabel, QListWidget, QHBoxLayout, QPushButton, QListWidgetItem
from PyQt6.QtCore import Qt
from core.config import Config

class ChatSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(450, 550)
        self.selected_hwnd = None
        self.init_ui()
        self.scan_rooms()

    def init_ui(self):
        font_family = "'Pretendard Variable', Pretendard, 'Malgun Gothic', sans-serif"
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        self.container = QFrame()
        self.container.setStyleSheet(f"""
            QFrame {{ 
                background-color: #16171B; 
                border: 1px solid #282828; 
                border-radius: 20px; 
            }}
        """)
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(30, 30, 30, 25)
        
        header_layout = QHBoxLayout()
        title = QLabel("활성 대화방 선택")
        title.setStyleSheet(f"color: white; font-size: 18px; font-weight: 800; border: none; background: transparent; font-family: {font_family};")
        header_layout.addWidget(title)
        header_layout.addStretch()
        container_layout.addLayout(header_layout)
        
        desc = QLabel("봇 엔진을 실행할 카카오톡 대화방을 선택하세요.")
        desc.setStyleSheet(f"color: #666; font-size: 13px; font-weight: 500; border: none; background: transparent; margin-bottom: 10px; font-family: {font_family};")
        container_layout.addWidget(desc)
        
        self.room_list = QListWidget()
        self.room_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.room_list.setStyleSheet(f"""
            QListWidget {{ 
                background-color: rgba(0, 0, 0, 0.2); 
                border: 1px solid #222; 
                border-radius: 12px; 
                padding: 5px; 
                color: #AAA; 
                outline: none;
                font-family: {font_family};
            }}
            QListWidget::item {{ 
                padding: 15px; 
                border-radius: 8px; 
                margin: 2px 5px;
                font-weight: 600;
                font-size: 13px;
                background: transparent;
                border: none;
            }}
            QListWidget::item:hover {{ 
                background-color: rgba(255, 255, 255, 0.03); 
                color: #EEE;
            }}
            QListWidget::item:selected {{ 
                background-color: rgba(0, 209, 255, 0.1); 
                color: {Config.COLOR_ACCENT}; 
                border: 1px solid rgba(0, 209, 255, 0.2);
            }}
        """)
        container_layout.addWidget(self.room_list)
        
        container_layout.addSpacing(20)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        self.btn_cancel = QPushButton("취소")
        self.btn_cancel.setFixedHeight(40)
        self.btn_cancel.setFixedWidth(100)
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.setStyleSheet(f"""
            QPushButton {{ 
                background: transparent;
                color: #666; 
                border: 1px solid #333; 
                border-radius: 20px; 
                font-weight: 700; 
                font-size: 13px;
                font-family: {font_family};
            }} 
            QPushButton:hover {{ 
                color: #EEE; 
                background: rgba(255, 255, 255, 0.05);
            }}
        """)
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_select = QPushButton("확인")
        self.btn_select.setFixedHeight(40)
        self.btn_select.setFixedWidth(120)
        self.btn_select.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_select.setStyleSheet(f"""
            QPushButton {{ 
                background-color: {Config.COLOR_ACCENT}; 
                color: #000; 
                border-radius: 20px; 
                font-weight: 800; 
                font-size: 13px;
                font-family: {font_family};
            }}
            QPushButton:hover {{ 
                background-color: white; 
            }}
        """)
        self.btn_select.clicked.connect(self.accept_selection)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_select)
        container_layout.addLayout(btn_layout)
        
        layout.addWidget(self.container)

    def scan_rooms(self):
        self.room_list.clear()
        def callback(hwnd, results):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if win32gui.GetClassName(hwnd) == "EVA_Window_Dblclk" and title and title != "카카오톡":
                    results.append((hwnd, title))
        rooms = []
        win32gui.EnumWindows(callback, rooms)
        for hwnd, title in rooms:
            item = QListWidgetItem(title)
            item.setData(Qt.ItemDataRole.UserRole, hwnd)
            self.room_list.addItem(item)
        self.room_list.setCurrentItem(None)
        self.room_list.clearFocus()

    def accept_selection(self):
        item = self.room_list.currentItem()
        if item:
            self.selected_hwnd = item.data(Qt.ItemDataRole.UserRole)
            self.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._old_pos = event.globalPosition().toPoint()
    def mouseMoveEvent(self, event):
        if hasattr(self, '_old_pos'):
            delta = event.globalPosition().toPoint() - self._old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self._old_pos = event.globalPosition().toPoint()
    def mouseReleaseEvent(self, event):
        if hasattr(self, '_old_pos'): del self._old_pos
