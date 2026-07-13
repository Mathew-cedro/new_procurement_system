import sys
import os
from pathlib import Path
from PySide6.QtCore import Qt, QRectF, QDate
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QKeySequence
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, 
    QVBoxLayout, QPushButton, QLabel, QFrame, QStackedWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea,
    QGridLayout, QLineEdit, QMessageBox, QFileDialog, QGroupBox,
    QDialog, QComboBox, QDateEdit, QCheckBox
)

import database_config
import Cardsystem
import excel_export
import form_dialogs


class StatCard(QFrame):
    """A custom widget representing a metric card."""
    def __init__(self, title, value, color_hex):
        super().__init__()
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

class SimpleChart(QWidget):
    """A custom chart widget drawn using QPainter showing project budgets."""
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(250)
        self.data = []
        self.labels = []
        self.load_data()

    def load_data(self):
        try:
            projects = database_config.get_projects()
            if projects:
                # Take up to last 7 projects for display, chronological
                projects = projects[:7]
                projects.reverse()
                self.data = [p.get("abc_amount", 0.0) or 0.0 for p in projects]
                self.labels = [p.get("proj_id_no", "N/A") for p in projects]
            else:
                self.data = [0]
                self.labels = ["None"]
        except Exception as e:
            self.data = [0]
            self.labels = ["Error"]
            print(f"Error loading chart data: {e}")

    def paintEvent(self, event):
        if not self.data:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background grid
        painter.setPen(QPen(QColor("#3a3a4a"), 1, Qt.DashLine))
        for i in range(1, 4):
            y = int(self.height() * (i / 4))
            painter.drawLine(40, y, self.width() - 20, y)
            
        padding = 60
        width_step = (self.width() - padding - 40) / (len(self.data) - 1) if len(self.data) > 1 else self.width() - padding - 40
        points = []
        
        max_val = max(self.data) if max(self.data) > 0 else 1
        
        for i, val in enumerate(self.data):
            x = int(padding + (i * width_step))
            y = int(self.height() - 50 - (val / max_val * (self.height() - 80)))
            points.append((x, y))
            
            # X Labels
            painter.setPen(QColor("#a0a0b0"))
            painter.setFont(QFont("Arial", 8))
            painter.drawText(x - 20, self.height() - 15, self.labels[i])
            
            # Y value label
            painter.setPen(QColor("#00ffcc"))
            painter.setFont(QFont("Arial", 8))
            painter.drawText(x - 20, y - 10, f"₱{val/1000:,.0f}k")

        # Draw the line graph
        painter.setPen(QPen(QColor("#00ffcc"), 3, Qt.SolidLine))
        if len(points) > 1:
            for i in range(len(points) - 1):
                painter.drawLine(points[i][0], points[i][1], points[i+1][0], points[i+1][1])
        else:
            painter.setBrush(QColor("#00ffcc"))
            painter.drawEllipse(points[0][0] - 6, points[0][1] - 6, 12, 12)
            
        # Draw data nodes
        painter.setBrush(QColor("#ffffff"))
        painter.setPen(QPen(QColor("#00ffcc"), 2))
        for pt in points:
            painter.drawEllipse(pt[0] - 4, pt[1] - 4, 8, 8)

