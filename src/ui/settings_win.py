from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QPushButton,
    QLabel, QComboBox, QMessageBox, QHBoxLayout, QSpinBox,
    QFileDialog, QFrame
)
from PyQt6.QtCore import pyqtSignal, QThread
from PyQt6.QtGui import QColor
from src.core.ai_generator import AIGenerator
from src.utils.doc_parser import extract_text
from src.utils.logger import get_logger

logger = get_logger()

PROVIDER_PRESETS = {
    "DeepSeek": {"base_url": "https://api.deepseek.com",                              "model": "deepseek-chat"},
    "OpenAI":   {"base_url": "https://api.openai.com/v1",                             "model": "gpt-4o-mini"},
    "Kimi":     {"base_url": "https://api.moonshot.cn/v1",                            "model": "moonshot-v1-8k"},
    "Qwen":     {"base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",     "model": "qwen-plus"},
    "GLM":      {"base_url": "https://open.bigmodel.cn/api/paas/v4",                  "model": "glm-4-flash"},
    "Custom":   {"base_url": "",                                                       "model": ""},
}


class DocGeneratorWorker(QThread):
    """后台线程：解析文档 → 调用 AI 生成单词"""
    finished = pyqtSignal(list, str)   # (words, error_msg)

    def __init__(self, api_key, base_url, model, file_path, count):
        super().__init__()
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.file_path = file_path
        self.count = count

    def run(self):
        try:
            text = extract_text(self.file_path)
            if not text.strip():
                self.finished.emit([], "文档内容为空，无法提取文本")
                return
            gen = AIGenerator(self.api_key, self.base_url, self.model)
            words = gen.generate_words_from_doc(text, self.count)
            self.finished.emit(words, "")
        except Exception as e:
            self.finished.emit([], str(e))


