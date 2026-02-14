import time
import win32gui
import re
import hashlib
import json
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
#  REFINED GLASS UI COMPONENTS
# ==================================================================================
class RouteCard(QFrame):
    """미래지향적 유리 계보 카드 (텍스트 배경 제거)"""
    clicked = pyqtSignal()

    def __init__(self, route_id, route_info):
        super().__init__()
        self.setObjectName("RouteCard")
        self.setFixedSize(220, 150)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        grade = route_info["grade"]
        levels = route_info["levels"]
        max_lv = max([int(k) for k in levels.keys()])
        highest_name = levels[str(max_lv)]
        progress = (len(levels) / 21) * 100
        color = Config.COLOR_ACCENT if grade == "희귀" else "#888"
        
        self.normal_style = f"QFrame#RouteCard {{ background-color: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 20px; }}"
        self.hover_style = f"QFrame#RouteCard {{ background-color: rgba(255, 255, 255, 0.06); border: 1px solid {color}; border-radius: 20px; }}"
        self.press_style = f"QFrame#RouteCard {{ background-color: rgba(0, 0, 0, 0.2); border: 1px solid {color}; border-radius: 20px; }}"
        self.setStyleSheet(self.normal_style)
        
        layout = QVBoxLayout(self); layout.setContentsMargins(20, 20, 20, 20)
        
        # [HEADER] - No background/border for labels
        top_h = QHBoxLayout()
        grade_tag = QLabel(grade.upper())
        grade_tag.setStyleSheet(f"color: {color}; font-size: 9px; font-weight: 900; letter-spacing: 1px; border: none; background: transparent;")
        top_h.addWidget(grade_tag); top_h.addStretch()
        
        # LV 배지는 시각적 구분을 위해 최소한의 강조 유지
        lv_badge = QLabel(f"LV.{max_lv}")
        lv_badge.setStyleSheet(f"color: {color}; font-size: 10px; font-weight: 900; border: none; background: transparent;")
        top_h.addWidget(lv_badge)
        layout.addLayout(top_h)
        
        # [NAME] - Pure text
        name_lbl = QLabel(highest_name)
        name_lbl.setWordWrap(True)
        name_lbl.setStyleSheet("color: #EEE; font-size: 15px; font-weight: 800; margin-top: 10px; border: none; background: transparent;")
        layout.addWidget(name_lbl)
        
        layout.addStretch()
        
        # [PROGRESS] - Clean info
        prog_info = QHBoxLayout()
        comp_lbl = QLabel("COMPLETION"); comp_lbl.setStyleSheet("color: #444; font-size: 8px; font-weight: 800; border: none; background: transparent;")
        prog_text = QLabel(f"{int(progress)}%"); prog_text.setStyleSheet(f"color: {color}; font-size: 10px; font-weight: 900; border: none; background: transparent;")
        prog_info.addWidget(comp_lbl); prog_info.addStretch(); prog_info.addWidget(prog_text)
        layout.addLayout(prog_info)
        
        self.bar = QProgressBar()
        self.bar.setFixedHeight(3); self.bar.setRange(0, 100); self.bar.setValue(int(progress)); self.bar.setTextVisible(False)
        self.bar.setStyleSheet(f"QProgressBar {{ background: rgba(255,255,255,0.03); border: none; border-radius: 1px; }} QProgressBar::chunk {{ background: {color}; }}")
        layout.addWidget(self.bar)

    def enterEvent(self, e): self.setStyleSheet(self.hover_style)
    def leaveEvent(self, e): self.setStyleSheet(self.normal_style)
    def mousePressEvent(self, e): 
        if e.button() == Qt.MouseButton.LeftButton: self.setStyleSheet(self.press_style)
    def mouseReleaseEvent(self, e): 
        if e.button() == Qt.MouseButton.LeftButton: self.setStyleSheet(self.hover_style); self.clicked.emit()

