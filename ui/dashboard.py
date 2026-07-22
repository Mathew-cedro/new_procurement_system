import sys
import os
from PySide6.QtCore import Qt, QRectF, QDate
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QKeySequence
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, 
    QVBoxLayout, QPushButton, QLabel, QFrame, QStackedWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea,
    QGridLayout, QLineEdit, QMessageBox, QFileDialog, QGroupBox,
    QDialog, QComboBox, QDateEdit, QCheckBox, QFormLayout, QTabWidget,
    QSplashScreen, QProgressBar
)

import database as database_config
import ui.cards as Cardsystem
import ui.dialogs as form_dialogs
from ui.widgets import StatCard, SimpleChart

class PremiumSplashScreen(QSplashScreen):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(500, 300)
        
        # Main layout frame
        self.frame = QFrame(self)
        self.frame.setGeometry(0, 0, 500, 300)
        self.frame.setStyleSheet("""
            QFrame {
                background-color: #13131a;
                border: 1px solid #2b2b36;
                border-radius: 15px;
            }
        """)
        
        layout = QVBoxLayout(self.frame)
        layout.setContentsMargins(30, 40, 30, 30)
        layout.setSpacing(15)
        
        # App Title
        self.title_lbl = QLabel("NEXUS PROCUREMENT")
        self.title_lbl.setStyleSheet("""
            QLabel {
                color: #00ffcc;
                font-size: 26px;
                font-weight: bold;
                font-family: 'Montserrat', 'Arial';
                background: transparent;
                border: none;
            }
        """)
        self.title_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_lbl)
        
        # Subtitle
        self.subtitle_lbl = QLabel("Payment & Contract Tracking System")
        self.subtitle_lbl.setStyleSheet("""
            QLabel {
                color: #a0a0b0;
                font-size: 13px;
                background: transparent;
                border: none;
            }
        """)
        self.subtitle_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.subtitle_lbl)
        
        layout.addStretch()
        
        # Progress status text
        self.status_lbl = QLabel("Initializing system components...")
        self.status_lbl.setStyleSheet("""
            QLabel {
                color: #8c8c9a;
                font-size: 11px;
                background: transparent;
                border: none;
            }
        """)
        self.status_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_lbl)
        
        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #1e1e24;
                border: none;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background-color: #00ffcc;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
    def set_progress(self, val, status_text):
        self.progress_bar.setValue(val)
        self.status_lbl.setText(status_text)
        QApplication.processEvents()

