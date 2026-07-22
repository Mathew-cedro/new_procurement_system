from PySide6.QtWidgets import (
    QFrame, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, 
    QDialog, QScrollArea, QGroupBox, QGridLayout, QPushButton,
    QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QCursor, QDesktopServices
import os
import database as database_config

class ProcurementStepperWidget(QWidget):
    def __init__(self, project_data, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(4)
        
        status_text = (project_data.get("status") or "").lower()
        has_contract = bool(project_data.get("po_jo_contract_no") or (project_data.get("contract_amount", 0.0) or 0.0) > 0)
        has_supplier = bool(project_data.get("supplier_name"))
        has_abstract = bool(project_data.get("abstract_of_quotations_no"))
        has_warranty = "warranty" in status_text
        has_delivery = "deliver" in status_text or "payment" in status_text
        
        stages = [
            ("P0: PR/ABC", "🟢 Completed"),
            ("P1: Bidding", "🟢 Completed" if (has_abstract or has_contract or has_supplier) else ("🟡 Active" if "bid" in status_text or "plan" in status_text else "⚪ Pending")),
            ("P2: Contract", "🟢 Completed" if (has_contract and has_supplier) else ("🟡 Active" if ("contract" in status_text or "award" in status_text) else "⚪ Pending")),
            ("P3: Delivery", "🟢 Completed" if (has_delivery and has_warranty) else ("🟡 Active" if has_delivery else "⚪ Pending")),
            ("P4: Warranty", "🟢 Active" if has_warranty else "⚪ Pending")
        ]
        
        for name, state in stages:
            pill = QLabel(name)
            if "🟢" in state:
                pill.setStyleSheet("background-color: #123d24; color: #1F9D55; border: 1px solid #1F9D55; border-radius: 3px; font-size: 10px; font-weight: bold; padding: 2px 5px;")
                pill.setToolTip(f"{name}: Completed")
            elif "🟡" in state:
                pill.setStyleSheet("background-color: #3b350e; color: #FFDE15; border: 1px solid #FFDE15; border-radius: 3px; font-size: 10px; font-weight: bold; padding: 2px 5px;")
                pill.setToolTip(f"{name}: In Progress")
            else:
                pill.setStyleSheet("background-color: #1a2333; color: #64748b; border: 1px solid #253454; border-radius: 3px; font-size: 10px; padding: 2px 5px;")
                pill.setToolTip(f"{name}: Pending")
                
            layout.addWidget(pill)
            
            if name != "P4: Warranty":
                arrow = QLabel("➔")
                arrow.setStyleSheet("color: #475569; font-size: 9px; border: none; background: transparent;")
                layout.addWidget(arrow)
        layout.addStretch()

class ProjectCardWidget(QFrame):
    clicked = Signal(str)  # Emits project_id when clicked
    
    def __init__(self, project_data):
        super().__init__()
        self.project_id = project_data["id"]
        self.project_data = project_data
        
        self.setFrameShape(QFrame.StyledPanel)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setMinimumWidth(650)
        self.setMaximumWidth(1600)
        self.setMinimumHeight(155)
        self.setMaximumHeight(195)
        
        # Style sheet with hover effects
        import database as database_config
        theme = database_config.get_theme_setting()
        if theme == "light":
            c_bg_card = "#F4F6F9"
            c_border_card = "#cbd5e1"
            c_bg_hover = "#ffffff"
            c_accent = "#002C76"
            c_text_main = "#10182B"
            c_text_muted = "#475569"
        else:
            c_bg_card = "#182238"
            c_border_card = "#253454"
            c_bg_hover = "#1e2c47"
            c_accent = "#FFDE15"
            c_text_main = "#ffffff"
            c_text_muted = "#94a3b8"

        self.setObjectName("ProjectCard")
        self.setStyleSheet(f"""
            #ProjectCard {{
                background-color: {c_bg_card};
                border: 1px solid {c_border_card};
                border-radius: 10px;
            }}
            #ProjectCard:hover {{
                border: 1px solid {c_accent};
                background-color: {c_bg_hover};
            }}
        """)
        
        main_h_layout = QHBoxLayout(self)
        main_h_layout.setSpacing(25)
        main_h_layout.setContentsMargins(20, 15, 20, 15)
        
        # 1. LEFT COLUMN (Project Primary Info)
        left_layout = QVBoxLayout()
        left_layout.setSpacing(6)
        
        id_row_layout = QHBoxLayout()
        id_label = QLabel(project_data.get("proj_id_no", "N/A"))
        id_label.setStyleSheet(f"""
            font-size: 11px;
            font-weight: bold;
            color: #ffffff;
            background-color: {c_accent};
            border-radius: 4px;
            padding: 3px 8px;
            border: none;
        """)
        id_row_layout.addWidget(id_label)
        
        mode_label = QLabel(project_data.get("mode_of_procurement", "N/A"))
        mode_label.setStyleSheet(f"""
            font-size: 11px;
            font-weight: bold;
            color: #ffffff;
            background-color: #1f4e78;
            border-radius: 4px;
            padding: 3px 8px;
            border: none;
        """)
        id_row_layout.addWidget(mode_label)
        
        date_label = QLabel(project_data.get("date_received_bacsec", "N/A"))
        date_label.setStyleSheet(f"""
            font-size: 11px;
            font-weight: bold;
            color: {c_text_muted};
            border: none;
            background: transparent;
        """)
        id_row_layout.addWidget(date_label)
        
        id_row_layout.addStretch()
        left_layout.addLayout(id_row_layout)
        
        title_label = QLabel(project_data.get("project_name", "Unnamed Project"))
        title_label.setWordWrap(True)
        title_label.setStyleSheet(f"color: {c_text_main}; font-size: 14px; font-weight: bold; border: none; background: transparent;")
        left_layout.addWidget(title_label)
        
        meta_layout = QHBoxLayout()
        div_label = QLabel(f"🏢 {project_data.get('bureau_division_name', 'N/A')}")
        div_label.setStyleSheet(f"color: {c_text_muted}; font-size: 11px; border: none; background: transparent;")
        focal_label = QLabel(f"👤 {project_data.get('focal_person', 'N/A')}")
        focal_label.setStyleSheet(f"color: {c_text_muted}; font-size: 11px; margin-left: 15px; border: none; background: transparent;")
        meta_layout.addWidget(div_label)
        meta_layout.addWidget(focal_label)
        meta_layout.addStretch()
        left_layout.addLayout(meta_layout)
        
        # Procurement Stage Stepper
        stepper = ProcurementStepperWidget(project_data)
        left_layout.addWidget(stepper)
        
        remarks = project_data.get("remarks")
        if remarks and remarks.strip():
            truncated = remarks if len(remarks) <= 80 else remarks[:77] + "..."
            remarks_lbl = QLabel(f"💬 <i>Remarks: {truncated}</i>")
            remarks_lbl.setWordWrap(True)
            remarks_lbl.setStyleSheet(f"color: {c_accent}; font-size: 11px; margin-top: 5px; border: none; background: transparent;")
            left_layout.addWidget(remarks_lbl)
            
        main_h_layout.addLayout(left_layout, stretch=4)
        
        # 2. MIDDLE COLUMN (Registry & Contract Details)
        middle_layout = QVBoxLayout()
        middle_layout.setSpacing(5)
        middle_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        mid_title = QLabel("Registry & Procurement Details")
        mid_title.setStyleSheet(f"color: {c_accent}; font-size: 11px; font-weight: bold; border: none; background: transparent;")
        middle_layout.addWidget(mid_title)
        
        saro = project_data.get("saro_number") or "N/A"
        funds = project_data.get("fund_source") or "N/A"
        saro_label = QLabel(f"🔑 SARO: {saro} ({funds})")
        saro_label.setStyleSheet(f"color: {c_text_muted}; font-size: 11px; border: none; background: transparent;")
        middle_layout.addWidget(saro_label)
        
        ors_serial = project_data.get("ors_serial_no")
        ors_amt = project_data.get("ors_amount", 0.0) or 0.0
        if ors_serial:
            ors_label = QLabel(f"💵 ORS Serial: {ors_serial} | ₱{ors_amt:,.2f}")
        else:
            ors_label = QLabel("💵 ORS Serial: Pending ORS assignment")
        ors_label.setStyleSheet(f"color: {c_text_muted}; font-size: 11px; border: none; background: transparent;")
        middle_layout.addWidget(ors_label)
        
        supplier = project_data.get("supplier_name")
        po_no = project_data.get("po_jo_contract_no")
        if supplier:
            sup_label = QLabel(f"🤝 Supplier: {supplier} ({po_no})")
            sup_label.setStyleSheet(f"color: {c_accent}; font-size: 11px; font-weight: bold; border: none; background: transparent;")
        else:
            sup_label = QLabel("🤝 Supplier: Pending award")
            sup_label.setStyleSheet(f"color: {c_text_muted}; font-size: 11px; border: none; background: transparent;")
        middle_layout.addWidget(sup_label)
        
        main_h_layout.addLayout(middle_layout, stretch=4)
        
        # 3. RIGHT COLUMN (Status, Progress & Financial Values)
        right_layout = QVBoxLayout()
        right_layout.setSpacing(6)
        right_layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        status_label = QLabel(project_data.get("status", "Planning & Bidding"))
        status_color = "#33ccff"
        status_bg = "#1e3a4a"
        status_lower = status_label.text().lower()
        if "warranty" in status_lower:
            status_color = "#2ecc71"
            status_bg = "#1a3a2a"
        elif "deliver" in status_lower or "payment" in status_lower:
            status_color = "#33ccff"
            status_bg = "#1e3a4a"
        elif "bid" in status_lower or "plan" in status_lower:
            status_color = "#ffaa00"
            status_bg = "#3a2a1a"
        elif "contract" in status_lower or "award" in status_lower:
            status_color = "#33ccff"
            status_bg = "#1e3a4a"
        elif "delay" in status_lower or "cancel" in status_lower:
            status_color = "#ff6666"
            status_bg = "#3a1a1a"
            
        status_label.setStyleSheet(f"""
            color: {status_color}; font-size: 11px; font-weight: bold; 
            background-color: {status_bg}; border-radius: 4px; padding: 3px 8px; border: none;
        """)
        
        status_container = QHBoxLayout()
        status_container.addStretch()
        status_container.addWidget(status_label)
        right_layout.addLayout(status_container)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setMinimumWidth(150)
        
        progress_val = 25
        if "warranty" in status_lower or "complete" in status_lower:
            progress_val = 100
        elif "deliver" in status_lower or "payment" in status_lower:
            progress_val = 75
        elif "contract" in status_lower or "award" in status_lower:
            progress_val = 50
        elif "bid" in status_lower or "plan" in status_lower:
            progress_val = 25
            
        self.progress_bar.setValue(progress_val)
        
        bar_color = "#33ccff"
        if progress_val == 100:
            bar_color = "#2ecc71"
        elif progress_val == 25:
            bar_color = "#ffaa00"
            
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: #1a1a24;
                border: none;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {bar_color};
                border-radius: 3px;
            }}
        """)
        
        pb_container = QHBoxLayout()
        pb_container.addStretch()
        pb_container.addWidget(self.progress_bar)
        right_layout.addLayout(pb_container)
        
        amounts_layout = QVBoxLayout()
        amounts_layout.setSpacing(3)
        
        abc_amount = project_data.get("abc_amount", 0.0) or 0.0
        contract_amount = project_data.get("contract_amount", 0.0) or 0.0
        
        abc_val = QLabel(f"ABC: ₱{abc_amount:,.2f}")
        abc_val.setStyleSheet("color: #a0a0b0; font-size: 11px; text-align: right; border: none; background: transparent;")
        abc_val.setAlignment(Qt.AlignRight)
        amounts_layout.addWidget(abc_val)
        
        if contract_amount > 0:
            ctr_val = QLabel(f"Contract Price: ₱{contract_amount:,.2f}")
            ctr_val.setStyleSheet("color: #00ffcc; font-size: 11px; font-weight: bold; text-align: right; border: none; background: transparent;")
            ctr_val.setAlignment(Qt.AlignRight)
            amounts_layout.addWidget(ctr_val)
            
            savings_amount = max(0.0, abc_amount - contract_amount)
            savings_val = QLabel(f"Savings: ₱{savings_amount:,.2f}")
            savings_val.setStyleSheet("color: #2befa3; font-size: 11px; font-weight: bold; text-align: right; border: none; background: transparent;")
            savings_val.setAlignment(Qt.AlignRight)
            amounts_layout.addWidget(savings_val)
            
        right_layout.addLayout(amounts_layout)
        
        main_h_layout.addLayout(right_layout, stretch=3)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.project_id)
        try:
            super().mousePressEvent(event)
        except RuntimeError:
            pass  # C++ object already deleted by refresh

class ProjectDetailDialog(QDialog):
    def __init__(self, project_id, parent=None):
        super().__init__(parent)
        self.project_id = project_id
        # Make the window adjustable, resizable, and maximizable
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint)
        
        # Fetch data
        import database as database_config
        self.project_data = database_config.get_project_detail(project_id)
        
        if not self.project_data:
            self.setWindowTitle("Project Not Found")
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel("Error: Could not retrieve project details."))
            return
            
        self.setWindowTitle(f"Project Timeline - {self.project_data.get('proj_id_no', 'N/A')}")
        self.resize(1000, 820)
        theme = database_config.get_theme_setting()
        if theme == "light":
            c_bg_app = "#f1f5f9"
            c_bg_card = "#ffffff"
            c_border_card = "#cbd5e1"
            c_text_main = "#0f172a"
        else:
            c_bg_app = "#1e1e24"
            c_bg_card = "#13131a"
            c_border_card = "#2b2b36"
            c_text_main = "#ffffff"
            
        self.setStyleSheet(f"background-color: {c_bg_app}; color: {c_text_main};")
        
        # Main Layout
        self.dialog_layout = QVBoxLayout(self)
        self.dialog_layout.setContentsMargins(20, 20, 20, 20)
        self.dialog_layout.setSpacing(15)
        
        # Header Section
        self.header = QFrame()
        self.header.setStyleSheet(f"background-color: {c_bg_card}; border-radius: 8px; border: 1px solid {c_border_card};")
        self.header_layout = QVBoxLayout(self.header)
        self.header_layout.setContentsMargins(20, 15, 20, 15)
        self.header_layout.setSpacing(8)
        self.dialog_layout.addWidget(self.header)
        
        # Scroll Area for Details Timeline
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        self.dialog_layout.addWidget(self.scroll)
        
        # Bottom Button Row Layout
        btn_row_layout = QHBoxLayout()
        
        self.delete_btn = QPushButton("🗑️ Delete Project")
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #5c1d1d; color: #ff9999;
                font-weight: bold; border-radius: 5px; padding: 10px 20px;
                border: 1px solid #8c2d2d; font-size: 13px;
            }
            QPushButton:hover { background-color: #7c2d2d; color: #ffffff; }
        """)
        self.delete_btn.clicked.connect(self.confirm_delete_project)
        btn_row_layout.addWidget(self.delete_btn)
        
        btn_row_layout.addStretch()
        
        self.close_btn = QPushButton("Close")
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a3a4a; color: #ffffff;
                font-weight: bold; border-radius: 5px; padding: 10px 20px;
                border: 1px solid #5a5a6a; font-size: 13px;
            }
            QPushButton:hover { background-color: #4a4a5a; }
        """)
        self.close_btn.clicked.connect(self.accept)
        btn_row_layout.addWidget(self.close_btn)
        
        self.dialog_layout.addLayout(btn_row_layout)
        
        self.build_timeline()

    def build_timeline(self):
        project_docs = {}
        for doc in self.project_data.get("documents", []):
            project_docs[doc["document_type"]] = doc.get("file_reference")

        def open_uploaded_document(doc_type, relative_path):
            if not relative_path:
                return
            if relative_path.startswith("http://") or relative_path.startswith("https://"):
                QDesktopServices.openUrl(QUrl(relative_path))
                return
            try:
                import tempfile
                import shutil
                import database as database_config
                
                # Fetch BLOB from database
                content, ref_name = database_config.get_document_data(self.project_id, doc_type)
                
                if content:
                    ref_name = ref_name or relative_path
                    suffix = os.path.splitext(ref_name)[1] or ".pdf"
                    
                    # Write to a deterministic temporary file path
                    temp_dir = tempfile.gettempdir()
                    temp_filename = f"procurement_temp_proj_{self.project_id}_{doc_type}{suffix}"
                    temp_path = os.path.normpath(os.path.join(temp_dir, temp_filename))
                    
                    with open(temp_path, "wb") as tmp_f:
                        tmp_f.write(content)
                        
                    if hasattr(os, "startfile"):
                        os.startfile(temp_path)
                    else:
                        QDesktopServices.openUrl(QUrl.fromLocalFile(temp_path))
                else:
                    # Fallback to filesystem if BLOB is not yet set
                    base_dir = os.path.dirname(os.path.abspath(__file__))
                    full_path = os.path.normpath(os.path.join(base_dir, relative_path))
                    if os.path.exists(full_path):
                        if hasattr(os, "startfile"):
                            os.startfile(full_path)
                        else:
                            QDesktopServices.openUrl(QUrl.fromLocalFile(full_path))
                    else:
                        QMessageBox.warning(self, "File Not Found", f"The document file could not be found in DB or at:\n{full_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load document: {e}")

        def make_doc_btn(doc_type, display_name):
            file_ref = project_docs.get(doc_type)
            if file_ref:
                btn = QPushButton(f"📄 Open {display_name}")
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #1a2d3c;
                        color: #33ccff;
                        font-weight: bold;
                        border: 1px solid #33ccff;
                        border-radius: 4px;
                        padding: 4px 8px;
                        font-size: 12px;
                    }
                    QPushButton:hover {
                        background-color: #33ccff;
                        color: #13131a;
                    }
                """)
                btn.clicked.connect(lambda checked=False, dtype=doc_type, path=file_ref: open_uploaded_document(dtype, path))
                return btn
            else:
                lbl = QLabel(f"<i>No {display_name} Uploaded</i>")
                lbl.setStyleSheet("color: #aaaaaa; font-size: 12px; border: none; background: transparent;")
                return lbl

        # Clear header layout
        while self.header_layout.count():
            child = self.header_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        # Rebuild header contents
        title_label = QLabel(self.project_data.get("project_name", "N/A"))
        title_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #00ffcc; border: none; background: transparent;")
        title_label.setWordWrap(True)
        self.header_layout.addWidget(title_label)
        
        meta_layout = QHBoxLayout()
        meta_layout.setSpacing(10)
        
        id_lbl = QLabel(f"ID: {self.project_data.get('proj_id_no', 'N/A')}")
        id_lbl.setStyleSheet("color: #00ffcc; font-size: 12px; font-weight: bold; background-color: #1a332d; border-radius: 4px; padding: 4px 10px; border: none;")
        
        div_lbl = QLabel(f"Division: {self.project_data.get('bureau_division_name', 'N/A')}")
        div_lbl.setStyleSheet("color: #33ccff; font-size: 12px; font-weight: bold; background-color: #1a2d3c; border-radius: 4px; padding: 4px 10px; border: none;")
        
        focal_lbl = QLabel(f"Focal: {self.project_data.get('focal_person', 'N/A')}")
        focal_lbl.setStyleSheet("color: #ffffff; font-size: 12px; font-weight: bold; background-color: #2b2b36; border-radius: 4px; padding: 4px 10px; border: none;")
        
        meta_layout.addWidget(id_lbl)
        meta_layout.addWidget(div_lbl)
        meta_layout.addWidget(focal_lbl)
        meta_layout.addStretch()
        self.header_layout.addLayout(meta_layout)
        
        # Rebuild scroll widget
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: transparent;")
        timeline_layout = QVBoxLayout(scroll_content)
        timeline_layout.setSpacing(20)
        timeline_layout.setContentsMargins(0, 0, 10, 0)
        
        # Helper to set word wrap on Grid/Form QLabels
        def wrap_lbl(text, style="color: #ffffff; font-size: 13px; border: none; background: transparent;"):
            lbl = QLabel(text)
            lbl.setStyleSheet(style)
            lbl.setWordWrap(True)
            return lbl

        # Phase 1: Planning & Bidding (Merges original Phase 1 & 2)
        planning_box = QGroupBox("Phase 1: Planning & Bidding")
        planning_box.setStyleSheet(self.groupbox_style())
        planning_layout = QGridLayout(planning_box)
        planning_layout.setContentsMargins(15, 20, 15, 15)
        planning_layout.setSpacing(10)
        
        planning_layout.addWidget(wrap_lbl("<b>ABC Amount:</b>"), 0, 0)
        abc_amount = self.project_data.get("abc_amount", 0.0) or 0.0
        planning_layout.addWidget(wrap_lbl(f"₱{abc_amount:,.2f}"), 0, 1)
        planning_layout.addWidget(wrap_lbl("<b>Source of Funds:</b>"), 0, 2)
        planning_layout.addWidget(wrap_lbl(f"{self.project_data.get('source_of_funds', 'N/A')} ({self.project_data.get('fund_source', 'N/A')})"), 0, 3)
        planning_layout.addWidget(wrap_lbl("<b>Mode of Procurement:</b>"), 1, 0)
        planning_layout.addWidget(wrap_lbl(self.project_data.get("mode_of_procurement", "N/A")), 1, 1)
        planning_layout.addWidget(wrap_lbl("<b>App Cycle:</b>"), 1, 2)
        planning_layout.addWidget(wrap_lbl(f"Cycle {self.project_data.get('app_cycle', 'N/A')}"), 1, 3)
        
        edit_plan_btn = QPushButton("✏️ Edit Details")
        edit_plan_btn.setStyleSheet(self.btn_edit_style())
        edit_plan_btn.clicked.connect(self.edit_project_details)
        planning_layout.addWidget(edit_plan_btn, 0, 4, 1, 1, Qt.AlignRight | Qt.AlignTop)
        
        # Add SARO view row
        planning_layout.addWidget(wrap_lbl("<b>SARO Number:</b>"), 2, 0)
        planning_layout.addWidget(wrap_lbl(self.project_data.get("saro_number", "N/A")), 2, 1)
        
        budgets = self.project_data.get("budgets", [])
        if budgets:
            planning_layout.addWidget(wrap_lbl("<b>Budget Lines:</b>"), 3, 0)
            b_info = []
            for b in budgets:
                b_info.append(f"{b.get('budget_type', 'N/A')} - App: ₱{b.get('app_amount', 0.0):,.2f} | ORS: ₱{b.get('ors_amount', 0.0):,.2f} ({b.get('ors_serial_no', 'N/A')})")
            planning_layout.addWidget(wrap_lbl("\n".join(b_info)), 3, 1, 1, 3)
            
        # Spacing
        planning_layout.addWidget(wrap_lbl("<hr style='border: 1px solid #2b2b36;' />"), 4, 0, 1, 5)
        
        # Bids section
        bids = self.project_data.get("bids", [])
        if bids:
            b = bids[0]
            planning_layout.addWidget(wrap_lbl("<b>Bids Received:</b>"), 5, 0)
            bid_info = f"🎟️ Bid Ref: {b.get('bid_reference_no', 'N/A')} | BACSec Recd: {b.get('date_received_bacsec', 'N/A')} | PCMD Recd: {b.get('date_received_pcmd_initial', 'N/A') or 'Pending'}"
            planning_layout.addWidget(wrap_lbl(bid_info), 5, 1, 1, 3)
            
            planning_layout.addWidget(wrap_lbl("<b>Purchase Request:</b>"), 6, 0)
            pr_val = b.get('purchase_request_no') or "N/A"
            planning_layout.addWidget(wrap_lbl(pr_val), 6, 1)
            
            planning_layout.addWidget(wrap_lbl("<b>PhilGEPS Posting:</b>"), 6, 2)
            phil_val = b.get('post_to_philgeps') or "Auto-detect by Value (>= ₱200k)"
            if "Auto-detect" in phil_val:
                abc = self.project_data.get("abc_amount", 0.0) or 0.0
                decision = "Yes (Auto-detected: ABC ₱{:,.2f} >= ₱200k)".format(abc) if abc >= 200000 else "No (Auto-detected: ABC ₱{:,.2f} < ₱200k)".format(abc)
                planning_layout.addWidget(wrap_lbl(decision), 6, 3)
            else:
                planning_layout.addWidget(wrap_lbl(phil_val), 6, 3)
                
            planning_layout.addWidget(wrap_lbl("<b>Abstract No:</b>"), 7, 0)
            abs_val = b.get('abstract_of_quotations_no') or "N/A"
            planning_layout.addWidget(wrap_lbl(abs_val), 7, 1)
            
            planning_layout.addWidget(wrap_lbl("<b>BAC Resolution No:</b>"), 7, 2)
            reso_val = b.get('bac_resolution_no') or "N/A (Using Notice of Award)"
            planning_layout.addWidget(wrap_lbl(reso_val), 7, 3)
            
            edit_bid_btn = QPushButton("✏️ Edit Bidding")
            edit_bid_btn.setStyleSheet(self.btn_edit_style())
            edit_bid_btn.clicked.connect(lambda checked=False, b_data=b: self.edit_bidding_details(b_data))
            planning_layout.addWidget(edit_bid_btn, 5, 4, 1, 1, Qt.AlignRight | Qt.AlignTop)
        else:
            planning_layout.addWidget(wrap_lbl("<b>Bidding Details:</b>"), 5, 0)
            planning_layout.addWidget(wrap_lbl("No bidding details recorded yet."), 5, 1, 1, 2)
            
            add_bid_btn = QPushButton("➕ Add Bidding Details")
            add_bid_btn.setStyleSheet(self.btn_progression_style())
            add_bid_btn.clicked.connect(self.add_bidding_details)
            planning_layout.addWidget(add_bid_btn, 5, 3, 1, 1, Qt.AlignRight | Qt.AlignVCenter)

        # Document buttons at the bottom of Phase 1
        p1_doc_row = planning_layout.rowCount()
        planning_layout.addWidget(wrap_lbl("<b>Phase 1 Documents:</b>"), p1_doc_row, 0)
        p1_docs_layout = QHBoxLayout()
        p1_docs_layout.setSpacing(6)
        p1_docs_layout.addWidget(make_doc_btn("SARO", "SARO"))
        p1_docs_layout.addWidget(make_doc_btn("PPMP", "PPMP"))
        p1_docs_layout.addWidget(make_doc_btn("MS", "Market Scoping"))
        p1_docs_layout.addWidget(make_doc_btn("TS", "Tech Specs/TOR"))
        p1_docs_layout.addWidget(make_doc_btn("Abstract", "Abstract"))
        p1_docs_layout.addStretch()
        planning_layout.addLayout(p1_docs_layout, p1_doc_row, 1, 1, 4)
        
        timeline_layout.addWidget(planning_box)
        
        # Phase 2: Contract Award & Supplier (Original Phase 3)
        contracts = self.project_data.get("contracts", [])
        contract_box = QGroupBox("Phase 2: Contract Award & Supplier details")
        contract_box.setStyleSheet(self.groupbox_style())
        contract_layout = QGridLayout(contract_box)
        contract_layout.setContentsMargins(15, 20, 15, 15)
        contract_layout.setSpacing(10)
        
        if contracts:
            c = contracts[0]
            contract_layout.addWidget(wrap_lbl("<b>Supplier Name:</b>"), 0, 0)
            contract_layout.addWidget(wrap_lbl(c.get("supplier_name", "N/A")), 0, 1)
            contract_layout.addWidget(wrap_lbl("<b>Supplier TIN:</b>"), 0, 2)
            contract_layout.addWidget(wrap_lbl(c.get("supplier_tin_no", "N/A")), 0, 3)
            
            contract_layout.addWidget(wrap_lbl("<b>Supplier Address:</b>"), 1, 0)
            contract_layout.addWidget(wrap_lbl(c.get("supplier_address", "N/A")), 1, 1, 1, 3)
            
            contract_layout.addWidget(wrap_lbl("<b>PO/JO Contract No:</b>"), 2, 0)
            contract_layout.addWidget(wrap_lbl(c.get("po_jo_contract_no", "N/A")), 2, 1)
            contract_layout.addWidget(wrap_lbl("<b>Contract Price:</b>"), 2, 2)
            c_amount = c.get("contract_amount", 0.0) or 0.0
            contract_layout.addWidget(wrap_lbl(f"₱{c_amount:,.2f}"), 2, 3)
            
            contract_layout.addWidget(wrap_lbl("<b>Notice of Award:</b>"), 3, 0)
            contract_layout.addWidget(wrap_lbl(c.get("notice_of_award_date", "N/A")), 3, 1)
            contract_layout.addWidget(wrap_lbl("<b>Notice to Proceed:</b>"), 3, 2)
            contract_layout.addWidget(wrap_lbl(c.get("notice_to_proceed_date", "N/A")), 3, 3)
            
            contract_layout.addWidget(wrap_lbl("<b>Contract Period:</b>"), 4, 0)
            contract_layout.addWidget(wrap_lbl(f"{c.get('contract_duration_days', 'N/A')} days (Ends: {c.get('expected_end_of_contract', 'N/A')})"), 4, 1)
            contract_layout.addWidget(wrap_lbl("<b>Nature of Procurement:</b>"), 4, 2)
            contract_layout.addWidget(wrap_lbl(c.get("nature_of_procurement", "N/A")), 4, 3)
            
            contract_layout.addWidget(wrap_lbl("<b>Security Form:</b>"), 5, 0)
            contract_layout.addWidget(wrap_lbl(f"{c.get('performance_security_form', 'N/A')}"), 5, 1)
            contract_layout.addWidget(wrap_lbl("<b>Security Amount:</b>"), 5, 2)
            sec_amount = c.get("performance_security_amount", 0.0) or 0.0
            contract_layout.addWidget(wrap_lbl(f"₱{sec_amount:,.2f}"), 5, 3)
            
            # Savings (ABC - Contract Price)
            contract_layout.addWidget(wrap_lbl("<b>Savings (ABC - Contract):</b>"), 6, 0)
            abc_val = self.project_data.get("abc_amount", 0.0) or 0.0
            savings_val = max(0.0, abc_val - c_amount)
            contract_layout.addWidget(wrap_lbl(f"₱{savings_val:,.2f}"), 6, 1)
            
            amends = c.get("amendments", [])
            last_row = 7
            if amends:
                contract_layout.addWidget(wrap_lbl("<b>Amendments:</b>"), last_row, 0)
                amend_info = []
                for a in amends:
                    amend_info.append(f"🔄 {a.get('amendment_type', 'N/A')} | Variation: ₱{a.get('variation_order_amount', 0.0):,.2f} | Extension: {a.get('extension_days', 0)} days | Remarks: {a.get('remarks', 'None')}")
                contract_layout.addWidget(wrap_lbl("\n".join(amend_info)), last_row, 1, 1, 3)
                last_row += 1
                
            contract_layout.addWidget(wrap_lbl("<b>Phase 2 Documents:</b>"), last_row, 0)
            p2_docs_layout = QHBoxLayout()
            p2_docs_layout.setSpacing(6)
            p2_docs_layout.addWidget(make_doc_btn("NOA", "Notice of Award"))
            p2_docs_layout.addWidget(make_doc_btn("Contract", "Signed Contract"))
            p2_docs_layout.addWidget(make_doc_btn("BAC_Reso", "BAC Resolution"))
            p2_docs_layout.addWidget(make_doc_btn("RQ", "Request Order"))
            p2_docs_layout.addStretch()
            contract_layout.addLayout(p2_docs_layout, last_row, 1, 1, 3)
                
            edit_con_btn = QPushButton("✏️ Edit Details")
            edit_con_btn.setStyleSheet(self.btn_edit_style())
            edit_con_btn.clicked.connect(lambda checked=False, c_data=c: self.edit_contract_details(c_data))
            contract_layout.addWidget(edit_con_btn, 0, 4, 1, 1, Qt.AlignRight | Qt.AlignTop)
        else:
            contract_layout.addWidget(wrap_lbl("No contract awarded yet."), 0, 0, 1, 2)
            
            if bids:
                add_con_btn = QPushButton("➕ Add Contract Details")
                add_con_btn.setStyleSheet(self.btn_progression_style())
                bid_id = bids[0]["id"]
                add_con_btn.clicked.connect(lambda checked=False, b_id=bid_id: self.add_contract_details(b_id))
                contract_layout.addWidget(add_con_btn, 0, 3, 1, 1, Qt.AlignRight | Qt.AlignVCenter)
            else:
                contract_layout.addWidget(wrap_lbl("<i>Complete Bidding phase to proceed.</i>"), 0, 3, 1, 1)
                
        timeline_layout.addWidget(contract_box)
        
        # Phase 3: Deliveries & Payments (Merges original Phase 4 & 5)
        deliv_box = QGroupBox("Phase 3: Deliveries & Payments")
        deliv_box.setStyleSheet(self.groupbox_style())
        deliv_layout = QVBoxLayout(deliv_box)
        deliv_layout.setContentsMargins(15, 20, 15, 15)
        deliv_layout.setSpacing(10)
        
        # Document buttons at the top of Phase 3
        p3_docs_frame = QFrame()
        p3_docs_frame.setStyleSheet("background-color: transparent; border: none;")
        p3_docs_inner = QHBoxLayout(p3_docs_frame)
        p3_docs_inner.setContentsMargins(0, 0, 0, 0)
        p3_docs_inner.setSpacing(6)
        p3_docs_inner.addWidget(wrap_lbl("<b>Phase 3 Documents:</b>"))
        p3_docs_inner.addWidget(make_doc_btn("IAR", "IAR"))
        p3_docs_inner.addWidget(make_doc_btn("PO_Phase3", "Purchase Order"))
        p3_docs_inner.addWidget(make_doc_btn("Abstract", "Abstract of Quotations"))
        p3_docs_inner.addStretch()
        deliv_layout.addWidget(p3_docs_frame)
        
        # Section header
        deliv_layout.addWidget(wrap_lbl("<b>Milestone Deliverables:</b>", "color: #00ffcc; font-size: 13px; font-weight: bold; margin-top: 5px;"))
        
        has_deliv = False
        if contracts:
            for c in contracts:
                delivs = c.get("deliverables", [])
                if delivs:
                    has_deliv = True
                    for d in delivs:
                        d_frame = QFrame()
                        d_frame.setStyleSheet("background-color: #242430; border: 1px solid #3a3a4a; border-radius: 6px;")
                        df_layout = QGridLayout(d_frame)
                        df_layout.setContentsMargins(15, 15, 15, 15)
                        df_layout.setSpacing(8)
                        
                        df_layout.addWidget(wrap_lbl(f"<b>Milestone:</b> {d.get('milestone_deliverable', 'N/A')}"), 0, 0, 1, 3)
                        
                        edit_del_btn = QPushButton("✏️ Edit Milestone")
                        edit_del_btn.setStyleSheet(self.btn_edit_style())
                        edit_del_btn.clicked.connect(lambda checked=False, d_data=d: self.edit_deliverable_details(d_data))
                        df_layout.addWidget(edit_del_btn, 0, 3, 1, 1, Qt.AlignRight | Qt.AlignTop)
                        
                        df_layout.addWidget(wrap_lbl(f"<b>Status:</b> {d.get('status_of_delivery', 'N/A')}"), 1, 0)
                        df_layout.addWidget(wrap_lbl(f"<b>Expected Date:</b> {d.get('original_expected_delivery_date', 'N/A')}"), 1, 1)
                        df_layout.addWidget(wrap_lbl(f"<b>Revised Date:</b> {d.get('revised_delivery_date', 'N/A') or 'N/A'}"), 1, 2)
                        df_layout.addWidget(wrap_lbl(f"<b>Actual Date:</b> {d.get('actual_delivery_date', 'N/A') or 'Pending'}"), 1, 3)
                        
                        delay_days = d.get('days_delayed', 0)
                        df_layout.addWidget(wrap_lbl(f"<b>Delay:</b> {delay_days} days (LD Amount: ₱{d.get('liquidated_damages_amount', 0.0):,.2f})"), 2, 0, 1, 2)
                        df_layout.addWidget(wrap_lbl(f"<b>IAR No:</b> {d.get('iar_no', 'N/A')}"), 2, 2)
                        df_layout.addWidget(wrap_lbl(f"<b>Acceptance Date:</b> {d.get('acceptance_date', 'N/A')}"), 2, 3)
                        
                        deliv_layout.addWidget(d_frame)
            
            c_id = contracts[0]["id"]
            add_del_btn = QPushButton("➕ Add Deliverable Milestone")
            add_del_btn.setStyleSheet(self.btn_progression_style())
            add_del_btn.clicked.connect(lambda checked=False, con_id=c_id: self.add_deliverable_details(con_id))
            deliv_layout.addWidget(add_del_btn)
        else:
            deliv_layout.addWidget(wrap_lbl("No deliverables recorded yet."))
            deliv_layout.addWidget(wrap_lbl("<i>Complete Contract phase to proceed.</i>"))
            
        # Payments section header
        deliv_layout.addWidget(wrap_lbl("<b>Payment Disbursements:</b>", "color: #00ffcc; font-size: 13px; font-weight: bold; margin-top: 10px;"))
        
        has_payments = False
        if contracts:
            for c in contracts:
                for d in c.get("deliverables", []):
                    payments = d.get("payments", [])
                    if payments:
                        has_payments = True
                        for p in payments:
                            p_frame = QFrame()
                            p_frame.setStyleSheet("background-color: #242430; border: 1px solid #3a3a4a; border-radius: 6px;")
                            pf_layout = QGridLayout(p_frame)
                            pf_layout.setContentsMargins(15, 15, 15, 15)
                            pf_layout.setSpacing(8)
                            
                            pf_layout.addWidget(wrap_lbl(f"<b>Payment Type:</b> {p.get('types_of_payment', 'N/A')} ({p.get('payment_schedule_terms', 'N/A')})"), 0, 0, 1, 3)
                            
                            edit_pay_btn = QPushButton("✏️ Edit Record")
                            edit_pay_btn.setStyleSheet(self.btn_edit_style())
                            edit_pay_btn.clicked.connect(lambda checked=False, p_data=p: self.edit_payment_details(p_data))
                            pf_layout.addWidget(edit_pay_btn, 0, 3, 1, 1, Qt.AlignRight | Qt.AlignTop)
                            
                            gross = p.get('payment_amount_gross', 0.0) or 0.0
                            net = p.get('payment_amount_net', 0.0) or 0.0
                            pf_layout.addWidget(wrap_lbl(f"<b>Gross Amount:</b> ₱{gross:,.2f}"), 1, 0)
                            pf_layout.addWidget(wrap_lbl(f"<b>Net Amount:</b> ₱{net:,.2f}"), 1, 1)
                            pf_layout.addWidget(wrap_lbl(f"<b>Retention:</b> ₱{p.get('retention_fee', 0.0):,.2f} ({int(p.get('retention_rate', 0)*100)}%)"), 1, 2)
                            pf_layout.addWidget(wrap_lbl(f"<b>Withheld Tax:</b> ₱{p.get('ewt_1_goods', 0.0) + p.get('ewt_2_services', 0.0) + p.get('withholding_vat_5', 0.0):,.2f}"), 1, 3)
                            
                            pf_layout.addWidget(wrap_lbl(f"<b>DV/RCI Serial:</b> {p.get('rci_dv_acic_no', 'N/A')}"), 2, 0, 1, 2)
                            pf_layout.addWidget(wrap_lbl(f"<b>ADA No:</b> {p.get('check_lddap_ada_no', 'N/A')}"), 2, 2)
                            pf_layout.addWidget(wrap_lbl(f"<b>Check Date:</b> {p.get('check_date_lddap_ada', 'N/A')}"), 2, 3)
                            
                            pf_layout.addWidget(wrap_lbl(f"<b>Status:</b> {p.get('status_of_payment_documents', 'N/A')}"), 3, 0, 1, 4)
                            
                            deliv_layout.addWidget(p_frame)
            
            has_deliv_milestones = any(len(c.get("deliverables", [])) > 0 for c in contracts)
            if has_deliv_milestones:
                c_id = contracts[0]["id"]
                add_pay_btn = QPushButton("➕ Record Payment")
                add_pay_btn.setStyleSheet(self.btn_progression_style())
                add_pay_btn.clicked.connect(lambda checked=False, con_id=c_id, con_data=contracts[0]: self.add_payment_details(con_id, con_data))
                deliv_layout.addWidget(add_pay_btn)
            else:
                deliv_layout.addWidget(wrap_lbl("No payments recorded yet."))
                deliv_layout.addWidget(wrap_lbl("<i>Add Deliverable milestones first.</i>"))
        else:
            deliv_layout.addWidget(wrap_lbl("No payments recorded yet."))
            deliv_layout.addWidget(wrap_lbl("<i>Complete Contract phase to proceed.</i>"))
            
        timeline_layout.addWidget(deliv_box)
        
        # Phase 4: Warranty & Retention Release (Original Phase 6)
        warranty_box = QGroupBox("Phase 4: Warranty & Retention Release")
        warranty_box.setStyleSheet(self.groupbox_style())
        war_layout = QGridLayout(warranty_box)
        war_layout.setContentsMargins(15, 20, 15, 15)
        war_layout.setSpacing(10)
        
        has_war = False
        if contracts:
            for c in contracts:
                warranties = c.get("warranties", [])
                if warranties:
                    has_war = True
                    w = warranties[0]
                    war_layout.addWidget(wrap_lbl("<b>Warranty Period:</b>"), 0, 0)
                    war_layout.addWidget(wrap_lbl(f"{w.get('start_of_warranty_period', 'N/A')} to {w.get('end_date_of_warranty_period', 'N/A')}"), 0, 1)
                    war_layout.addWidget(wrap_lbl("<b>Retention Period:</b>"), 0, 2)
                    war_layout.addWidget(wrap_lbl(f"{w.get('warranty_retention_period_months', 'N/A')} months"), 0, 3)
                    
                    war_layout.addWidget(wrap_lbl("<b>Retention Security:</b>"), 1, 0)
                    war_layout.addWidget(wrap_lbl(w.get("retention_security", "N/A")), 1, 1)
                    war_layout.addWidget(wrap_lbl("<b>Warranty Status:</b>"), 1, 2)
                    
                    w_status = w.get("retention_period_warranty_status", "N/A")
                    war_layout.addWidget(wrap_lbl(w_status), 1, 3)
                    
                    war_layout.addWidget(wrap_lbl("<b>Actual Release Date:</b>"), 2, 0)
                    war_layout.addWidget(wrap_lbl(w.get("actual_date_release_retention", "N/A") or "Not Yet Released"), 2, 1)
                    war_layout.addWidget(wrap_lbl("<b>COA Petition Claims:</b>"), 2, 2)
                    coa_claims = "Yes" if w.get("with_petition_for_coa_claims") else "No"
                    war_layout.addWidget(wrap_lbl(coa_claims), 2, 3)
                    
                    # Warranty certificate document row
                    war_layout.addWidget(wrap_lbl("<b>Warranty Certificate:</b>"), 3, 0)
                    war_layout.addWidget(make_doc_btn("Warranty", "Warranty Certificate"), 3, 1, 1, 3)
                    
                    edit_war_btn = QPushButton("✏️ Edit Details")
                    edit_war_btn.setStyleSheet(self.btn_edit_style())
                    edit_war_btn.clicked.connect(lambda checked=False, w_data=w: self.edit_warranty_details(w_data))
                    war_layout.addWidget(edit_war_btn, 0, 4, 1, 1, Qt.AlignRight | Qt.AlignTop)
            
            if not has_war:
                war_layout.addWidget(wrap_lbl("No warranty info recorded yet."), 0, 0, 1, 2)
                
                c_id = contracts[0]["id"]
                add_war_btn = QPushButton("➕ Add Warranty Details")
                add_war_btn.setStyleSheet(self.btn_progression_style())
                add_war_btn.clicked.connect(lambda checked=False, con_id=c_id: self.add_warranty_details(con_id))
                war_layout.addWidget(add_war_btn, 0, 3, 1, 1, Qt.AlignRight | Qt.AlignVCenter)
        else:
            war_layout.addWidget(wrap_lbl("No warranty info recorded yet."), 0, 0, 1, 2)
            war_layout.addWidget(wrap_lbl("<i>Complete Contract phase to proceed.</i>"), 0, 3, 1, 1)
            
        timeline_layout.addWidget(warranty_box)
        
        # General Remarks / Notes box at the very bottom
        remarks_box = QGroupBox("General Project Notes & Remarks")
        remarks_box.setStyleSheet(self.groupbox_style())
        rem_layout = QHBoxLayout(remarks_box)
        rem_layout.setContentsMargins(15, 15, 15, 15)
        rem_layout.setSpacing(10)
        
        from PySide6.QtWidgets import QTextEdit
        self.remarks_edit = QTextEdit()
        self.remarks_edit.setPlaceholderText("Write project notes, reminders, or general remarks here...")
        self.remarks_edit.setText(self.project_data.get("remarks", "") or "")
        self.remarks_edit.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a24;
                color: #ffffff;
                border: 1px solid #3a3a4a;
                border-radius: 4px;
                padding: 6px;
                font-size: 13px;
            }
        """)
        self.remarks_edit.setFixedHeight(70)
        rem_layout.addWidget(self.remarks_edit, stretch=4)
        
        save_rem_btn = QPushButton("💾 Save Remarks")
        save_rem_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a2d3c; color: #33ccff;
                font-weight: bold; border-radius: 4px; padding: 10px 15px;
                border: 1px solid #33ccff; font-size: 12px;
            }
            QPushButton:hover { background-color: #33ccff; color: #13131a; }
        """)
        save_rem_btn.clicked.connect(self.save_general_remarks)
        rem_layout.addWidget(save_rem_btn, stretch=1, alignment=Qt.AlignVCenter)
        
        timeline_layout.addWidget(remarks_box)
        
        self.scroll.setWidget(scroll_content)

    def btn_progression_style(self):
        return """
            QPushButton {
                background-color: #00ffcc;
                color: #13131a;
                font-weight: bold;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #00ccaa;
            }
        """

    def refresh_data(self):
        import database as database_config
        self.project_data = database_config.get_project_detail(self.project_id)
        self.build_timeline()
        if self.parent() and hasattr(self.parent(), "refresh_all_data"):
            self.parent().refresh_all_data()

    def save_general_remarks(self):
        remarks_txt = self.remarks_edit.toPlainText().strip()
        try:
            import database as database_config
            conn = database_config.get_db_connection()
            cur = conn.cursor()
            cur.execute("UPDATE projects SET remarks = ? WHERE project_id = ?", (remarks_txt, self.project_id))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Success", "Project remarks saved successfully!")
            self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save remarks: {e}")

    def add_bidding_details(self):
        import ui.dialogs as form_dialogs
        dialog = form_dialogs.AddBidDialog(self.project_id, self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_data()

    def edit_project_details(self):
        import ui.dialogs as form_dialogs
        dialog = form_dialogs.CreateProjectDialog(self, self.project_data)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_data()

    def edit_bidding_details(self, bid_data):
        import ui.dialogs as form_dialogs
        dialog = form_dialogs.AddBidDialog(self.project_id, self, bid_data)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_data()

    def add_contract_details(self, bid_id):
        import ui.dialogs as form_dialogs
        dialog = form_dialogs.AddContractDialog(self.project_id, bid_id, self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_data()

    def edit_contract_details(self, contract_data):
        import ui.dialogs as form_dialogs
        dialog = form_dialogs.AddContractDialog(self.project_id, contract_data.get("bid_id"), self, contract_data)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_data()

    def add_deliverable_details(self, contract_id):
        import ui.dialogs as form_dialogs
        dialog = form_dialogs.AddDeliverableDialog(contract_id, self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_data()

    def edit_deliverable_details(self, deliverable_data):
        import ui.dialogs as form_dialogs
        dialog = form_dialogs.AddDeliverableDialog(deliverable_data.get("contract_id"), self, deliverable_data)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_data()

    def add_payment_details(self, contract_id, contract_data):
        import ui.dialogs as form_dialogs
        dialog = form_dialogs.AddPaymentDialog(contract_id, contract_data, self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_data()

    def edit_payment_details(self, payment_data):
        import ui.dialogs as form_dialogs
        dialog = form_dialogs.AddPaymentDialog(payment_data.get("contract_id"), self.project_data["contracts"][0], self, payment_data)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_data()

    def add_warranty_details(self, contract_id):
        import ui.dialogs as form_dialogs
        dialog = form_dialogs.AddWarrantyDialog(contract_id, self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_data()

    def edit_warranty_details(self, warranty_data):
        import ui.dialogs as form_dialogs
        dialog = form_dialogs.AddWarrantyDialog(warranty_data.get("contract_id"), self, warranty_data)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_data()

    def confirm_delete_project(self):
        proj_name = self.project_data.get("project_name", "N/A")
        proj_id = self.project_data.get("proj_id_no", "N/A")
        reply = QMessageBox.question(
            self, "Confirm Delete Project",
            f"Are you sure you want to permanently delete project {proj_id}?\n\n"
            f"Name: {proj_name}\n\n"
            "This action cannot be undone and will delete all associated bids, contracts, deliverables, payments, and warranties.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            import database as database_config
            success, error = database_config.delete_project(self.project_id)
            if success:
                QMessageBox.information(self, "Deleted", f"Project {proj_id} has been successfully deleted.")
                if self.parent() and hasattr(self.parent(), "refresh_all_data"):
                    self.parent().refresh_all_data()
                self.accept()
            else:
                QMessageBox.critical(self, "Error", f"Failed to delete project: {error}")

    def btn_edit_style(self):
        return """
            QPushButton {
                background-color: #3a3a4a;
                color: #00ffcc;
                font-weight: bold;
                border-radius: 4px;
                padding: 4px 10px;
                border: 1px solid #5a5a6a;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #4a4a5a;
                color: #ffffff;
            }
        """

    def groupbox_style(self):
        return """
            QGroupBox {
                border: 1px solid #3a3a4a;
                border-radius: 8px;
                margin-top: 15px;
                font-weight: bold;
                color: #00ffcc;
                font-size: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                left: 15px;
            }
            QLabel {
                color: #ffffff;
                font-size: 13px;
            }
        """