class CollectionCard(QFrame):
    """미분류용 유리카드 (라벨 배경 제거)"""
    def __init__(self, name, grade, is_unclassified=False):
        super().__init__()
        self.setFixedSize(180, 110)
        color = "#FFA500" if is_unclassified else (Config.COLOR_ACCENT if grade == "희귀" else "#888")
        
        self.setStyleSheet(f"""
            QFrame {{ 
                background-color: rgba(255, 255, 255, 0.03); 
                border: 1px solid rgba(255, 255, 255, 0.06); 
                border-radius: 16px; 
            }} 
            QFrame:hover {{ 
                background-color: rgba(255, 255, 255, 0.06); 
                border: 1px solid {color}; 
            }}
            QLabel {{ border: none !important; background: transparent !important; outline: none !important; }}
        """)
        layout = QVBoxLayout(self); layout.setContentsMargins(18, 15, 18, 15)
        
        grade_lbl = QLabel("UNCLASSIFIED" if is_unclassified else grade.upper())
        grade_lbl.setStyleSheet(f"color: {color}; font-size: 9px; font-weight: 900; letter-spacing: 1px;")
        
        name_lbl = QLabel(name); name_lbl.setWordWrap(True)
        name_lbl.setStyleSheet(f"color: white; font-size: 13px; font-weight: 700; margin-top: 5px;")
        
        layout.addWidget(grade_lbl); layout.addWidget(name_lbl); layout.addStretch()
        
        status_lbl = QLabel("AWAITING ID" if is_unclassified else "COLLECTED")
        status_lbl.setStyleSheet(f"color: #444; font-size: 8px; font-weight: 800; letter-spacing: 0.5px;")
        layout.addWidget(status_lbl)

