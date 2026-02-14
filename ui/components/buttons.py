from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt, QPropertyAnimation, pyqtProperty, QTimer
from PyQt6.QtGui import QPainter, QLinearGradient, QColor
from core.config import Config

class RunButton(QPushButton):
    """엔진 상태에 따라 유동적으로 변화하는 실행 버튼"""
    def __init__(self, parent=None):
        super().__init__("실행", parent)
        self.setFixedSize(140, 46)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._is_running = False
        self._glint_pos = -1.0
        
        self.animation = QPropertyAnimation(self, b"glint_pos")
        self.animation.setDuration(1500)
        self.animation.setStartValue(-1.0)
        self.animation.setEndValue(2.0)
        self.animation.setLoopCount(-1)
        self.update_style()

    @pyqtProperty(float)
    def glint_pos(self):
        return self._glint_pos

    @glint_pos.setter
    def glint_pos(self, pos):
        self._glint_pos = pos
        self.update()

    def update_style(self):
        font_family = "'Pretendard Variable', Pretendard, 'Malgun Gothic', sans-serif"
        if self._is_running:
            self.setText("실행 중...")
            self.setStyleSheet(f"""
                QPushButton {{ 
                    background-color: #1A1C23; 
                    color: {Config.COLOR_ACCENT}; 
                    border-radius: 23px; 
                    font-weight: 800; 
                    font-size: 14px; 
                    border: 1px solid {Config.COLOR_ACCENT}; 
                    font-family: {font_family}; 
                }}
            """)
        else:
            self.setText("실행")
            self.setStyleSheet(f"""
                QPushButton {{ 
                    background-color: #FFFFFF; 
                    color: #000000; 
                    border-radius: 23px; 
                    font-weight: 800; 
                    font-size: 15px; 
                    border: none; 
                    font-family: {font_family};
                }} 
                QPushButton:hover {{ 
                    background-color: {Config.COLOR_ACCENT}; 
                    color: #000;
                }}
            """)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._is_running:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            gradient = QLinearGradient(self.width() * self._glint_pos, 0, self.width() * (self._glint_pos + 0.4), self.height())
            gradient.setColorAt(0, QColor(255, 255, 255, 0))
            gradient.setColorAt(0.5, QColor(255, 255, 255, 40))
            gradient.setColorAt(1, QColor(255, 255, 255, 0))
            painter.setBrush(gradient)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(self.rect(), 23, 23)

    def start_running(self):
        self._is_running = True
        self.animation.start()
        self.update_style()

    def stop_running(self):
        self._is_running = False
        self.animation.stop()
        self.update_style()
        self.setEnabled(True)
