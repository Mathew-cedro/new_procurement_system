from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
    QTableWidgetItem, QPushButton, QHeaderView, QCheckBox
)
from PySide6.QtCore import Qt
import database as database_config

class SyncConflictDialog(QDialog):
    def __init__(self, conflicts, parent=None):
        super().__init__(parent)
        self.conflicts = conflicts # List of dicts: {table, record_id, field, local_val, online_val, choice}
        self.setWindowTitle("⚖️ Sync Conflict Resolver - Google Sheets vs Local SQLite")
        self.resize(850, 500)
        
        theme = database_config.get_theme_setting()
        if theme == "light":
            self.setStyleSheet("QDialog { background-color: #f1f5f9; color: #0f172a; }")
        else:
            self.setStyleSheet("QDialog { background-color: #1e1e24; color: #ffffff; }")
            
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        lbl_header = QLabel("The following fields have different values online in Google Sheets vs your local database. Choose which version to keep:")
        lbl_header.setWordWrap(True)
        lbl_header.setStyleSheet("font-size: 13px; font-weight: bold;")
        layout.addWidget(lbl_header)
        
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(5)
        self.table_widget.setHorizontalHeaderLabels(["Table & Record ID", "Field", "Local (SQLite)", "Online (Google Sheets)", "Action"])
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        self.populate_table()
        layout.addWidget(self.table_widget)
        
        # Bottom controls
        btn_layout = QHBoxLayout()
        self.btn_keep_all_local = QPushButton("Keep All Local")
        self.btn_accept_all_online = QPushButton("Accept All Online")
        self.btn_apply = QPushButton("Apply Selected Resolutions")
        self.btn_apply.setStyleSheet("background-color: #0284c7; color: #ffffff; font-weight: bold; padding: 6px 15px; border-radius: 4px;")
        
        self.btn_keep_all_local.clicked.connect(self.keep_all_local)
        self.btn_accept_all_online.clicked.connect(self.accept_all_online)
        self.btn_apply.clicked.connect(self.accept)
        
        btn_layout.addWidget(self.btn_keep_all_local)
        btn_layout.addWidget(self.btn_accept_all_online)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_apply)
        
        layout.addLayout(btn_layout)
        
    def populate_table(self):
        self.table_widget.setRowCount(len(self.conflicts))
        for row, c in enumerate(self.conflicts):
            self.table_widget.setItem(row, 0, QTableWidgetItem(f"{c['table']} (#{c['record_id']})"))
            self.table_widget.setItem(row, 1, QTableWidgetItem(c['field']))
            self.table_widget.setItem(row, 2, QTableWidgetItem(str(c['local_val'])))
            self.table_widget.setItem(row, 3, QTableWidgetItem(str(c['online_val'])))
            
            cb = QCheckBox("Accept Online")
            cb.setChecked(c.get("choice") == "online")
            cb.toggled.connect(lambda checked, idx=row: self.update_choice(idx, checked))
            self.table_widget.setCellWidget(row, 4, cb)
            
    def update_choice(self, idx, accept_online):
        self.conflicts[idx]["choice"] = "online" if accept_online else "local"

    def keep_all_local(self):
        for i in range(len(self.conflicts)):
            self.conflicts[i]["choice"] = "local"
            widget = self.table_widget.cellWidget(i, 4)
            if isinstance(widget, QCheckBox):
                widget.setChecked(False)

    def accept_all_online(self):
        for i in range(len(self.conflicts)):
            self.conflicts[i]["choice"] = "online"
            widget = self.table_widget.cellWidget(i, 4)
            if isinstance(widget, QCheckBox):
                widget.setChecked(True)

    def get_resolved_conflicts(self):
        return self.conflicts
