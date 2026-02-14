import time
import win32gui
import re # 정규표현식
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

from core.config import Config
from core.database import Database
from engine.bot_engine import BotEngine
from ui.components.buttons import RunButton
from ui.components.toggles import FeatureRow, ToggleSwitch
from ui.components.dialogs import ChatSelectionDialog

# 전역 폰트 스택 정의
FONT_FAMILY = "'Pretendard Variable', Pretendard, -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif"

# ==================================================================================
#  REFINED UI COMPONENTS
# ==================================================================================
class SegmentedControl(QFrame):
    currentIndexChanged = pyqtSignal(int)
    def __init__(self, options):
        super().__init__()
        self.buttons = []
        self.current_idx = 0
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

class CollectionCard(QFrame):
    def __init__(self, name, grade, is_unclassified=False):
        super().__init__()
        self.setFixedSize(160, 100)
        color = "#FFA500" if is_unclassified else (Config.COLOR_ACCENT if grade == "희귀" else "#888")
        bg_alpha = 0.04 if is_unclassified else 0.08
        self.setStyleSheet(f"""
            QFrame {{ 
                background-color: rgba(255, 255, 255, {bg_alpha}); 
                border: 1px solid rgba(255, 255, 255, 0.1); 
                border-radius: 12px; 
            }} 
            QFrame:hover {{ 
                background-color: rgba(255, 255, 255, 0.12); 
                border: 1px solid {color}; 
            }}
            /* 내부 텍스트 영역의 테두리와 호버 효과 완전 제거 */
            QLabel {{
                border: none !important;
                background: transparent !important;
                outline: none !important;
            }}
            QLabel:hover {{
                border: none !important;
                background: transparent !important;
            }}
        """)
        layout = QVBoxLayout(self); layout.setContentsMargins(15, 15, 15, 15)
        grade_lbl = QLabel("미분류" if is_unclassified else grade); grade_lbl.setStyleSheet(f"color: {color}; font-size: 10px; font-weight: 900;")
        name_lbl = QLabel(name); name_lbl.setWordWrap(True); name_lbl.setStyleSheet(f"color: {'#777' if is_unclassified else 'white'}; font-size: 13px; font-weight: 700;")
        status_lbl = QLabel("식별 대기 중" if is_unclassified else "수집 완료"); status_lbl.setStyleSheet(f"color: {color if not is_unclassified else '#555'}; font-size: 10px; font-weight: 600;")
        layout.addWidget(grade_lbl); layout.addWidget(name_lbl); layout.addStretch(); layout.addWidget(status_lbl)

