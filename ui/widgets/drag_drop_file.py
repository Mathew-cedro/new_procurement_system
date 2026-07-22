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
        
        bg_col = "#002C76" if is_dragged else ("#F4F6F9" if theme == "light" else "#182238")
        border_col = "#FFDE15" if is_dragged else ("#cbd5e1" if theme == "light" else "#253454")
        text_col = "#ffffff" if is_dragged else ("#10182B" if theme == "light" else "#94a3b8")
        
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
                background-color: {"#002C76" if theme == "light" else "#002C76"};
                color: #ffffff;
                border: 1px solid #1a428a;
                border-radius: 4px;
                padding: 4px;
                font-size: 11px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #003896;
            }}
        """)

    def set_file_path(self, path):
        self.file_path = path
        if path:
            filename = os.path.basename(path)
            self.lbl_info.setText(f"📄 {filename}")
            self.lbl_info.setStyleSheet("color: #1F9D55; font-weight: bold; font-size: 11px;")
            self.btn_clear.setVisible(True)
        else:
            self.lbl_info.setText(self.placeholder_text)
            self.btn_clear.setVisible(False)
            self.update_style(is_dragged=False)
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
