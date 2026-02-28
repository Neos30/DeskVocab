from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QPushButton,
    QLabel, QComboBox, QMessageBox, QHBoxLayout, QSpinBox,
    QFileDialog, QFrame, QGroupBox
)
from PyQt6.QtCore import pyqtSignal, QThread
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


class SceneGeneratorWorker(QThread):
    """后台线程：场景生成单词"""
    finished = pyqtSignal(list, str)   # (words, error_or_scene)

    def __init__(self, api_key, base_url, model, scene, count):
        super().__init__()
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.scene = scene
        self.count = count

    def run(self):
        try:
            gen = AIGenerator(self.api_key, self.base_url, self.model)
            words = gen.generate_words(self.scene, self.count)
            self.finished.emit(words, self.scene)
        except Exception as e:
            self.finished.emit([], str(e))


class SettingsWin(QWidget):
    settings_saved = pyqtSignal()
    doc_words_ready = pyqtSignal(list)
    scene_words_ready = pyqtSignal(list, str)   # (words, scene)

    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self._test_worker = None
        self._doc_worker = None
        self._scene_worker = None
        self._config_saved = False
        self._init_ui()
        self._load_settings()

    # ─────────────────────────────────────────────────────────────
    # UI 初始化
    # ─────────────────────────────────────────────────────────────
    def _init_ui(self):
        self.setWindowTitle("SpeedDic 设置")
        self.setMinimumWidth(440)

        layout = QVBoxLayout()
        layout.setSpacing(12)

        layout.addWidget(self._build_model_config_group())
        layout.addWidget(self._build_scene_gen_group())
        layout.addWidget(self._build_doc_gen_group())

        self.setLayout(layout)
        self.adjustSize()

    def _build_model_config_group(self) -> QGroupBox:
        """区块 A：模型配置"""
        group = QGroupBox("模型配置")
        v = QVBoxLayout()

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

        v.addLayout(form)

        self.test_btn = QPushButton("验证连接")
        self.test_btn.clicked.connect(self._test_connection)
        v.addWidget(self.test_btn)

        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        v.addWidget(self.status_label)

        self.save_config_btn = QPushButton("保存模型配置")
        self.save_config_btn.clicked.connect(self._save_model_config)
        v.addWidget(self.save_config_btn)

        group.setLayout(v)
        return group

    def _build_scene_gen_group(self) -> QGroupBox:
        """区块 B：选择场景生成新词"""
        group = QGroupBox("选择场景生成新词")
        v = QVBoxLayout()

        form = QFormLayout()

        self.scene_input = QLineEdit()
        self.scene_input.setPlaceholderText("如：互联网架构, 雅思核心词")
        form.addRow("当前场景:", self.scene_input)

        self.scene_count_input = QSpinBox()
        self.scene_count_input.setRange(5, 30)
        self.scene_count_input.setValue(10)
        form.addRow("生成数量:", self.scene_count_input)

        v.addLayout(form)

        self.scene_gen_btn = QPushButton("生成新词")
        self.scene_gen_btn.clicked.connect(self._generate_by_scene)
        v.addWidget(self.scene_gen_btn)

        self.scene_status_label = QLabel("")
        self.scene_status_label.setWordWrap(True)
        v.addWidget(self.scene_status_label)

        group.setLayout(v)
        return group

    def _build_doc_gen_group(self) -> QGroupBox:
        """区块 C：导入文档生成新词"""
        group = QGroupBox("导入文档生成新词")
        v = QVBoxLayout()

        doc_form = QFormLayout()

        file_row = QHBoxLayout()
        self.file_path_input = QLineEdit()
        self.file_path_input.setPlaceholderText("选择 .pdf / .docx / .doc / .txt 文件")
        self.file_path_input.setReadOnly(True)
        self.browse_btn = QPushButton("浏览…")
        self.browse_btn.setFixedWidth(60)
        self.browse_btn.clicked.connect(self._browse_file)
        file_row.addWidget(self.file_path_input)
        file_row.addWidget(self.browse_btn)
        doc_form.addRow("文件:", file_row)

        self.doc_count_input = QSpinBox()
        self.doc_count_input.setRange(5, 30)
        self.doc_count_input.setValue(10)
        doc_form.addRow("生成数量:", self.doc_count_input)

        v.addLayout(doc_form)

        self.doc_import_btn = QPushButton("导入并生成单词")
        self.doc_import_btn.clicked.connect(self._import_doc)
        v.addWidget(self.doc_import_btn)

        self.doc_status_label = QLabel("")
        self.doc_status_label.setWordWrap(True)
        v.addWidget(self.doc_status_label)

        group.setLayout(v)
        return group

    # ─────────────────────────────────────────────────────────────
    # 状态管理
    # ─────────────────────────────────────────────────────────────
    def _update_gen_buttons_state(self):
        """根据 _config_saved 启用或禁用区块 B / C 的所有交互控件。"""
        enabled = self._config_saved
        for w in (
            self.scene_input, self.scene_count_input, self.scene_gen_btn,
            self.file_path_input, self.browse_btn,
            self.doc_count_input, self.doc_import_btn,
        ):
            w.setEnabled(enabled)

        if not enabled:
            self.scene_status_label.setStyleSheet("color: gray")
            self.scene_status_label.setText("请先保存模型配置")
            self.doc_status_label.setStyleSheet("color: gray")
            self.doc_status_label.setText("请先保存模型配置")
        else:
            # 清除提示，保留已有的成功/错误状态
            if self.scene_status_label.text() == "请先保存模型配置":
                self.scene_status_label.setText("")
            if self.doc_status_label.text() == "请先保存模型配置":
                self.doc_status_label.setText("")

    # ─────────────────────────────────────────────────────────────
    # 区块 A 操作
    # ─────────────────────────────────────────────────────────────
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

    def _save_model_config(self):
        api_key = self.api_key_input.text().strip()
        model = self.model_input.text().strip()
        if not api_key or not model:
            self.status_label.setStyleSheet("color: orange")
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
            f"[设置] 保存模型配置 provider={settings['provider']} model={settings['model']}"
        )

        self._config_saved = True
        self._update_gen_buttons_state()
        self.status_label.setStyleSheet("color: green")
        self.status_label.setText("✓ 模型配置已保存")
        self.settings_saved.emit()

    # ─────────────────────────────────────────────────────────────
    # 区块 B 操作
    # ─────────────────────────────────────────────────────────────
    def _generate_by_scene(self):
        scene = self.scene_input.text().strip()
        if not scene:
            self.scene_status_label.setStyleSheet("color: orange")
            self.scene_status_label.setText("请填写场景关键词")
            return

        # 保存 scene 到 DB
        self.db.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", ("scene", scene)
        )

        self.scene_gen_btn.setEnabled(False)
        self.scene_gen_btn.setText("生成中…")
        self.scene_status_label.setStyleSheet("")
        self.scene_status_label.setText("")

        res = self.db.fetch_all("SELECT key, value FROM settings")
        s = {k: v for k, v in res}

        logger.info(f"[设置] 启动场景生成 scene={scene!r} count={self.scene_count_input.value()}")

        self._scene_worker = SceneGeneratorWorker(
            s["api_key"], s.get("base_url", ""), s.get("model", ""),
            scene, self.scene_count_input.value()
        )
        self._scene_worker.finished.connect(self._on_scene_finished)
        self._scene_worker.start()

    def _on_scene_finished(self, words, scene_or_err):
        self.scene_gen_btn.setEnabled(True)
        self.scene_gen_btn.setText("生成新词")
        if not words:
            self.scene_status_label.setStyleSheet("color: red")
            self.scene_status_label.setText(f"✗ 生成失败：{scene_or_err}")
            logger.error(f"[设置] 场景生成失败: {scene_or_err}")
        else:
            self.scene_status_label.setStyleSheet("color: green")
            self.scene_status_label.setText(f"✓ 已生成 {len(words)} 个单词")
            logger.info(f"[设置] 场景生成成功，共 {len(words)} 个单词")
            self.scene_words_ready.emit(words, scene_or_err)

    # ─────────────────────────────────────────────────────────────
    # 区块 C 操作
    # ─────────────────────────────────────────────────────────────
    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择文档", "",
            "文档文件 (*.pdf *.docx *.doc *.txt)"
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

    # ─────────────────────────────────────────────────────────────
    # 初始化加载
    # ─────────────────────────────────────────────────────────────
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

        # 存量用户：已有配置直接解锁生成区块
        if settings.get("api_key") and settings.get("model"):
            self._config_saved = True

        self._update_gen_buttons_state()
