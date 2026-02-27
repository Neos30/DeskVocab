import sys
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QIcon
from src.ui.wallpaper_win import WordBoard
from src.ui.settings_win import SettingsWin
from src.utils.hotkey_handler import HotkeyHandler
from src.core.database import DatabaseManager
from src.core.srs_engine import SRSCoordinator
from src.core.ai_generator import AIGenerator

class AppCoordinator(QObject):
    toggle_signal = pyqtSignal()
    refresh_signal = pyqtSignal()

    def __init__(self, board, db, srs, settings_win):
        super().__init__()
        self.board = board
        self.db = db
        self.srs = srs
        self.settings_win = settings_win
        
        self.toggle_signal.connect(self._handle_toggle)
        self.refresh_signal.connect(self._refresh_data)
        self.board.review_signal.connect(self._handle_review)
        self.settings_win.settings_saved.connect(self._generate_new_words)

    def _handle_toggle(self):
        self.board.set_interaction_mode(not self.board.is_interactive)

    def _handle_review(self, word_id, quality):
        self.srs.update_word_review(word_id, quality)
        self._refresh_data()

    def _refresh_data(self):
        words = self.srs.get_todays_words()
        self.board.refresh_words(words)

    def _generate_new_words(self):
        # 从数据库加载设置
        res = self.db.fetch_all("SELECT key, value FROM settings")
        s = {k: v for k, v in res}
        
        if not s.get("api_key"):
            return

        gen = AIGenerator(s["api_key"], s["base_url"], s["model"])
        new_words = gen.generate_words(s.get("scene", "日常口语"))
        
        for w in new_words:
            self.db.execute(
                "INSERT OR IGNORE INTO words (word, phonetic, definition, example_en, example_cn, scene_tag) VALUES (?, ?, ?, ?, ?, ?)",
                (w.word, w.phonetic, w.definition, w.example_en, w.example_cn, s.get("scene"))
            )
        self._refresh_data()

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    db = DatabaseManager()
    srs = SRSCoordinator(db)
    
    board = WordBoard()
    settings_win = SettingsWin(db)
    
    coordinator = AppCoordinator(board, db, srs, settings_win)
    
    # 托盘图标
    tray = QSystemTrayIcon(app)
    # 暂时使用一个简单的文本作为图标（如果有 assets/icon.png 则更好）
    tray.setToolTip("SpeedDic - 桌面语言学习")
    menu = QMenu()
    show_action = menu.addAction("显示/隐藏看板 (Ctrl+Alt+S)")
    show_action.triggered.connect(coordinator._handle_toggle)
    settings_action = menu.addAction("设置")
    settings_action.triggered.connect(settings_win.show)
    exit_action = menu.addAction("退出")
    exit_action.triggered.connect(app.quit)
    tray.setContextMenu(menu)
    tray.show()

    # 启动快捷键
    hotkey = HotkeyHandler(lambda: coordinator.toggle_signal.emit())
    hotkey.start()
    
    # 初始加载
    coordinator._refresh_data()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()