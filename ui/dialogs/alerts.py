from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, 
    QListWidgetItem, QPushButton, QFrame
)
from PySide6.QtCore import Qt
import database as database_config

class AlertsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔔 System Alerts & Expiry Notifications")
        self.resize(700, 500)
        
        theme = database_config.get_theme_setting()
        if theme == "light":
            self.setStyleSheet("QDialog { background-color: #f1f5f9; color: #0f172a; }")
        else:
            self.setStyleSheet("QDialog { background-color: #1e1e24; color: #ffffff; }")
            
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        lbl_title = QLabel("🔔 Upcoming Deadlines & Warranty Expirations")
        lbl_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(lbl_title)
        
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                border: 1px solid #3a3a4a;
                border-radius: 6px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 10px;
                margin-bottom: 5px;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.list_widget)
        
        self.refresh_alerts()
        
        btn_close = QPushButton("Close")
        btn_close.setFixedWidth(100)
        btn_close.clicked.connect(self.accept)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)

    def refresh_alerts(self):
        self.list_widget.clear()
        alerts = database_config.get_upcoming_alerts(days=90)
        
        if not alerts:
            item = QListWidgetItem("✅ No upcoming deadlines or warranty expirations within 90 days!")
            self.list_widget.addItem(item)
            return
            
        for a in alerts:
            sev = a.get("severity")
            icon = "🔴" if sev == "urgent" else ("🟠" if sev == "warning" else "🔵")
            days = a.get("days_remaining", 0)
            
            if days < 0:
                time_str = f"OVERDUE by {abs(days)} day(s)!"
            elif days == 0:
                time_str = "DUE TODAY!"
            else:
                time_str = f"in {days} day(s) ({a.get('date')})"
                
            text = f"{icon} [{a.get('type').upper()}] {a.get('title')}\n   Project: {a.get('project_name')} | {time_str}"
            
            item = QListWidgetItem(text)
            self.list_widget.addItem(item)
