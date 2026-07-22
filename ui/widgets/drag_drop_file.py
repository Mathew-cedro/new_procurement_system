import os
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QFileDialog
from PySide6.QtCore import Qt, Signal

class DragDropFileWidget(QFrame):
    file_selected = Signal(str)
    
    def __init__(self, placeholder_text="📁 Drag & Drop PDF here or Click to Browse", parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.file_path = ""
        self.placeholder_text = placeholder_text
        
        self.setMinimumHeight(55)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(10, 5, 10, 5)
        
        self.lbl_info = QLabel(self.placeholder_text)
        self.lbl_info.setAlignment(Qt.AlignCenter)
        
        self.btn_browse = QPushButton("Browse...")
        self.btn_browse.setFixedWidth(80)
        self.btn_browse.clicked.connect(self.open_file_dialog)
        
        self.btn_clear = QPushButton("❌")
        self.btn_clear.setFixedWidth(30)
        self.btn_clear.setToolTip("Clear file")
        self.btn_clear.setVisible(False)
        self.btn_clear.clicked.connect(self.clear_file)
        
        self.layout.addWidget(self.lbl_info, stretch=1)
        self.layout.addWidget(self.btn_browse)
        self.layout.addWidget(self.btn_clear)
        
        self.update_style(is_dragged=False)
        
    def update_style(self, is_dragged=False):
        import database as database_config
        theme = database_config.get_theme_setting()
        
        bg_col = "#0284c7" if is_dragged else ("#ffffff" if theme == "light" else "#1e1e24")
        border_col = "#0284c7" if is_dragged else ("#cbd5e1" if theme == "light" else "#3a3a4a")
        text_col = "#ffffff" if is_dragged else ("#0f172a" if theme == "light" else "#a0a0b0")
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_col};
                border: 2px dashed {border_col};
                border-radius: 6px;
            }}
            QLabel {{
                color: {text_col};
                font-size: 11px;
                border: none;
                background: transparent;
            }}
            QPushButton {{
                background-color: {"#0284c7" if theme == "light" else "#2b2b36"};
                color: #ffffff;
                border: 1px solid {"#0284c7" if theme == "light" else "#3a3a4a"};
                border-radius: 4px;
                padding: 4px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {"#0369a1" if theme == "light" else "#323242"};
            }}
        """)

    def set_file_path(self, path):
        self.file_path = path or ""
        if self.file_path:
            filename = os.path.basename(self.file_path)
            self.lbl_info.setText(f"📄 {filename}")
            self.lbl_info.setToolTip(self.file_path)
            self.btn_clear.setVisible(True)
        else:
            self.lbl_info.setText(self.placeholder_text)
            self.lbl_info.setToolTip("")
            self.btn_clear.setVisible(False)
        self.file_selected.emit(self.file_path)

    def get_file_path(self):
        return self.file_path

    def clear_file(self):
        self.set_file_path("")

    def open_file_dialog(self):
        filePath, _ = QFileDialog.getOpenFileName(
            self, "Select PDF Document", "", "PDF Files (*.pdf);;All Files (*)"
        )
        if filePath:
            self.set_file_path(filePath)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if any(u.toLocalFile().lower().endswith(".pdf") for u in urls):
                event.acceptProposedAction()
                self.update_style(is_dragged=True)
                return
        event.ignore()

    def dragLeaveEvent(self, event):
        self.update_style(is_dragged=False)

    def dropEvent(self, event):
        self.update_style(is_dragged=False)
        urls = event.mimeData().urls()
        for u in urls:
            path = u.toLocalFile()
            if path.lower().endswith(".pdf"):
                self.set_file_path(path)
                event.acceptProposedAction()
                break
