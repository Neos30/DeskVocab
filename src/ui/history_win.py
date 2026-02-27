from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QLineEdit, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor, QFont
from datetime import datetime


# ── 辅助函数 ────────────────────────────────────────────────

def _fmt_countdown(ts: str | None) -> str:
    if not ts:
        return "待复习"
    try:
        nxt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return "—"
    secs = (nxt - datetime.now()).total_seconds()
    if secs <= 0:
        return "待复习"
    if secs < 3600:
        return f"还有 {int(secs / 60)}min"
    if secs < 86400:
        return f"还有 {int(secs / 3600)}h"
    return f"还有 {int(secs / 86400)}天"


def _status_label(rep, status) -> tuple[str, str]:
    """返回 (文字, 颜色)"""
    if rep is None:
        return "新词", "#90A4AE"
    if status == 1:
        return "已掌握", "#4CAF50"
    if rep == 0:
        return "学习中", "#FF9800"
    return f"第 {rep} 次复习", "#2196F3"


# ── 环形图 ──────────────────────────────────────────────────

class _DonutChart(QWidget):
    _HOLE_COLOR = QColor(14, 22, 40)

    def __init__(self):
        super().__init__()
        self.setFixedSize(100, 100)
        self._segs: list[tuple[int, QColor]] = []
        self._total = 0

    def set_data(self, segs: list[tuple[int, QColor]], total: int):
        self._segs = segs
        self._total = total
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx, cy = self.width() // 2, self.height() // 2
        r = min(cx, cy) - 4
        total = sum(v for v, _ in self._segs) or 1
        angle = 90 * 16  # 从顶部开始

        if all(v == 0 for v, _ in self._segs):
            p.setBrush(QColor(60, 70, 90))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(cx - r, cy - r, r * 2, r * 2)
        else:
            for val, color in self._segs:
                if val == 0:
                    continue
                span = int(val / total * 360 * 16)
                p.setBrush(color)
                p.setPen(Qt.PenStyle.NoPen)
                p.drawPie(cx - r, cy - r, r * 2, r * 2, angle, span)
                angle -= span

        # 镂空
        inner = int(r * 0.56)
        p.setBrush(self._HOLE_COLOR)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(cx - inner, cy - inner, inner * 2, inner * 2)

        # 中心文字
        p.setPen(QColor(255, 255, 255))
        f = QFont()
        f.setPointSize(8)
        f.setBold(True)
        p.setFont(f)
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, f"{self._total}\n单词")
        p.end()


# ── 单词行 ──────────────────────────────────────────────────

class _WordRow(QFrame):
    def __init__(self, word, phonetic, definition, rep, status, next_review):
        super().__init__()
        self.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,8);
                border-radius: 8px;
                border: 1px solid rgba(255,255,255,10);
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(12)

        # 左侧：单词 + 音标 + 释义
        left = QVBoxLayout()
        left.setSpacing(3)

        top_row = QHBoxLayout()
        top_row.setSpacing(8)
        word_lbl = QLabel(f"<b>{word}</b>")
        word_lbl.setStyleSheet("color: white; font-size: 14px; background: transparent; border: none;")
        top_row.addWidget(word_lbl)
        if phonetic:
            ph_lbl = QLabel(f"[{phonetic}]")
            ph_lbl.setStyleSheet("color: #7ec8e3; font-size: 12px; background: transparent; border: none;")
            top_row.addWidget(ph_lbl)
        top_row.addStretch()
        left.addLayout(top_row)

        def_lbl = QLabel(definition or "")
        def_lbl.setStyleSheet("color: rgba(190,210,255,180); font-size: 12px; background: transparent; border: none;")
        def_lbl.setWordWrap(True)
        left.addWidget(def_lbl)

        layout.addLayout(left, stretch=4)

        # 右侧：状态标签 + 倒计时
        right = QVBoxLayout()
        right.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        right.setSpacing(5)

        st_text, st_color = _status_label(rep, status)
        st_lbl = QLabel(st_text)
        st_lbl.setStyleSheet(f"""
            color: {st_color};
            font-size: 11px;
            background: transparent;
            border: 1px solid {st_color};
            border-radius: 4px;
            padding: 1px 6px;
        """)
        st_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right.addWidget(st_lbl, alignment=Qt.AlignmentFlag.AlignRight)

        countdown = _fmt_countdown(next_review)
        cd_color = "#EF5350" if countdown == "待复习" else "rgba(170,190,255,140)"
        cd_lbl = QLabel(countdown)
        cd_lbl.setStyleSheet(f"color: {cd_color}; font-size: 11px; background: transparent; border: none;")
        cd_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        right.addWidget(cd_lbl)

        layout.addLayout(right, stretch=1)


