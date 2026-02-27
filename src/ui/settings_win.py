from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QLabel, QComboBox, QMessageBox
from PyQt6.QtCore import pyqtSignal

class SettingsWin(QWidget):
    settings_saved = pyqtSignal()

    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self._init_ui()
        self._load_settings()

    def _init_ui(self):
        self.setWindowTitle("SpeedDic 设置")
        self.setFixedSize(400, 350)
        layout = QVBoxLayout()

        self.form = QFormLayout()
        
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["DeepSeek", "OpenAI", "Kimi", "Qwen", "GLM", "Custom"])
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

        self.save_btn = QPushButton("保存设置并生成新词")
        self.save_btn.clicked.connect(self._save_settings)
        layout.addWidget(self.save_btn)

        self.setLayout(layout)

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
        
        QMessageBox.information(self, "成功", "设置已保存！")
        self.settings_saved.emit()
        self.hide()

    def _load_settings(self):
        res = self.db.fetch_all("SELECT key, value FROM settings")
        settings = {k: v for k, v in res}
        if "provider" in settings:
            index = self.provider_combo.findText(settings["provider"])
            self.provider_combo.setCurrentIndex(index)
        self.api_key_input.setText(settings.get("api_key", ""))
        self.base_url_input.setText(settings.get("base_url", ""))
        self.model_input.setText(settings.get("model", ""))
        self.scene_input.setText(settings.get("scene", "日常口语"))