class Dashboard(QMainWindow):
    """The main application layout containing the sidebar and stacked views."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Procurement & Payment Tracking Dashboard")
        self.resize(1100, 700)
        self.setStyleSheet("background-color: #1e1e24; color: #ffffff;")
        self.current_cards_page = 1
        self.cards_per_page = 20
        
        # Central Layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # ---- SIDEBAR ----
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(200)
        self.sidebar.setStyleSheet("background-color: #13131a; border-right: 1px solid #2b2b36;")
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(10, 20, 10, 20)
        
        # Header Layout containing title and collapse button
        header_h_layout = QHBoxLayout()
        header_h_layout.setContentsMargins(5, 0, 5, 0)
        
        self.app_title = QLabel("NEXUS PTP")
        self.app_title.setStyleSheet("""
            font-size: 18px; 
            font-weight: bold; 
            color: #00ffcc;
        """)
        header_h_layout.addWidget(self.app_title)
        
        self.sidebar_toggle_btn = QPushButton("☰")
        self.sidebar_toggle_btn.setFixedSize(30, 30)
        self.sidebar_toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #00ffcc;
                font-size: 16px;
                font-weight: bold;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2b2b36;
            }
        """)
        self.sidebar_toggle_btn.clicked.connect(self.toggle_sidebar)
        header_h_layout.addWidget(self.sidebar_toggle_btn)
        
        sidebar_layout.addLayout(header_h_layout)
        sidebar_layout.addSpacing(15)
        
        self.nav_buttons = []
        nav_items = [
            ("📊 Overview", 0),
            ("🗂️ Project Cards", 1),
            ("👥 Suppliers List", 2),
            ("⚙️ Settings", 3)
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
        
        # Network Status Indicator Badge
        self.net_status_container = QHBoxLayout()
        self.net_status_container.setContentsMargins(5, 5, 5, 5)
        self.net_status_label = QLabel("🟢 Online")
        self.net_status_label.setAlignment(Qt.AlignCenter)
        self.net_status_label.setToolTip("Connected to Internet (Sync available)")
        self.net_status_label.setStyleSheet("""
            QLabel {
                color: #22c55e;
                font-size: 12px;
                font-weight: bold;
                padding: 5px 10px;
                background-color: rgba(34, 197, 94, 0.15);
                border: 1px solid rgba(34, 197, 94, 0.3);
                border-radius: 6px;
            }
        """)
        self.net_status_container.addWidget(self.net_status_label)
        sidebar_layout.addLayout(self.net_status_container)
        sidebar_layout.addSpacing(5)
        
        # 🚪 Exit Button at the bottom of the sidebar
        self.exit_btn = QPushButton("🚪 Exit")
        self.exit_btn.clicked.connect(self.close)
        sidebar_layout.addWidget(self.exit_btn)
        
        main_layout.addWidget(self.sidebar)
        
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
        self.header_title = QLabel("System Overview")
        self.header_title.setStyleSheet("font-size: 24px; font-weight: bold;")
        header_layout.addWidget(self.header_title)
        header_layout.addStretch()
        
        self.create_project_btn = QPushButton("➕ Create Project")
        self.create_project_btn.setStyleSheet("""
            QPushButton {
                background-color: #00ffcc; color: #13131a;
                font-weight: bold; border-radius: 5px; padding: 8px 15px;
            }
            QPushButton:hover { background-color: #00ccaa; }
        """)
        self.create_project_btn.clicked.connect(self.create_new_project)
        header_layout.addWidget(self.create_project_btn)
        
        self.export_btn = QPushButton("☁️ Sync Sheets")
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #1f4e78; color: #ffffff;
                font-weight: bold; border-radius: 5px; padding: 8px 15px;
                margin-left: 10px;
            }
            QPushButton:hover { background-color: #1a4063; }
        """)
        self.export_btn.clicked.connect(self.sync_google_sheets_action)
        header_layout.addWidget(self.export_btn)
        
        self.open_sheets_header_btn = QPushButton("🟢 Open Sheets")
        self.open_sheets_header_btn.setStyleSheet("""
            QPushButton {
                background-color: #0284c7; color: #ffffff;
                font-weight: bold; border-radius: 5px; padding: 8px 15px;
                border: none;
                margin-left: 10px;
            }
            QPushButton:hover { background-color: #0369a1; }
        """)
        self.open_sheets_header_btn.clicked.connect(self.open_google_sheet_in_browser)
        header_layout.addWidget(self.open_sheets_header_btn)
        
        self.refresh_btn = QPushButton("Refresh Data")
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a3a4a; color: #ffffff;
                font-weight: bold; border-radius: 5px; padding: 8px 15px;
                border: 1px solid #5a5a6a;
                margin-left: 10px;
            }
            QPushButton:hover { background-color: #4a4a5a; }
        """)
        self.refresh_btn.clicked.connect(self.refresh_all_data)
        header_layout.addWidget(self.refresh_btn)
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
        
        # Panel A: Project Timeline Tracker & Schedule Alerts
        self.timeline_panel = QFrame()
        self.timeline_panel.setObjectName("TimelinePanel")
        self.timeline_panel.setStyleSheet("""
            #TimelinePanel {
                background-color: #2b2b36; border-radius: 8px; border: 1px solid #3a3a4a;
            }
        """)
        timeline_p_layout = QVBoxLayout(self.timeline_panel)
        timeline_p_layout.setContentsMargins(15, 15, 15, 15)
        
        self.timeline_title = QLabel("📅 Project Schedule & Action Tracker")
        self.timeline_title.setStyleSheet("color: #00ffcc; font-size: 14px; font-weight: bold; margin-bottom: 8px;")
        timeline_p_layout.addWidget(self.timeline_title)
        
        self.timeline_list_layout = QVBoxLayout()
        self.timeline_list_layout.setSpacing(6)
        timeline_p_layout.addLayout(self.timeline_list_layout)
        timeline_p_layout.addStretch()
        
        analytics_layout.addWidget(self.timeline_panel, stretch=1)
        
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
        
        self.stats_title = QLabel("📊 Financial Savings & Supplier Directory")
        self.stats_title.setStyleSheet("color: #00ffcc; font-size: 14px; font-weight: bold;")
        stats_layout.addWidget(self.stats_title)
        
        # Financial rows layout
        self.savings_lbl = QLabel("Savings Amount: ₱0.00 (0.00%)")
        self.savings_lbl.setStyleSheet("color: #ffffff; font-size: 12px; font-weight: bold;")
        stats_layout.addWidget(self.savings_lbl)
        
        self.balance_lbl = QLabel("Unpaid Contract Balance: ₱0.00")
        self.balance_lbl.setStyleSheet("color: #ffffff; font-size: 12px; font-weight: bold;")
        stats_layout.addWidget(self.balance_lbl)
        
        # Horizontal line spacer
        self.sep = QFrame()
        self.sep.setFrameShape(QFrame.HLine)
        self.sep.setFrameShadow(QFrame.Sunken)
        self.sep.setStyleSheet("background-color: #3a3a4a; max-height: 1px; border: none;")
        stats_layout.addWidget(self.sep)
        
        # Leaderboard title
        self.leaderboard_title = QLabel("🏆 Top Supplier Leaderboard")
        self.leaderboard_title.setStyleSheet("color: #00ffcc; font-size: 12px; font-weight: bold;")
        stats_layout.addWidget(self.leaderboard_title)
        
        self.leaderboard_layout = QVBoxLayout()
        self.leaderboard_layout.setSpacing(4)
        stats_layout.addLayout(self.leaderboard_layout)
        stats_layout.addStretch()
        
        analytics_layout.addWidget(self.stats_panel, stretch=1)
        
        overview_layout.addLayout(analytics_layout)
        
        # Table of Projects
        table_panel = QVBoxLayout()
        
        table_header_layout = QHBoxLayout()
        self.table_label = QLabel("Active Procurement Projects")
        self.table_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        table_header_layout.addWidget(self.table_label)
        table_header_layout.addStretch()
        
        # Overview Filters
        self.status_lbl = QLabel("Status:")
        self.status_lbl.setStyleSheet("color: #a0a0b0; font-size: 11px;")
        self.overview_status_filter = QComboBox()
        self.overview_status_filter.addItems(["All Statuses", "Planning & Bidding", "Contract Awarded", "Deliveries & Payments", "Under Warranty"])
        self.overview_status_filter.setStyleSheet("""
            QComboBox {
                background-color: #2b2b36; color: #ffffff; border: 1px solid #3a3a4a;
                border-radius: 4px; padding: 4px 8px; min-width: 120px; font-size: 11px;
            }
        """)
        self.overview_status_filter.currentIndexChanged.connect(self.apply_filters_and_refresh)
        
        self.div_lbl = QLabel("Division:")
        self.div_lbl.setStyleSheet("color: #a0a0b0; font-size: 11px; margin-left: 10px;")
        self.overview_division_filter = QComboBox()
        self.overview_division_filter.addItem("All Divisions")
        self.overview_division_filter.setStyleSheet("""
            QComboBox {
                background-color: #2b2b36; color: #ffffff; border: 1px solid #3a3a4a;
                border-radius: 4px; padding: 4px 8px; min-width: 140px; font-size: 11px;
            }
        """)
        self.overview_division_filter.currentIndexChanged.connect(self.apply_filters_and_refresh)
        
        self.date_lbl = QLabel("Timeline:")
        self.date_lbl.setStyleSheet("color: #a0a0b0; font-size: 11px; margin-left: 10px;")
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
        
        table_header_layout.addWidget(self.status_lbl)
        table_header_layout.addWidget(self.overview_status_filter)
        table_header_layout.addWidget(self.div_lbl)
        table_header_layout.addWidget(self.overview_division_filter)
        table_header_layout.addWidget(self.date_lbl)
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
        self.cards_title = QLabel("Project Progression Cards")
        self.cards_title.setStyleSheet("font-size: 24px; font-weight: bold;")
        cards_header.addWidget(self.cards_title)
        cards_header.addStretch()
        
        self.create_project_btn_cards = QPushButton("➕ Create Project")
        self.create_project_btn_cards.setStyleSheet("""
            QPushButton {
                background-color: #00ffcc; color: #13131a;
                font-weight: bold; border-radius: 5px; padding: 8px 15px;
                margin-right: 15px;
            }
            QPushButton:hover { background-color: #00ccaa; }
        """)
        self.create_project_btn_cards.clicked.connect(self.create_new_project)
        cards_header.addWidget(self.create_project_btn_cards)
        
        self.export_btn_cards = QPushButton("☁️ Sync Sheets")
        self.export_btn_cards.setStyleSheet("""
            QPushButton {
                background-color: #1f4e78; color: #ffffff;
                font-weight: bold; border-radius: 5px; padding: 8px 15px;
                margin-right: 15px;
            }
            QPushButton:hover { background-color: #1a4063; }
        """)
        self.export_btn_cards.clicked.connect(self.sync_google_sheets_action)
        cards_header.addWidget(self.export_btn_cards)
        
        self.open_sheets_header_btn_cards = QPushButton("🟢 Open Sheets")
        self.open_sheets_header_btn_cards.setStyleSheet("""
            QPushButton {
                background-color: #0284c7; color: #ffffff;
                font-weight: bold; border-radius: 5px; padding: 8px 15px;
                border: none;
                margin-right: 15px;
            }
            QPushButton:hover { background-color: #0369a1; }
        """)
        self.open_sheets_header_btn_cards.clicked.connect(self.open_google_sheet_in_browser)
        cards_header.addWidget(self.open_sheets_header_btn_cards)
        
        # Cards Page Filters
        self.cards_status_filter = QComboBox()
        self.cards_status_filter.addItems(["All Statuses", "Planning & Bidding", "Contract Awarded", "Deliveries & Payments", "Under Warranty"])
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
        
        # Pagination Layout under Scroll View
        pagination_layout = QHBoxLayout()
        pagination_layout.setContentsMargins(0, 10, 0, 10)
        pagination_layout.setSpacing(10)
        pagination_layout.addStretch()
        
        self.btn_prev_page = QPushButton("◀ Prev")
        self.btn_prev_page.setFixedSize(80, 30)
        self.btn_prev_page.setStyleSheet("""
            QPushButton {
                background-color: #2b2b36; color: #ffffff; border: 1px solid #3a3a4a;
                border-radius: 4px; font-weight: bold; font-size: 12px;
            }
            QPushButton:hover { background-color: #323242; border: 1px solid #00ffcc; }
            QPushButton:disabled { background-color: #1e1e24; color: #5a5a6a; border: 1px solid #2b2b36; }
        """)
        self.btn_prev_page.clicked.connect(self.prev_cards_page)
        pagination_layout.addWidget(self.btn_prev_page)
        
        self.lbl_page_num = QLabel("Page 1 of 1")
        self.lbl_page_num.setStyleSheet("color: #a0a0b0; font-size: 13px; font-weight: bold; margin-left: 10px; margin-right: 10px;")
        pagination_layout.addWidget(self.lbl_page_num)
        
        self.btn_next_page = QPushButton("Next ▶")
        self.btn_next_page.setFixedSize(80, 30)
        self.btn_next_page.setStyleSheet("""
            QPushButton {
                background-color: #2b2b36; color: #ffffff; border: 1px solid #3a3a4a;
                border-radius: 4px; font-weight: bold; font-size: 12px;
            }
            QPushButton:hover { background-color: #323242; border: 1px solid #00ffcc; }
            QPushButton:disabled { background-color: #1e1e24; color: #5a5a6a; border: 1px solid #2b2b36; }
        """)
        self.btn_next_page.clicked.connect(self.next_cards_page)
        pagination_layout.addWidget(self.btn_next_page)
        pagination_layout.addStretch()
        
        cards_page_layout.addLayout(pagination_layout)
        
        self.stacked_widget.addWidget(cards_page)
        
        # 3. SUPPLIERS PAGE
        suppliers_page = QWidget()
        suppliers_layout = QVBoxLayout(suppliers_page)
        suppliers_layout.setContentsMargins(30, 20, 30, 30)
        
        sup_header_layout = QHBoxLayout()
        self.sup_title = QLabel("Supplier Directory & Bank Details")
        self.sup_title.setStyleSheet("font-size: 24px; font-weight: bold;")
        sup_header_layout.addWidget(self.sup_title)
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
        
        edit_sup_btn = QPushButton("📝 Edit Supplier")
        edit_sup_btn.setStyleSheet("""
            QPushButton {
                background-color: #1f4e78; color: #ffffff;
                font-weight: bold; border-radius: 5px; padding: 8px 15px;
                margin-left: 10px;
            }
            QPushButton:hover { background-color: #1a4063; }
        """)
        edit_sup_btn.clicked.connect(self.edit_selected_supplier)
        sup_header_layout.addWidget(edit_sup_btn)
        
        delete_sup_btn = QPushButton("🗑️ Delete Supplier")
        delete_sup_btn.setStyleSheet("""
            QPushButton {
                background-color: #5c1d1d; color: #ff9999;
                font-weight: bold; border-radius: 5px; padding: 8px 15px;
                margin-left: 10px; border: 1px solid #8c2d2d;
            }
            QPushButton:hover { background-color: #7c2d2d; color: #ffffff; }
        """)
        delete_sup_btn.clicked.connect(self.delete_selected_supplier)
        sup_header_layout.addWidget(delete_sup_btn)
        
        suppliers_layout.addLayout(sup_header_layout)
        
        self.suppliers_table = QTableWidget()
        self.suppliers_table.setColumnCount(6)
        self.suppliers_table.setHorizontalHeaderLabels([
            "Supplier Name", "TIN No", "Address", "Contact Info", "Bank Branch", "Account Number"
        ])
        self.suppliers_table.setStyleSheet(table_style)
        self.suppliers_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.suppliers_table.setSelectionMode(QTableWidget.SingleSelection)
        self.suppliers_table.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.EditKeyPressed)
        self.suppliers_table.itemChanged.connect(self.on_supplier_cell_edited)
        self.suppliers_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.suppliers_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        
        suppliers_layout.addWidget(self.suppliers_table)
        self.stacked_widget.addWidget(suppliers_page)
        
        # 4. SYSTEM SETTINGS & TOOLS PAGE
        settings_page = QWidget()
        settings_layout = QVBoxLayout(settings_page)
        settings_layout.setContentsMargins(30, 20, 30, 30)
        settings_layout.setSpacing(20)
        
        self.settings_title = QLabel("System Settings & Tools")
        self.settings_title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 10px;")
        settings_layout.addWidget(self.settings_title)
        
        # Theme Settings Box
        self.theme_box = QGroupBox("Appearance & Theme")
        self.theme_box.setObjectName("ThemeBox")
        theme_box_layout = QVBoxLayout(self.theme_box)
        
        self.theme_desc = QLabel("Customize the visual appearance of the application. Toggle between a sleek dark theme or a bright light theme.")
        self.theme_desc.setWordWrap(True)
        theme_box_layout.addWidget(self.theme_desc)
        
        theme_btn_layout = QHBoxLayout()
        self.btn_dark_theme = QPushButton("🌙 Dark Mode")
        self.btn_dark_theme.setCheckable(True)
        self.btn_dark_theme.setFixedHeight(35)
        self.btn_dark_theme.setFixedWidth(150)
        self.btn_dark_theme.clicked.connect(lambda: self.change_theme("dark"))
        
        self.btn_light_theme = QPushButton("☀️ Light Mode")
        self.btn_light_theme.setCheckable(True)
        self.btn_light_theme.setFixedHeight(35)
        self.btn_light_theme.setFixedWidth(150)
        self.btn_light_theme.clicked.connect(lambda: self.change_theme("light"))
        
        theme_btn_layout.addWidget(self.btn_dark_theme)
        theme_btn_layout.addWidget(self.btn_light_theme)
        theme_btn_layout.addStretch()
        theme_box_layout.addLayout(theme_btn_layout)
        settings_layout.addWidget(self.theme_box)
        
        # Google API Settings Box
        self.google_box = QGroupBox("Google Sheets & Drive Integration")
        self.google_box.setObjectName("GoogleBox")
        google_box_layout = QVBoxLayout(self.google_box)
        
        self.google_desc = QLabel("Sync local records dynamically with Google Sheets and upload attachments to Google Drive.")
        self.google_desc.setStyleSheet("color: #a0a0b0; font-size: 11px;")
        google_box_layout.addWidget(self.google_desc)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # Credentials File Path Row
        creds_h_layout = QHBoxLayout()
        self.creds_input = QLineEdit()
        self.creds_input.setReadOnly(True)
        self.creds_input.setPlaceholderText("Select credentials.json file secrets path...")
        btn_browse_creds = QPushButton("Browse...")
        btn_browse_creds.setStyleSheet("""
            QPushButton {
                background-color: #3a3a4a; color: #ffffff;
                font-weight: bold; border-radius: 4px; padding: 5px 12px;
            }
            QPushButton:hover { background-color: #4a4a5a; }
        """)
        btn_browse_creds.clicked.connect(self.browse_google_credentials)
        creds_h_layout.addWidget(self.creds_input)
        creds_h_layout.addWidget(btn_browse_creds)
        form_layout.addRow("OAuth Client Secrets (JSON):", creds_h_layout)
        
        # Spreadsheet ID Row
        sheet_h_layout = QHBoxLayout()
        self.sheet_id_input = QLineEdit()
        self.sheet_id_input.setPlaceholderText("Paste Google Spreadsheet ID (or leave blank to create)...")
        self.sheet_id_input.textChanged.connect(self.on_google_config_changed)
        
        self.btn_open_sheet = QPushButton("🔗 Open Sheet")
        self.btn_open_sheet.clicked.connect(self.open_google_sheet_in_browser)
        
        btn_create_sheet = QPushButton("Create New")
        btn_create_sheet.setStyleSheet("""
            QPushButton {
                background-color: #1f4e78; color: #ffffff;
                font-weight: bold; border-radius: 4px; padding: 5px 12px;
                border: none;
            }
            QPushButton:hover { background-color: #1a4063; }
        """)
        btn_create_sheet.clicked.connect(self.create_new_google_sheet)
        sheet_h_layout.addWidget(self.sheet_id_input)
        sheet_h_layout.addWidget(self.btn_open_sheet)
        sheet_h_layout.addWidget(btn_create_sheet)
        form_layout.addRow("Google Spreadsheet ID:", sheet_h_layout)
        
        # Folder ID Row
        folder_h_layout = QHBoxLayout()
        self.folder_id_input = QLineEdit()
        self.folder_id_input.setPlaceholderText("Paste Google Drive Folder ID (or leave blank to create)...")
        self.folder_id_input.textChanged.connect(self.on_google_config_changed)
        
        self.btn_open_folder = QPushButton("🔗 Open Folder")
        self.btn_open_folder.clicked.connect(self.open_google_folder_in_browser)
        
        btn_create_folder = QPushButton("Create New")
        btn_create_folder.setStyleSheet("""
            QPushButton {
                background-color: #1f4e78; color: #ffffff;
                font-weight: bold; border-radius: 4px; padding: 5px 12px;
                border: none;
            }
            QPushButton:hover { background-color: #1a4063; }
        """)
        btn_create_folder.clicked.connect(self.create_new_google_folder)
        folder_h_layout.addWidget(self.folder_id_input)
        folder_h_layout.addWidget(self.btn_open_folder)
        folder_h_layout.addWidget(btn_create_folder)
        form_layout.addRow("Google Drive Folder ID:", folder_h_layout)
        
        google_box_layout.addLayout(form_layout)
        google_box_layout.addSpacing(10)
        
        # Sync Action Buttons
        sync_actions_layout = QHBoxLayout()
        self.btn_push_sheets = QPushButton("🔄 Push SQLite to Sheets")
        self.btn_push_sheets.setFixedHeight(35)
        self.btn_push_sheets.setStyleSheet("""
            QPushButton {
                background-color: #00ffcc; color: #13131a;
                font-weight: bold; border-radius: 5px; padding: 8px 15px;
            }
            QPushButton:hover { background-color: #00ccaa; }
        """)
        self.btn_push_sheets.clicked.connect(self.push_data_to_sheets)
        
        self.btn_pull_sheets = QPushButton("📥 Pull Sheets to SQLite")
        self.btn_pull_sheets.setFixedHeight(35)
        self.btn_pull_sheets.setStyleSheet("""
            QPushButton {
                background-color: #0284c7; color: #ffffff;
                font-weight: bold; border-radius: 5px; padding: 8px 15px;
            }
            QPushButton:hover { background-color: #0369a1; }
        """)
        self.btn_pull_sheets.clicked.connect(self.pull_data_from_sheets)
        
        sync_actions_layout.addWidget(self.btn_push_sheets)
        sync_actions_layout.addWidget(self.btn_pull_sheets)
        sync_actions_layout.addStretch()
        google_box_layout.addLayout(sync_actions_layout)
        
        # Database Admin Box
        self.db_box = QGroupBox("Database Administration")
        self.db_box.setObjectName("DbBox")
        db_layout = QVBoxLayout(self.db_box)
        self.db_desc = QLabel("Reset the system database to its original state. This deletes all custom records and refills the local SQLite file with default sample projects, contracts, suppliers, payments, and warranty metrics.")
        self.db_desc.setWordWrap(True)
        db_layout.addWidget(self.db_desc)
        
        self.reseed_btn = QPushButton("⚠️ Re-Seed System Database")
        self.reseed_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff6666; color: #ffffff;
                font-weight: bold; border-radius: 5px; padding: 10px 20px;
                font-size: 13px;
                max-width: 250px;
                border: none;
            }
            QPushButton:hover { background-color: #cc4444; }
        """)
        self.reseed_btn.clicked.connect(self.reseed_database)
        db_layout.addWidget(self.reseed_btn)

        # Google Account Status Group Box
        self.account_box = QGroupBox("Google Account Authentication")
        self.account_box.setObjectName("AccountBox")
        account_box_layout = QVBoxLayout(self.account_box)
        
        self.status_desc = QLabel("Authenticate your Google Account to connect with sheets and drive APIs.")
        self.status_desc.setStyleSheet("color: #a0a0b0; font-size: 11px;")
        account_box_layout.addWidget(self.status_desc)
        
        status_form = QFormLayout()
        status_form.setSpacing(10)
        
        self.lbl_auth_status = QLabel("Disconnected")
        self.lbl_auth_status.setStyleSheet("font-weight: bold; color: #ff6666;")
        status_form.addRow("Connection Status:", self.lbl_auth_status)
        
        self.lbl_auth_email = QLabel("Not Logged In")
        self.lbl_auth_email.setStyleSheet("font-weight: bold;")
        status_form.addRow("Google Account Email:", self.lbl_auth_email)
        
        account_box_layout.addLayout(status_form)
        account_box_layout.addSpacing(10)
        
        account_btns_layout = QHBoxLayout()
        self.btn_connect_google = QPushButton("🔑 Connect Account")
        self.btn_connect_google.setFixedHeight(35)
        self.btn_connect_google.setStyleSheet("""
            QPushButton {
                background-color: #00ffcc; color: #13131a;
                font-weight: bold; border-radius: 5px; padding: 8px 15px;
            }
            QPushButton:hover { background-color: #00ccaa; }
        """)
        self.btn_connect_google.clicked.connect(self.connect_google_account)
        
        self.btn_disconnect_google = QPushButton("🔌 Disconnect Account")
        self.btn_disconnect_google.setFixedHeight(35)
        self.btn_disconnect_google.setStyleSheet("""
            QPushButton {
                background-color: #ff6666; color: #ffffff;
                font-weight: bold; border-radius: 5px; padding: 8px 15px;
                border: none;
            }
            QPushButton:hover { background-color: #cc4444; }
        """)
        self.btn_disconnect_google.clicked.connect(self.disconnect_google_account)
        
        account_btns_layout.addWidget(self.btn_connect_google)
        account_btns_layout.addWidget(self.btn_disconnect_google)
        account_btns_layout.addStretch()
        account_box_layout.addLayout(account_btns_layout)

        # Create Tab Widget
        self.settings_tabs = QTabWidget()
        self.settings_tabs.setObjectName("SettingsTabs")
        
        # Tab 1: Appearance & Database
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        general_layout.setContentsMargins(15, 15, 15, 15)
        general_layout.setSpacing(15)
        general_layout.addWidget(self.theme_box)
        general_layout.addWidget(self.db_box)
        general_layout.addStretch()
        
        # Tab 2: Google Account & Synchronization
        google_tab = QWidget()
        google_layout = QVBoxLayout(google_tab)
        google_layout.setContentsMargins(15, 15, 15, 15)
        google_layout.setSpacing(15)
        google_layout.addWidget(self.account_box)
        google_layout.addWidget(self.google_box)
        google_layout.addStretch()
        
        # Add tabs
        self.settings_tabs.addTab(general_tab, "🎨 General & Theme")
        self.settings_tabs.addTab(google_tab, "☁️ Google Sync & Account")
        
        settings_layout.addWidget(self.settings_tabs)
        self.stacked_widget.addWidget(settings_page)
        
        main_layout.addWidget(self.stacked_widget)
        
        # Load theme setting from DB and apply it
        import database as database_config
        self.current_theme = database_config.get_theme_setting()
        
        # Load Google Integration configuration
        self.creds_input.setText(database_config.get_system_setting("google_credentials_path", ""))
        self.sheet_id_input.setText(database_config.get_system_setting("google_spreadsheet_id", ""))
        self.folder_id_input.setText(database_config.get_system_setting("google_drive_folder_id", ""))
        
        self.refresh_google_account_status()
        self.update_theme_styles()
        
        # Auto-initialize Google sheets/drive if credentials exist but sheets/drive is empty
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, self.perform_google_auto_setup)
        
        # Set active page highlights
        self.switch_page(0)
        self.refresh_all_data()

        # Start background network monitor thread
        from services import NetworkMonitorThread
        self.network_monitor = NetworkMonitorThread(interval_seconds=10)
        self.network_monitor.status_changed.connect(self.update_network_status)
        self.network_monitor.start()

    def update_network_status(self, is_online):
        self.is_online = is_online
        is_collapsed = getattr(self, "sidebar_collapsed", False)
        
        if is_online:
            txt = "🟢 Online" if not is_collapsed else "🟢"
            self.net_status_label.setText(txt)
            self.net_status_label.setToolTip("Connected to Internet (Sync available)")
            self.net_status_label.setStyleSheet("""
                QLabel {
                    color: #22c55e;
                    font-size: 12px;
                    font-weight: bold;
                    padding: 5px 10px;
                    background-color: rgba(34, 197, 94, 0.15);
                    border: 1px solid rgba(34, 197, 94, 0.3);
                    border-radius: 6px;
                }
            """)
        else:
            txt = "🔴 Offline" if not is_collapsed else "🔴"
            self.net_status_label.setText(txt)
            self.net_status_label.setToolTip("Offline Mode (No Internet Connection)")
            self.net_status_label.setStyleSheet("""
                QLabel {
                    color: #ef4444;
                    font-size: 12px;
                    font-weight: bold;
                    padding: 5px 10px;
                    background-color: rgba(239, 68, 68, 0.15);
                    border: 1px solid rgba(239, 68, 68, 0.3);
                    border-radius: 6px;
                }
            """)

    def closeEvent(self, event):
        if hasattr(self, "network_monitor"):
            self.network_monitor.stop()
        super().closeEvent(event)

    def toggle_sidebar(self):
        is_collapsed = getattr(self, "sidebar_collapsed", False)
        if not is_collapsed:
            self.sidebar.setFixedWidth(60)
            self.app_title.setVisible(False)
            self.sidebar_collapsed = True
        else:
            self.sidebar.setFixedWidth(200)
            self.app_title.setVisible(True)
            self.sidebar_collapsed = False
        self.update_theme_styles()

    def switch_page(self, index):
        self.stacked_widget.setCurrentIndex(index)
        self.update_theme_styles()

    def change_theme(self, theme_name):
        self.current_theme = theme_name
        import database as database_config
        database_config.update_theme_setting(theme_name)
        self.update_theme_styles()
        # Trigger redraw of chart
        if hasattr(self, "chart"):
            self.chart.update()
        self.refresh_all_data()

    def update_theme_styles(self):
        theme = getattr(self, "current_theme", "dark")
        
        # Define palette colors based on theme
        if theme == "light":
            c_bg_app = "#f1f5f9"
            c_bg_sidebar = "#e2e8f0"
            c_border_sidebar = "#cbd5e1"
            c_bg_card = "#ffffff"
            c_border_card = "#cbd5e1"
            c_text_main = "#0f172a"
            c_text_muted = "#64748b"
            c_accent = "#0284c7"
            c_accent_hover = "#0369a1"
            c_table_header_bg = "#f1f5f9"
            c_table_header_text = "#0f172a"
            c_table_item_selected_bg = "#0284c7"
            c_table_item_selected_text = "#ffffff"
        else:
            c_bg_app = "#1e1e24"
            c_bg_sidebar = "#13131a"
            c_border_sidebar = "#2b2b36"
            c_bg_card = "#2b2b36"
            c_border_card = "#3a3a4a"
            c_text_main = "#ffffff"
            c_text_muted = "#a0a0b0"
            c_accent = "#00ffcc"
            c_accent_hover = "#00ccaa"
            c_table_header_bg = "#13131a"
            c_table_header_text = "#00ffcc"
            c_table_item_selected_bg = "#00ffcc"
            c_table_item_selected_text = "#13131a"

        # Apply main window and sidebar styling
        self.setStyleSheet(f"background-color: {c_bg_app}; color: {c_text_main};")
        self.sidebar.setStyleSheet(f"background-color: {c_bg_sidebar}; border-right: 1px solid {c_border_sidebar};")
        self.app_title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {c_accent};")
        self.sidebar_toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {c_accent};
                font-size: 16px;
                font-weight: bold;
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {c_bg_card};
            }}
        """)

        # Style Sidebar nav buttons dynamically based on expanded/collapsed state
        is_collapsed = getattr(self, "sidebar_collapsed", False)
        nav_items_list = [
            ("📊 Overview" if not is_collapsed else "📊", 0),
            ("🗂️ Project Cards" if not is_collapsed else "🗂️", 1),
            ("👥 Suppliers List" if not is_collapsed else "👥", 2),
            ("⚙️ Settings" if not is_collapsed else "⚙️", 3)
        ]
        
        for idx, (label, index) in enumerate(nav_items_list):
            btn = self.nav_buttons[idx]
            btn.setText(label)
            active = (idx == self.stacked_widget.currentIndex())
            if is_collapsed:
                if active:
                    btn.setStyleSheet(f"QPushButton {{ background-color: {c_bg_card}; color: {c_accent}; border: none; border-radius: 5px; padding: 10px 0; text-align: center; font-size: 16px; }}")
                else:
                    btn.setStyleSheet(f"QPushButton {{ background-color: transparent; color: {c_text_muted}; border: none; border-radius: 5px; padding: 10px 0; text-align: center; font-size: 16px; }} QPushButton:hover {{ background-color: {c_bg_card}; color: {c_text_main}; }}")
            else:
                if active:
                    btn.setStyleSheet(f"QPushButton {{ background-color: {c_bg_card}; color: {c_accent}; border-left: 3px solid {c_accent}; border-radius: 0px 5px 5px 0px; padding: 10px; text-align: left; font-size: 14px; font-weight: bold; }}")
                else:
                    btn.setStyleSheet(f"QPushButton {{ background-color: transparent; color: {c_text_muted}; border: none; border-radius: 5px; padding: 10px; text-align: left; font-size: 14px; }} QPushButton:hover {{ background-color: {c_bg_card}; color: {c_text_main}; }}")

        # Style Exit Button dynamically based on theme and expanded/collapsed state
        if theme == "light":
            c_exit_text = "#dc2626"
            c_exit_hover_bg = "#fee2e2"
            c_exit_hover_text = "#991b1b"
        else:
            c_exit_text = "#ff6666"
            c_exit_hover_bg = "#4d2222"
            c_exit_hover_text = "#ff8888"
            
        exit_label = "🚪 Exit" if not is_collapsed else "🚪"
        self.exit_btn.setText(exit_label)
        if is_collapsed:
            self.exit_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {c_exit_text};
                    border: none;
                    border-radius: 5px;
                    padding: 10px 0;
                    text-align: center;
                    font-size: 16px;
                }}
                QPushButton:hover {{
                    background-color: {c_exit_hover_bg};
                    color: {c_exit_hover_text};
                }}
            """)
        else:
            self.exit_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {c_exit_text};
                    border: none;
                    border-radius: 5px;
                    padding: 10px;
                    text-align: left;
                    font-size: 14px;
                }}
                QPushButton:hover {{
                    background-color: {c_exit_hover_bg};
                    color: {c_exit_hover_text};
                    font-weight: bold;
                }}
            """)

        # Overview titles & panels styling
        self.header_title.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {c_text_main};")
        self.timeline_panel.setStyleSheet(f"#TimelinePanel {{ background-color: {c_bg_card}; border-radius: 8px; border: 1px solid {c_border_card}; }}")
        self.timeline_title.setStyleSheet(f"color: {c_accent}; font-size: 14px; font-weight: bold; margin-bottom: 8px; border: none; background: transparent;")
        
        self.stats_panel.setStyleSheet(f"#StatsPanel {{ background-color: {c_bg_card}; border-radius: 8px; border: 1px solid {c_border_card}; }}")
        self.stats_title.setStyleSheet(f"color: {c_accent}; font-size: 14px; font-weight: bold; border: none; background: transparent;")
        self.savings_lbl.setStyleSheet(f"color: {c_text_main}; font-size: 12px; font-weight: bold; border: none; background: transparent;")
        self.balance_lbl.setStyleSheet(f"color: {c_text_main}; font-size: 12px; font-weight: bold; border: none; background: transparent;")
        self.sep.setStyleSheet(f"background-color: {c_border_card}; max-height: 1px; border: none;")
        self.leaderboard_title.setStyleSheet(f"color: {c_accent}; font-size: 12px; font-weight: bold; border: none; background: transparent;")
        self.table_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {c_text_main};")
        
        # Action Buttons styling
        self.create_project_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c_accent}; color: #13131a;
                font-weight: bold; border-radius: 5px; padding: 8px 15px; border: none;
            }}
            QPushButton:hover {{ background-color: {c_accent_hover}; }}
        """)
        self.export_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c_bg_sidebar}; color: {c_text_main};
                font-weight: bold; border-radius: 5px; padding: 8px 15px; border: 1px solid {c_border_card};
                margin-left: 10px;
            }}
            QPushButton:hover {{ background-color: {c_bg_card}; }}
        """)
        self.refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c_bg_sidebar}; color: {c_text_main};
                font-weight: bold; border-radius: 5px; padding: 8px 15px; border: 1px solid {c_border_card};
                margin-left: 10px;
            }}
            QPushButton:hover {{ background-color: {c_bg_card}; }}
        """)
        self.open_sheets_header_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c_bg_sidebar}; color: {c_text_main};
                font-weight: bold; border-radius: 5px; padding: 8px 15px; border: 1px solid {c_border_card};
                margin-left: 10px;
            }}
            QPushButton:hover {{ background-color: {c_bg_card}; }}
        """)
        
        # Overview Comboboxes
        combo_style = f"""
            QComboBox {{
                background-color: {c_bg_card};
                color: {c_text_main};
                border: 1px solid {c_border_card};
                border-radius: 4px;
                padding: 4px 8px;
                min-width: 120px;
                font-size: 11px;
            }}
        """
        self.overview_status_filter.setStyleSheet(combo_style)
        self.overview_division_filter.setStyleSheet(combo_style)
        self.overview_date_filter.setStyleSheet(combo_style)
        self.status_lbl.setStyleSheet(f"color: {c_text_muted}; font-size: 11px;")
        self.div_lbl.setStyleSheet(f"color: {c_text_muted}; font-size: 11px; margin-left: 10px;")
        self.date_lbl.setStyleSheet(f"color: {c_text_muted}; font-size: 11px; margin-left: 10px;")

        # Style Tables
        table_style = f"""
            QTableWidget {{
                background-color: {c_bg_card};
                border: 1px solid {c_border_card};
                border-radius: 8px;
                gridline-color: {c_border_card};
                color: {c_text_main};
            }}
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {c_border_card};
            }}
            QTableWidget::item:selected {{
                background-color: {c_table_item_selected_bg};
                color: {c_table_item_selected_text};
            }}
            QHeaderView::section {{
                background-color: {c_table_header_bg};
                color: {c_table_header_text};
                padding: 6px;
                border: 1px solid {c_border_card};
                font-weight: bold;
            }}
        """
        self.project_table.setStyleSheet(table_style)
        self.suppliers_table.setStyleSheet(table_style)

        # StatCards styling
        for card in [self.budget_card, self.awarded_card, self.paid_card]:
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: {c_bg_card};
                    border: 1px solid {c_border_card};
                    border-radius: 8px;
                    padding: 15px;
                }}
            """)
            card.title_label.setStyleSheet(f"color: {c_text_muted}; font-size: 11px; font-weight: bold; border: none; background: transparent;")
            card.val_label.setStyleSheet(f"color: {card.color_hex}; font-size: 22px; font-weight: bold; border: none; background: transparent;")

        # Page 2 (Project Cards Page) styling
        self.cards_title.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {c_text_main};")
        self.create_project_btn_cards.setStyleSheet(f"""
            QPushButton {{
                background-color: {c_accent}; color: #13131a;
                font-weight: bold; border-radius: 5px; padding: 8px 15px; border: none;
                margin-right: 15px;
            }}
            QPushButton:hover {{ background-color: {c_accent_hover}; }}
        """)
        self.export_btn_cards.setStyleSheet(f"""
            QPushButton {{
                background-color: {c_bg_sidebar}; color: {c_text_main};
                font-weight: bold; border-radius: 5px; padding: 8px 15px; border: 1px solid {c_border_card};
                margin-right: 15px;
            }}
            QPushButton:hover {{ background-color: {c_bg_card}; }}
        """)
        self.open_sheets_header_btn_cards.setStyleSheet(f"""
            QPushButton {{
                background-color: {c_bg_sidebar}; color: {c_text_main};
                font-weight: bold; border-radius: 5px; padding: 8px 15px; border: 1px solid {c_border_card};
                margin-right: 15px;
            }}
            QPushButton:hover {{ background-color: {c_bg_card}; }}
        """)
        
        cards_combo_style = f"""
            QComboBox {{
                background-color: {c_bg_card}; color: {c_text_main}; border: 1px solid {c_border_card};
                border-radius: 4px; padding: 8px; margin-right: 10px; min-width: 120px; font-size: 13px;
            }}
        """
        self.cards_status_filter.setStyleSheet(cards_combo_style)
        self.cards_division_filter.setStyleSheet(cards_combo_style)
        self.cards_date_filter.setStyleSheet(cards_combo_style)
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {c_bg_card};
                color: {c_text_main};
                border: 1px solid {c_border_card};
                border-radius: 5px;
                padding: 8px;
                font-size: 13px;
                max-width: 300px;
            }}
            QLineEdit:focus {{
                border: 1px solid {c_accent};
            }}
        """)

        # Page 3 (Suppliers Directory Page) styling
        self.sup_title.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {c_text_main};")
        
        # Settings Page styling
        self.settings_title.setStyleSheet(f"font-size: 24px; font-weight: bold; margin-bottom: 10px; color: {c_text_main};")
        
        theme_box_qss = f"""
            QGroupBox {{
                border: 1px solid {c_border_card};
                border-radius: 8px;
                padding: 15px;
                font-weight: bold;
                color: {c_accent};
                font-size: 14px;
                background-color: transparent;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """
        self.theme_box.setStyleSheet(theme_box_qss)
        self.google_box.setStyleSheet(theme_box_qss)
        self.account_box.setStyleSheet(theme_box_qss)
        self.google_desc.setStyleSheet(f"color: {c_text_muted}; font-size: 12px; margin-bottom: 10px; border: none; background: transparent;")
        self.status_desc.setStyleSheet(f"color: {c_text_muted}; font-size: 12px; margin-bottom: 10px; border: none; background: transparent;")
        
        google_input_style = f"""
            QLineEdit {{
                background-color: {c_bg_app};
                color: {c_text_main};
                border: 1px solid {c_border_card};
                border-radius: 4px;
                padding: 6px;
            }}
            QLineEdit:focus {{
                border: 1px solid {c_accent};
            }}
        """
        self.creds_input.setStyleSheet(google_input_style)
        self.sheet_id_input.setStyleSheet(google_input_style)
        self.folder_id_input.setStyleSheet(google_input_style)
        
        btn_open_style = f"""
            QPushButton {{
                background-color: {c_bg_card};
                color: {c_text_main};
                border: 1px solid {c_border_card};
                font-weight: bold;
                border-radius: 4px;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background-color: {c_bg_sidebar};
            }}
        """
        self.btn_open_sheet.setStyleSheet(btn_open_style)
        self.btn_open_folder.setStyleSheet(btn_open_style)

        self.db_box.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid {c_border_card};
                border-radius: 8px;
                padding: 15px;
                font-weight: bold;
                color: #ff6666;
                font-size: 14px;
                background-color: transparent;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)
        self.theme_desc.setStyleSheet(f"color: {c_text_muted}; font-size: 12px; margin-bottom: 10px; border: none; background: transparent;")
        self.db_desc.setStyleSheet(f"color: {c_text_muted}; font-size: 12px; margin-bottom: 10px; border: none; background: transparent;")
        
        # Style Settings Tabs
        tab_style = f"""
            QTabWidget::pane {{
                border: 1px solid {c_border_card};
                background-color: {c_bg_card};
                border-radius: 8px;
                padding: 15px;
            }}
            QTabBar::tab {{
                background-color: {c_bg_sidebar};
                color: {c_text_muted};
                border: 1px solid {c_border_card};
                border-bottom-color: transparent;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 8px 20px;
                margin-right: 2px;
                font-weight: bold;
                font-size: 12px;
            }}
            QTabBar::tab:selected {{
                background-color: {c_bg_card};
                color: {c_accent};
                border-bottom-color: {c_bg_card};
            }}
            QTabBar::tab:hover {{
                background-color: {c_bg_card};
                color: {c_text_main};
            }}
        """
        self.settings_tabs.setStyleSheet(tab_style)
        
        # Theme toggle buttons state styling
        if theme == "light":
            self.btn_light_theme.setChecked(True)
            self.btn_dark_theme.setChecked(False)
            self.btn_light_theme.setStyleSheet(f"QPushButton {{ background-color: #0284c7; color: #ffffff; font-weight: bold; border-radius: 5px; border: none; }}")
            self.btn_dark_theme.setStyleSheet(f"QPushButton {{ background-color: transparent; color: {c_text_muted}; border: 1px solid {c_border_card}; border-radius: 5px; }} QPushButton:hover {{ background-color: #e2e8f0; }}")
        else:
            self.btn_dark_theme.setChecked(True)
            self.btn_light_theme.setChecked(False)
            self.btn_dark_theme.setStyleSheet(f"QPushButton {{ background-color: #00ffcc; color: #13131a; font-weight: bold; border-radius: 5px; border: none; }}")
            self.btn_light_theme.setStyleSheet(f"QPushButton {{ background-color: transparent; color: {c_text_muted}; border: 1px solid {c_border_card}; border-radius: 5px; }} QPushButton:hover {{ background-color: #2b2b36; }}")
            
        # Update metric cards and chart widgets theme
        if hasattr(self, "budget_card"):
            self.budget_card.update_theme(theme)
        if hasattr(self, "awarded_card"):
            self.awarded_card.update_theme(theme)
        if hasattr(self, "paid_card"):
            self.paid_card.update_theme(theme)
        if hasattr(self, "chart"):
            self.chart.set_theme(theme)
            
        # Update pagination controls theme
        if hasattr(self, "btn_prev_page") and hasattr(self, "btn_next_page"):
            if theme == "light":
                btn_pag_style = """
                    QPushButton {
                        background-color: #ffffff; color: #0f172a; border: 1px solid #cbd5e1;
                        border-radius: 4px; font-weight: bold; font-size: 12px;
                    }
                    QPushButton:hover { background-color: #f1f5f9; border: 1px solid #0284c7; }
                    QPushButton:disabled { background-color: #f8fafc; color: #94a3b8; border: 1px solid #e2e8f0; }
                """
                self.btn_prev_page.setStyleSheet(btn_pag_style)
                self.btn_next_page.setStyleSheet(btn_pag_style)
                self.lbl_page_num.setStyleSheet("color: #64748b; font-size: 13px; font-weight: bold; margin-left: 10px; margin-right: 10px;")
            else:
                btn_pag_style = """
                    QPushButton {
                        background-color: #2b2b36; color: #ffffff; border: 1px solid #3a3a4a;
                        border-radius: 4px; font-weight: bold; font-size: 12px;
                    }
                    QPushButton:hover { background-color: #323242; border: 1px solid #00ffcc; }
                    QPushButton:disabled { background-color: #1e1e24; color: #5a5a6a; border: 1px solid #2b2b36; }
                """
                self.btn_prev_page.setStyleSheet(btn_pag_style)
                self.btn_next_page.setStyleSheet(btn_pag_style)
                self.lbl_page_num.setStyleSheet("color: #a0a0b0; font-size: 13px; font-weight: bold; margin-left: 10px; margin-right: 10px;")
                
        if hasattr(self, "net_status_label"):
            self.update_network_status(getattr(self, "is_online", True))
                
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
            self.suppliers_table.blockSignals(True)
            suppliers = database_config.get_suppliers()
            self.suppliers_table.setRowCount(len(suppliers))
            for idx, s in enumerate(suppliers):
                name_item = QTableWidgetItem(s.get("supplier_name", "N/A"))
                name_item.setData(Qt.UserRole, s.get("id"))
                self.suppliers_table.setItem(idx, 0, name_item)
                self.suppliers_table.setItem(idx, 1, QTableWidgetItem(s.get("supplier_tin_no", "N/A")))
                self.suppliers_table.setItem(idx, 2, QTableWidgetItem(s.get("supplier_address", "N/A")))
                self.suppliers_table.setItem(idx, 3, QTableWidgetItem(s.get("supplier_contact_details", "N/A")))
                self.suppliers_table.setItem(idx, 4, QTableWidgetItem(s.get("supplier_bank_branch", "N/A")))
                self.suppliers_table.setItem(idx, 5, QTableWidgetItem(s.get("supplier_bank_account_number", "N/A")))
            self.suppliers_table.blockSignals(False)
            
            # Silent automatic background sync to Google Sheets
            self.trigger_background_push(silent=True)
                
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to refresh dashboard data: {e}")

    def update_dashboard_analytics(self):
        # Clear previous leaderboard
        while self.leaderboard_layout.count():
            child = self.leaderboard_layout.takeAt(0)
            if child:
                w = child.widget()
                if w:
                    w.deleteLater()
                    
        # Clear previous timeline list
        while self.timeline_list_layout.count():
            child = self.timeline_list_layout.takeAt(0)
            if child:
                w = child.widget()
                if w:
                    w.deleteLater()
                
        try:
            data = database_config.get_dashboard_analytics()
                    
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
                    
            # Populate timeline progress schedules
            events = database_config.get_upcoming_timeline_events()
            if not events:
                empty_lbl = QLabel("No upcoming schedules or deadlines found.")
                empty_lbl.setStyleSheet("color: #a0a0b0; font-size: 11px; font-style: italic; border: none; background: transparent;")
                self.timeline_list_layout.addWidget(empty_lbl)
            else:
                # Display up to 5 timeline events
                current_date = QDate.currentDate()
                for event in events[:5]:
                    evt_date = QDate.fromString(event["date"], "yyyy-MM-dd")
                    days = current_date.daysTo(evt_date)
                    if days < 0:
                        days_str = f"Overdue by {abs(days)} days"
                        badge_color = "#ff4d4d"
                    elif days == 0:
                        days_str = "Due today!"
                        badge_color = "#ffaa00"
                    elif days == 1:
                        days_str = "Due tomorrow"
                        badge_color = "#ffaa00"
                    else:
                        days_str = f"In {days} days"
                        badge_color = "#00ffcc"
                        
                    lbl_text = f"📅 <b>{event['date']}</b> — <font color='#00ffcc'>{event['proj_id']}</font><br>{event['event_name']} (<font color='{badge_color}'>{days_str}</font>)"
                    lbl = QLabel(lbl_text)
                    lbl.setWordWrap(True)
                    lbl.setStyleSheet("color: #a0a0b0; font-size: 11px; border: none; background: transparent; padding-bottom: 4px;")
                    self.timeline_list_layout.addWidget(lbl)
                    
        except Exception as e:
            print(f"Error loading dashboard analytics components: {e}")

    def refresh_cards_grid(self, search_text=""):
        self.current_cards_page = 1
        self.refresh_filtered_views()

    def prev_cards_page(self):
        if self.current_cards_page > 1:
            self.current_cards_page -= 1
            self.refresh_filtered_views()

    def next_cards_page(self):
        self.current_cards_page += 1
        self.refresh_filtered_views()

    def show_project_detail(self, project_id):
        dialog = Cardsystem.ProjectDetailDialog(project_id, self)
        dialog.exec()
        self.refresh_all_data()

    def on_row_double_clicked(self, row, column):
        id_item = self.project_table.item(row, 0)
        if id_item:
            project_id = id_item.data(Qt.UserRole)
            if project_id is not None:
                self.show_project_detail(project_id)



    def create_new_project(self):
        import ui.dialogs as form_dialogs
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
            
        self.current_cards_page = 1
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
            # Status normalization for compatibility
            p_status = p.get("status", "")
            if p_status in ["Initiated", "Bidding"]:
                p_status = "Planning & Bidding"
                p["status"] = "Planning & Bidding"
            elif p_status == "Delivering":
                p_status = "Deliveries & Payments"
                p["status"] = "Deliveries & Payments"
                
            # Status filter
            if status_text != "All Statuses" and p_status != status_text:
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
            
        # 4. Populate cards grid (applying text search filter as well with pagination)
        if hasattr(self, "grid_layout"):
            # Clear previous stretches
            for r in range(self.grid_layout.rowCount()):
                self.grid_layout.setRowStretch(r, 0)
                
            while self.grid_layout.count():
                child = self.grid_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
                    
            # Filter projects that match the search text
            cards_projects = []
            for proj in filtered:
                name_match = search_text.lower() in proj.get("project_name", "").lower()
                id_match = search_text.lower() in proj.get("proj_id_no", "").lower()
                if not search_text or (name_match or id_match):
                    cards_projects.append(proj)
                    
            # Calculate pagination
            total_cards = len(cards_projects)
            total_pages = max(1, (total_cards + self.cards_per_page - 1) // self.cards_per_page)
            
            # Clamp current page to safe boundaries
            if self.current_cards_page > total_pages:
                self.current_cards_page = total_pages
            if self.current_cards_page < 1:
                self.current_cards_page = 1
                
            # Slice projects for the current page
            start_idx = (self.current_cards_page - 1) * self.cards_per_page
            end_idx = start_idx + self.cards_per_page
            page_projects = cards_projects[start_idx:end_idx]
            
            # Update pagination label and button states
            if hasattr(self, "lbl_page_num"):
                self.lbl_page_num.setText(f"Page {self.current_cards_page} of {total_pages} (Total: {total_cards})")
            if hasattr(self, "btn_prev_page"):
                self.btn_prev_page.setEnabled(self.current_cards_page > 1)
            if hasattr(self, "btn_next_page"):
                self.btn_next_page.setEnabled(self.current_cards_page < total_pages)
                
            # Instantiate card widgets for the page
            row = 0
            for proj in page_projects:
                card = Cardsystem.ProjectCardWidget(proj)
                card.clicked.connect(self.show_project_detail)
                self.grid_layout.addWidget(card, row, 0)
                row += 1
                
            # Add vertical stretch to bottom row to push all cards up
            self.grid_layout.setRowStretch(row, 1)

    def create_new_project(self):
        import ui.dialogs as form_dialogs
        dialog = form_dialogs.CreateProjectDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_all_data()

    def create_new_supplier(self):
        import ui.dialogs as form_dialogs
        dialog = form_dialogs.AddSupplierDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_all_data()

    def edit_selected_supplier(self):
        selected_row = self.suppliers_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a supplier row from the table to edit.")
            return
            
        id_item = self.suppliers_table.item(selected_row, 0)
        if not id_item:
            return
            
        supplier_id = id_item.data(Qt.UserRole)
        
        # Fetch the current list of suppliers to get full dict details
        suppliers = database_config.get_suppliers()
        s_data = next((s for s in suppliers if s["id"] == supplier_id), None)
        
        if not s_data:
            QMessageBox.critical(self, "Error", "Could not locate selected supplier data.")
            return
            
        import ui.dialogs as form_dialogs
        dialog = form_dialogs.AddSupplierDialog(self, s_data)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_all_data()

    def delete_selected_supplier(self):
        selected_row = self.suppliers_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a supplier row from the table to delete.")
            return
            
        id_item = self.suppliers_table.item(selected_row, 0)
        if not id_item:
            return
            
        supplier_id = id_item.data(Qt.UserRole)
        supplier_name = id_item.text()
        
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to permanently delete supplier '{supplier_name}'?\n\n"
            "This will delete the supplier from directory. Any contracts pointing to this supplier will have a missing supplier name.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            success, result = database_config.delete_supplier(supplier_id)
            if success:
                QMessageBox.information(self, "Deleted", f"Supplier '{supplier_name}' successfully deleted.")
                self.refresh_all_data()
            else:
                QMessageBox.critical(self, "Error", f"Failed to delete supplier:\n{result}")

    def on_supplier_cell_edited(self, item):
        row = item.row()
        col = item.column()
        
        # Get the first column item to retrieve the supplier ID
        id_item = self.suppliers_table.item(row, 0)
        if not id_item:
            return
            
        supplier_id = id_item.data(Qt.UserRole)
        if supplier_id is None:
            return
            
        new_val = item.text().strip()
        
        # Map column index to db column name
        db_cols = {
            0: "supplier_name",
            1: "tin",
            2: "address",
            3: "contact",
            4: "branch",
            5: "bank_name"
        }
        
        db_col = db_cols.get(col)
        if not db_col:
            return
            
        # Validate that supplier name is not empty
        if col == 0 and not new_val:
            QMessageBox.warning(self, "Invalid Input", "Supplier name cannot be empty!")
            self.refresh_all_data()
            return
            
        conn = database_config.get_db_connection()
        cur = conn.cursor()
        try:
            if db_col == "supplier_name":
                # For bank_account field, we keep it in sync with supplier_name
                cur.execute("""
                    UPDATE suppliers 
                    SET supplier_name = ?, bank_account = ?
                    WHERE supplier_id = ?
                """, (new_val, new_val, supplier_id))
            else:
                cur.execute(f"""
                    UPDATE suppliers 
                    SET {db_col} = ?
                    WHERE supplier_id = ?
                """, (new_val, supplier_id))
            conn.commit()
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to save changes inline:\n{e}")
        finally:
            conn.close()
            
        # Refresh the dashboard stats/panels without firing the itemChanged recursion
        self.suppliers_table.blockSignals(True)
        self.refresh_all_data()
        self.suppliers_table.blockSignals(False)



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

    def browse_google_credentials(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select credentials.json", "", "JSON Files (*.json)")
        if file_path:
            self.creds_input.setText(file_path)
            import database as database_config
            database_config.set_system_setting("google_credentials_path", file_path)
            QMessageBox.information(self, "Credentials Selected", "Google OAuth Client Secrets JSON file configured successfully!")

    def create_new_google_sheet(self):
        import database as database_config
        creds = database_config.get_system_setting("google_credentials_path", "")
        if not creds or not os.path.exists(creds):
            QMessageBox.warning(self, "Credentials Needed", "Please configure the Client Secrets JSON file path first before creating a spreadsheet.")
            return
        
        self.setCursor(Qt.WaitCursor)
        try:
            import services.google_sheets as google_sync
            sid = google_sync.ensure_spreadsheet()
            self.sheet_id_input.setText(sid)
            QMessageBox.information(self, "Spreadsheet Created", f"Successfully created a new Google Spreadsheet online!\n\nSpreadsheet ID: {sid}\n\nYou can share this ID with other team members.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create Google Spreadsheet:\n{e}")
        finally:
            self.unsetCursor()

    def create_new_google_folder(self):
        import database as database_config
        creds = database_config.get_system_setting("google_credentials_path", "")
        if not creds or not os.path.exists(creds):
            QMessageBox.warning(self, "Credentials Needed", "Please configure the Client Secrets JSON file path first before creating a folder.")
            return
            
        self.setCursor(Qt.WaitCursor)
        try:
            import services.google_sheets as google_sync
            fid = google_sync.ensure_drive_folder()
            self.folder_id_input.setText(fid)
            QMessageBox.information(self, "Folder Created", f"Successfully created a new Google Drive Folder online!\n\nFolder ID: {fid}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create Google Drive Folder:\n{e}")
        finally:
            self.unsetCursor()

    def on_google_config_changed(self):
        import database as database_config
        database_config.set_system_setting("google_spreadsheet_id", self.sheet_id_input.text().strip())
        database_config.set_system_setting("google_drive_folder_id", self.folder_id_input.text().strip())

    def set_sync_buttons_enabled(self, enabled):
        buttons = [
            getattr(self, "export_btn", None),
            getattr(self, "export_btn_cards", None),
            getattr(self, "btn_push_sheets", None),
            getattr(self, "btn_pull_sheets", None)
        ]
        for btn in buttons:
            if btn is not None:
                btn.setEnabled(enabled)

    def sync_google_sheets_action(self):
        reply = QMessageBox.question(
            self, "Sync with Google Sheets",
            "Would you like to synchronize your local database and push all records to Google Sheets?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )
        if reply == QMessageBox.Yes:
            self.push_data_to_sheets()

    def push_data_to_sheets(self):
        import database as database_config
        creds = database_config.get_system_setting("google_credentials_path", "")
        if not creds or not os.path.exists(creds):
            reply = QMessageBox.warning(
                self, "Credentials Needed",
                "Google credentials file path is empty or does not exist.\n\nWould you like to open the Settings tab to select your credentials.json file?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
            )
            if reply == QMessageBox.Yes:
                self.switch_page(3)
            return
            
        self.statusBar().showMessage("Syncing database to Google Sheets in background...", 5000)
        self.setCursor(Qt.WaitCursor)
        self.set_sync_buttons_enabled(False)
        
        from services.google_sheets import GoogleSyncWorker
        from ui.dialogs import SyncProgressDialog
        
        self.push_worker = GoogleSyncWorker(action_type="push")
        self.progress_dlg = SyncProgressDialog(title="Syncing Database to Google Sheets...", parent=self)
        self.push_worker.progress.connect(self.progress_dlg.update_progress)
        
        def on_push_finished(success, result):
            self.progress_dlg.close()
            self.unsetCursor()
            self.set_sync_buttons_enabled(True)
            if success:
                self.statusBar().showMessage("Google Sheets Sync Completed!", 5000)
                QMessageBox.information(self, "Sync Complete", f"All SQLite tables successfully pushed to Google Sheets!\n\nSpreadsheet ID: {result}")
            else:
                self.statusBar().showMessage(f"Sync Failed: {result}", 5000)
                if "NETWORK_ERROR" in str(result) or "getaddrinfo" in str(result) or "nameresolutionerror" in str(result).lower():
                    QMessageBox.warning(
                        self, "📡 Internet Connection Required",
                        "Unable to connect to Google Servers.\n\nPlease check your internet connection or Wi-Fi settings and try again.\n\n(Your local records in SQLite remain completely safe!)"
                    )
                else:
                    reply = QMessageBox.critical(
                        self, "Authentication Failed",
                        f"Synchronization failed:\n{result}\n\nWould you like to open the Settings tab to locate your credentials file?",
                        QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
                    )
                    if reply == QMessageBox.Yes:
                        self.switch_page(3)
                
        self.push_worker.finished.connect(on_push_finished)
        self.push_worker.start()
        self.progress_dlg.show()

    def pull_data_from_sheets(self):
        import database as database_config
        creds = database_config.get_system_setting("google_credentials_path", "")
        if not creds or not os.path.exists(creds):
            reply = QMessageBox.warning(
                self, "Credentials Needed",
                "Google credentials file path is empty or does not exist.\n\nWould you like to open the Settings tab to select your credentials.json file?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
            )
            if reply == QMessageBox.Yes:
                self.switch_page(3)
            return
            
        reply = QMessageBox.question(
            self, "Confirm Pull & Merge",
            "This will overwrite local records with the latest row values from Google Sheets. Proceed?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )
        if reply != QMessageBox.Yes:
            return
            
        self.statusBar().showMessage("Pulling online data from Google Sheets in background...", 5000)
        self.setCursor(Qt.WaitCursor)
        self.set_sync_buttons_enabled(False)
        
        from services.google_sheets import GoogleSyncWorker
        from ui.dialogs import SyncProgressDialog
        
        self.pull_worker = GoogleSyncWorker(action_type="pull")
        self.progress_dlg = SyncProgressDialog(title="Pulling Data from Google Sheets...", parent=self)
        self.pull_worker.progress.connect(self.progress_dlg.update_progress)
        
        def on_pull_finished(success, result):
            self.progress_dlg.close()
            self.unsetCursor()
            self.set_sync_buttons_enabled(True)
            if success:
                self.statusBar().showMessage("Google Sheets Pull Completed!", 5000)
                QMessageBox.information(self, "Sync Complete", "Successfully pulled online changes from Google Sheets and merged them into the local database!")
                self.refresh_all_data()
            else:
                self.statusBar().showMessage(f"Pull Failed: {result}", 5000)
                if "NETWORK_ERROR" in str(result) or "getaddrinfo" in str(result) or "nameresolutionerror" in str(result).lower():
                    QMessageBox.warning(
                        self, "📡 Internet Connection Required",
                        "Unable to connect to Google Servers.\n\nPlease check your internet connection or Wi-Fi settings and try again.\n\n(Your local records in SQLite remain completely safe!)"
                    )
                else:
                    reply = QMessageBox.critical(
                        self, "Authentication Failed",
                        f"Pull failed:\n{result}\n\nWould you like to open the Settings tab to locate your credentials file?",
                        QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
                    )
                    if reply == QMessageBox.Yes:
                        self.switch_page(3)
                
        self.pull_worker.finished.connect(on_pull_finished)
        self.pull_worker.start()
        self.progress_dlg.show()

    def trigger_background_push(self, silent=True):
        import database as database_config
        import os
        creds = database_config.get_system_setting("google_credentials_path", "")
        if not creds or not os.path.exists(creds):
            return
            
        token_path = os.path.join(os.path.dirname(creds), 'token.json')
        if not os.path.exists(token_path):
            return
            
        try:
            if hasattr(self, "_bg_push_worker") and self._bg_push_worker.isRunning():
                return
                
            from services.google_sheets import GoogleSyncWorker
            self._bg_push_worker = GoogleSyncWorker(action_type="push")
            
            if silent:
                self.statusBar().showMessage("Syncing database to Google Sheets in background...", 3000)
                self._bg_push_worker.finished.connect(lambda success, msg: self.statusBar().showMessage("Google Sheets Sync Completed!" if success else f"Auto-Sync Failed: {msg}", 4000))
            else:
                self.setCursor(Qt.WaitCursor)
                def on_finished(success, result):
                    self.unsetCursor()
                    if success:
                        self.statusBar().showMessage("Google Sheets Sync Completed!", 4000)
                        QMessageBox.information(self, "Sync Complete", f"All SQLite tables successfully pushed to Google Sheets!\n\nSpreadsheet ID: {result}")
                    else:
                        self.statusBar().showMessage(f"Sync Failed: {result}", 4000)
                        QMessageBox.critical(self, "Sync Failed", f"Synchronization failed:\n{result}")
                self._bg_push_worker.finished.connect(on_finished)
                
            self._bg_push_worker.start()
        except Exception as e:
            print(f"Failed to trigger auto background push: {e}")

    def open_google_sheet_in_browser(self):
        import database as database_config
        sid = database_config.get_system_setting("google_spreadsheet_id", "").strip()
        if not sid:
            sid = self.sheet_id_input.text().strip()
        if sid:
            url = f"https://docs.google.com/spreadsheets/d/{sid}"
            from PySide6.QtGui import QDesktopServices
            from PySide6.QtCore import QUrl
            QDesktopServices.openUrl(QUrl(url))
        else:
            QMessageBox.warning(self, "No Spreadsheet ID", "Please specify or create a Google Spreadsheet ID first.")

    def open_google_folder_in_browser(self):
        import database as database_config
        fid = database_config.get_system_setting("google_drive_folder_id", "").strip()
        if not fid:
            fid = self.folder_id_input.text().strip()
        if fid:
            url = f"https://drive.google.com/drive/folders/{fid}"
            from PySide6.QtGui import QDesktopServices
            from PySide6.QtCore import QUrl
            QDesktopServices.openUrl(QUrl(url))
        else:
            QMessageBox.warning(self, "No Folder ID", "Please specify or create a Google Drive Folder ID first.")

    def perform_google_auto_setup(self):
        import database as database_config
        sheet_id = database_config.get_system_setting("google_spreadsheet_id", "")
        folder_id = database_config.get_system_setting("google_drive_folder_id", "")
        creds = database_config.get_system_setting("google_credentials_path", "")
        
        import os
        if creds and os.path.exists(creds):
            if not sheet_id or not folder_id:
                try:
                    import services.google_sheets as google_sync
                    created_new = False
                    if not sheet_id:
                        sheet_id = google_sync.ensure_spreadsheet()
                        self.sheet_id_input.setText(sheet_id)
                        created_new = True
                    if not folder_id:
                        folder_id = google_sync.ensure_drive_folder()
                        self.folder_id_input.setText(folder_id)
                    
                    if created_new:
                        google_sync.push_sqlite_to_sheets()
                        
                    print("Google auto-setup completed successfully.")
                    self.refresh_google_account_status()
                except Exception as e:
                    print(f"Google auto-setup skipped or failed: {e}")
                    self.refresh_google_account_status()

    def disconnect_google_account(self):
        reply = QMessageBox.question(
            self, "Confirm Disconnect",
            "Are you sure you want to disconnect and log out of your Google Account?\n\nThis will clear all local session tokens and reset your Spreadsheet/Folder links.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
            
        try:
            import database as database_config
            import os
            
            # 1. Delete token.json
            creds_path = database_config.get_system_setting("google_credentials_path", "")
            if creds_path:
                token_path = os.path.join(os.path.dirname(creds_path), 'token.json')
                if os.path.exists(token_path):
                    os.remove(token_path)
            
            # 2. Reset database configurations
            database_config.set_system_setting("google_spreadsheet_id", "")
            database_config.set_system_setting("google_drive_folder_id", "")
            
            # 3. Update GUI inputs
            self.sheet_id_input.setText("")
            self.folder_id_input.setText("")
            
            QMessageBox.information(
                self, "Disconnected",
                "Google Account successfully disconnected!\n\nThe local session has been cleared."
            )
            self.refresh_google_account_status()
        except Exception as e:
            QMessageBox.critical(
                self, "Error",
                f"Failed to disconnect Google Account:\n{e}"
            )

    def connect_google_account(self):
        self.setCursor(Qt.WaitCursor)
        try:
            import services.google_sheets as google_sync
            google_sync.get_google_services()
            QMessageBox.information(self, "Connected", "Google Account successfully connected!")
            self.refresh_google_account_status()
        except Exception as e:
            QMessageBox.critical(self, "Authentication Failed", f"Failed to authenticate:\n{e}")
        finally:
            self.unsetCursor()

    def refresh_google_account_status(self):
        try:
            import services.google_sheets as google_sync
            email = google_sync.get_connected_email()
            if email:
                self.lbl_auth_status.setText("🟢 Connected")
                self.lbl_auth_status.setStyleSheet("font-weight: bold; color: #00ffcc;")
                self.lbl_auth_email.setText(email)
                self.btn_connect_google.setEnabled(False)
                self.btn_disconnect_google.setEnabled(True)
            else:
                self.lbl_auth_status.setText("🔴 Disconnected")
                self.lbl_auth_status.setStyleSheet("font-weight: bold; color: #ff6666;")
                self.lbl_auth_email.setText("Not Logged In")
                self.btn_connect_google.setEnabled(True)
                self.btn_disconnect_google.setEnabled(False)
        except Exception:
            self.lbl_auth_status.setText("🔴 Disconnected")
            self.lbl_auth_status.setStyleSheet("font-weight: bold; color: #ff6666;")
            self.lbl_auth_email.setText("Not Logged In")
            self.btn_connect_google.setEnabled(True)
            self.btn_disconnect_google.setEnabled(False)

def clean_temp_files():
    import tempfile
    import glob
    try:
        temp_dir = tempfile.gettempdir()
        pattern = os.path.join(temp_dir, "procurement_temp_*")
        for f in glob.glob(pattern):
            try:
                os.unlink(f)
            except Exception:
                pass
    except Exception as e:
        print(f"Error cleaning temp files: {e}")

