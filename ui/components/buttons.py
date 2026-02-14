from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt, QPropertyAnimation, pyqtProperty, QTimer
from PyQt6.QtGui import QPainter, QLinearGradient, QColor
from core.config import Config

class RunButton(QPushButton):
    """'실행' 상태를 관리하는 핵심 액션 버튼 (Pretendard 적용)"""
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
    def glint_pos(self): return self._glint_pos
    @glint_pos.setter
    def glint_pos(self, pos): self._glint_pos = pos; self.update()

    def update_style(self, active=False):
        font_family = "'Pretendard Variable', Pretendard, 'Malgun Gothic', sans-serif"
        if self._is_running:
            self.setText("실행 중...")
            self.setStyleSheet(f"QPushButton {{ background-color: #1A1C23; color: {Config.COLOR_ACCENT}; border-radius: 23px; font-weight: 800; font-size: 14px; border: 1px solid {Config.COLOR_ACCENT}; font-family: {font_family}; }}")
        elif active:
            self.setText("엔진 정지")
            self.setStyleSheet(f"QPushButton {{ background-color: #222; color: {Config.COLOR_DANGER}; border-radius: 23px; font-weight: 800; font-size: 14px; border: 1px solid {Config.COLOR_DANGER}; font-family: {font_family}; }}")
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
        self.update_style()
        self.animation.start()

    def stop_running(self, success=True):
        self._is_running = False
        self.animation.stop()
        self.setEnabled(True)
        self.update_style(active=success)