# ... (나머지 클래스 및 로직 유지) ...
class RouteDetailDialog(QDialog):
    def __init__(self, route_id, route_info, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(450, 650)
        layout = QVBoxLayout(self); layout.setContentsMargins(10, 10, 10, 10)
        container = QFrame(); container.setObjectName("Modal")
        container.setStyleSheet(f"QFrame#Modal {{ background-color: #121214; border: 1px solid #282828; border-radius: 24px; }}")
        c_layout = QVBoxLayout(container); c_layout.setContentsMargins(35, 40, 35, 35)
        grade = route_info["grade"]; color = Config.COLOR_ACCENT if grade == "희귀" else "#888"
        h_lbl = QLabel("EVOLUTION PATH"); h_lbl.setStyleSheet(f"color: {color}; font-size: 10px; font-weight: 900; letter-spacing: 2px; border:none; background:transparent;")
        title = QLabel(route_id); title.setWordWrap(True); title.setStyleSheet("font-size: 24px; font-weight: 800; color: white; margin-bottom: 20px; border:none; background:transparent;")
        c_layout.addWidget(h_lbl); c_layout.addWidget(title)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll_content = QWidget(); scroll_vbox = QVBoxLayout(scroll_content); scroll_vbox.setSpacing(12)
        levels = route_info["levels"]
        for lv in range(21):
            lv_str = str(lv); is_found = lv_str in levels
            row = QFrame(); row.setFixedHeight(55)
            row.setStyleSheet(f"QFrame {{ background-color: {'rgba(255,255,255,0.03)' if is_found else 'rgba(0,0,0,0.1)'}; border-radius: 12px; border: 1px solid {'rgba(0,209,255,0.15)' if is_found else '#222'}; }}")
            rl = QHBoxLayout(row); rl.setContentsMargins(20, 0, 20, 0)
            ll = QLabel(f"+{lv}"); ll.setStyleSheet(f"color: {color if is_found else '#333'}; font-weight: 900; font-size: 15px; border:none; background:transparent;")
            nl = QLabel(levels[lv_str] if is_found else "Locked Data"); nl.setStyleSheet(f"color: {'#EEE' if is_found else '#444'}; font-weight: 600; font-size: 13px; border:none; background:transparent;")
            rl.addWidget(ll); rl.addSpacing(15); rl.addWidget(nl); rl.addStretch(); scroll_vbox.addWidget(row)
        scroll.setWidget(scroll_content); scroll.verticalScrollBar().setStyleSheet("QScrollBar:vertical { background: transparent; width: 4px; } QScrollBar::handle:vertical { background: #333; border-radius: 2px; }")
        c_layout.addWidget(scroll)
        close_btn = QPushButton("CLOSE"); close_btn.setFixedHeight(45); close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("QPushButton { background-color: #1A1A1C; color: #666; border: 1px solid #333; border-radius: 22px; font-weight: 800; margin-top: 20px; } QPushButton:hover { color: white; border-color: #555; }")
        close_btn.clicked.connect(self.close); c_layout.addWidget(close_btn); layout.addWidget(container)

class SegmentedControl(QFrame):
    currentIndexChanged = pyqtSignal(int)
    def __init__(self, options):
        super().__init__()
        self.buttons = []; self.current_idx = 0
        self.setStyleSheet("QFrame { background: transparent; border: none; }")
        layout = QHBoxLayout(self); layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(8)
        for i, text in enumerate(options):
            btn = QPushButton(text); btn.setCheckable(True); btn.setFixedHeight(34); btn.setCursor(Qt.CursorShape.PointingHandCursor); btn.setMinimumWidth(80)
            btn.setStyleSheet(f"QPushButton {{ background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 8px; color: #666; font-size: 11px; font-weight: 800; padding: 0 15px; font-family: {FONT_FAMILY}; }} QPushButton:hover {{ color: #EEE; background: rgba(255, 255, 255, 0.05); }} QPushButton:checked {{ background: rgba(0, 209, 255, 0.12); border: 1px solid rgba(0, 209, 255, 0.3); color: {Config.COLOR_ACCENT}; }}")
            btn.clicked.connect(lambda checked, idx=i: self.set_index(idx)); self.buttons.append(btn); layout.addWidget(btn)
        if self.buttons: self.buttons[0].setChecked(True)
    def set_index(self, index):
        self.current_idx = index
        for i, btn in enumerate(self.buttons): btn.setChecked(i == index)
        self.currentIndexChanged.emit(index)

class ModItem(QFrame):
    def __init__(self, title, control_widget):
        super().__init__()
        self.setFixedHeight(75); self.setStyleSheet(f"QFrame {{ background-color: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 14px; }} QFrame:hover {{ background-color: rgba(255, 255, 255, 0.06); }} QLabel {{ background: transparent; border: none; color: #E0E0E0; font-size: 14px; font-weight: 600; font-family: {FONT_FAMILY}; }}")
        layout = QHBoxLayout(self); layout.setContentsMargins(25, 0, 15, 0); layout.addWidget(QLabel(title)); layout.addStretch(); layout.addWidget(control_widget)

class StatText(QWidget):
    def __init__(self, label, value_color):
        super().__init__()
        layout = QVBoxLayout(self); layout.setContentsMargins(0, 0, 25, 0); layout.setSpacing(2); self.val = QLabel(label); self.val.setStyleSheet(f"color: {value_color}; font-size: 12px; font-weight: 800; letter-spacing: 0.5px; background: transparent; font-family: {FONT_FAMILY};"); layout.addWidget(self.val)
    def setText(self, text): self.val.setText(text)

class SectionHeader(QLabel):
    def __init__(self, title):
        super().__init__(title.upper()); self.setStyleSheet(f"color: #555; font-size: 11px; font-weight: 900; letter-spacing: 2px; margin-top: 15px; margin-bottom: 5px; background: transparent; font-family: {FONT_FAMILY};")

# ==================================================================================
#  MAIN DASHBOARD
# ==================================================================================
class KaBlackSmithDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint); self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground); self.setFixedSize(Config.WINDOW_WIDTH, Config.WINDOW_HEIGHT)
        self.db = Database.load_all()
        self.active_route_id = None; self.pending_origin = None; self.engine = None; self._drag_pos = None
        self.init_ui(); self.refresh_encyclopedia_ui()

    def init_ui(self):
        self.setStyleSheet(f"* {{ font-family: {FONT_FAMILY}; color: #E0E0E0; }} QWidget#BG {{ background-color: #0E0E10; border-radius: 16px; border: 1px solid #282828; }} QScrollBar:vertical {{ background: transparent; width: 6px; margin: 0px; }} QScrollBar::handle:vertical {{ background: rgba(255, 255, 255, 0.1); min-height: 30px; border-radius: 3px; }} QScrollBar::handle:vertical:hover {{ background: rgba(255, 255, 255, 0.3); }} QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ background: none; }} QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }} QScrollArea {{ border: none; background: transparent; }} QLineEdit {{ background: rgba(0,0,0,0.4); border: 1px solid #333; border-radius: 8px; padding: 10px 15px; color: {Config.COLOR_ACCENT}; font-weight: bold; min-width: 200px; font-size: 13px; text-align: right; }} QSpinBox {{ background: rgba(0,0,0,0.4); border: 1px solid #333; border-radius: 8px; padding: 10px 15px; min-width: 100px; font-weight: 900; color: white; font-size: 13px; }} QSpinBox::up-button, QSpinBox::down-button {{ width: 0px; }}")
        self.bg = QWidget(); self.bg.setObjectName("BG"); self.setCentralWidget(self.bg); main_layout = QHBoxLayout(self.bg); main_layout.setContentsMargins(0, 0, 0, 0); main_layout.setSpacing(0)
        sidebar = QFrame(); sidebar.setFixedWidth(240); sidebar.setStyleSheet("background-color: #111217; border-top-left-radius: 16px; border-bottom-left-radius: 16px; border-right: 1px solid #1A1A1A;"); sb_layout = QVBoxLayout(sidebar); sb_layout.setContentsMargins(0, 40, 0, 30); logo = QLabel("KaBlackSmith"); logo.setStyleSheet("color: white; margin-left: 30px; margin-bottom: 40px; font-size: 20px; font-weight: 800;"); sb_layout.addWidget(logo); self.nav_group = QButtonGroup(self); self.nav_group.setExclusive(True)
        for i, name in enumerate(["대장간", "도감", "통계 분석"]):
            btn = QPushButton(name); btn.setFixedHeight(50); btn.setCheckable(True); btn.setCursor(Qt.CursorShape.PointingHandCursor); btn.setStyleSheet(f"QPushButton {{ text-align: left; font-size: 14px; font-weight: 700; background: transparent; border: none; padding-left: 35px; color: #666; letter-spacing: 0.5px; }} QPushButton:hover {{ color: white; background: #16171C; }} QPushButton:checked {{ color: {Config.COLOR_ACCENT}; background: #1A1C23; border-left: 3px solid {Config.COLOR_ACCENT}; }}"); btn.clicked.connect(lambda checked, idx=i: self.switch_page(idx)); self.nav_group.addButton(btn, i); sb_layout.addWidget(btn)
        self.nav_group.buttons()[0].setChecked(True); sb_layout.addStretch(); main_layout.addWidget(sidebar); content_wrapper = QWidget(); content_layout = QVBoxLayout(content_wrapper); content_layout.setContentsMargins(0, 0, 0, 0); content_layout.setSpacing(0); title_bar = QFrame(); title_bar.setFixedHeight(45); tb_layout = QHBoxLayout(title_bar); tb_layout.setContentsMargins(0, 0, 15, 0); tb_layout.addStretch()
        for b_txt, cb in [("—", self.showMinimized), ("✕", self.close)]:
            b = QPushButton(b_txt); b.setFixedSize(32, 32); b.setStyleSheet("QPushButton { color: #555; border: none; background: transparent; font-size: 14px; } QPushButton:hover { color: white; }"); b.clicked.connect(cb); tb_layout.addWidget(b)
        content_layout.addWidget(title_bar); self.stack = QStackedWidget()
        page_smithy = QWidget(); smithy_layout = QVBoxLayout(page_smithy); smithy_layout.setContentsMargins(0, 0, 0, 0); header = QFrame(); header.setFixedHeight(140); header.setStyleSheet("background: transparent; border-bottom: 1px solid #222;"); h_layout = QHBoxLayout(header); h_layout.setContentsMargins(50, 0, 50, 0); title_box = QVBoxLayout(); title_box.setSpacing(5); title_box.setAlignment(Qt.AlignmentFlag.AlignVCenter); h_title = QLabel("검 키우기"); h_title.setStyleSheet("color: white; border: none; font-size: 32px; font-weight: 800;"); info_row = QHBoxLayout(); info_row.setSpacing(25); self.badge_weapon = StatText("보유 무기 없음", Config.COLOR_ACCENT); self.badge_gold = StatText("0 G", "#FFD700"); self.badge_status = StatText("대기 중", "#888"); info_row.addWidget(self.badge_weapon); info_row.addWidget(self.badge_gold); info_row.addWidget(self.badge_status); info_row.addStretch(); title_box.addWidget(h_title); title_box.addLayout(info_row); h_layout.addLayout(title_box); h_layout.addStretch(); self.btn_run = RunButton(); self.btn_run.clicked.connect(self.handle_run); h_layout.addWidget(self.btn_run); smithy_layout.addWidget(header); body_split = QHBoxLayout(); body_split.setContentsMargins(50, 20, 30, 30); body_split.setSpacing(40); settings_scroll = QScrollArea(); settings_content = QWidget(); settings_content.setStyleSheet("background: transparent;"); set_vbox = QVBoxLayout(settings_content); set_vbox.setContentsMargins(0, 0, 35, 0); set_vbox.setSpacing(15); set_vbox.addWidget(SectionHeader("봇 운용 전략")); self.toggle_mode = SegmentedControl(["골드 수급", "자동 강화"]); self.toggle_mode.currentIndexChanged.connect(self.switch_settings_mode); set_vbox.addWidget(ModItem("실행 모드 선택", self.toggle_mode)); self.setting_stack = QStackedWidget(); self.setting_stack.setStyleSheet("background: transparent;"); p_gold = QWidget(); gl = QVBoxLayout(p_gold); gl.setContentsMargins(0,0,0,0); gl.setSpacing(15); gl.addWidget(SectionHeader("경제적 목표 설정")); self.edit_target_gold = QLineEdit("1,000,000,000"); self.edit_target_gold.setAlignment(Qt.AlignmentFlag.AlignRight); gl.addWidget(ModItem("목표 골드 보유량", self.edit_target_gold)); self.spin_sell = QSpinBox(); self.spin_sell.setRange(1, 20); self.spin_sell.setValue(10); self.spin_sell.setAlignment(Qt.AlignmentFlag.AlignRight); gl.addWidget(ModItem("판매 임계 레벨", self.spin_sell)); gl.addStretch(); self.setting_stack.addWidget(p_gold); p_auto = QWidget(); al = QVBoxLayout(p_auto); al.setContentsMargins(0,0,0,0); al.setSpacing(15); al.addWidget(SectionHeader("강화 세부 규칙")); self.edit_start = QLineEdit("10,000,000"); self.edit_start.setAlignment(Qt.AlignmentFlag.AlignRight); al.addWidget(ModItem("시작 최소 골드", self.edit_start)); self.toggle_grade = SegmentedControl(["전체", "일반", "레어"]); al.addWidget(ModItem("무기 등급 필터", self.toggle_grade)); self.spin_target = QSpinBox(); self.spin_target.setRange(1, 20); self.spin_target.setValue(10); self.spin_target.setAlignment(Qt.AlignmentFlag.AlignRight); al.addWidget(ModItem("目標 강화 레벨", self.spin_target)); self.toggle_collect = ToggleSwitch(); al.addWidget(ModItem("완료된 컬렉션 제외", self.toggle_collect)); al.addStretch(); self.setting_stack.addWidget(p_auto); set_vbox.addWidget(self.setting_stack); set_vbox.addStretch(); settings_scroll.setWidget(settings_content); settings_scroll.setWidgetResizable(True); body_split.addWidget(settings_scroll, 65); log_col = QVBoxLayout(); log_col.setContentsMargins(0, 0, 0, 0); log_col.setSpacing(0); log_col.addWidget(SectionHeader("실시간 정보")); log_panel = QFrame(); log_panel.setFixedWidth(320); log_panel.setStyleSheet("background-color: rgba(255, 255, 255, 0.02); border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.05);"); log_layout = QVBoxLayout(log_panel); log_layout.setContentsMargins(20, 20, 20, 20); self.console = QTextEdit(); self.console.setReadOnly(True); self.console.setFrameStyle(QFrame.Shape.NoFrame); self.console.setStyleSheet("border: none; background: transparent; color: #888; font-family: 'Consolas', 'Pretendard'; font-size: 11px; line-height: 150%; padding: 0px;"); log_layout.addWidget(self.console); log_col.addWidget(log_panel); body_split.addLayout(log_col, 35); smithy_layout.addLayout(body_split); self.stack.addWidget(page_smithy)
        page_ency = QWidget(); ency_layout = QVBoxLayout(page_ency); ency_layout.setContentsMargins(50, 40, 50, 40); ency_header = QHBoxLayout(); ency_header.setSpacing(20); ency_title = QLabel("무기 도감"); ency_title.setStyleSheet("font-size: 28px; font-weight: 800; color: white;"); ency_header.addWidget(ency_title); ency_header.addStretch(); self.progress_container = QWidget(); self.progress_container.setFixedWidth(240); progress_box = QVBoxLayout(self.progress_container); progress_box.setContentsMargins(0, 0, 0, 0); progress_box.setSpacing(5); self.progress_lbl = QLabel("총 수집 계보: 0종"); self.progress_lbl.setStyleSheet("font-size: 11px; color: #888; font-weight: 700;"); self.progress_bar = QProgressBar(); self.progress_bar.setFixedHeight(6); self.progress_bar.setRange(0, 100); self.progress_bar.setValue(0); self.progress_bar.setTextVisible(False); self.progress_bar.setStyleSheet(f"QProgressBar {{ background: rgba(255,255,255,0.05); border: none; border-radius: 3px; }} QProgressBar::chunk {{ background: {Config.COLOR_ACCENT}; border-radius: 3px; }}"); progress_box.addWidget(self.progress_lbl); progress_box.addWidget(self.progress_bar); ency_header.addWidget(self.progress_container); ency_layout.addLayout(ency_header); self.ency_filter = SegmentedControl(["전체 계보", "일반 루트", "희귀 루트", "미분류"]); self.ency_filter.currentIndexChanged.connect(self.on_ency_filter_changed); ency_layout.addSpacing(20); ency_layout.addWidget(self.ency_filter); ency_layout.addSpacing(20); scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll_content = QWidget(); scroll_content.setStyleSheet("background: transparent;"); self.grid_layout = QGridLayout(scroll_content); self.grid_layout.setSpacing(20); self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft); scroll.setWidget(scroll_content); ency_layout.addWidget(scroll); self.stack.addWidget(page_ency)
        page_analytics = QWidget(); ana_layout = QVBoxLayout(page_analytics); ana_layout.setContentsMargins(50, 40, 50, 40); ana_layout.addWidget(QLabel("통계 분석 데이터 준비 중...")); self.stack.addWidget(page_analytics); content_layout.addWidget(self.stack); main_layout.addWidget(content_wrapper)

    def switch_page(self, idx): self.stack.setCurrentIndex(idx)
    def switch_settings_mode(self, idx): self.setting_stack.setCurrentIndex(idx)
    def on_ency_filter_changed(self, idx): self.refresh_encyclopedia_ui()

    def refresh_encyclopedia_ui(self):
        for i in reversed(range(self.grid_layout.count())): 
            if self.grid_layout.itemAt(i).widget(): self.grid_layout.itemAt(i).widget().setParent(None)
        f_idx = self.ency_filter.current_idx; count = 0
        for rid, info in self.db["routes"].items():
            if f_idx == 1 and info["grade"] != "일반": continue
            if f_idx == 2 and info["grade"] != "희귀": continue
            if f_idx == 3: continue
            card = RouteCard(rid, info)
            card.clicked.connect(lambda r_id=rid, r_info=info: self.show_route_detail(r_id, r_info))
            self.grid_layout.addWidget(card, count // 4, count % 4); count += 1
        if f_idx in [0, 3]:
            for name in self.db["unclassified"].keys():
                self.grid_layout.addWidget(CollectionCard(name, "", is_unclassified=True), count // 4, count % 4); count += 1
        self.progress_lbl.setText(f"총 수집 계보: {len(self.db['routes'])}종"); self.progress_bar.setValue(min(100, len(self.db['routes'])))

    def show_route_detail(self, rid, info):
        dialog = RouteDetailDialog(rid, info, self); dialog.exec()

    def smart_classify_weapon(self, name, level):
        rid, info = Database.get_route_by_weapon_name(self.db, name)
        if level == 0:
            sfx = ["검", "막대", "몽둥이", "도끼", "망치"]
            self.pending_origin = {"name": name, "grade": "일반" if any(name.endswith(s) for s in sfx) else "희귀"}
            self.active_route_id = None; return
        if level > 0:
            if rid:
                self.active_route_id = rid; self.db["routes"][rid]["levels"][str(level)] = name
            elif self.pending_origin:
                route_id = name; self.active_route_id = route_id
                if route_id not in self.db["routes"]:
                    self.db["routes"][route_id] = {"grade": self.pending_origin["grade"], "origin": self.pending_origin["name"], "levels": {"0": self.pending_origin["name"], str(level): name}}
                    self.log(f"⚔️ 새 루트 개척: {name}")
                else: self.db["routes"][route_id]["levels"][str(level)] = name
                self.pending_origin = None
            if name in self.db["unclassified"]: del self.db["unclassified"][name]
            Database.save_all(self.db); self.refresh_encyclopedia_ui()
        elif not rid and name not in self.db["unclassified"]:
            self.db["unclassified"][name] = level; Database.save_all(self.db); self.refresh_encyclopedia_ui()

    def handle_run(self):
        dialog = ChatSelectionDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.btn_run.start_running()
            try:
                conf = {'mode': self.toggle_mode.current_idx, 'target_gold': int(self.edit_target_gold.text().replace(',', '')), 'sale_threshold': self.spin_sell.value(), 'start_fund': int(self.edit_start.text().replace(',', '')), 'target_grade': self.toggle_grade.current_idx, 'target_level': self.spin_target.value(), 'exclude_collection': self.toggle_collect.isChecked()}
                self.engine = BotEngine(dialog.selected_hwnd, conf)
                self.engine.log_signal.connect(self.log); self.engine.data_signal.connect(self.update_game_data); self.engine.handshake_signal.connect(self.on_handshake_result); self.engine.start()
            except Exception as e: self.log(f"설정 오류: {e}"); self.btn_run.stop_running(False)

    def on_handshake_result(self, success):
        if success: self.btn_run.stop_running(True); self.badge_status.setText("연결됨"); self.badge_status.val.setStyleSheet(f"color: #00D1FF; font-weight: 800;")
        else: self.btn_run.stop_running(False); self.badge_status.setText("연결 실패"); self.badge_status.val.setStyleSheet("color: #FF4757; font-weight: 800;")

    def update_game_data(self, data):
        weapon_raw = data['weapon']
        if not weapon_raw or "없음" in weapon_raw or "감지" in weapon_raw: self.active_route_id = None; self.badge_weapon.setText("보유 무기 없음"); return
        level = 0; name = weapon_raw; match = re.search(r'\+?(\d+)', weapon_raw)
        if match: level = int(match.group(1)); name = re.sub(r'\[?\+?\d+\]?\s*', '', weapon_raw).strip()
        self.badge_weapon.setText(weapon_raw.upper()); self.badge_gold.setText(f"{int(data['current_gold']):,} G")
        if name: self.smart_classify_weapon(name, level)

    def log(self, text):
        t = time.strftime("%H:%M:%S"); self.console.append(f"<font color='#444'>[{t}]</font>  <font color='#BBB'>{text}</font>"); self.console.verticalScrollBar().setValue(self.console.verticalScrollBar().maximum())

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton: self._drag_pos = e.globalPosition().toPoint()
    def mouseMoveEvent(self, e):
        if self._drag_pos: delta = e.globalPosition().toPoint() - self._drag_pos; self.move(self.x() + delta.x(), self.y() + delta.y()); self._drag_pos = e.globalPosition().toPoint()
    def mouseReleaseEvent(self, e): self._drag_pos = None

if __name__ == "__main__":
    import sys; app = QApplication(sys.argv); window = KaBlackSmithDashboard(); window.show(); sys.exit(app.exec())
