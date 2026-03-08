from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QLabel, QComboBox
)
from PyQt6.QtCore import pyqtSignal, QThread
from src.core.ai_generator import AIGenerator
from src.utils.logger import get_logger
from src.ui.md3_theme import apply_md3_theme

logger = get_logger()

PROVIDER_PRESETS = {
    "DeepSeek": {"base_url": "https://api.deepseek.com",                              "model": "deepseek-chat"},
    "OpenAI":   {"base_url": "https://api.openai.com/v1",                             "model": "gpt-4o-mini"},
    "Kimi":     {"base_url": "https://api.moonshot.cn/v1",                            "model": "moonshot-v1-8k"},
    "Qwen":     {"base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",     "model": "qwen-plus"},
    "GLM":      {"base_url": "https://open.bigmodel.cn/api/paas/v4",                  "model": "glm-4-flash"},
    "Custom":   {"base_url": "",                                                       "model": ""},
}


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


class ModelConfigDialog(QDialog):
    settings_saved = pyqtSignal()

    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self._test_worker = None
        self._init_ui()
        self._load_settings()
        apply_md3_theme(self)

    def _init_ui(self):
        self.setWindowTitle("模型配置")
        self.setMinimumWidth(420)

        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        form = QFormLayout()

        self.provider_combo = QComboBox()
        self.provider_combo.addItems(list(PROVIDER_PRESETS.keys()))
        self.provider_combo.currentTextChanged.connect(self._on_provider_changed)
        form.addRow("AI 提供商:", self.provider_combo)

        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("API Key:", self.api_key_input)

        self.base_url_input = QLineEdit()
        self.base_url_input.setPlaceholderText("https://api.deepseek.com")
        form.addRow("Base URL:", self.base_url_input)

        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("deepseek-chat")
        form.addRow("模型名称:", self.model_input)

        layout.addLayout(form)

        self.test_btn = QPushButton("验证连接")
        self.test_btn.clicked.connect(self._test_connection)
        layout.addWidget(self.test_btn)

        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        self.save_btn = QPushButton("保存模型配置")
        self.save_btn.clicked.connect(self._save_model_config)
        layout.addWidget(self.save_btn)

        self.setLayout(layout)
        self.adjustSize()

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
            self.status_label.setStyleSheet("color: #FFB951")
            self.status_label.setText("请先填写 API Key 和模型名称")
            return

        self.test_btn.setEnabled(False)
        self.test_btn.setText("验证中...")
        self.status_label.setStyleSheet("")
        self.status_label.setText("")

        logger.info(f"[模型配置] 用户发起连接验证 provider={self.provider_combo.currentText()}")

        self._test_worker = TestWorker(api_key, base_url, model)
        self._test_worker.finished.connect(self._on_test_finished)
        self._test_worker.start()

    def _on_test_finished(self, ok: bool, msg: str):
        self.test_btn.setEnabled(True)
        self.test_btn.setText("验证连接")
        if ok:
            self.status_label.setStyleSheet("color: #69DC9E")
            self.status_label.setText(f"✓ {msg}")
        else:
            self.status_label.setStyleSheet("color: #CF6679")
            self.status_label.setText(f"✗ {msg}")

    def _save_model_config(self):
        api_key = self.api_key_input.text().strip()
        model = self.model_input.text().strip()
        if not api_key or not model:
            self.status_label.setStyleSheet("color: #FFB951")
            self.status_label.setText("API Key 和模型名称不能为空")
            return

        settings = {
            "provider": self.provider_combo.currentText(),
            "api_key":  self.api_key_input.text(),
            "base_url": self.base_url_input.text(),
            "model":    model,
        }
        for k, v in settings.items():
            self.db.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (k, v)
            )

        logger.info(
            f"[模型配置] 保存配置 provider={settings['provider']} model={settings['model']}"
        )

        self.status_label.setStyleSheet("color: #69DC9E")
        self.status_label.setText("✓ 模型配置已保存")
        self.settings_saved.emit()

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
