from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QApplication, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QPainter, QColor, QPainterPath, QPen, QCursor

# ── 玻璃色调常量 ────────────────────────────────────────────
_BG          = QColor(12, 22, 48, 168)   # 深蓝半透明主背景
_TITLE_IDLE  = QColor(255, 255, 255, 18) # 标题栏叠加（锁定）
_TITLE_LIVE  = QColor(60, 180, 100, 55)  # 标题栏叠加（交互）
_BORDER      = QColor(255, 255, 255, 60) # 玻璃边框
_SEP         = QColor(255, 255, 255, 22) # 单词分隔线
_RADIUS      = 14


class WordItemWidget(QWidget):
    review_clicked = pyqtSignal(int, int)

    def __init__(self, word_id, word, phonetic, definition):
        super().__init__()
        self.word_id = word_id
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 8, 14, 10)
        layout.setSpacing(4)

        # 单词 + 音标
        word_label = QLabel(
            f"<b>{word}</b>&nbsp;&nbsp;"
            f"<span style='font-weight:normal;color:#8dd'>[{phonetic}]</span>"
        )
        word_label.setStyleSheet("color: white; font-size: 15px; background: transparent;")
        layout.addWidget(word_label)

        # 释义
        def_label = QLabel(definition)
        def_label.setStyleSheet(
            "color: rgba(210, 228, 255, 210); font-size: 13px; background: transparent;"
        )
        def_label.setWordWrap(True)
        layout.addWidget(def_label)

        # 复习按钮
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        btn_row.setContentsMargins(0, 4, 0, 0)
        for text, q, color in [
            ("已掌握", 5, "#4CAF50"),
            ("模糊",   3, "#FF9800"),
            ("不清楚", 0, "#EF5350"),
        ]:
            btn = QPushButton(text)
            btn.setFixedHeight(22)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {color};
                    border: 1px solid {color};
                    border-radius: 4px;
                    font-size: 11px;
                    padding: 0 8px;
                }}
                QPushButton:hover {{
                    background: {color};
                    color: white;
                }}
            """)
            btn.clicked.connect(lambda _, quality=q: self.review_clicked.emit(self.word_id, quality))
            btn_row.addWidget(btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setPen(QPen(_SEP, 1))
        y = self.height() - 1
        p.drawLine(14, y, self.width() - 14, y)
        p.end()


class _TitleBar(QWidget):
    """可拖动标题栏；交互模式下按住拖动整个 WordBoard。"""

    def __init__(self, board: "WordBoard"):
        super().__init__(board)
        self.board = board
        self._drag_pos: QPoint | None = None

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedHeight(42)

        row = QHBoxLayout(self)
        row.setContentsMargins(14, 0, 14, 0)

        self.label = QLabel("今日待复习")
        self.label.setStyleSheet(
            "color: white; font-size: 14px; font-weight: bold; background: transparent;"
        )
        row.addWidget(self.label)
        row.addStretch()

        self.dot = QLabel("●")
        self.dot.setStyleSheet(
            "color: rgba(255,255,255,70); font-size: 9px; background: transparent;"
        )
        row.addWidget(self.dot)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.board.is_interactive:
            self._drag_pos = (
                event.globalPosition().toPoint() - self.board.frameGeometry().topLeft()
            )
            self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
            event.accept()

    def mouseMoveEvent(self, event):
        if (
            self._drag_pos is not None
            and event.buttons() & Qt.MouseButton.LeftButton
            and self.board.is_interactive
        ):
            self.board.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        self.setCursor(
            QCursor(Qt.CursorShape.OpenHandCursor)
            if self.board.is_interactive
            else QCursor(Qt.CursorShape.ArrowCursor)
        )


class WordBoard(QWidget):
    review_signal = pyqtSignal(int, int)

    def __init__(self):
        super().__init__()
        self.is_interactive = False
        self._init_ui()

    def _init_ui(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnBottomHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.title_bar = _TitleBar(self)
        outer.addWidget(self.title_bar)

        # 滚动区域
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical {
                background: transparent; width: 4px; margin: 0;
            }
            QScrollBar::handle:vertical {
                background: rgba(255,255,255,55);
                border-radius: 2px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical { height: 0; }
        """)

        self.scroll_content = QWidget()
        self.scroll_content.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.scroll_content.setStyleSheet("background: transparent;")

        self.list_layout = QVBoxLayout(self.scroll_content)
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.list_layout.setContentsMargins(0, 0, 0, 10)
        self.list_layout.setSpacing(0)

        self.scroll.setWidget(self.scroll_content)
        outer.addWidget(self.scroll)

        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen.width() - 330, 80, 310, 560)
        self.set_interaction_mode(False)

    # ── 绘制玻璃背景 ────────────────────────────────────────
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        path = QPainterPath()
        path.addRoundedRect(0.5, 0.5, self.width() - 1, self.height() - 1, _RADIUS, _RADIUS)

        # 主背景
        p.setClipPath(path)
        p.fillRect(self.rect(), _BG)

        # 标题栏叠加色（区分交互状态）
        th = self.title_bar.height()
        overlay = _TITLE_LIVE if self.is_interactive else _TITLE_IDLE
        p.fillRect(0, 0, self.width(), th, overlay)

        # 玻璃边框
        p.setClipping(False)
        p.setPen(QPen(_BORDER, 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(path)

        p.end()

    # ── 切换交互模式 ────────────────────────────────────────
    def set_interaction_mode(self, active: bool):
        self.is_interactive = active
        self.hide()  # Windows 限制：改 Flag 前必须隐藏
        self.setWindowFlag(Qt.WindowType.WindowTransparentForInput, not active)

        if active:
            self.title_bar.label.setText("今日待复习  ·  拖动可移动")
            self.title_bar.dot.setStyleSheet(
                "color: #4CAF50; font-size: 9px; background: transparent;"
            )
            self.title_bar.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
        else:
            self.title_bar.label.setText("今日待复习")
            self.title_bar.dot.setStyleSheet(
                "color: rgba(255,255,255,70); font-size: 9px; background: transparent;"
            )
            self.title_bar.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

        self.update()
        self.show()

    # ── 刷新单词列表 ────────────────────────────────────────
    def refresh_words(self, words_data):
        for i in reversed(range(self.list_layout.count())):
            w = self.list_layout.itemAt(i).widget()
            if w:
                w.setParent(None)

        if not words_data:
            empty = QLabel("暂无待复习单词")
            empty.setStyleSheet(
                "color: rgba(255,255,255,110); font-size: 13px; background: transparent;"
            )
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setContentsMargins(0, 20, 0, 0)
            self.list_layout.addWidget(empty)
            return

        for w in words_data:
            item = WordItemWidget(w[0], w[1], w[2], w[3])
            item.review_clicked.connect(self.review_signal.emit)
            self.list_layout.addWidget(item)
