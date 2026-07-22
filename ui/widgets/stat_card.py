from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

class StatCard(QFrame):
    """A custom widget representing a metric card."""
    def __init__(self, title, value, color_hex):
        super().__init__()
        self.color_hex = color_hex
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #2b2b36;
                border: 1px solid #3a3a4a;
                border-radius: 8px;
                padding: 15px;
            }}
        """)
        layout = QVBoxLayout(self)
        
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("color: #a0a0b0; font-size: 12px; font-weight: bold;")
        
        self.val_label = QLabel(value)
        self.val_label.setStyleSheet(f"color: {color_hex}; font-size: 22px; font-weight: bold;")
        
        layout.addWidget(self.title_label)
        layout.addWidget(self.val_label)

    def update_value(self, value):
        self.val_label.setText(value)

    def update_theme(self, theme="dark", color_hex=None):
        if color_hex:
            self.color_hex = color_hex
        if theme == "light":
            self.setStyleSheet("""
                QFrame {
                    background-color: #ffffff;
                    border: 1px solid #dbe2ea;
                    border-radius: 8px;
                    padding: 15px;
                }
            """)
            self.title_label.setStyleSheet("color: #526075; font-size: 11px; font-weight: bold; border: none; background: transparent;")
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: #182238;
                    border: 1px solid #253454;
                    border-radius: 8px;
                    padding: 15px;
                }
            """)
            self.title_label.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: bold; border: none; background: transparent;")
        self.val_label.setStyleSheet(f"color: {self.color_hex}; font-size: 22px; font-weight: bold; border: none; background: transparent;")