class TestWorker(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(self, api_key, base_url, model):
        super().__init__()
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    def run(self):
        gen = AIGenerator(self.api_key, self.base_url, self.model)
        ok, msg = gen.test_connection()
        self.finished.emit(ok, msg)


class SettingsWin(QWidget):
    settings_saved = pyqtSignal()
    doc_words_ready = pyqtSignal(list)   # 文档导入生成完成，携带单词列表

    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self._test_worker = None
        self._doc_worker = None
        self._init_ui()
        self._load_settings()

    def _init_ui(self):
        self.setWindowTitle("SpeedDic 设置")
        self.setFixedSize(420, 560)
        layout = QVBoxLayout()

        self.form = QFormLayout()

        self.provider_combo = QComboBox()
        self.provider_combo.addItems(list(PROVIDER_PRESETS.keys()))
        self.provider_combo.currentTextChanged.connect(self._on_provider_changed)
        self.form.addRow("AI 提供商:", self.provider_combo)

        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.form.addRow("API Key:", self.api_key_input)

        self.base_url_input = QLineEdit()
        self.base_url_input.setPlaceholderText("https://api.deepseek.com")
        self.form.addRow("Base URL:", self.base_url_input)

        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("deepseek-chat")
        self.form.addRow("模型名称:", self.model_input)

        self.scene_input = QLineEdit()
        self.scene_input.setPlaceholderText("如：互联网架构, 雅思核心词")
        self.form.addRow("当前场景:", self.scene_input)

        layout.addLayout(self.form)

        self.test_btn = QPushButton("验证连接")
        self.test_btn.clicked.connect(self._test_connection)
        layout.addWidget(self.test_btn)

        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        self.save_btn = QPushButton("保存设置并生成新词")
        self.save_btn.clicked.connect(self._save_settings)
        layout.addWidget(self.save_btn)

        # ── 分隔线 ──────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #ccc;")
        layout.addWidget(sep)

        # ── 从文档导入生成单词 ────────────────────────────────
        doc_title = QLabel("从文档导入生成单词")
        doc_title.setStyleSheet("font-weight: bold; margin-top: 4px;")
        layout.addWidget(doc_title)

        doc_form = QFormLayout()

        file_row = QHBoxLayout()
        self.file_path_input = QLineEdit()
        self.file_path_input.setPlaceholderText("选择 .pdf / .docx / .doc 文件")
        self.file_path_input.setReadOnly(True)
        browse_btn = QPushButton("浏览…")
        browse_btn.setFixedWidth(60)
        browse_btn.clicked.connect(self._browse_file)
        file_row.addWidget(self.file_path_input)
        file_row.addWidget(browse_btn)
        doc_form.addRow("文件:", file_row)

        self.doc_count_input = QSpinBox()
        self.doc_count_input.setRange(5, 30)
        self.doc_count_input.setValue(10)
        doc_form.addRow("生成数量:", self.doc_count_input)

        layout.addLayout(doc_form)

        self.doc_import_btn = QPushButton("导入并生成单词")
        self.doc_import_btn.clicked.connect(self._import_doc)
        layout.addWidget(self.doc_import_btn)

        self.doc_status_label = QLabel("")
        self.doc_status_label.setWordWrap(True)
        layout.addWidget(self.doc_status_label)

        self.setLayout(layout)

    def _on_provider_changed(self, provider: str):
        preset = PROVIDER_PRESETS.get(provider, {})
        if preset.get("base_url"):
            self.base_url_input.setText(preset["base_url"])
        if preset.get("model"):
            self.model_input.setText(preset["model"])
        self.status_label.setText("")

    def _test_connection(self):
        api_key = self.api_key_input.text().strip()
        base_url = self.base_url_input.text().strip()
        model = self.model_input.text().strip()

        if not api_key or not model:
            self.status_label.setStyleSheet("color: orange")
            self.status_label.setText("请先填写 API Key 和模型名称")
            return

        self.test_btn.setEnabled(False)
        self.test_btn.setText("验证中...")
        self.status_label.setStyleSheet("")
        self.status_label.setText("")

        logger.info(f"[设置] 用户发起连接验证 provider={self.provider_combo.currentText()}")

        self._test_worker = TestWorker(api_key, base_url, model)
        self._test_worker.finished.connect(self._on_test_finished)
        self._test_worker.start()

    def _on_test_finished(self, ok: bool, msg: str):
        self.test_btn.setEnabled(True)
        self.test_btn.setText("验证连接")
        if ok:
            self.status_label.setStyleSheet("color: green")
            self.status_label.setText(f"✓ {msg}")
        else:
            self.status_label.setStyleSheet("color: red")
            self.status_label.setText(f"✗ {msg}")

    def _save_settings(self):
        settings = {
            "provider": self.provider_combo.currentText(),
            "api_key": self.api_key_input.text(),
            "base_url": self.base_url_input.text(),
            "model": self.model_input.text(),
            "scene": self.scene_input.text()
        }
        for k, v in settings.items():
            self.db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (k, v))

        logger.info(
            f"[设置] 保存配置 provider={settings['provider']} "
            f"model={settings['model']} scene={settings['scene']!r}"
        )

        QMessageBox.information(self, "成功", "设置已保存！")
        self.settings_saved.emit()
        self.hide()

    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择文档", "",
            "文档文件 (*.pdf *.docx *.doc)"
        )
        if path:
            self.file_path_input.setText(path)
            self.doc_status_label.setText("")

    def _import_doc(self):
        file_path = self.file_path_input.text().strip()
        if not file_path:
            self.doc_status_label.setStyleSheet("color: orange")
            self.doc_status_label.setText("请先选择文件")
            return

        res = self.db.fetch_all("SELECT key, value FROM settings")
        s = {k: v for k, v in res}
        if not s.get("api_key") or not s.get("model"):
            self.doc_status_label.setStyleSheet("color: orange")
            self.doc_status_label.setText("请先保存 API Key 和模型配置")
            return

        self.doc_import_btn.setEnabled(False)
        self.doc_import_btn.setText("生成中…")
        self.doc_status_label.setStyleSheet("")
        self.doc_status_label.setText("")

        logger.info(f"[设置] 启动文档导入 file={file_path!r} count={self.doc_count_input.value()}")

        self._doc_worker = DocGeneratorWorker(
            s["api_key"], s.get("base_url", ""), s.get("model", ""),
            file_path, self.doc_count_input.value()
        )
        self._doc_worker.finished.connect(self._on_doc_finished)
        self._doc_worker.start()

    def _on_doc_finished(self, words, error_msg):
        self.doc_import_btn.setEnabled(True)
        self.doc_import_btn.setText("导入并生成单词")
        if error_msg:
            self.doc_status_label.setStyleSheet("color: red")
            self.doc_status_label.setText(f"✗ {error_msg}")
            logger.error(f"[设置] 文档导入失败: {error_msg}")
        elif not words:
            self.doc_status_label.setStyleSheet("color: orange")
            self.doc_status_label.setText("未生成任何单词，请检查文件内容或 API 配置")
        else:
            self.doc_status_label.setStyleSheet("color: green")
            self.doc_status_label.setText(f"✓ 已生成 {len(words)} 个单词")
            logger.info(f"[设置] 文档导入成功，共 {len(words)} 个单词")
            self.doc_words_ready.emit(words)

    def _load_settings(self):
        res = self.db.fetch_all("SELECT key, value FROM settings")
        settings = {k: v for k, v in res}
        if "provider" in settings:
            index = self.provider_combo.findText(settings["provider"])
            if index >= 0:
                self.provider_combo.blockSignals(True)
                self.provider_combo.setCurrentIndex(index)
                self.provider_combo.blockSignals(False)
        self.api_key_input.setText(settings.get("api_key", ""))
        self.base_url_input.setText(settings.get("base_url", ""))
        self.model_input.setText(settings.get("model", ""))
        self.scene_input.setText(settings.get("scene", "日常口语"))
