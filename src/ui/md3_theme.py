from PyQt6.QtWidgets import QWidget


def apply_md3_theme(widget: QWidget) -> None:
    """Apply Material Design 3 dark theme QSS to a widget."""
    widget.setStyleSheet("""
        QWidget {
            background-color: #1C1B1F;
            color: #E6E1E5;
        }
        QPushButton {
            background-color: #006AFF;
            color: white;
            border: none;
            border-radius: 20px;
            padding: 8px 24px;
            font-size: 13px;
        }
        QPushButton:hover {
            background-color: #1A79FF;
        }
        QPushButton:pressed {
            background-color: #0055CC;
        }
        QPushButton:disabled {
            background-color: #2E2D33;
            color: #5A5966;
        }
        QLineEdit {
            border: 1px solid #938F99;
            border-radius: 4px;
            padding: 6px 10px;
            background-color: #1C1B1F;
            color: #E6E1E5;
        }
        QLineEdit:focus {
            border: 2px solid #006AFF;
        }
        QComboBox {
            border: 1px solid #938F99;
            border-radius: 4px;
            padding: 6px 10px;
            background-color: #1C1B1F;
            color: #E6E1E5;
        }
        QComboBox:focus {
            border: 2px solid #006AFF;
        }
        QComboBox::drop-down {
            border: none;
            width: 20px;
        }
        QComboBox QAbstractItemView {
            background-color: #211F26;
            color: #E6E1E5;
            selection-background-color: #006AFF;
            border: 1px solid #938F99;
        }
        QGroupBox {
            background-color: #211F26;
            border-radius: 12px;
            border: 1px solid #3A3740;
            margin-top: 12px;
            padding-top: 16px;
            font-size: 13px;
            font-weight: bold;
            color: #E6E1E5;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 4px;
            color: #CAC4D0;
        }
        QLabel {
            color: #E6E1E5;
            background-color: transparent;
        }
        QSpinBox {
            border: 1px solid #938F99;
            border-radius: 4px;
            padding: 6px 10px;
            background-color: #1C1B1F;
            color: #E6E1E5;
        }
        QScrollBar:vertical {
            background: transparent;
            width: 6px;
        }
        QScrollBar::handle:vertical {
            background: #938F99;
            border-radius: 3px;
            min-height: 20px;
        }
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {
            height: 0;
        }
    """)