class ModItem(QFrame):
    def __init__(self, title, control_widget):
        super().__init__()
        self.setFixedHeight(75)
        self.setStyleSheet(f"QFrame {{ background-color: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 14px; }} QFrame:hover {{ background-color: rgba(255, 255, 255, 0.06); }} QLabel {{ background: transparent; border: none; color: #E0E0E0; font-size: 14px; font-weight: 600; font-family: {FONT_FAMILY}; }}")
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
        self.engine = None; self._drag_pos = None
        
        # [데이터 상태]
        self.db = Database.load_all()
        self.current_route_grade = None # 현재 추적 중인 계보의 등급
        
        self.init_ui()
        self.refresh_encyclopedia_ui()

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
        page_ency = QWidget(); ency_layout = QVBoxLayout(page_ency); ency_layout.setContentsMargins(50, 40, 50, 40); ency_header = QHBoxLayout(); ency_header.setSpacing(20); ency_title = QLabel("무기 도감"); ency_title.setStyleSheet("font-size: 28px; font-weight: 800; color: white;"); ency_header.addWidget(ency_title); ency_header.addStretch(); self.progress_container = QWidget(); self.progress_container.setFixedWidth(240); progress_box = QVBoxLayout(self.progress_container); progress_box.setContentsMargins(0, 0, 0, 0); progress_box.setSpacing(5); self.progress_lbl = QLabel("수집된 무기: 0종"); self.progress_lbl.setStyleSheet("font-size: 11px; color: #888; font-weight: 700;"); self.progress_bar = QProgressBar(); self.progress_bar.setFixedHeight(6); self.progress_bar.setRange(0, 100); self.progress_bar.setValue(0); self.progress_bar.setTextVisible(False); self.progress_bar.setStyleSheet(f"QProgressBar {{ background: rgba(255,255,255,0.05); border: none; border-radius: 3px; }} QProgressBar::chunk {{ background: {Config.COLOR_ACCENT}; border-radius: 3px; }}"); progress_box.addWidget(self.progress_lbl); progress_box.addWidget(self.progress_bar); ency_header.addWidget(self.progress_container); ency_layout.addLayout(ency_header); self.ency_filter = SegmentedControl(["전체 무기", "일반 등급", "희귀 등급", "미분류"]); self.ency_filter.currentIndexChanged.connect(self.on_ency_filter_changed); ency_layout.addSpacing(20); ency_layout.addWidget(self.ency_filter); ency_layout.addSpacing(20); scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll_content = QWidget(); scroll_content.setStyleSheet("background: transparent;"); self.grid_layout = QGridLayout(scroll_content); self.grid_layout.setSpacing(15); self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft); scroll.setWidget(scroll_content); ency_layout.addWidget(scroll); self.stack.addWidget(page_ency)
        page_analytics = QWidget(); ana_layout = QVBoxLayout(page_analytics); ana_layout.setContentsMargins(50, 40, 50, 40); ana_layout.addWidget(QLabel("통계 분석 데이터 준비 중...")); self.stack.addWidget(page_analytics); content_layout.addWidget(self.stack); main_layout.addWidget(content_wrapper)

    def switch_page(self, idx): self.stack.setCurrentIndex(idx)
    def switch_settings_mode(self, idx): self.setting_stack.setCurrentIndex(idx)
    def on_ency_filter_changed(self, idx): self.refresh_encyclopedia_ui()

    def refresh_encyclopedia_ui(self):
        for i in reversed(range(self.grid_layout.count())): 
            if self.grid_layout.itemAt(i).widget(): self.grid_layout.itemAt(i).widget().setParent(None)
        filter_idx = self.ency_filter.current_idx
        count = 0
        for name, info in self.db["classified"].items():
            if filter_idx == 1 and info['grade'] != "일반": continue
            if filter_idx == 2 and info['grade'] != "희귀": continue
            if filter_idx == 3: continue
            self.grid_layout.addWidget(CollectionCard(name, info['grade']), count // 4, count % 4); count += 1
        if filter_idx in [0, 3]:
            for name in self.db["unclassified"].keys():
                self.grid_layout.addWidget(CollectionCard(name, "", is_unclassified=True), count // 4, count % 4); count += 1
        self.progress_lbl.setText(f"수집된 무기: {len(self.db['classified'])}종"); self.progress_bar.setValue(min(100, len(self.db['classified'])))

    def smart_classify_weapon(self, name, level):
        """지능형 분류 및 도감 자동 등록 로직"""
        if not name: return
        
        # 이미 정식 도감에 있다면 통과 (단, 계보를 모를 때 이미 등록된 무기를 만나면 계보 동기화)
        if name in self.db["classified"]:
            if not self.current_route_grade:
                self.current_route_grade = self.db["classified"][name]["grade"]
            return

        # 1. 0강 무기를 만난 경우 (새로운 계보 추적 시작)
        if level == 0:
            normal_suffixes = ["검", "막대", "몽둥이", "도끼", "망치"]
            self.current_route_grade = "일반" if any(name.endswith(s) for s in normal_suffixes) else "희귀"
            self.log(f"⚔️ 새 계보 확인: {name} ({self.current_route_grade} 등급)")
        
        # 2. 계보를 아는 상태 (강화 도중 획득한 모든 이름 기록)
        if self.current_route_grade:
            # 정식 도감 등록 및 승격 (미분류에 있었다면 자동 승격됨)
            self.db = Database.promote_weapon(name, self.current_route_grade)
            self.refresh_encyclopedia_ui()
            self.log(f"📖 도감 등록: {name} ({self.current_route_grade})")
        else:
            # 3. 계보를 모르는 상태 (중간 시작)
            if name not in self.db["unclassified"]:
                self.db["unclassified"][name] = {"level": level}
                Database.save_all(self.db)
                self.refresh_encyclopedia_ui()
                self.log(f"❓ 미분류 감지: {name} (식별 대기 중)")

    def handle_run(self):
        dialog = ChatSelectionDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.btn_run.start_running()
            try:
                config_data = {
                    'mode': self.toggle_mode.current_idx,
                    'target_gold': int(self.edit_target_gold.text().replace(',', '')),
                    'sale_threshold': self.spin_sell.value(),
                    'start_fund': int(self.edit_start.text().replace(',', '')),
                    'target_grade': self.toggle_grade.current_idx,
                    'target_level': self.spin_target.value(),
                    'exclude_collection': self.toggle_collect.isChecked()
                }
                self.engine = BotEngine(dialog.selected_hwnd, config_data)
                self.engine.log_signal.connect(self.log); self.engine.data_signal.connect(self.update_game_data); self.engine.handshake_signal.connect(self.on_handshake_result); self.engine.start()
            except Exception as e: self.log(f"설정 오류: {e}"); self.btn_run.stop_running(False)

    def on_handshake_result(self, success):
        if success: self.btn_run.stop_running(True); self.badge_status.setText("연결됨"); self.badge_status.val.setStyleSheet(f"color: {Config.COLOR_ACCENT}; font-weight: 800;")
        else: self.btn_run.stop_running(False); self.badge_status.setText("연결 실패"); self.badge_status.val.setStyleSheet("color: #FF4757; font-weight: 800;")

    def update_game_data(self, data):
        weapon_raw = data['weapon']
        if not weapon_raw or weapon_raw == "보유 무기 없음": 
            self.current_route_grade = None
            self.badge_weapon.setText("보유 무기 없음")
            return
        
        level = 0; name = weapon_raw
        match = re.search(r'\+?(\d+)', weapon_raw)
        if match:
            level = int(match.group(1))
            name = re.sub(r'\[?\+?\d+\]?\s*', '', weapon_raw).strip()
        
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
