from PyQt6.QtWidgets import QWidget, QFrame, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, QPropertyAnimation, pyqtProperty, pyqtSignal
from PyQt6.QtGui import QPainter, QColor

class ToggleSwitch(QWidget):
    toggled = pyqtSignal(bool)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(46, 24)
        self._checked = False
        self._circle_pos = 3
        self.animation = QPropertyAnimation(self, b"circle_pos", self)
        self.animation.setDuration(150)

    @pyqtProperty(int)
    def circle_pos(self): return self._circle_pos
    @circle_pos.setter
    def circle_pos(self, pos): self._circle_pos = pos; self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QColor("#00F5D4") if self._checked else QColor("#3D3D3D"))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(0, 0, 46, 24, 12, 12)
        p.setBrush(Qt.GlobalColor.white)
        p.drawEllipse(self._circle_pos, 3, 18, 18)

    def mouseReleaseEvent(self, e):
        self._checked = not self._checked
        self.animation.setStartValue(self._circle_pos)
        self.animation.setEndValue(25 if self._checked else 3)
        self.animation.start()
        self.toggled.emit(self._checked)

    def setChecked(self, checked):
        self._checked = checked
        self._circle_pos = 25 if checked else 3
        self.update()

    def isChecked(self):
        return self._checked

class FeatureRow(QFrame):
    def __init__(self, title, hotkey, callback=None):
        super().__init__()
        self.setFixedHeight(64)
        self.setStyleSheet("background-color: transparent; border-bottom: 1px solid #222;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 0, 15, 0)
        lbl = QLabel(title)
        lbl.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: 600;")
        layout.addWidget(lbl)
        layout.addStretch()
        hk = QLabel(hotkey)
        hk.setStyleSheet("color: #555; font-size: 12px; font-weight: 800; margin-right: 15px;")
        layout.addWidget(hk)
        self.toggle = ToggleSwitch()
        if callback: self.toggle.toggled.connect(callback)
        layout.addWidget(self.toggle)
