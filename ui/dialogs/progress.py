from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar
from PySide6.QtCore import Qt
import database as database_config

class SyncProgressDialog(QDialog):
    def __init__(self, title="Synchronizing Data...", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(480, 160)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowCloseButtonHint)
        
        theme = database_config.get_theme_setting()
        if theme == "light":
            self.setStyleSheet("QDialog { background-color: #ffffff; color: #0f172a; }")
        else:
            self.setStyleSheet("QDialog { background-color: #1e1e24; color: #ffffff; }")
            
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        self.lbl_status = QLabel("Initializing background synchronization...")
        self.lbl_status.setStyleSheet("font-size: 13px; font-weight: bold;")
        self.lbl_status.setWordWrap(True)
        layout.addWidget(self.lbl_status)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        
        bar_bg = "#f1f5f9" if theme == "light" else "#2b2b36"
        border_col = "#cbd5e1" if theme == "light" else "#3a3a4a"
        text_col = "#0f172a" if theme == "light" else "#ffffff"
        
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {bar_bg};
                border: 1px solid {border_col};
                border-radius: 6px;
                text-align: center;
                height: 24px;
                font-weight: bold;
                color: {text_col};
            }}
            QProgressBar::chunk {{
                background-color: #002C76;
                border-radius: 5px;
            }}
        """)
        layout.addWidget(self.progress_bar)
        
    def update_progress(self, percent, status_text):
        self.progress_bar.setValue(percent)
        self.lbl_status.setText(status_text)
