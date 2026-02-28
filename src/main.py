import sys
import os
# Add project root to sys.path to allow running from any directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtCore import QObject, pyqtSignal, QThread
from PyQt6.QtGui import QIcon
from src.ui.wallpaper_win import WordBoard
from src.ui.settings_win import SettingsWin
from src.ui.history_win import HistoryWin
from src.utils.hotkey_handler import HotkeyHandler
from src.utils.logger import get_logger
from src.core.database import DatabaseManager
from src.core.srs_engine import SRSCoordinator
from src.core.ai_generator import AIGenerator

logger = get_logger()

class AIGeneratorWorker(QThread):
    finished = pyqtSignal(list, str)

    def __init__(self, api_key, base_url, model, scene):
        super().__init__()
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.scene = scene

    def run(self):
        try:
            gen = AIGenerator(self.api_key, self.base_url, self.model)
            new_words = gen.generate_words(self.scene)
            self.finished.emit(new_words, self.scene)
        except Exception as e:
            logger.error(f"[Worker] 未捕获异常: {e}", exc_info=True)
            self.finished.emit([], str(e))

class AppCoordinator(QObject):
    toggle_signal = pyqtSignal()
    refresh_signal = pyqtSignal()

    def __init__(self, board, db, srs, settings_win):
        super().__init__()
        self.board = board
        self.db = db
        self.srs = srs
        self.settings_win = settings_win
        self.worker = None
        self.tray = None
        
        self.toggle_signal.connect(self._handle_toggle)
        self.refresh_signal.connect(self._refresh_data)
        self.board.review_signal.connect(self._handle_review)
        self.settings_win.settings_saved.connect(self._on_config_saved)
        self.settings_win.scene_words_ready.connect(self._on_scene_words_generated)
        self.settings_win.doc_words_ready.connect(self._on_doc_words_generated)

    def _handle_toggle(self):
        self.board.set_interaction_mode(not self.board.is_interactive)

    def _handle_review(self, word_id, action):
        if action == "skip":
            self.srs.skip_word(word_id)
        else:
            self.srs.update_word_review(word_id, action)
        self._refresh_data()

    def _refresh_data(self):
        words = self.srs.get_todays_words()
        self.board.refresh_words(words)

    def _on_config_saved(self):
        """模型配置保存成功，刷新壁纸词库（不触发生成）。"""
        self._refresh_data()

    def _on_scene_words_generated(self, new_words, scene):
        self._on_words_generated(new_words, scene)

    def _generate_new_words(self):
        # 保留兼容入口，供外部直接调用
        res = self.db.fetch_all("SELECT key, value FROM settings")
        s = {k: v for k, v in res}
        if not s.get("api_key"):
            return
        scene = s.get("scene", "日常口语")
        logger.info(f"[Coordinator] 启动生成任务 scene={scene!r} model={s.get('model','')}")
        self.worker = AIGeneratorWorker(s["api_key"], s.get("base_url", ""), s.get("model", ""), scene)
        self.worker.finished.connect(self._on_words_generated)
        self.worker.start()
        if self.tray:
            self.tray.showMessage("SpeedDic", "正在使用 AI 生成新单词，请稍候...", QSystemTrayIcon.MessageIcon.Information)

    def _on_doc_words_generated(self, new_words):
        for w in new_words:
            self.db.execute(
                "INSERT OR IGNORE INTO words (word, phonetic, definition, example_en, example_cn, scene_tag) VALUES (?, ?, ?, ?, ?, ?)",
                (w.word, w.phonetic, w.definition, w.example_en, w.example_cn, "文档导入")
            )
        self._refresh_data()
        if self.tray:
            self.tray.showMessage("SpeedDic", f"已从文档导入 {len(new_words)} 个新单词！", QSystemTrayIcon.MessageIcon.Information)

    def _on_words_generated(self, new_words, scene):
        if not new_words:
            logger.warning(f"[Coordinator] 生成失败，返回为空 scene={scene!r}")
            if self.tray:
                self.tray.showMessage("SpeedDic - 错误", f"生成单词失败: {scene}", QSystemTrayIcon.MessageIcon.Warning)
            return

        for w in new_words:
            self.db.execute(
                "INSERT OR IGNORE INTO words (word, phonetic, definition, example_en, example_cn, scene_tag) VALUES (?, ?, ?, ?, ?, ?)",
                (w.word, w.phonetic, w.definition, w.example_en, w.example_cn, scene)
            )
        self._refresh_data()
        if self.tray:
            self.tray.showMessage("SpeedDic", f"已为您生成 {len(new_words)} 个新单词！", QSystemTrayIcon.MessageIcon.Information)

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    db = DatabaseManager()
    srs = SRSCoordinator(db)

    board = WordBoard()
    settings_win = SettingsWin(db)
    history_win = HistoryWin(db)
    
    coordinator = AppCoordinator(board, db, srs, settings_win)
    
    # 托盘图标
    from PyQt6.QtWidgets import QStyle
    tray = QSystemTrayIcon(app)
    tray.setIcon(app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
    # 暂时使用一个简单的文本作为图标（如果有 assets/icon.png 则更好）
    tray.setToolTip("SpeedDic - 桌面语言学习")
    menu = QMenu()
    show_action = menu.addAction("显示/隐藏看板 (Ctrl+Alt+S)")
    show_action.triggered.connect(coordinator._handle_toggle)
    settings_action = menu.addAction("设置")
    settings_action.triggered.connect(settings_win.show)
    history_action = menu.addAction("查看学习记录")
    history_action.triggered.connect(history_win.show)
    exit_action = menu.addAction("退出")
    exit_action.triggered.connect(app.quit)
    tray.setContextMenu(menu)
    tray.show()
    coordinator.tray = tray

    # 启动快捷键
    hotkey = HotkeyHandler(lambda: coordinator.toggle_signal.emit())
    hotkey.start()
    
    # 初始加载
    coordinator._refresh_data()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()