class Dashboard(QMainWindow):
    """The main application layout containing the sidebar and stacked views."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Procurement & Payment Tracking Dashboard")
        self.resize(1100, 700)
        self.setStyleSheet("background-color: #1e1e24; color: #ffffff;")
        
        # Central Layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # ---- SIDEBAR ----
        sidebar = QWidget()
        sidebar.setFixedWidth(200)
        sidebar.setStyleSheet("background-color: #13131a; border-right: 1px solid #2b2b36;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(10, 20, 10, 20)
        
        app_title = QLabel("NEXUS PTP")
        app_title.setStyleSheet("""
            font-size: 18px; 
            font-weight: bold; 
            margin-bottom: 20px; 
            color: #00ffcc; 
            padding-left: 10px;
        """)
        sidebar_layout.addWidget(app_title)
        
        self.nav_buttons = []
        nav_items = [
            ("📊 Overview", 0),
            ("🗂️ Project Cards", 1),
            ("👥 Suppliers List", 2),
            ("🛠️ Tools & Export", 3)
        ]
        
        for item, idx in nav_items:
            btn = QPushButton(item)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #a0a0b0;
                    border: none;
                    border-radius: 5px;
                    padding: 10px;
                    text-align: left;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #2b2b36;
                    color: #ffffff;
                }
            """)
            btn.clicked.connect(lambda checked=False, index=idx: self.switch_page(index))
            self.nav_buttons.append(btn)
            sidebar_layout.addWidget(btn)
            
        sidebar_layout.addStretch()
        main_layout.addWidget(sidebar)
        
        # ---- STACKED CONTENT CENTRAL AREA ----
        self.stacked_widget = QStackedWidget()
        
        # Styles
        table_style = """
            QTableWidget {
                background-color: #2b2b36;
                border: 1px solid #3a3a4a;
                border-radius: 8px;
                gridline-color: #3a3a4a;
                color: #ffffff;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #323242;
                color: #00ffcc;
                font-weight: bold;
            }
            QHeaderView::section {
                background-color: #13131a;
                color: #00ffcc;
                padding: 6px;
                border: 1px solid #2b2b36;
                font-weight: bold;
            }
        """
        
        # 1. OVERVIEW PAGE
        overview_page = QWidget()
        overview_page_layout = QVBoxLayout(overview_page)
        overview_page_layout.setContentsMargins(0, 0, 0, 0)
        
        overview_scroll = QScrollArea()
        overview_scroll.setWidgetResizable(True)
        overview_scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        overview_content = QWidget()
        overview_content.setStyleSheet("background-color: transparent;")
        
        overview_layout = QVBoxLayout(overview_content)
        overview_layout.setContentsMargins(30, 20, 30, 30)
        overview_layout.setSpacing(20)
        
        # Header Row
        header_layout = QHBoxLayout()
        header_title = QLabel("System Overview")
        header_title.setStyleSheet("font-size: 24px; font-weight: bold;")
        header_layout.addWidget(header_title)
        header_layout.addStretch()
        
        create_project_btn = QPushButton("➕ Create Project")
        create_project_btn.setStyleSheet("""
            QPushButton {
                background-color: #00ffcc; color: #13131a;
                font-weight: bold; border-radius: 5px; padding: 8px 15px;
            }
            QPushButton:hover { background-color: #00ccaa; }
        """)
        create_project_btn.clicked.connect(self.create_new_project)
        header_layout.addWidget(create_project_btn)
        
        export_btn = QPushButton("📂 Export Data")
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #1f4e78; color: #ffffff;
                font-weight: bold; border-radius: 5px; padding: 8px 15px;
                margin-left: 10px;
            }
            QPushButton:hover { background-color: #1a4063; }
        """)
        export_btn.clicked.connect(self.export_data)
        header_layout.addWidget(export_btn)
        
        refresh_btn = QPushButton("Refresh Data")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a3a4a; color: #ffffff;
                font-weight: bold; border-radius: 5px; padding: 8px 15px;
                border: 1px solid #5a5a6a;
                margin-left: 10px;
            }
            QPushButton:hover { background-color: #4a4a5a; }
        """)
        refresh_btn.clicked.connect(self.refresh_all_data)
        header_layout.addWidget(refresh_btn)
        overview_layout.addLayout(header_layout)
        
        # Stats Cards
        self.cards_layout = QHBoxLayout()
        self.budget_card = StatCard("TOTAL PROCUREMENT BUDGET (ABC)", "₱0.00", "#00ffcc")
        self.awarded_card = StatCard("TOTAL CONTRACT VALUE", "₱0.00", "#33ccff")
        self.paid_card = StatCard("TOTAL DISBURSED (NET)", "₱0.00", "#2ecc71")
        self.cards_layout.addWidget(self.budget_card)
        self.cards_layout.addWidget(self.awarded_card)
        self.cards_layout.addWidget(self.paid_card)
        overview_layout.addLayout(self.cards_layout)
        
        # Middle area: Dynamic Analytics Panels (Timeline Alerts & Financials Leaderboard)
        analytics_layout = QHBoxLayout()
        analytics_layout.setSpacing(20)
        
        # Panel A: Critical Timeline Alerts
        self.alerts_panel = QFrame()
        self.alerts_panel.setObjectName("AlertsPanel")
        self.alerts_panel.setStyleSheet("""
            #AlertsPanel {
                background-color: #2b2b36; border-radius: 8px; border: 1px solid #3a3a4a;
            }
        """)
        alerts_layout = QVBoxLayout(self.alerts_panel)
        alerts_layout.setContentsMargins(15, 15, 15, 15)
        
        alerts_title = QLabel("📢 Critical Timeline & Action Alerts")
        alerts_title.setStyleSheet("color: #00ffcc; font-size: 14px; font-weight: bold; margin-bottom: 8px;")
        alerts_layout.addWidget(alerts_title)
        
        self.alerts_list_layout = QVBoxLayout()
        self.alerts_list_layout.setSpacing(6)
        alerts_layout.addLayout(self.alerts_list_layout)
        alerts_layout.addStretch()
        
        analytics_layout.addWidget(self.alerts_panel, stretch=1)
        
        # Panel B: Financial Savings & Contractor Analytics
        self.stats_panel = QFrame()
        self.stats_panel.setObjectName("StatsPanel")
        self.stats_panel.setStyleSheet("""
            #StatsPanel {
                background-color: #2b2b36; border-radius: 8px; border: 1px solid #3a3a4a;
            }
        """)
        stats_layout = QVBoxLayout(self.stats_panel)
        stats_layout.setContentsMargins(15, 15, 15, 15)
        stats_layout.setSpacing(12)
        
        stats_title = QLabel("📊 Financial Savings & Supplier Directory")
        stats_title.setStyleSheet("color: #00ffcc; font-size: 14px; font-weight: bold;")
        stats_layout.addWidget(stats_title)
        
        # Financial rows layout
        self.savings_lbl = QLabel("Savings Amount: ₱0.00 (0.00%)")
        self.savings_lbl.setStyleSheet("color: #ffffff; font-size: 12px; font-weight: bold;")
        stats_layout.addWidget(self.savings_lbl)
        
        self.balance_lbl = QLabel("Unpaid Contract Balance: ₱0.00")
        self.balance_lbl.setStyleSheet("color: #ffffff; font-size: 12px; font-weight: bold;")
        stats_layout.addWidget(self.balance_lbl)
        
        # Horizontal line spacer
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        sep.setStyleSheet("background-color: #3a3a4a; max-height: 1px; border: none;")
        stats_layout.addWidget(sep)
        
        # Leaderboard title
        leaderboard_title = QLabel("🏆 Top Supplier Leaderboard")
        leaderboard_title.setStyleSheet("color: #00ffcc; font-size: 12px; font-weight: bold;")
        stats_layout.addWidget(leaderboard_title)
        
        self.leaderboard_layout = QVBoxLayout()
        self.leaderboard_layout.setSpacing(4)
        stats_layout.addLayout(self.leaderboard_layout)
        stats_layout.addStretch()
        
        analytics_layout.addWidget(self.stats_panel, stretch=1)
        
        overview_layout.addLayout(analytics_layout)
        
        # Table of Projects
        table_panel = QVBoxLayout()
        
        table_header_layout = QHBoxLayout()
        table_label = QLabel("Active Procurement Projects")
        table_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        table_header_layout.addWidget(table_label)
        table_header_layout.addStretch()
        
        # Overview Filters
        status_lbl = QLabel("Status:")
        status_lbl.setStyleSheet("color: #a0a0b0; font-size: 11px;")
        self.overview_status_filter = QComboBox()
        self.overview_status_filter.addItems(["All Statuses", "Initiated", "Bidding", "Contract Awarded", "Delivering", "Under Warranty"])
        self.overview_status_filter.setStyleSheet("""
            QComboBox {
                background-color: #2b2b36; color: #ffffff; border: 1px solid #3a3a4a;
                border-radius: 4px; padding: 4px 8px; min-width: 120px; font-size: 11px;
            }
        """)
        self.overview_status_filter.currentIndexChanged.connect(self.apply_filters_and_refresh)
        
        div_lbl = QLabel("Division:")
        div_lbl.setStyleSheet("color: #a0a0b0; font-size: 11px; margin-left: 10px;")
        self.overview_division_filter = QComboBox()
        self.overview_division_filter.addItem("All Divisions")
        self.overview_division_filter.setStyleSheet("""
            QComboBox {
                background-color: #2b2b36; color: #ffffff; border: 1px solid #3a3a4a;
                border-radius: 4px; padding: 4px 8px; min-width: 140px; font-size: 11px;
            }
        """)
        self.overview_division_filter.currentIndexChanged.connect(self.apply_filters_and_refresh)
        
        date_lbl = QLabel("Timeline:")
        date_lbl.setStyleSheet("color: #a0a0b0; font-size: 11px; margin-left: 10px;")
        self.overview_date_filter = QComboBox()
        self.overview_date_filter.addItems([
            "All Dates", 
            "Within 24 hours only", 
            "Within a week only", 
            "Within a month only", 
            "Newest First", 
            "Oldest First"
        ])
        self.overview_date_filter.setStyleSheet("""
            QComboBox {
                background-color: #2b2b36; color: #ffffff; border: 1px solid #3a3a4a;
                border-radius: 4px; padding: 4px 8px; min-width: 140px; font-size: 11px;
            }
        """)
        self.overview_date_filter.currentIndexChanged.connect(self.apply_filters_and_refresh)
        
        table_header_layout.addWidget(status_lbl)
        table_header_layout.addWidget(self.overview_status_filter)
        table_header_layout.addWidget(div_lbl)
        table_header_layout.addWidget(self.overview_division_filter)
        table_header_layout.addWidget(date_lbl)
        table_header_layout.addWidget(self.overview_date_filter)
        
        table_panel.addLayout(table_header_layout)
        

        self.project_table = QTableWidget()
        self.project_table.setColumnCount(6)
        self.project_table.setHorizontalHeaderLabels([
            "Project ID", "Project Name", "Bureau/Division", "Focal Person", "ABC Budget", "Status"
        ])
        self.project_table.setStyleSheet(table_style)
        self.project_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.project_table.setSelectionMode(QTableWidget.SingleSelection)
        self.project_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.project_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.project_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch) # Stretch project name
        self.project_table.cellDoubleClicked.connect(self.on_row_double_clicked)
        
        self.project_table.setMinimumHeight(380)
        table_panel.addWidget(self.project_table)
        overview_layout.addLayout(table_panel)
        
        overview_scroll.setWidget(overview_content)
        overview_page_layout.addWidget(overview_scroll)
        
        self.stacked_widget.addWidget(overview_page)
        
        # 2. CARDS PAGE
        cards_page = QWidget()
        cards_page_layout = QVBoxLayout(cards_page)
        cards_page_layout.setContentsMargins(30, 20, 30, 30)
        
        cards_header = QHBoxLayout()
        cards_title = QLabel("Project Progression Cards")
        cards_title.setStyleSheet("font-size: 24px; font-weight: bold;")
        cards_header.addWidget(cards_title)
        cards_header.addStretch()
        
        create_project_btn_cards = QPushButton("➕ Create Project")
        create_project_btn_cards.setStyleSheet("""
            QPushButton {
                background-color: #00ffcc; color: #13131a;
                font-weight: bold; border-radius: 5px; padding: 8px 15px;
                margin-right: 15px;
            }
            QPushButton:hover { background-color: #00ccaa; }
        """)
        create_project_btn_cards.clicked.connect(self.create_new_project)
        cards_header.addWidget(create_project_btn_cards)
        
        export_btn_cards = QPushButton("📂 Export Data")
        export_btn_cards.setStyleSheet("""
            QPushButton {
                background-color: #1f4e78; color: #ffffff;
                font-weight: bold; border-radius: 5px; padding: 8px 15px;
                margin-right: 15px;
            }
            QPushButton:hover { background-color: #1a4063; }
        """)
        export_btn_cards.clicked.connect(self.export_data)
        cards_header.addWidget(export_btn_cards)
        
        # Cards Page Filters
        self.cards_status_filter = QComboBox()
        self.cards_status_filter.addItems(["All Statuses", "Initiated", "Bidding", "Contract Awarded", "Delivering", "Under Warranty"])
        self.cards_status_filter.setStyleSheet("""
            QComboBox {
                background-color: #2b2b36; color: #ffffff; border: 1px solid #3a3a4a;
                border-radius: 4px; padding: 8px; margin-right: 10px; min-width: 120px; font-size: 13px;
            }
        """)
        self.cards_status_filter.currentIndexChanged.connect(self.apply_cards_filters_and_refresh)
        cards_header.addWidget(self.cards_status_filter)
        
        self.cards_division_filter = QComboBox()
        self.cards_division_filter.addItem("All Divisions")
        self.cards_division_filter.setStyleSheet("""
            QComboBox {
                background-color: #2b2b36; color: #ffffff; border: 1px solid #3a3a4a;
                border-radius: 4px; padding: 8px; margin-right: 15px; min-width: 140px; font-size: 13px;
            }
        """)
        self.cards_division_filter.currentIndexChanged.connect(self.apply_cards_filters_and_refresh)
        cards_header.addWidget(self.cards_division_filter)
        
        self.cards_date_filter = QComboBox()
        self.cards_date_filter.addItems([
            "All Dates", 
            "Within 24 hours only", 
            "Within a week only", 
            "Within a month only", 
            "Newest First", 
            "Oldest First"
        ])
        self.cards_date_filter.setStyleSheet("""
            QComboBox {
                background-color: #2b2b36; color: #ffffff; border: 1px solid #3a3a4a;
                border-radius: 4px; padding: 8px; margin-right: 15px; min-width: 140px; font-size: 13px;
            }
        """)
        self.cards_date_filter.currentIndexChanged.connect(self.apply_cards_filters_and_refresh)
        cards_header.addWidget(self.cards_date_filter)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search projects by ID or Name...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #2b2b36;
                color: #ffffff;
                border: 1px solid #3a3a4a;
                border-radius: 5px;
                padding: 8px;
                font-size: 13px;
                max-width: 300px;
            }
            QLineEdit:focus {
                border: 1px solid #00ffcc;
            }
        """)
        self.search_input.textChanged.connect(self.refresh_cards_grid)
        cards_header.addWidget(self.search_input)
        cards_page_layout.addLayout(cards_header)
        

        
        cards_scroll = QScrollArea()
        cards_scroll.setWidgetResizable(True)
        cards_scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        self.cards_container = QWidget()
        self.cards_container.setStyleSheet("background-color: transparent;")
        self.grid_layout = QGridLayout(self.cards_container)
        self.grid_layout.setSpacing(15)
        self.grid_layout.setContentsMargins(0, 10, 0, 10)
        
        cards_scroll.setWidget(self.cards_container)
        cards_page_layout.addWidget(cards_scroll)
        
        self.stacked_widget.addWidget(cards_page)
        
        # 3. SUPPLIERS PAGE
        suppliers_page = QWidget()
        suppliers_layout = QVBoxLayout(suppliers_page)
        suppliers_layout.setContentsMargins(30, 20, 30, 30)
        
        sup_header_layout = QHBoxLayout()
        sup_title = QLabel("Supplier Directory & Bank Details")
        sup_title.setStyleSheet("font-size: 24px; font-weight: bold;")
        sup_header_layout.addWidget(sup_title)
        sup_header_layout.addStretch()
        
        add_sup_btn = QPushButton("➕ Add Supplier")
        add_sup_btn.setStyleSheet("""
            QPushButton {
                background-color: #00ffcc; color: #13131a;
                font-weight: bold; border-radius: 5px; padding: 8px 15px;
            }
            QPushButton:hover { background-color: #00ccaa; }
        """)
        add_sup_btn.clicked.connect(self.create_new_supplier)
        sup_header_layout.addWidget(add_sup_btn)
        suppliers_layout.addLayout(sup_header_layout)
        
        self.suppliers_table = QTableWidget()
        self.suppliers_table.setColumnCount(6)
        self.suppliers_table.setHorizontalHeaderLabels([
            "Supplier Name", "TIN No", "Address", "Contact Info", "Bank Branch", "Account Number"
        ])
        self.suppliers_table.setStyleSheet(table_style)
        self.suppliers_table.setSelectionBehavior(QTableWidget.SelectItems)
        self.suppliers_table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.suppliers_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.suppliers_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.suppliers_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        
        suppliers_layout.addWidget(self.suppliers_table)
        self.stacked_widget.addWidget(suppliers_page)
        
        # 4. TOOLS & SETTINGS PAGE
        tools_page = QWidget()
        tools_layout = QVBoxLayout(tools_page)
        tools_layout.setContentsMargins(30, 20, 30, 30)
        tools_layout.setSpacing(20)
        
        tools_title = QLabel("System Tools & Settings")
        tools_title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 10px;")
        tools_layout.addWidget(tools_title)
        

        
        # Database Admin Box
        db_box = QGroupBox("Database Administration")
        db_box.setStyleSheet("""
            QGroupBox {
                border: 1px solid #3a3a4a;
                border-radius: 8px;
                padding: 15px;
                font-weight: bold;
                color: #ff6666;
                font-size: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        db_layout = QVBoxLayout(db_box)
        db_desc = QLabel("Reset the system database to its original state. This deletes all custom records and refills the local SQLite file with default sample projects, contracts, suppliers, payments, and warranty metrics.")
        db_desc.setWordWrap(True)
        db_desc.setStyleSheet("color: #a0a0b0; font-size: 12px; margin-bottom: 10px;")
        db_layout.addWidget(db_desc)
        
        reseed_btn = QPushButton("⚠️ Re-Seed System Database")
        reseed_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff6666; color: #ffffff;
                font-weight: bold; border-radius: 5px; padding: 10px 20px;
                font-size: 13px;
                max-width: 250px;
            }
            QPushButton:hover { background-color: #cc4444; }
        """)
        reseed_btn.clicked.connect(self.reseed_database)
        db_layout.addWidget(reseed_btn)
        tools_layout.addWidget(db_box)
        
        tools_layout.addStretch()
        self.stacked_widget.addWidget(tools_page)
        
        main_layout.addWidget(self.stacked_widget)
        
        # Set active page highlights
        self.switch_page(0)
        self.refresh_all_data()

    def switch_page(self, index):
        self.stacked_widget.setCurrentIndex(index)
        for idx, btn in enumerate(self.nav_buttons):
            if idx == index:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #2b2b36;
                        color: #00ffcc;
                        border-left: 3px solid #00ffcc;
                        border-radius: 0px 5px 5px 0px;
                        padding: 10px;
                        text-align: left;
                        font-size: 14px;
                        font-weight: bold;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        color: #a0a0b0;
                        border: none;
                        border-radius: 5px;
                        padding: 10px;
                        text-align: left;
                        font-size: 14px;
                    }
                    QPushButton:hover {
                        background-color: #2b2b36;
                        color: #ffffff;
                    }
                """)
                
    def refresh_all_data(self):
        """Fetches the latest metrics and populates all widgets, lists, grids, and charts."""
        try:
            # 1. Update stats
            stats = database_config.get_stats()
            self.budget_card.update_value(f"₱{stats.get('total_budget', 0.0):,.2f}")
            self.awarded_card.update_value(f"₱{stats.get('total_contracted', 0.0):,.2f}")
            self.paid_card.update_value(f"₱{stats.get('total_paid', 0.0):,.2f}")
            
            # 2. Update Dashboard Analytics Panels
            self.update_dashboard_analytics()
            
            # 3. Dynamic division filters update
            self.populate_division_filters()
            
            # 4. Refresh table and card views using filter parameters
            self.refresh_filtered_views()
            
            # 5. Populate Suppliers Directory
            suppliers = database_config.get_suppliers()
            self.suppliers_table.setRowCount(len(suppliers))
            for idx, s in enumerate(suppliers):
                self.suppliers_table.setItem(idx, 0, QTableWidgetItem(s.get("supplier_name", "N/A")))
                self.suppliers_table.setItem(idx, 1, QTableWidgetItem(s.get("supplier_tin_no", "N/A")))
                self.suppliers_table.setItem(idx, 2, QTableWidgetItem(s.get("supplier_address", "N/A")))
                self.suppliers_table.setItem(idx, 3, QTableWidgetItem(s.get("supplier_contact_details", "N/A")))
                self.suppliers_table.setItem(idx, 4, QTableWidgetItem(s.get("supplier_bank_branch", "N/A")))
                self.suppliers_table.setItem(idx, 5, QTableWidgetItem(s.get("supplier_bank_account_number", "N/A")))
                
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to refresh dashboard data: {e}")

    def update_dashboard_analytics(self):
        # Clear previous alerts
        while self.alerts_list_layout.count():
            child = self.alerts_list_layout.takeAt(0)
            if child:
                w = child.widget()
                if w:
                    w.deleteLater()
                
        # Clear previous leaderboard
        while self.leaderboard_layout.count():
            child = self.leaderboard_layout.takeAt(0)
            if child:
                w = child.widget()
                if w:
                    w.deleteLater()
                
        try:
            data = database_config.get_dashboard_analytics()
            
            # Populate alerts list
            alerts = data.get("alerts", [])
            if not alerts:
                ok_lbl = QLabel("✅ All project timelines are operating on track!")
                ok_lbl.setStyleSheet("color: #2ecc71; font-size: 12px; font-weight: bold; border: none; background: transparent;")
                self.alerts_list_layout.addWidget(ok_lbl)
            else:
                for alert in alerts:
                    color = "#ff6666" if alert["type"] == "error" else ("#ffaa00" if alert["type"] == "warning" else "#33ccff")
                    lbl = QLabel(alert["text"])
                    lbl.setWordWrap(True)
                    lbl.setStyleSheet(f"color: {color}; font-size: 12px; border: none; background: transparent;")
                    self.alerts_list_layout.addWidget(lbl)
                    
            # Populate financial summaries
            self.savings_lbl.setText(f"Savings Realized: ₱{data.get('savings_amount', 0.0):,.2f} ({data.get('savings_percent', 0.0):.2f}%)")
            self.balance_lbl.setText(f"Unpaid Contract Balance: ₱{data.get('unpaid_balance', 0.0):,.2f}")
            
            # Populate leaderboard
            leaderboard = data.get("suppliers_leaderboard", [])
            if not leaderboard:
                empty_lbl = QLabel("No contract awards registered yet.")
                empty_lbl.setStyleSheet("color: #a0a0b0; font-size: 11px; font-style: italic; border: none; background: transparent;")
                self.leaderboard_layout.addWidget(empty_lbl)
            else:
                for idx, sup in enumerate(leaderboard, 1):
                    lbl = QLabel(f"{idx}. {sup['supplier_name']} — {sup['contract_count']} contracts (₱{sup['total_value']:,.2f})")
                    lbl.setStyleSheet("color: #a0a0b0; font-size: 11px; border: none; background: transparent;")
                    self.leaderboard_layout.addWidget(lbl)
                    
        except Exception as e:
            print(f"Error loading dashboard analytics components: {e}")

    def refresh_cards_grid(self, search_text=""):
        self.refresh_filtered_views()

    def show_project_detail(self, project_id):
        dialog = Cardsystem.ProjectDetailDialog(project_id, self)
        dialog.exec()

    def on_row_double_clicked(self, row, column):
        id_item = self.project_table.item(row, 0)
        if id_item:
            project_id = id_item.data(Qt.UserRole)
            if project_id is not None:
                self.show_project_detail(project_id)

    def export_data(self):
        default_name = str(Path.home() / "Documents" / "procurement_master_export.csv")
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save Export File",
            default_name,
            "CSV Files (*.csv)"
        )
        if filepath:
            success, result = excel_export.export_master_data(filepath)
            if success:
                QMessageBox.information(
                    self, "Export Successful",
                    f"Successfully exported {result} procurement timeline records to:\n{filepath}"
                )
            else:
                QMessageBox.critical(
                    self, "Export Failed",
                    f"Error exporting database: {result}"
                )

    def create_new_project(self):
        import form_dialogs
        dialog = form_dialogs.CreateProjectDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_all_data()

    def populate_division_filters(self):
        try:
            divisions = set()
            projects = database_config.get_projects()
            for p in projects:
                div = p.get("bureau_division_name")
                if div:
                    divisions.add(div.strip())
            
            # Overview division filter
            self.overview_division_filter.blockSignals(True)
            current_overview_sel = self.overview_division_filter.currentText()
            self.overview_division_filter.clear()
            self.overview_division_filter.addItem("All Divisions")
            for d in sorted(list(divisions)):
                self.overview_division_filter.addItem(d)
            idx = self.overview_division_filter.findText(current_overview_sel)
            if idx >= 0:
                self.overview_division_filter.setCurrentIndex(idx)
            else:
                self.overview_division_filter.setCurrentIndex(0)
            self.overview_division_filter.blockSignals(False)
            
            # Cards page division filter
            self.cards_division_filter.blockSignals(True)
            current_cards_sel = self.cards_division_filter.currentText()
            self.cards_division_filter.clear()
            self.cards_division_filter.addItem("All Divisions")
            for d in sorted(list(divisions)):
                self.cards_division_filter.addItem(d)
            idx = self.cards_division_filter.findText(current_cards_sel)
            if idx >= 0:
                self.cards_division_filter.setCurrentIndex(idx)
            else:
                self.cards_division_filter.setCurrentIndex(0)
            self.cards_division_filter.blockSignals(False)
        except Exception as e:
            print(f"Error populating division filters: {e}")

    def filter_overview_table(self):
        self.refresh_filtered_views()

    def apply_filters_and_refresh(self):
        # Synchronize Overview filters to Cards filters
        if hasattr(self, "cards_status_filter") and hasattr(self, "overview_status_filter"):
            self.cards_status_filter.blockSignals(True)
            self.cards_status_filter.setCurrentIndex(self.overview_status_filter.currentIndex())
            self.cards_status_filter.blockSignals(False)
            
        if hasattr(self, "cards_division_filter") and hasattr(self, "overview_division_filter"):
            self.cards_division_filter.blockSignals(True)
            self.cards_division_filter.setCurrentIndex(self.overview_division_filter.currentIndex())
            self.cards_division_filter.blockSignals(False)
            
        if hasattr(self, "cards_date_filter") and hasattr(self, "overview_date_filter"):
            self.cards_date_filter.blockSignals(True)
            self.cards_date_filter.setCurrentIndex(self.overview_date_filter.currentIndex())
            self.cards_date_filter.blockSignals(False)
            
        self.refresh_filtered_views()

    def apply_cards_filters_and_refresh(self):
        # Synchronize Cards filters to Overview filters
        if hasattr(self, "overview_status_filter") and hasattr(self, "cards_status_filter"):
            self.overview_status_filter.blockSignals(True)
            self.overview_status_filter.setCurrentIndex(self.cards_status_filter.currentIndex())
            self.overview_status_filter.blockSignals(False)
            
        if hasattr(self, "overview_division_filter") and hasattr(self, "cards_division_filter"):
            self.overview_division_filter.blockSignals(True)
            self.overview_division_filter.setCurrentIndex(self.cards_division_filter.currentIndex())
            self.overview_division_filter.blockSignals(False)
            
        if hasattr(self, "overview_date_filter") and hasattr(self, "cards_date_filter"):
            self.overview_date_filter.blockSignals(True)
            self.overview_date_filter.setCurrentIndex(self.cards_date_filter.currentIndex())
            self.overview_date_filter.blockSignals(False)
            
        self.refresh_filtered_views()

    def refresh_filtered_views(self):
        # Read filter options
        status_text = self.overview_status_filter.currentText() if hasattr(self, "overview_status_filter") else "All Statuses"
        division_text = self.overview_division_filter.currentText() if hasattr(self, "overview_division_filter") else "All Divisions"
        date_filter = self.overview_date_filter.currentText() if hasattr(self, "overview_date_filter") else "All Dates"
        search_text = self.search_input.text() if hasattr(self, "search_input") else ""
        
        current_date = QDate.currentDate()
        
        try:
            all_projects = database_config.get_projects()
        except Exception as e:
            print(f"Error fetching projects: {e}")
            return
            
        # 1. Filter status, division and relative date presets
        filtered = []
        for p in all_projects:
            # Status filter
            if status_text != "All Statuses" and p.get("status", "") != status_text:
                continue
                
            # Division filter
            proj_div = p.get("bureau_division_name", "")
            if division_text != "All Divisions" and (proj_div is None or proj_div.strip() != division_text.strip()):
                continue
                
            # Date filter relative presets
            proj_date_str = p.get("project_date", "")
            proj_date = QDate.fromString(proj_date_str, "yyyy-MM-dd") if proj_date_str else QDate(2026, 1, 1)
            
            if date_filter == "Within 24 hours only":
                days = proj_date.daysTo(current_date)
                if not (0 <= days <= 1):
                    continue
            elif date_filter == "Within a week only" or date_filter == "within a week only":
                days = proj_date.daysTo(current_date)
                if not (0 <= days <= 7):
                    continue
            elif date_filter == "Within a month only" or date_filter == "Within a month, only O":
                days = proj_date.daysTo(current_date)
                if not (0 <= days <= 30):
                    continue
                    
            filtered.append(p)
            
        # 2. Sort by date if "Newest First" or "Oldest First"
        if date_filter == "Newest First" or date_filter == "Newest":
            filtered.sort(key=lambda x: x.get("project_date", ""), reverse=True)
        elif date_filter == "Oldest First" or date_filter == "Oldest":
            filtered.sort(key=lambda x: x.get("project_date", ""), reverse=False)
            
        # 3. Populate project table
        self.project_table.setRowCount(len(filtered))
        for idx, p in enumerate(filtered):
            id_item = QTableWidgetItem(p.get("proj_id_no", "N/A"))
            id_item.setData(Qt.UserRole, p.get("id"))
            id_item.setData(Qt.UserRole + 1, p.get("project_date"))
            self.project_table.setItem(idx, 0, id_item)
            
            self.project_table.setItem(idx, 1, QTableWidgetItem(p.get("project_name", "N/A")))
            self.project_table.setItem(idx, 2, QTableWidgetItem(p.get("bureau_division_name", "N/A")))
            self.project_table.setItem(idx, 3, QTableWidgetItem(p.get("focal_person", "N/A")))
            
            abc = p.get("abc_amount", 0.0) or 0.0
            self.project_table.setItem(idx, 4, QTableWidgetItem(f"₱{abc:,.2f}"))
            self.project_table.setItem(idx, 5, QTableWidgetItem(p.get("status", "N/A")))
            
        # 4. Populate cards grid (applying text search filter as well)
        if hasattr(self, "grid_layout"):
            while self.grid_layout.count():
                child = self.grid_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
                    
            row = 0
            for proj in filtered:
                name_match = search_text.lower() in proj.get("project_name", "").lower()
                id_match = search_text.lower() in proj.get("proj_id_no", "").lower()
                if search_text and not (name_match or id_match):
                    continue
                    
                card = Cardsystem.ProjectCardWidget(proj)
                card.clicked.connect(self.show_project_detail)
                self.grid_layout.addWidget(card, row, 0)
                row += 1

    def create_new_project(self):
        import form_dialogs
        dialog = form_dialogs.CreateProjectDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_all_data()

    def create_new_supplier(self):
        import form_dialogs
        dialog = form_dialogs.AddSupplierDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_all_data()

    def export_data(self):
        import form_dialogs
        filter_dialog = form_dialogs.ExportFilterDialog(self)
        if filter_dialog.exec() == QDialog.Accepted:
            filters = filter_dialog.get_filters()
            
            default_name = str(Path.home() / "Documents" / "procurement_master_export.xlsx")
            filepath, _ = QFileDialog.getSaveFileName(
                self, "Save Export File",
                default_name,
                "Excel Worksheets (*.xlsx)"
            )
            if filepath:
                success, result = excel_export.export_master_data(filepath, filters)
                if success:
                    QMessageBox.information(
                        self, "Export Successful",
                        f"Successfully exported {result} filtered procurement records to styled Excel workbook:\n{filepath}"
                    )
                else:
                    QMessageBox.critical(
                        self, "Export Failed",
                        f"Error exporting database: {result}"
                    )

    def reseed_database(self):
        reply = QMessageBox.question(
            self, "Confirm Re-seed",
            "Are you sure you want to reset the database? This will overwrite any changes.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                database_config.seed()
                self.refresh_all_data()
                QMessageBox.information(self, "Success", "Database has been successfully reset to sample data.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to seed database: {e}")

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.Copy):
            focused = self.focusWidget()
            if isinstance(focused, QTableWidget):
                self.copy_table_selection_to_clipboard(focused)
                event.accept()
                return
        super().keyPressEvent(event)

    def copy_table_selection_to_clipboard(self, table_widget):
        selected_ranges = table_widget.selectedRanges()
        if not selected_ranges:
            return
            
        copied_text = ""
        for r_range in selected_ranges:
            for r in range(r_range.topRow(), r_range.bottomRow() + 1):
                row_text = []
                for c in range(r_range.leftColumn(), r_range.rightColumn() + 1):
                    item = table_widget.item(r, c)
                    row_text.append(item.text() if item else "")
                copied_text += "\t".join(row_text) + "\n"
                
        QApplication.clipboard().setText(copied_text.strip())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Dashboard()
    window.show()
    sys.exit(app.exec())
