import time
import win32gui
import re
import hashlib
import json
import os
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

from core.config import Config
from core.database import Database
from engine.bot_engine import BotEngine
from ui.components.buttons import RunButton
from ui.components.toggles import FeatureRow, ToggleSwitch
from ui.components.dialogs import ChatSelectionDialog

FONT_FAMILY = "'Pretendard Variable', Pretendard, -apple-system, system-ui, sans-serif"

# ==================================================================================
#  CYBER ARCHIVE DETAIL DIALOG (ADVANCED DESIGN)
# ==================================================================================
class RouteDetailDialog(QDialog):
    """SF 홀로그램 감성의 세련된 도감 상세창"""
    def __init__(self, route_id, route_info, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(550, 800)
        
        self.route_id = route_id
        self.route_info = route_info
        self.grade = route_info["grade"]
        self.color = Config.COLOR_ACCENT if self.grade == "희귀" else "#888"
        
        self.init_ui()
        
        self.setWindowOpacity(0)
        self.opacity_ani = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_ani.setDuration(400)
        self.opacity_ani.setStartValue(0)
        self.opacity_ani.setEndValue(1)
        self.opacity_ani.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.opacity_ani.start()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.container = QFrame()
        self.container.setObjectName("MainFrame")
        self.container.setStyleSheet(f"""
            QFrame#MainFrame {{ 
                background-color: rgba(10, 10, 12, 0.95); 
                border: 1px solid rgba(255, 255, 255, 0.1); 
                border-radius: 40px; 
            }}
        """)
        c_layout = QVBoxLayout(self.container)
        c_layout.setContentsMargins(40, 50, 40, 40)
        
        header_vbox = QVBoxLayout(); header_vbox.setSpacing(5)
        tag_lbl = QLabel("WEAPON EVOLUTION ARCHIVE")
        tag_lbl.setStyleSheet(f"color: {self.color}; font-size: 10px; font-weight: 900; letter-spacing: 4px; border:none; background:transparent;")
        header_vbox.addWidget(tag_lbl)
        
        title_lbl = QLabel(self.route_id); title_lbl.setWordWrap(True)
        title_lbl.setStyleSheet("font-size: 32px; font-weight: 800; color: white; margin-top: 10px; border:none; background:transparent;")
        header_vbox.addWidget(title_lbl)
        
        meta_lbl = QLabel(f"BLOODLINE: {self.grade.upper()}   |   DATA ENTRIES: {len(self.route_info['levels'])}/21")
        meta_lbl.setStyleSheet("color: #444; font-size: 11px; font-weight: 700; margin-top: 5px; letter-spacing: 1px; border:none; background:transparent;")
        header_vbox.addWidget(meta_lbl)
        c_layout.addLayout(header_vbox); c_layout.addSpacing(35)
        
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll_content = QWidget(); scroll_content.setStyleSheet("background: transparent;"); scroll_vbox = QVBoxLayout(scroll_content)
        scroll_vbox.setSpacing(15); scroll_vbox.setContentsMargins(0, 0, 15, 0)
        
        lv_map = self.route_info["levels"]
        for lv in range(21):
            lv_str = str(lv); is_found = lv_str in lv_map
            row = QFrame(); row.setFixedHeight(60)
            
            if is_found:
                bg_color = "rgba(0, 209, 255, 0.05)"
                border_color = "rgba(0, 209, 255, 0.3)"
                num_color = self.color
                text_color = "#FFF"
            else:
                bg_color = "rgba(255, 255, 255, 0.01)"
                border_color = "rgba(255, 255, 255, 0.03)"
                num_color = "#333"
                text_color = "#444"
                
            row.setStyleSheet(f"""
                QFrame {{ 
                    background-color: {bg_color}; 
                    border: 1px solid {border_color}; 
                    border-radius: 15px; 
                }}
                QFrame:hover {{
                    background-color: rgba(255, 255, 255, 0.08);
                    border: 1px solid {self.color if is_found else '#444'};
                }}
                QLabel {{
                    border: none !important;
                    background: transparent !important;
                    outline: none !important;
                }}
            """)
            
            rl = QHBoxLayout(row); rl.setContentsMargins(25, 0, 25, 0)
            num_lbl = QLabel(f"{lv:02d}"); num_lbl.setStyleSheet(f"color: {num_color}; font-size: 20px; font-weight: 900;")
            div = QFrame(); div.setFixedWidth(1); div.setStyleSheet(f"background: {border_color}; margin: 15px 0;")
            name_lbl = QLabel(lv_map[lv_str] if is_found else "LOCKED CORE DATA")
            name_lbl.setStyleSheet(f"color: {text_color}; font-size: 14px; font-weight: 700;")
            
            rl.addWidget(num_lbl); rl.addWidget(div); rl.addSpacing(15); rl.addWidget(name_lbl); rl.addStretch()
            if is_found:
                check = QLabel("●"); check.setStyleSheet(f"color: {self.color}; font-size: 8px; border:none; background:transparent;")
                rl.addWidget(check)
            scroll_vbox.addWidget(row)
            
        scroll.setWidget(scroll_content)
        scroll.verticalScrollBar().setStyleSheet("QScrollBar:vertical { background: transparent; width: 4px; } QScrollBar::handle:vertical { background: #333; border-radius: 2px; }")
        c_layout.addWidget(scroll)
        
        close_btn = QPushButton("TERMINATE ARCHIVE")
        close_btn.setFixedHeight(50); close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{ 
                background-color: rgba(255, 255, 255, 0.02); 
                color: #666; 
                border: 1px solid #333; 
                border-radius: 25px; 
                font-weight: 800; 
                font-size: 11px;
                letter-spacing: 2px;
                margin-top: 30px;
            }} 
            QPushButton:hover {{ 
                color: white; 
                border-color: {self.color}; 
                background-color: rgba(0, 209, 255, 0.1);
            }}
        """)
        close_btn.clicked.connect(self.close_with_animation); c_layout.addWidget(close_btn)
        layout.addWidget(self.container)

    def close_with_animation(self):
        self.opacity_ani.setDirection(QPropertyAnimation.Direction.Backward)
        self.opacity_ani.finished.connect(self.close)
        self.opacity_ani.start()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton: self._old_pos = e.globalPosition().toPoint()
    def mouseMoveEvent(self, e):
        if hasattr(self, '_old_pos'):
            delta = e.globalPosition().toPoint() - self._old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y()); self._old_pos = e.globalPosition().toPoint()
    def mouseReleaseEvent(self, e): 
        if hasattr(self, '_old_pos'): del self._old_pos

# ==================================================================================
#  REMAINING UI COMPONENTS (StatCard, RouteCard, CollectionCard, etc.)
# ==================================================================================
class StatCard(QFrame):
    def __init__(self, title, value, sub_text, color="#00D1FF"):
        super().__init__()
        self.setFixedSize(240, 120)
        self.setStyleSheet(f"QFrame {{ background-color: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 16px; }} QLabel {{ border: none !important; background: transparent !important; }}")
        layout = QVBoxLayout(self); layout.setContentsMargins(25, 20, 25, 20)
        t_lbl = QLabel(title.upper()); t_lbl.setStyleSheet("color: #666; font-size: 10px; font-weight: 800; letter-spacing: 1px;")
        self.v_lbl = QLabel(value); self.v_lbl.setStyleSheet(f"color: {color}; font-size: 26px; font-weight: 900; margin-top: 5px;")
        self.s_lbl = QLabel(sub_text); self.s_lbl.setStyleSheet("color: #444; font-size: 11px; font-weight: 600;")
        layout.addWidget(t_lbl); layout.addWidget(self.v_lbl); layout.addStretch(); layout.addWidget(self.s_lbl)

class RouteCard(QFrame):
    clicked = pyqtSignal()
    def __init__(self, route_id, route_info):
        super().__init__()
        self.setObjectName("RouteCard"); self.setFixedSize(220, 150); self.setCursor(Qt.CursorShape.PointingHandCursor)
        grade = route_info["grade"]; levels = route_info["levels"]; l_keys = [int(k) for k in levels.keys()]; max_lv = max(l_keys) if l_keys else 0; highest_name = levels.get(str(max_lv), "Unknown"); progress = (len(levels) / 21) * 100; color = Config.COLOR_ACCENT if grade == "희귀" else "#888"
        self.normal_style = f"QFrame#RouteCard {{ background-color: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 20px; }}"
        self.hover_style = f"QFrame#RouteCard {{ background-color: rgba(255, 255, 255, 0.06); border: 1px solid {color}; border-radius: 20px; }}"
        self.press_style = f"QFrame#RouteCard {{ background-color: rgba(0, 0, 0, 0.2); border: 1px solid {color}; border-radius: 20px; }}"
        self.setStyleSheet(self.normal_style); layout = QVBoxLayout(self); layout.setContentsMargins(20, 20, 20, 20)
        top_h = QHBoxLayout(); gt = QLabel(grade.upper()); gt.setStyleSheet(f"color: {color}; font-size: 9px; font-weight: 900; letter-spacing: 1px;"); top_h.addWidget(gt); top_h.addStretch(); lb = QLabel(f"LV.{max_lv}"); lb.setStyleSheet(f"color: {color}; font-size: 10px; font-weight: 900;"); top_h.addWidget(lb); layout.addLayout(top_h)
        name_lbl = QLabel(highest_name); name_lbl.setWordWrap(True); name_lbl.setStyleSheet("color: #EEE; font-size: 15px; font-weight: 800; margin-top: 10px; border:none; background:transparent;"); layout.addWidget(name_lbl); layout.addStretch()
        prog_info = QHBoxLayout(); comp_lbl = QLabel("COMPLETION"); comp_lbl.setStyleSheet("color: #444; font-size: 8px; font-weight: 800; border:none; background:transparent;"); prog_text = QLabel(f"{int(progress)}%"); prog_text.setStyleSheet(f"color: {color}; font-size: 10px; font-weight: 900; border:none; background:transparent;"); prog_info.addWidget(comp_lbl); prog_info.addStretch(); prog_info.addWidget(prog_text); layout.addLayout(prog_info)
        self.bar = QProgressBar(); self.bar.setFixedHeight(3); self.bar.setRange(0, 100); self.bar.setValue(int(progress)); self.bar.setTextVisible(False); self.bar.setStyleSheet(f"QProgressBar {{ background: rgba(255,255,255,0.03); border: none; border-radius: 1px; }} QProgressBar::chunk {{ background: {color}; }}"); layout.addWidget(self.bar)
    def enterEvent(self, e): self.setStyleSheet(self.hover_style)
    def leaveEvent(self, e): self.setStyleSheet(self.normal_style)
    def mousePressEvent(self, e): 
        if e.button() == Qt.MouseButton.LeftButton: self.setStyleSheet(self.press_style)
    def mouseReleaseEvent(self, e): 
        if e.button() == Qt.MouseButton.LeftButton: self.setStyleSheet(self.hover_style); self.clicked.emit()

class CollectionCard(QFrame):
    def __init__(self, name, grade, is_unclassified=False):
        super().__init__()
        self.setFixedSize(180, 110); color = "#FFA500" if is_unclassified else (Config.COLOR_ACCENT if grade == "희귀" else "#888")
        self.setStyleSheet(f"QFrame {{ background-color: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 16px; }} QFrame:hover {{ background-color: rgba(255, 255, 255, 0.06); border: 1px solid {color}; }} QLabel {{ border: none !important; background: transparent !important; outline: none !important; }}")
        layout = QVBoxLayout(self); layout.setContentsMargins(18, 15, 18, 15); gl = QLabel("UNCLASSIFIED" if is_unclassified else grade.upper()); gl.setStyleSheet(f"color: {color}; font-size: 9px; font-weight: 900; letter-spacing: 1px;"); nl = QLabel(name); nl.setWordWrap(True); nl.setStyleSheet(f"color: white; font-size: 13px; font-weight: 700; margin-top: 5px;"); layout.addWidget(gl); layout.addWidget(nl); layout.addStretch(); sl = QLabel("AWAITING ID" if is_unclassified else "COLLECTED"); sl.setStyleSheet(f"color: #444; font-size: 8px; font-weight: 800; letter-spacing: 0.5px;"); layout.addWidget(sl)

class SegmentedControl(QFrame):
    currentIndexChanged = pyqtSignal(int)
    def __init__(self, options):
        super().__init__()
        self.buttons = []; self.current_idx = 0; self.setStyleSheet("QFrame { background: transparent; border: none; }")
        layout = QHBoxLayout(self); layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(8)
        for i, text in enumerate(options):
            btn = QPushButton(text); btn.setCheckable(True); btn.setFixedHeight(34); btn.setMinimumWidth(80)
            btn.setStyleSheet(f"QPushButton {{ background: transparent; border: none; border-radius: 8px; color: #666; font-size: 11px; font-weight: 800; padding: 0 15px; font-family: {FONT_FAMILY}; }} QPushButton:hover {{ color: #EEE; background: rgba(255, 255, 255, 0.03); }} QPushButton:checked {{ background: rgba(0, 209, 255, 0.12); color: {Config.COLOR_ACCENT}; font-weight: 900; }}")
            btn.clicked.connect(lambda checked, idx=i: self.set_index(idx)); self.buttons.append(btn); layout.addWidget(btn)
        if self.buttons: self.buttons[0].setChecked(True)
    def set_index(self, index): self.current_idx = index; [b.setChecked(i == index) for i, b in enumerate(self.buttons)]; self.currentIndexChanged.emit(index)

class ModItem(QFrame):
    def __init__(self, title, control_widget):
        super().__init__()
        self.setFixedHeight(75); self.setStyleSheet(f"QFrame {{ background-color: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 14px; }} QFrame:hover {{ background-color: rgba(255, 255, 255, 0.06); }} QLabel {{ border: none !important; background: transparent !important; color: #E0E0E0; font-size: 14px; font-weight: 600; font-family: {FONT_FAMILY}; }} QLabel:hover {{ border: none !important; background: transparent !important; }}")
        layout = QHBoxLayout(self); layout.setContentsMargins(25, 0, 15, 0); layout.addWidget(QLabel(title)); layout.addStretch(); layout.addWidget(control_widget)

class StatText(QWidget):
    def __init__(self, label, value_color):
        super().__init__()
        layout = QVBoxLayout(self); layout.setContentsMargins(0, 0, 25, 0); layout.setSpacing(2); self.val = QLabel(label); self.val.setStyleSheet(f"color: {value_color}; font-size: 12px; font-weight: 800; background: transparent; font-family: {FONT_FAMILY}; border:none;"); layout.addWidget(self.val)
    def setText(self, text): self.val.setText(text)

class SectionHeader(QLabel):
    def __init__(self, title):
        super().__init__(title.upper()); self.setStyleSheet(f"color: #555; font-size: 11px; font-weight: 900; letter-spacing: 2px; margin-top: 15px; margin-bottom: 5px; background: transparent; font-family: {FONT_FAMILY}; border:none;")

# ==================================================================================
#  MAIN DASHBOARD
# ==================================================================================
class KaBlackSmithDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint); self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground); self.setFixedSize(Config.WINDOW_WIDTH, Config.WINDOW_HEIGHT)
        icon_path = os.path.join("assets", "icons", "icon.ico"); 
        if os.path.exists(icon_path): self.setWindowIcon(QIcon(icon_path))
        self.db = Database.load_all(); self.active_route_id = None; self.pending_origin = None; self.engine = None; self._drag_pos = None
        self.init_ui(); self.refresh_encyclopedia_ui(); self.refresh_analytics_ui(); self.restore_config()

    def init_ui(self):
        self.setStyleSheet(f"* {{ font-family: {FONT_FAMILY}; color: #E0E0E0; }} QWidget#BG {{ background-color: #0E0E10; border-radius: 16px; border: 1px solid #282828; }} QScrollBar:vertical {{ background: transparent; width: 6px; margin: 0px; }} QScrollBar::handle:vertical {{ background: rgba(255, 255, 255, 0.1); min-height: 30px; border-radius: 3px; }} QScrollBar::handle:vertical:hover {{ background: rgba(255, 255, 255, 0.3); }} QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ background: none; }} QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }} QScrollArea {{ border: none; background: transparent; }} QLineEdit {{ background: rgba(0,0,0,0.4); border: 1px solid #333; border-radius: 8px; padding: 10px 15px; color: {Config.COLOR_ACCENT}; font-weight: bold; min-width: 200px; font-size: 13px; text-align: right; }} QSpinBox {{ background: rgba(0,0,0,0.4); border: 1px solid #333; border-radius: 8px; padding: 10px 15px; min-width: 100px; font-weight: 900; color: white; font-size: 13px; }} QSpinBox::up-button, QSpinBox::down-button {{ width: 0px; }}")
        self.bg = QWidget(); self.bg.setObjectName("BG"); self.setCentralWidget(self.bg); main_layout = QHBoxLayout(self.bg); main_layout.setContentsMargins(0, 0, 0, 0); main_layout.setSpacing(0)
        sidebar = QFrame(); sidebar.setFixedWidth(240); sidebar.setStyleSheet("background-color: #111217; border-top-left-radius: 16px; border-bottom-left-radius: 16px; border-right: 1px solid #1A1A1A;"); sb_layout = QVBoxLayout(sidebar); sb_layout.setContentsMargins(0, 40, 0, 30); logo_container = QLabel(); logo_path = os.path.join("assets", "images", "logo.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path); scaled_pixmap = pixmap.scaled(180, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation); logo_container.setPixmap(scaled_pixmap); logo_container.setAlignment(Qt.AlignmentFlag.AlignCenter); logo_container.setStyleSheet("margin-bottom: 40px; background: transparent;")
        else: logo_container.setText("KaBlackSmith"); logo_container.setStyleSheet("color: white; margin-left: 30px; margin-bottom: 40px; font-size: 20px; font-weight: 800;")
        sb_layout.addWidget(logo_container); self.nav_group = QButtonGroup(self); self.nav_group.setExclusive(True)
        for i, name in enumerate(["대장간", "도감", "통계 분석"]):
            btn = QPushButton(name); btn.setFixedHeight(50); btn.setCheckable(True); btn.setStyleSheet(f"QPushButton {{ text-align: left; font-size: 14px; font-weight: 700; background: transparent; border: none; padding-left: 35px; color: #666; letter-spacing: 0.5px; }} QPushButton:hover {{ color: white; background: #16171C; }} QPushButton:checked {{ color: {Config.COLOR_ACCENT}; background: #1A1C23; border-left: 3px solid {Config.COLOR_ACCENT}; }}"); btn.clicked.connect(lambda checked, idx=i: self.switch_page(idx)); self.nav_group.addButton(btn, i); sb_layout.addWidget(btn)
        self.nav_group.buttons()[0].setChecked(True); sb_layout.addStretch(); main_layout.addWidget(sidebar); content_wrapper = QWidget(); content_layout = QVBoxLayout(content_wrapper); content_layout.setContentsMargins(0, 0, 0, 0); content_layout.setSpacing(0); title_bar = QFrame(); title_bar.setFixedHeight(45); tb_layout = QHBoxLayout(title_bar); tb_layout.setContentsMargins(0, 0, 15, 0); tb_layout.addStretch()
        for b_txt, cb in [("—", self.showMinimized), ("✕", self.close)]:
            b = QPushButton(b_txt); b.setFixedSize(32, 32); b.setStyleSheet("QPushButton { color: #555; border: none; background: transparent; font-size: 14px; } QPushButton:hover { color: white; }"); b.clicked.connect(cb); tb_layout.addWidget(b)
        content_layout.addWidget(title_bar); self.stack = QStackedWidget()
        page_smithy = QWidget(); smithy_layout = QVBoxLayout(page_smithy); smithy_layout.setContentsMargins(0, 0, 0, 0); header = QFrame(); header.setFixedHeight(140); header.setStyleSheet("background: transparent; border-bottom: 1px solid #222;"); h_layout = QHBoxLayout(header); h_layout.setContentsMargins(50, 0, 50, 0); title_box = QVBoxLayout(); title_box.setSpacing(5); title_box.setAlignment(Qt.AlignmentFlag.AlignVCenter); h_title = QLabel("검 키우기"); h_title.setStyleSheet("color: white; border: none; font-size: 32px; font-weight: 800;"); info_row = QHBoxLayout(); info_row.setSpacing(25); self.badge_weapon = StatText("보유 무기 없음", Config.COLOR_ACCENT); self.badge_gold = StatText("0 G", "#FFD700"); self.badge_status = StatText("대기 중", "#888"); info_row.addWidget(self.badge_weapon); info_row.addWidget(self.badge_gold); info_row.addWidget(self.badge_status); info_row.addStretch(); title_box.addWidget(h_title); title_box.addLayout(info_row); h_layout.addLayout(title_box); h_layout.addStretch(); self.btn_run = RunButton(); self.btn_run.clicked.connect(self.handle_run); h_layout.addWidget(self.btn_run); smithy_layout.addWidget(header)
        body_container = QWidget(); body_layout = QHBoxLayout(body_container); body_layout.setContentsMargins(50, 20, 50, 30); body_layout.setSpacing(0); settings_scroll = QScrollArea(); settings_content = QWidget(); settings_content.setStyleSheet("background: transparent;"); set_vbox = QVBoxLayout(settings_content); set_vbox.setContentsMargins(0, 0, 20, 0); set_vbox.setSpacing(15); set_vbox.addWidget(SectionHeader("봇 운용 전략")); self.toggle_mode = SegmentedControl(["골드 수급", "자동 강화"]); self.toggle_mode.currentIndexChanged.connect(self.switch_settings_mode); set_vbox.addWidget(ModItem("실행 모드 선택", self.toggle_mode)); self.setting_stack = QStackedWidget(); self.setting_stack.setStyleSheet("background: transparent;"); p_gold = QWidget(); gl = QVBoxLayout(p_gold); gl.setContentsMargins(0,0,0,0); gl.setSpacing(15); gl.addWidget(SectionHeader("경제적 목표 설정")); self.edit_target_gold = QLineEdit("1,000,000,000"); gl.addWidget(ModItem("목표 골드 보유량", self.edit_target_gold)); self.spin_sell = QSpinBox(); self.spin_sell.setRange(1, 20); self.spin_sell.setValue(10); gl.addWidget(ModItem("판매 임계 레벨", self.spin_sell)); gl.addStretch(); self.setting_stack.addWidget(p_gold); p_auto = QWidget(); al = QVBoxLayout(p_auto); al.setContentsMargins(0,0,0,0); al.setSpacing(15); al.addWidget(SectionHeader("자금 및 강화 규칙")); self.edit_start_fund = QLineEdit("50,000,000"); al.addWidget(ModItem("강화 시작 골드", self.edit_start_fund)); self.edit_min_fund = QLineEdit("10,000,000"); al.addWidget(ModItem("최소 보유 금액", self.edit_min_fund)); self.toggle_grade = SegmentedControl(["전체", "일반", "레어"]); al.addWidget(ModItem("무기 등급 필터", self.toggle_grade)); self.spin_target = QSpinBox(); self.spin_target.setRange(1, 20); self.spin_target.setValue(10); al.addWidget(ModItem("최종 강화 레벨", self.spin_target)); self.toggle_collect = ToggleSwitch(); al.addWidget(ModItem("완료된 컬렉션 제외", self.toggle_collect)); al.addStretch(); self.setting_stack.addWidget(p_auto); set_vbox.addWidget(self.setting_stack); set_vbox.addStretch(); settings_scroll.setWidget(settings_content); settings_scroll.setWidgetResizable(True); body_layout.addWidget(settings_scroll); smithy_layout.addWidget(body_container); self.stack.addWidget(page_smithy)
        page_ency = QWidget(); ency_layout = QVBoxLayout(page_ency); ency_layout.setContentsMargins(50, 40, 50, 40); ency_header = QHBoxLayout(); ency_header.setSpacing(20); ency_title = QLabel("무기 도감"); ency_title.setStyleSheet("font-size: 28px; font-weight: 800; color: white;"); ency_header.addWidget(ency_title); ency_header.addStretch(); self.progress_container = QWidget(); self.progress_container.setFixedWidth(240); progress_box = QVBoxLayout(self.progress_container); progress_box.setContentsMargins(0, 0, 0, 0); progress_box.setSpacing(5); self.progress_lbl = QLabel("총 수집 계보: 0종"); self.progress_lbl.setStyleSheet("font-size: 11px; color: #888; font-weight: 700; border:none; background:transparent;"); self.progress_bar = QProgressBar(); self.progress_bar.setFixedHeight(6); self.progress_bar.setRange(0, 100); self.progress_bar.setValue(0); self.progress_bar.setTextVisible(False); self.progress_bar.setStyleSheet(f"QProgressBar {{ background: rgba(255,255,255,0.05); border: none; border-radius: 3px; }} QProgressBar::chunk {{ background: {Config.COLOR_ACCENT}; border-radius: 3px; }}"); progress_box.addWidget(self.progress_lbl); progress_box.addWidget(self.progress_bar); ency_header.addWidget(self.progress_container); ency_layout.addLayout(ency_header); self.ency_filter = SegmentedControl(["전체 계보", "일반 루트", "희귀 루트", "미분류"]); self.ency_filter.currentIndexChanged.connect(self.on_ency_filter_changed); ency_layout.addSpacing(20); ency_layout.addWidget(self.ency_filter); ency_layout.addSpacing(20); scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll_content = QWidget(); scroll_content.setStyleSheet("background: transparent;"); self.grid_layout = QGridLayout(scroll_content); self.grid_layout.setSpacing(20); self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft); scroll.setWidget(scroll_content); ency_layout.addWidget(scroll); self.stack.addWidget(page_ency)
        page_analytics = QWidget(); ana_layout = QVBoxLayout(page_analytics); ana_layout.setContentsMargins(50, 40, 50, 40); ana_title = QLabel("데이터 분석 실시간 리포트"); ana_title.setStyleSheet("font-size: 28px; font-weight: 800; color: white; margin-bottom: 25px; border:none; background:transparent;"); ana_layout.addWidget(ana_title); summary_h = QHBoxLayout(); summary_h.setSpacing(20); self.card_rare_rate = StatCard("희귀 무기 출현율", "0.0%", "전체 0회 획득 중"); self.card_avg_cost = StatCard("평균 강화 비용", "0 G", "+10강 도달 기준", "#FFD700"); self.card_total_tries = StatCard("전체 강화 시도", "0회", "성공 0 | 유지 0 | 파괴 0", "#FF4757"); summary_h.addWidget(self.card_rare_rate); summary_h.addWidget(self.card_avg_cost); summary_h.addWidget(self.card_total_tries); summary_h.addStretch(); ana_layout.addLayout(summary_h); ana_layout.addSpacing(40); ana_layout.addWidget(SectionHeader("등급별 강화 상세 확률 (실시간 집계)")); self.stats_table = QTableWidget(); self.stats_table.setColumnCount(5); self.stats_table.setHorizontalHeaderLabels(["강화 단계", "등급", "성공률", "파괴율", "평균 비용"]); self.stats_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers); self.stats_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection); self.stats_table.setStyleSheet("QTableWidget { background: transparent; border: none; gridline-color: #222; color: #AAA; } QHeaderView::section { background: #1A1A1C; color: #666; font-weight: 800; border: none; padding: 10px; }"); self.stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch); ana_layout.addWidget(self.stats_table); self.stack.addWidget(page_analytics); content_layout.addWidget(self.stack); main_layout.addWidget(content_wrapper)

    def switch_page(self, idx): self.stack.setCurrentIndex(idx); self.refresh_analytics_ui()
    def switch_settings_mode(self, idx): self.setting_stack.setCurrentIndex(idx)
    def on_ency_filter_changed(self, idx): self.refresh_encyclopedia_ui()

    def restore_config(self):
        c = Database.load_config(); self.toggle_mode.set_index(c.get("mode", 0)); self.edit_target_gold.setText(c.get("target_gold", "1,000,000,000")); self.spin_sell.setValue(c.get("sale_threshold", 10)); self.edit_start_fund.setText(c.get("start_fund", "50,000,000")); self.edit_min_fund.setText(c.get("min_fund", "10,000,000")); self.toggle_grade.set_index(c.get("target_grade", 0)); self.spin_target.setValue(c.get("target_level", 10)); self.toggle_collect.setChecked(c.get("exclude_collection", False)); self.setting_stack.setCurrentIndex(c.get("mode", 0))

    def save_current_config(self):
        config_data = {"mode": self.toggle_mode.current_idx, "target_gold": self.edit_target_gold.text(), "sale_threshold": self.spin_sell.value(), "start_fund": self.edit_start_fund.text(), "min_fund": self.edit_min_fund.text(), "target_grade": self.toggle_grade.current_idx, "target_level": self.spin_target.value(), "exclude_collection": self.toggle_collect.isChecked()}
        Database.save_config(config_data)

    def refresh_analytics_ui(self):
        stats = Database.load_stats(); total_spawn = stats["spawn_counts"]["일반"] + stats["spawn_counts"]["희귀"]; rare_rate = (stats["spawn_counts"]["희귀"] / total_spawn * 100) if total_spawn > 0 else 0
        self.card_rare_rate.v_lbl.setText(f"{rare_rate:.1f}%"); self.card_rare_rate.s_lbl.setText(f"전체 {total_spawn}회 획득 중")
        s_count = sum(1 for a in stats["attempts"] if a["r"] == "성공"); m_count = sum(1 for a in stats["attempts"] if a["r"] == "유지"); d_count = sum(1 for a in stats["attempts"] if a["r"] == "파괴")
        self.card_total_tries.v_lbl.setText(f"{len(stats['attempts'])}회"); self.card_total_tries.s_lbl.setText(f"성공 {s_count} | 유지 {m_count} | 파괴 {d_count}")
        self.stats_table.setRowCount(0); row = 0
        for grade in ["일반", "희귀"]:
            if grade in stats["level_stats"]:
                for lv, data in stats["level_stats"][grade].items():
                    self.stats_table.insertRow(row); success_p = (data["success"] / data["tries"] * 100) if data["tries"] > 0 else 0; destroy_p = (data["destroy"] / data["tries"] * 100) if data["tries"] > 0 else 0; avg_c = (data["cost"] / data["tries"]) if data["tries"] > 0 else 0
                    self.stats_table.setItem(row, 0, QTableWidgetItem(f"+{lv}")); self.stats_table.setItem(row, 1, QTableWidgetItem(grade)); self.stats_table.setItem(row, 2, QTableWidgetItem(f"{success_p:.1f}%")); self.stats_table.setItem(row, 3, QTableWidgetItem(f"{destroy_p:.1f}%")); self.stats_table.setItem(row, 4, QTableWidgetItem(f"{int(avg_c):,} G")); row += 1

    def refresh_encyclopedia_ui(self):
        for i in reversed(range(self.grid_layout.count())): 
            if self.grid_layout.itemAt(i).widget(): self.grid_layout.itemAt(i).widget().setParent(None)
        f_idx = self.ency_filter.current_idx; count = 0
        for rid, info in self.db["routes"].items():
            if f_idx == 1 and info["grade"] != "일반": continue
            if f_idx == 2 and info["grade"] != "희귀": continue
            if f_idx == 3: continue
            card = RouteCard(rid, info); card.clicked.connect(lambda r_id=rid, r_info=info: self.show_route_detail(r_id, r_info)); self.grid_layout.addWidget(card, count // 4, count % 4); count += 1
        if f_idx in [0, 3]:
            for name in self.db["unclassified"].keys(): self.grid_layout.addWidget(CollectionCard(name, "", is_unclassified=True), count // 4, count % 4); count += 1
        total_classified = sum(len(r["levels"]) for r in self.db["routes"].values())
        self.progress_lbl.setText(f"총 수집 계보: {len(self.db['routes'])}종"); self.progress_bar.setValue(min(100, len(self.db['routes'])))

    def show_route_detail(self, rid, info): dialog = RouteDetailDialog(rid, info, self); dialog.exec()

    def smart_classify_weapon(self, name, level):
        rid, info = Database.get_route_by_weapon_name(self.db, name)
        if level == 0:
            sfx = ["검", "막대", "몽둥이", "도끼", "망치"]
            grade = "일반" if any(name.endswith(s) for s in sfx) else "희귀"
            self.pending_origin = {"name": name, "grade": grade}; self.active_route_id = rid; Database.record_spawn(grade); return
        if level > 0:
            target_route_id = rid or self.active_route_id
            if target_route_id:
                self.active_route_id = target_route_id; self.db["routes"][target_route_id]["levels"][str(level)] = name
                Database.save_all(self.db); self.refresh_encyclopedia_ui()
            elif self.pending_origin:
                route_id = name; self.active_route_id = route_id
                if route_id not in self.db["routes"]: self.db["routes"][route_id] = {"grade": self.pending_origin["grade"], "origin": self.pending_origin["name"], "levels": {"0": self.pending_origin["name"], str(level): name}}
                else: self.db["routes"][route_id]["levels"][str(level)] = name
                self.pending_origin = None; Database.save_all(self.db); self.refresh_encyclopedia_ui()
            elif name not in self.db["unclassified"]:
                self.db["unclassified"][name] = level; Database.save_all(self.db); self.refresh_encyclopedia_ui()
            if name in self.db["unclassified"]: del self.db["unclassified"][name]; Database.save_all(self.db); self.refresh_encyclopedia_ui()

    def handle_run(self):
        if self.engine and self.engine.isRunning(): self.engine.stop(); return
        dialog = ChatSelectionDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.btn_run.start_running(); self.save_current_config()
            try:
                completed_routes = [rid for rid, info in self.db["routes"].items() if len(info["levels"]) >= 21]
                config_data = {'mode': self.toggle_mode.current_idx, 'target_gold': int(self.edit_target_gold.text().replace(',', '')), 'sale_threshold': self.spin_sell.value(), 'start_fund': int(self.edit_start_fund.text().replace(',', '')), 'min_fund': int(self.edit_min_fund.text().replace(',', '')), 'target_grade': self.toggle_grade.current_idx, 'target_level': self.spin_target.value(), 'exclude_collection': self.toggle_collect.isChecked(), 'completed_routes': completed_routes}
                self.engine = BotEngine(dialog.selected_hwnd, config_data)
                self.engine.data_signal.connect(self.update_game_data); self.engine.handshake_signal.connect(self.on_handshake_result); self.engine.status_signal.connect(self.on_engine_status_changed); self.engine.start()
            except Exception as e: self.btn_run.stop_running()

    def on_engine_status_changed(self, running):
        if not running: self.btn_run.stop_running(); self.badge_status.setText("대기 중"); self.badge_status.val.setStyleSheet("color: #888; font-weight: 800;")

    def on_handshake_result(self, success):
        if success: self.badge_status.setText("연결됨"); self.badge_status.val.setStyleSheet(f"color: #00D1FF; font-weight: 800;")
        else: self.engine.stop()

    def update_game_data(self, data):
        weapon_raw = data['weapon']
        if not weapon_raw or "없음" in weapon_raw or "감지" in weapon_raw: self.active_route_id = None; self.badge_weapon.setText("보유 무기 없음"); return
        level = 0; name = weapon_raw; match = re.search(r'\+?(\d+)', weapon_raw)
        if match: level = int(match.group(1)); name = re.sub(r'\[?\+?\d+\]?\s*', '', weapon_raw).strip()
        self.badge_weapon.setText(weapon_raw.upper()); self.badge_gold.setText(f"{int(data['current_gold']):,} G")
        if name: self.smart_classify_weapon(name, level)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton: self._drag_pos = e.globalPosition().toPoint()
    def mouseMoveEvent(self, e):
        if self._drag_pos: delta = e.globalPosition().toPoint() - self._drag_pos; self.move(self.x() + delta.x(), self.y() + delta.y()); self._drag_pos = e.globalPosition().toPoint()
    def mouseReleaseEvent(self, e): self._drag_pos = None

if __name__ == "__main__":
    import sys; app = QApplication(sys.argv); window = KaBlackSmithDashboard(); window.show(); sys.exit(app.exec())
