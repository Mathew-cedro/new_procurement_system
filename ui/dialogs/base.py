import sys
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QDoubleSpinBox, QSpinBox, QDateEdit, QCheckBox, QPushButton,
    QFormLayout, QMessageBox, QFrame, QGroupBox, QRadioButton, QButtonGroup,
    QScrollArea, QWidget, QFileDialog
)
from PySide6.QtCore import Qt, QDate
import database as database_config

# Styling helper for form inputs
INPUT_STYLE = """
    QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {
        background-color: #2b2b36;
        color: #ffffff;
        border: 1px solid #3a3a4a;
        border-radius: 4px;
        padding: 6px;
        font-size: 12px;
    }
    QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
        border: 1px solid #00ffcc;
    }
    QLabel {
        color: #ffffff;
        font-size: 12px;
        font-weight: bold;
    }
    QCheckBox {
        color: #ffffff;
        font-size: 12px;
    }
    QRadioButton {
        color: #ffffff;
        font-size: 12px;
    }
"""

BUTTON_SUBMIT_STYLE = """
    QPushButton {
        background-color: #00ffcc;
        color: #13131a;
        font-weight: bold;
        border-radius: 4px;
        padding: 8px 16px;
        font-size: 12px;
    }
    QPushButton:hover {
        background-color: #00ccaa;
    }
"""

BUTTON_CANCEL_STYLE = """
    QPushButton {
        background-color: transparent;
        color: #ff6666;
        border: 1px solid #ff6666;
        border-radius: 4px;
        padding: 8px 16px;
        font-size: 12px;
    }
    QPushButton:hover {
        background-color: #3a1a1a;
    }
"""

class BaseFormDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint)
        theme = database_config.get_theme_setting()
        if theme == "light":
            self.setStyleSheet("""
                QDialog { background-color: #f1f5f9; color: #0f172a; }
                QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {
                    background-color: #ffffff; color: #0f172a; border: 1px solid #cbd5e1;
                    border-radius: 4px; padding: 6px; font-size: 12px;
                }
                QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
                    border: 1px solid #0284c7;
                }
                QLabel { color: #0f172a; font-size: 12px; font-weight: bold; }
                QCheckBox, QRadioButton { color: #0f172a; font-size: 12px; }
            """)
        else:
            self.setStyleSheet(f"QDialog {{ background-color: #1e1e24; color: #ffffff; }} {INPUT_STYLE}")
        
    def set_field_validation(self, widget, is_valid):
        cls_name = widget.metaObject().className()
        theme = database_config.get_theme_setting()
        accent_color = "#0284c7" if theme == "light" else "#00ffcc"
        bg_valid = "#ffffff" if theme == "light" else "#2b2b36"
        bg_invalid = "#fef2f2" if theme == "light" else "#3b2a2a"
        if is_valid:
            widget.setStyleSheet(f"{cls_name} {{ border: 1px solid {accent_color}; background-color: {bg_valid}; }}")
        else:
            widget.setStyleSheet(f"{cls_name} {{ border: 1px solid #ff4d4d; background-color: {bg_invalid}; }}")
            
    def clear_field_validation(self, widget):
        cls_name = widget.metaObject().className()
        theme = database_config.get_theme_setting()
        border_color = "#cbd5e1" if theme == "light" else "#3a3a4a"
        bg_color = "#ffffff" if theme == "light" else "#2b2b36"
        widget.setStyleSheet(f"{cls_name} {{ border: 1px solid {border_color}; background-color: {bg_color}; }}")

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            focus_w = self.focusWidget()
            if focus_w:
                if event.modifiers() & Qt.ControlModifier or not focus_w.inherits("QTextEdit"):
                    self.submit_data()
                    event.accept()
                    return
        super().keyPressEvent(event)

    def validate_inputs(self):
        return True
    
# Creates the whole windows for adding information