# ── 主窗口 ──────────────────────────────────────────────────

class HistoryWin(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self._all_rows: list = []
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("SpeedDic · 学习记录")
        self.setFixedSize(780, 600)
        self.setStyleSheet("""
            QWidget  { background: #0e1628; color: white; }
            QLineEdit {
                background: rgba(255,255,255,12);
                border: 1px solid rgba(255,255,255,30);
                border-radius: 6px;
                color: white;
                padding: 6px 12px;
                font-size: 13px;
            }
            QScrollBar:vertical          { background: transparent; width: 4px; }
            QScrollBar::handle:vertical  { background: rgba(255,255,255,50); border-radius: 2px; min-height: 20px; }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical { height: 0; }
        """)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(22, 20, 22, 20)
        outer.setSpacing(16)

        # 标题
        title = QLabel("学习记录")
        title.setStyleSheet("color: white; font-size: 20px; font-weight: bold; background: transparent;")
        outer.addWidget(title)

        # ── 统计行 ────────────────────────────────────────
        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)

        self._card_total = self._make_number_card("累计背诵", "个单词")
        self._card_due   = self._make_number_card("今日待复习", "个")
        self._donut_card, self.donut, self._legend = self._make_donut_card()

        stats_row.addWidget(self._card_total, stretch=1)
        stats_row.addWidget(self._card_due,   stretch=1)
        stats_row.addWidget(self._donut_card, stretch=2)
        outer.addLayout(stats_row)

        # ── 搜索框 ────────────────────────────────────────
        self.search = QLineEdit()
        self.search.setPlaceholderText("搜索单词或释义...")
        self.search.textChanged.connect(self._filter)
        outer.addWidget(self.search)

        # ── 单词列表 ──────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self._list_container = QWidget()
        self._list_container.setStyleSheet("background: transparent;")
        self._list_layout = QVBoxLayout(self._list_container)
        self._list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._list_layout.setSpacing(6)
        self._list_layout.setContentsMargins(0, 0, 4, 0)
        scroll.setWidget(self._list_container)
        outer.addWidget(scroll)

    # ── 构建统计卡片 ─────────────────────────────────────

    def _make_number_card(self, title: str, unit: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,10);
                border-radius: 10px;
                border: 1px solid rgba(255,255,255,14);
            }
        """)
        card.setFixedHeight(120)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(18, 14, 18, 14)
        lay.setSpacing(4)

        t = QLabel(title)
        t.setStyleSheet("color: rgba(180,200,255,170); font-size: 12px; background: transparent; border: none;")
        lay.addWidget(t)

        v = QLabel("0")
        v.setObjectName("value")
        v.setStyleSheet("color: white; font-size: 34px; font-weight: bold; background: transparent; border: none;")
        lay.addWidget(v)

        u = QLabel(unit)
        u.setStyleSheet("color: rgba(150,175,230,120); font-size: 11px; background: transparent; border: none;")
        lay.addWidget(u)
        lay.addStretch()
        return card

    def _make_donut_card(self) -> tuple[QFrame, _DonutChart, dict]:
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,10);
                border-radius: 10px;
                border: 1px solid rgba(255,255,255,14);
            }
        """)
        card.setFixedHeight(120)
        row = QHBoxLayout(card)
        row.setContentsMargins(18, 12, 18, 12)
        row.setSpacing(14)

        # 左侧标题
        left = QVBoxLayout()
        t = QLabel("掌握程度")
        t.setStyleSheet("color: rgba(180,200,255,170); font-size: 12px; background: transparent; border: none;")
        left.addWidget(t)
        left.addStretch()
        row.addLayout(left)

        donut = _DonutChart()
        row.addWidget(donut, alignment=Qt.AlignmentFlag.AlignVCenter)

        # 图例
        legend_layout = QVBoxLayout()
        legend_layout.setSpacing(4)
        legend: dict[str, QLabel] = {}
        for label, color in [
            ("陌生", "#78909C"),
            ("模糊", "#FF9800"),
            ("熟练", "#2196F3"),
            ("牢记", "#4CAF50"),
        ]:
            r = QHBoxLayout()
            r.setSpacing(5)
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {color}; font-size: 9px; background: transparent; border: none;")
            lbl = QLabel(f"{label}: 0")
            lbl.setStyleSheet("color: rgba(200,215,255,200); font-size: 11px; background: transparent; border: none;")
            legend[label] = lbl
            r.addWidget(dot)
            r.addWidget(lbl)
            r.addStretch()
            legend_layout.addLayout(r)
        row.addLayout(legend_layout)

        return card, donut, legend

    # ── 数据加载 ─────────────────────────────────────────

    def showEvent(self, event):
        super().showEvent(event)
        self._load_data()

    def _load_data(self):
        # 统计卡片
        total = self.db.fetch_all("SELECT COUNT(*) FROM review_stats")[0][0]
        due   = self.db.fetch_all(
            "SELECT COUNT(*) FROM review_stats WHERE next_review_time <= DATETIME('now','localtime')"
        )[0][0]
        self._card_total.findChild(QLabel, "value").setText(str(total))
        self._card_due.findChild(QLabel, "value").setText(str(due))

        # 掌握程度分桶
        unknown  = self.db.fetch_all(
            "SELECT COUNT(*) FROM words w LEFT JOIN review_stats r ON w.id = r.word_id WHERE r.word_id IS NULL"
        )[0][0]
        vague    = self.db.fetch_all(
            "SELECT COUNT(*) FROM review_stats WHERE repetition BETWEEN 1 AND 2 AND status = 0"
        )[0][0]
        skilled  = self.db.fetch_all(
            "SELECT COUNT(*) FROM review_stats WHERE repetition >= 3 AND status = 0"
        )[0][0]
        mastered = self.db.fetch_all(
            "SELECT COUNT(*) FROM review_stats WHERE status = 1"
        )[0][0]

        seg_data = [
            (unknown,  QColor(120, 144, 156), "陌生"),
            (vague,    QColor(255, 152, 0),   "模糊"),
            (skilled,  QColor(33,  150, 243), "熟练"),
            (mastered, QColor(76,  175, 80),  "牢记"),
        ]
        word_total = self.db.fetch_all("SELECT COUNT(*) FROM words")[0][0]
        self.donut.set_data([(v, c) for v, c, _ in seg_data], word_total)
        for v, _, label in seg_data:
            self._legend[label].setText(f"{label}: {v}")

        # 词表
        self._all_rows = self.db.fetch_all("""
            SELECT w.word, w.phonetic, w.definition,
                   r.repetition, r.status, r.next_review_time
            FROM words w
            LEFT JOIN review_stats r ON w.id = r.word_id
            ORDER BY w.create_time DESC
        """)
        self._render(self._all_rows)

    def _render(self, rows: list):
        for i in reversed(range(self._list_layout.count())):
            w = self._list_layout.itemAt(i).widget()
            if w:
                w.setParent(None)

        if not rows:
            lbl = QLabel("暂无学习记录")
            lbl.setStyleSheet("color: rgba(255,255,255,80); font-size: 13px; background: transparent;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setContentsMargins(0, 20, 0, 0)
            self._list_layout.addWidget(lbl)
            return

        for word, phonetic, definition, rep, status, next_review in rows:
            self._list_layout.addWidget(
                _WordRow(word, phonetic, definition, rep, status, next_review)
            )

    def _filter(self, text: str):
        text = text.strip().lower()
        if not text:
            self._render(self._all_rows)
        else:
            filtered = [
                r for r in self._all_rows
                if text in r[0].lower() or text in (r[2] or "").lower()
            ]
            self._render(filtered)
