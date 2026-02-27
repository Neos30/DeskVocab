from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QApplication, QScrollArea
from PyQt6.QtCore import Qt, pyqtSignal

class WordItemWidget(QWidget):
    """
    单个单词条目组件，包含操作按钮
    """
    review_clicked = pyqtSignal(int, int) # word_id, quality

    def __init__(self, word_id, word, phonetic, definition):
        super().__init__()
        self.word_id = word_id
        layout = QVBoxLayout()
        
        # 单词和音标
        self.title = QLabel(f"<b>{word}</b> [{phonetic}]")
        self.title.setStyleSheet("color: white; font-size: 16px;")
        layout.addWidget(self.title)
        
        # 释义
        self.meaning = QLabel(definition)
        self.meaning.setStyleSheet("color: #DDD; font-size: 14px;")
        self.meaning.setWordWrap(True)
        layout.addWidget(self.meaning)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        self.btn_mastered = QPushButton("已掌握")
        self.btn_vague = QPushButton("模糊")
        self.btn_unclear = QPushButton("不清楚")
        
        for btn, q in [(self.btn_mastered, 5), (self.btn_vague, 3), (self.btn_unclear, 0)]:
            btn.setFixedWidth(60)
            btn.setStyleSheet("""
                QPushButton { background: rgba(255,255,255,20); color: white; border: 1px solid #666; border-radius: 3px; font-size: 11px; }
                QPushButton:hover { background: rgba(255,255,255,40); }
            """)
            btn.clicked.connect(lambda checked, quality=q: self.review_clicked.emit(self.word_id, quality))
            btn_layout.addWidget(btn)
        
        layout.addLayout(btn_layout)
        layout.setContentsMargins(5, 5, 5, 10)
        self.setLayout(layout)

class WordBoard(QWidget):
    review_signal = pyqtSignal(int, int)

    def __init__(self):
        super().__init__()
        self.is_interactive = False
        self._init_ui()

    def _init_ui(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.main_layout = QVBoxLayout()
        
        # 标题栏
        self.title_label = QLabel("今日待复习")
        self.title_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold; background: rgba(0,0,0,100); padding: 8px; border-radius: 5px;")
        self.main_layout.addWidget(self.title_label)
        
        # 滚动区域用于展示单词列表
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background: transparent; border: none;")
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")
        self.list_layout = QVBoxLayout(self.scroll_content)
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.scroll_content)
        
        self.main_layout.addWidget(self.scroll)
        self.setLayout(self.main_layout)
        
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen.width() - 320, 100, 300, 600)
        self.set_interaction_mode(False)

    def set_interaction_mode(self, active: bool):
        self.is_interactive = active
        self.setWindowFlag(Qt.WindowType.WindowTransparentForInput, not active)
        if active:
            self.title_label.setText("今日待复习 (交互模式)")
            self.title_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold; background: rgba(76, 175, 80, 150); padding: 8px; border-radius: 5px;")
        else:
            self.title_label.setText("今日待复习")
            self.title_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold; background: rgba(0,0,0,100); padding: 8px; border-radius: 5px;")
        self.show()

    def refresh_words(self, words_data):
        # 清空现有列表
        for i in reversed(range(self.list_layout.count())): 
            self.list_layout.itemAt(i).widget().setParent(None)
        
        # 重新添加单词
        for w in words_data:
            # w: (id, word, phonetic, definition, ...)
            item = WordItemWidget(w[0], w[1], w[2], w[3])
            item.review_clicked.connect(self.review_signal.emit)
            self.list_layout.addWidget(item)