import sys
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QDoubleSpinBox, QSpinBox, QDateEdit, QCheckBox, QPushButton,
    QFormLayout, QMessageBox, QFrame, QGroupBox, QRadioButton, QButtonGroup,
    QScrollArea, QWidget, QFileDialog
)
from PySide6.QtCore import Qt, QDate
import database_config

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
        self.setStyleSheet(f"QDialog {{ background-color: #1e1e24; color: #ffffff; }} {INPUT_STYLE}")
        
    def set_field_validation(self, widget, is_valid):
        cls_name = widget.metaObject().className()
        if is_valid:
            widget.setStyleSheet(f"{cls_name} {{ border: 1px solid #00ffcc; background-color: #2b2b36; }}")
        else:
            widget.setStyleSheet(f"{cls_name} {{ border: 1px solid #ff4d4d; background-color: #3b2a2a; }}")
            
    def clear_field_validation(self, widget):
        cls_name = widget.metaObject().className()
        widget.setStyleSheet(f"{cls_name} {{ border: 1px solid #3a3a4a; background-color: #2b2b36; }}")

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
class CreateProjectDialog(BaseFormDialog):
    def __init__(self, parent=None, project_data=None):
        super().__init__(parent)
        self.project_data = project_data
        
        self.saro_file_path = None
        self.ppmp_file_path = None
        self.ms_file_path = None
        self.ts_file_path = None

        # 
        if self.project_data:
            self.setWindowTitle("Edit Project Details")
        else:
            self.setWindowTitle("Create New Procurement Project")
        self.resize(600, 760)
        self.setup_ui()
        
    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        
        title_text = "Edit Project (Phase 1: Planning)" if self.project_data else "Create Project (Phase 1: Planning)"
        title = QLabel(title_text)
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #00ffcc; margin-bottom: 5px;")
        self.layout.addWidget(title)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(10)
        
        # Information groupbox
        info_group = QGroupBox("Project Information")
        info_group.setStyleSheet("QGroupBox { color: #00ffcc; font-weight: bold; border: 1px solid #3a3a4a; padding-top: 10px; }")
        form = QFormLayout(info_group)
        form.setSpacing(10)
        
        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("e.g. PRJ-2026-0003")
        self.id_input.textChanged.connect(self.validate_inputs)
        form.addRow("Project ID / PR No *:", self.id_input)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. Supply and Delivery of Office Laptops")
        self.name_input.textChanged.connect(self.validate_inputs)
        form.addRow("Project Name *:", self.name_input)
        
        self.div_input = QLineEdit()
        self.div_input.setPlaceholderText("e.g. IT Division")
        form.addRow("Bureau / Division:", self.div_input)
        
        self.focal_input = QLineEdit()
        self.focal_input.setPlaceholderText("e.g. John Doe")
        form.addRow("Focal Person:", self.focal_input)
        
        self.contact_input = QLineEdit()
        self.contact_input.setPlaceholderText("e.g. john.doe@agency.gov.ph")
        form.addRow("Focal Contact Email:", self.contact_input)
        
        self.mode_input = QComboBox()
        self.mode_input.addItems([
            "Competitive Bidding",
            "Limited Source Bidding",
            "Competitive Dialogue",
            "Unsolicited Offer with Bid Matching",
            "Direct Contracting",
            "Direct Acquisition",
            "Repeat Order",
            "Small Value Procurement",
            "Negotiated Procurement",
            "Direct Sales",
            "Direct Procurement for Science, Technology, and Innovation"
        ])
        form.addRow("Mode of Procurement:", self.mode_input)
        
        self.abc_input = QDoubleSpinBox()
        self.abc_input.setRange(0, 999999999.99)
        self.abc_input.setSingleStep(10000.00)
        self.abc_input.setValue(100000.00)
        self.abc_input.setPrefix("₱")
        form.addRow("Approved Budget (ABC) *:", self.abc_input)
        
        self.funds_input = QLineEdit("General Fund")
        form.addRow("Source of Funds:", self.funds_input)
        
        self.source_input = QLineEdit("GAA")
        form.addRow("Fund Source Type:", self.source_input)
        
        self.cycle_input = QComboBox()
        self.cycle_input.addItems(["1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th", "9th", "10th", "11th", "12th"])
        form.addRow("APP *:", self.cycle_input)
        
        self.saro_input = QLineEdit()
        self.saro_input.setPlaceholderText("e.g. SARO-BMB-A-26-000123")
        form.addRow("SARO Control Number:", self.saro_input)
        
        scroll_layout.addWidget(info_group)
        
        # Documents groupbox
        doc_group = QGroupBox("Planning & Budget Documents")
        doc_group.setStyleSheet("QGroupBox { color: #00ffcc; font-weight: bold; border: 1px solid #3a3a4a; padding-top: 10px; }")
        doc_layout = QFormLayout(doc_group)
        doc_layout.setSpacing(8)
        
        # SARO Document PDF
        saro_doc_layout = QHBoxLayout()
        self.saro_lbl = QLabel("<i>No SARO PDF Uploaded</i>")
        self.saro_lbl.setStyleSheet("color: #aaaaaa; font-size: 11px;")
        saro_btn = QPushButton("Browse...")
        saro_btn.clicked.connect(self.browse_saro)
        saro_doc_layout.addWidget(self.saro_lbl)
        saro_doc_layout.addWidget(saro_btn)
        doc_layout.addRow("SARO PDF Document:", saro_doc_layout)
        
        # PPMP Document PDF
        ppmp_doc_layout = QHBoxLayout()
        self.ppmp_lbl = QLabel("<i>No PPMP PDF Uploaded</i>")
        self.ppmp_lbl.setStyleSheet("color: #aaaaaa; font-size: 11px;")
        ppmp_btn = QPushButton("Browse...")
        ppmp_btn.clicked.connect(self.browse_ppmp)
        ppmp_doc_layout.addWidget(self.ppmp_lbl)
        ppmp_doc_layout.addWidget(ppmp_btn)
        doc_layout.addRow("PPMP PDF Document:", ppmp_doc_layout)
        
        # MS Document PDF
        ms_doc_layout = QHBoxLayout()
        self.ms_lbl = QLabel("<i>No Market Scoping PDF Uploaded</i>")
        self.ms_lbl.setStyleSheet("color: #aaaaaa; font-size: 11px;")
        ms_btn = QPushButton("Browse...")
        ms_btn.clicked.connect(self.browse_ms)
        ms_doc_layout.addWidget(self.ms_lbl)
        ms_doc_layout.addWidget(ms_btn)
        doc_layout.addRow("Market Scoping PDF:", ms_doc_layout)
        
        # TS Document PDF
        ts_doc_layout = QHBoxLayout()
        self.ts_lbl = QLabel("<i>No Tech Specs/TOR PDF Uploaded</i>")
        self.ts_lbl.setStyleSheet("color: #aaaaaa; font-size: 11px;")
        ts_btn = QPushButton("Browse...")
        ts_btn.clicked.connect(self.browse_ts)
        ts_doc_layout.addWidget(self.ts_lbl)
        ts_doc_layout.addWidget(ts_btn)
        doc_layout.addRow("Tech Specs/TOR PDF:", ts_doc_layout)
        
        scroll_layout.addWidget(doc_group)
        
        # Populate if editing
        if self.project_data:
            pid = self.project_data["id"]
            self.id_input.setText(self.project_data.get("proj_id_no", ""))
            self.name_input.setText(self.project_data.get("project_name", ""))
            self.div_input.setText(self.project_data.get("bureau_division_name", ""))
            self.focal_input.setText(self.project_data.get("focal_person", ""))
            self.contact_input.setText(self.project_data.get("end_user_contact_details", ""))
            
            idx = self.mode_input.findText(self.project_data.get("mode_of_procurement", ""))
            if idx >= 0:
                self.mode_input.setCurrentIndex(idx)
                
            self.abc_input.setValue(self.project_data.get("abc_amount", 0.0))
            self.funds_input.setText(self.project_data.get("source_of_funds", ""))
            self.source_input.setText(self.project_data.get("fund_source", ""))
            
            cycle_val = self.project_data.get("app_cycle", 1)
            self.cycle_input.setCurrentIndex(max(0, min(cycle_val - 1, 11)))
            
            self.saro_input.setText(self.project_data.get("saro_number", ""))
            
            # Load documents
            try:
                import os
                conn = database_config.get_db_connection()
                cur = conn.cursor()
                
                cur.execute("SELECT saro_pdf, ppmp_pdf, market_scoping_pdf, tech_specs_pdf FROM projects WHERE project_id = ?", (pid,))
                row = cur.fetchone()
                if row:
                    if row["saro_pdf"]:
                        self.saro_file_path = row["saro_pdf"]
                        self.saro_lbl.setText("📄 " + os.path.basename(self.saro_file_path))
                        self.saro_lbl.setStyleSheet("color: #00ffcc; font-weight: bold;")
                    if row["ppmp_pdf"]:
                        self.ppmp_file_path = row["ppmp_pdf"]
                        self.ppmp_lbl.setText("📄 " + os.path.basename(self.ppmp_file_path))
                        self.ppmp_lbl.setStyleSheet("color: #00ffcc; font-weight: bold;")
                    if row["market_scoping_pdf"]:
                        self.ms_file_path = row["market_scoping_pdf"]
                        self.ms_lbl.setText("📄 " + os.path.basename(self.ms_file_path))
                        self.ms_lbl.setStyleSheet("color: #00ffcc; font-weight: bold;")
                    if row["tech_specs_pdf"]:
                        self.ts_file_path = row["tech_specs_pdf"]
                        self.ts_lbl.setText("📄 " + os.path.basename(self.ts_file_path))
                        self.ts_lbl.setStyleSheet("color: #00ffcc; font-weight: bold;")
                conn.close()
            except Exception as e:
                print(f"Error loading project docs in CreateProjectDialog: {e}")
                
        scroll_content.setLayout(scroll_layout)
        scroll.setWidget(scroll_content)
        self.layout.addWidget(scroll)
        
        # Buttons
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(BUTTON_CANCEL_STYLE)
        cancel_btn.clicked.connect(self.reject)
        
        submit_btn_text = "Save Changes" if self.project_data else "Create Project"
        submit_btn = QPushButton(submit_btn_text)
        submit_btn.setStyleSheet(BUTTON_SUBMIT_STYLE)
        submit_btn.clicked.connect(self.submit_data)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(submit_btn)
        self.layout.addLayout(btn_layout)
        
        self.validate_inputs()
        
    def browse_saro(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Upload SARO Document (PDF)", "", "PDF Files (*.pdf);;All Files (*)")
        if file_path:
            import os
            self.saro_lbl.setText("📄 " + os.path.basename(file_path))
            self.saro_lbl.setStyleSheet("color: #00ffcc; font-weight: bold;")
            self.saro_file_path = file_path
            
    def browse_ppmp(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Upload PPMP Document (PDF)", "", "PDF Files (*.pdf);;All Files (*)")
        if file_path:
            import os
            self.ppmp_lbl.setText("📄 " + os.path.basename(file_path))
            self.ppmp_lbl.setStyleSheet("color: #00ffcc; font-weight: bold;")
            self.ppmp_file_path = file_path
            
    def browse_ms(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Upload Market Scoping Document (PDF)", "", "PDF Files (*.pdf);;All Files (*)")
        if file_path:
            import os
            self.ms_lbl.setText("📄 " + os.path.basename(file_path))
            self.ms_lbl.setStyleSheet("color: #00ffcc; font-weight: bold;")
            self.ms_file_path = file_path
            
    def browse_ts(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Upload Tech Specs/TOR Document (PDF)", "", "PDF Files (*.pdf);;All Files (*)")
        if file_path:
            import os
            self.ts_lbl.setText("📄 " + os.path.basename(file_path))
            self.ts_lbl.setStyleSheet("color: #00ffcc; font-weight: bold;")
            self.ts_file_path = file_path

    def validate_inputs(self):
        id_valid = len(self.id_input.text().strip()) > 0
        name_valid = len(self.name_input.text().strip()) > 0
        self.set_field_validation(self.id_input, id_valid)
        self.set_field_validation(self.name_input, name_valid)
        return id_valid and name_valid
        
    def submit_data(self):
        if not self.validate_inputs():
            if not self.id_input.text().strip():
                self.id_input.setFocus()
            else:
                self.name_input.setFocus()
            return
            
        proj_id = self.id_input.text().strip()
        name = self.name_input.text().strip()
        abc = self.abc_input.value()
        app_cycle = self.cycle_input.currentIndex() + 1
        saro_no = self.saro_input.text().strip() or None
        
        if self.project_data:
            # Edit Mode
            success, result = database_config.update_project(
                self.project_data["id"], proj_id, name, saro_no,
                self.div_input.text().strip(), self.focal_input.text().strip(), self.contact_input.text().strip(),
                self.mode_input.currentText(), abc, self.funds_input.text().strip(),
                self.source_input.text().strip(), app_cycle, self.project_data.get("remarks")
            )
            action_name = "updated"
            project_id = self.project_data["id"]
        else:
            # Add Mode
            success, result = database_config.create_project(
                proj_id, name, saro_no, self.div_input.text().strip(), self.focal_input.text().strip(),
                self.contact_input.text().strip(), self.mode_input.currentText(), abc,
                self.funds_input.text().strip(), self.source_input.text().strip(), app_cycle, None
            )
            action_name = "created"
            project_id = result if success else None
            
        if success and project_id:
            # Save files
            if self.saro_file_path and not self.saro_file_path.startswith("uploaded_documents/"):
                database_config.save_project_document(project_id, "SARO", self.saro_file_path)
            if self.ppmp_file_path and not self.ppmp_file_path.startswith("uploaded_documents/"):
                database_config.save_project_document(project_id, "PPMP", self.ppmp_file_path)
            if self.ms_file_path and not self.ms_file_path.startswith("uploaded_documents/"):
                database_config.save_project_document(project_id, "MS", self.ms_file_path)
            if self.ts_file_path and not self.ts_file_path.startswith("uploaded_documents/"):
                database_config.save_project_document(project_id, "TS", self.ts_file_path)
                
            QMessageBox.information(self, "Success", f"Project {proj_id} successfully {action_name}!")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", f"Failed to save project:\n{result}")

class AddBidDialog(BaseFormDialog):
    def __init__(self, project_id, parent=None, bid_data=None):
        super().__init__(parent)
        self.project_id = project_id
        self.bid_data = bid_data
        
        self.abstract_file_path = None
        
        if self.bid_data:
            self.setWindowTitle("Phase 1: Edit Bidding Details")
        else:
            self.setWindowTitle("Phase 1: Add Bidding Details")
        self.resize(700, 680)
        self.setup_ui()
        
    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        
        title_text = "Edit Bidding Information" if self.bid_data else "Add Bidding Information"
        title = QLabel(title_text)
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #00ffcc; margin-bottom: 5px;")
        self.layout.addWidget(title)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(10)
        
        # Bidding Info groupbox
        bid_group = QGroupBox("Bidding details")
        bid_group.setStyleSheet("QGroupBox { color: #00ffcc; font-weight: bold; border: 1px solid #3a3a4a; padding-top: 10px; }")
        form = QFormLayout(bid_group)
        form.setSpacing(10)
        
        self.ref_input = QLineEdit()
        self.ref_input.setPlaceholderText("e.g. BID-2026-0002")
        self.ref_input.textChanged.connect(self.validate_inputs)
        form.addRow("Bid Reference No *:", self.ref_input)
        
        self.pr_input = QLineEdit()
        self.pr_input.setPlaceholderText("e.g. PR-2026-0044")
        form.addRow("Purchase Request No:", self.pr_input)
        
        self.philgeps_combo = QComboBox()
        self.philgeps_combo.addItems(["Auto-detect by Value (>= ₱200k)", "Yes (Posted)", "No (Not Posted)"])
        form.addRow("Post to PhilGEPS?:", self.philgeps_combo)
        
        self.abstract_input = QLineEdit()
        self.abstract_input.setPlaceholderText("e.g. Abstract-2026-88")
        form.addRow("Abstract of Quotations:", self.abstract_input)
        
        self.reso_input = QLineEdit()
        self.reso_input.setPlaceholderText("e.g. BAC-Reso-2026-12")
        form.addRow("BAC Resolution (if NOA unavailable):", self.reso_input)
        
        self.bacsec_date = QDateEdit(QDate.currentDate())
        self.bacsec_date.setCalendarPopup(True)
        form.addRow("Date Received BACSec *:", self.bacsec_date)
        
        self.pcmd_date_check = QCheckBox("Date Received PCMD")
        self.pcmd_date_check.setChecked(False)
        self.pcmd_date = QDateEdit(QDate.currentDate())
        self.pcmd_date.setCalendarPopup(True)
        self.pcmd_date.setEnabled(False)
        self.pcmd_date_check.stateChanged.connect(lambda state: self.pcmd_date.setEnabled(state == 2))
        form.addRow(self.pcmd_date_check, self.pcmd_date)
        
        self.box_a_input = QLineEdit("Maria Santos")
        form.addRow("Signatory Box A (Prepared by):", self.box_a_input)
        
        self.box_c_input = QLineEdit("Pedro Reyes")
        form.addRow("Signatory Box C (Approved by):", self.box_c_input)
        
        scroll_layout.addWidget(bid_group)
        
        # Document uploads groupbox
        doc_group = QGroupBox("Bidding Documents")
        doc_group.setStyleSheet("QGroupBox { color: #00ffcc; font-weight: bold; border: 1px solid #3a3a4a; padding-top: 10px; }")
        doc_layout = QFormLayout(doc_group)
        doc_layout.setSpacing(8)
        
        # Abstract Document PDF
        abs_doc_layout = QHBoxLayout()
        self.abs_lbl = QLabel("<i>No Abstract PDF Uploaded</i>")
        self.abs_lbl.setStyleSheet("color: #aaaaaa; font-size: 11px;")
        abs_btn = QPushButton("Browse...")
        abs_btn.clicked.connect(self.browse_abstract)
        abs_doc_layout.addWidget(self.abs_lbl)
        abs_doc_layout.addWidget(abs_btn)
        doc_layout.addRow("Abstract of Quotations PDF:", abs_doc_layout)
        
        scroll_layout.addWidget(doc_group)
        
        # Populate if editing
        if self.bid_data:
            self.ref_input.setText(self.bid_data.get("bid_reference_no", ""))
            self.pr_input.setText(self.bid_data.get("purchase_request_no", ""))
            
            p_phil = self.bid_data.get("post_to_philgeps", "")
            idx = self.philgeps_combo.findText(p_phil)
            if idx >= 0:
                self.philgeps_combo.setCurrentIndex(idx)
                
            self.abstract_input.setText(self.bid_data.get("abstract_of_quotations_no", ""))
            self.reso_input.setText(self.bid_data.get("bac_resolution_no", ""))
            
            b_date = self.bid_data.get("date_received_bacsec", "")
            if b_date:
                self.bacsec_date.setDate(QDate.fromString(b_date, "yyyy-MM-dd"))
                
            p_date = self.bid_data.get("date_received_pcmd_initial", "")
            if p_date:
                self.pcmd_date_check.setChecked(True)
                self.pcmd_date.setDate(QDate.fromString(p_date, "yyyy-MM-dd"))
                self.pcmd_date.setEnabled(True)
                
            self.box_a_input.setText(self.bid_data.get("signatory_box_a", ""))
            self.box_c_input.setText(self.bid_data.get("signatory_box_c", ""))
            
            # Load Abstract doc
            try:
                import os
                conn = database_config.get_db_connection()
                cur = conn.cursor()
                cur.execute("SELECT abstract_quotations_pdf FROM projects WHERE project_id = ?", (self.project_id,))
                row = cur.fetchone()
                if row and row["abstract_quotations_pdf"]:
                    self.abstract_file_path = row["abstract_quotations_pdf"]
                    self.abs_lbl.setText("📄 " + os.path.basename(self.abstract_file_path))
                    self.abs_lbl.setStyleSheet("color: #00ffcc; font-weight: bold;")
                conn.close()
            except Exception as e:
                print(f"Error loading Abstract doc in AddBidDialog: {e}")
                
        scroll_content.setLayout(scroll_layout)
        scroll.setWidget(scroll_content)
        self.layout.addWidget(scroll)
        
        # Buttons
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(BUTTON_CANCEL_STYLE)
        cancel_btn.clicked.connect(self.reject)
        
        submit_btn_text = "Save Changes" if self.bid_data else "Save Bidding Details"
        submit_btn = QPushButton(submit_btn_text)
        submit_btn.setStyleSheet(BUTTON_SUBMIT_STYLE)
        submit_btn.clicked.connect(self.submit_data)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(submit_btn)
        self.layout.addLayout(btn_layout)
        
        self.validate_inputs()
        
    def browse_abstract(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Upload Abstract of Quotations (PDF)", "", "PDF Files (*.pdf);;All Files (*)")
        if file_path:
            import os
            self.abs_lbl.setText("📄 " + os.path.basename(file_path))
            self.abs_lbl.setStyleSheet("color: #00ffcc; font-weight: bold;")
            self.abstract_file_path = file_path

    def validate_inputs(self):
        ref_valid = len(self.ref_input.text().strip()) > 0
        self.set_field_validation(self.ref_input, ref_valid)
        return ref_valid
        
    def submit_data(self):
        if not self.validate_inputs():
            self.ref_input.setFocus()
            return
            
        bid_ref = self.ref_input.text().strip()
        pr_no = self.pr_input.text().strip() or None
        post_phil = self.philgeps_combo.currentText()
        abstract_no = self.abstract_input.text().strip() or None
        reso_no = self.reso_input.text().strip() or None
        
        bacsec = self.bacsec_date.date().toString("yyyy-MM-dd")
        pcmd = self.pcmd_date.date().toString("yyyy-MM-dd") if self.pcmd_date_check.isChecked() else None
        
        if self.bid_data:
            success, result = database_config.update_bid(
                self.bid_data["id"], bid_ref, bacsec, pcmd,
                self.box_a_input.text().strip(), self.box_c_input.text().strip(),
                pr_no, post_phil, abstract_no, reso_no
            )
            action_name = "updated"
        else:
            success, result = database_config.add_bid(
                self.project_id, bid_ref, bacsec, pcmd,
                self.box_a_input.text().strip(), self.box_c_input.text().strip(),
                pr_no, post_phil, abstract_no, reso_no
            )
            action_name = "recorded"
            
        if success:
            if self.abstract_file_path and not self.abstract_file_path.startswith("uploaded_documents/"):
                database_config.save_project_document(self.project_id, "Abstract", self.abstract_file_path)
                
            QMessageBox.information(self, "Success", f"Bidding details successfully {action_name}!")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", f"Failed to save bidding details:\n{result}")

class AddContractDialog(BaseFormDialog):
    def __init__(self, project_id, bid_id, parent=None, contract_data=None):
        super().__init__(parent)
        self.project_id = project_id
        self.bid_id = bid_id
        self.contract_data = contract_data
        
        self.noa_file_path = None
        self.contract_file_path = None
        self.reso_file_path = None
        self.rq_file_path = None
        
        if self.contract_data:
            self.setWindowTitle("Phase 2: Edit Contract Details")
        else:
            self.setWindowTitle("Phase 2: Add Contract & Supplier Details")
        self.resize(700, 680)
        self.setup_ui()
        
    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        
        title_text = "Edit Contract & Supplier Information" if self.contract_data else "Contract Award & Supplier Information"
        title = QLabel(title_text)
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #00ffcc; margin-bottom: 5px;")
        self.layout.addWidget(title)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(10)
        
        # Section A: Supplier
        sup_group = QGroupBox("Supplier Directory Selection")
        sup_group.setStyleSheet("QGroupBox { color: #00ffcc; font-weight: bold; border: 1px solid #3a3a4a; padding-top: 10px; }")
        sup_layout = QVBoxLayout(sup_group)
        
        # Supplier ComboBox
        self.supplier_combo = QComboBox()
        self.populate_suppliers()
        sup_layout.addWidget(self.supplier_combo)
        
        # Checkbox for new supplier inline
        self.new_supplier_check = QCheckBox("Supplier not in directory? Check to add new:")
        self.new_supplier_check.setStyleSheet("color: #33ccff; font-weight: bold;")
        self.new_supplier_check.stateChanged.connect(self.toggle_new_supplier_form)
        self.new_supplier_check.stateChanged.connect(lambda: self.validate_inputs())
        sup_layout.addWidget(self.new_supplier_check)
        
        # New Supplier Form frame (initially collapsed)
        self.supplier_frame = QFrame()
        self.supplier_frame.setStyleSheet("background-color: #242430; border-radius: 6px; padding: 10px;")
        self.supplier_frame.setVisible(False)
        sf_layout = QFormLayout(self.supplier_frame)
        sf_layout.setSpacing(8)
        
        self.s_name = QLineEdit()
        self.s_name.textChanged.connect(self.validate_inputs)
        sf_layout.addRow("Supplier Name *:", self.s_name)
        self.s_tin = QLineEdit()
        self.s_tin.setPlaceholderText("e.g. 123-456-789-000")
        sf_layout.addRow("TIN Number:", self.s_tin)
        self.s_address = QLineEdit()
        sf_layout.addRow("Address:", self.s_address)
        self.s_contact = QLineEdit()
        self.s_contact.setPlaceholderText("Email or Phone")
        sf_layout.addRow("Contact Info:", self.s_contact)
        self.s_bank_name = QLineEdit()
        sf_layout.addRow("Bank Account Name:", self.s_bank_name)
        self.s_bank_branch = QLineEdit()
        self.s_bank_branch.setPlaceholderText("e.g. Landbank Intramuros")
        sf_layout.addRow("Bank Branch:", self.s_bank_branch)
        self.s_bank_no = QLineEdit()
        sf_layout.addRow("Bank Account Number:", self.s_bank_no)
        
        sup_layout.addWidget(self.supplier_frame)
        scroll_layout.addWidget(sup_group)
        
        # Section B: Contract details
        con_group = QGroupBox("Contract Information")
        con_group.setStyleSheet("QGroupBox { color: #00ffcc; font-weight: bold; border: 1px solid #3a3a4a; padding-top: 10px; }")
        con_layout = QFormLayout(con_group)
        con_layout.setSpacing(8)
        
        self.po_jo_no = QLineEdit()
        self.po_jo_no.setPlaceholderText("e.g. CTR-2026-0002")
        self.po_jo_no.textChanged.connect(self.validate_inputs)
        con_layout.addRow("PO/JO / Contract No *:", self.po_jo_no)
        
        self.con_amount = QDoubleSpinBox()
        self.con_amount.setRange(0, 999999999.99)
        self.con_amount.setSingleStep(10000.0)
        self.con_amount.setPrefix("₱")
        self.con_amount.valueChanged.connect(self.validate_inputs)
        con_layout.addRow("Contract Award Amount *:", self.con_amount)
        
        self.f_capacity = QDoubleSpinBox()
        self.f_capacity.setRange(0, 999999999.99)
        self.f_capacity.setPrefix("₱")
        con_layout.addRow("Financial Capacity Amt:", self.f_capacity)
        
        self.award_date = QDateEdit(QDate.currentDate())
        self.award_date.setCalendarPopup(True)
        con_layout.addRow("Notice of Award Date:", self.award_date)
        
        self.contract_date = QDateEdit(QDate.currentDate())
        self.contract_date.setCalendarPopup(True)
        self.contract_date.dateChanged.connect(self.calculate_end_date)
        con_layout.addRow("Contract Date:", self.contract_date)
        
        self.ntp_date = QDateEdit(QDate.currentDate())
        self.ntp_date.setCalendarPopup(True)
        self.ntp_date.dateChanged.connect(self.calculate_end_date)
        con_layout.addRow("Notice to Proceed Date:", self.ntp_date)
        
        self.duration = QSpinBox()
        self.duration.setRange(1, 730)
        self.duration.setValue(30)
        self.duration.setSuffix(" days")
        self.duration.valueChanged.connect(self.calculate_end_date)
        con_layout.addRow("Contract Duration:", self.duration)
        
        self.end_date_lbl = QLabel()
        self.calculate_end_date()
        con_layout.addRow("Expected End of Contract:", self.end_date_lbl)
        
        self.nature = QComboBox()
        self.nature.addItems(["Goods", "Services", "Infrastructure", "Consulting"])
        con_layout.addRow("Nature of Procurement:", self.nature)
        
        # Security Group Box
        sec_group = QGroupBox("Performance Security Details")
        sec_group.setStyleSheet("QGroupBox { color: #00ffcc; font-weight: bold; border: 1px solid #3a3a4a; padding-top: 10px; }")
        sec_layout = QFormLayout(sec_group)
        sec_layout.setSpacing(8)
        
        self.sec_form = QLineEdit("Surety Bond")
        sec_layout.addRow("Security Form Type:", self.sec_form)
        
        self.sec_amount = QDoubleSpinBox()
        self.sec_amount.setRange(0, 99999999.99)
        self.sec_amount.setPrefix("₱")
        self.con_amount.valueChanged.connect(self.calculate_security_default)
        sec_layout.addRow("Security Amount:", self.sec_amount)
        
        self.sec_valid = QDateEdit(QDate.currentDate().addDays(90))
        self.sec_valid.setCalendarPopup(True)
        sec_layout.addRow("Security Validity Date:", self.sec_valid)
        
        # Document Upload Group
        doc_group = QGroupBox("Contract & Award Documents")
        doc_group.setStyleSheet("QGroupBox { color: #00ffcc; font-weight: bold; border: 1px solid #3a3a4a; padding-top: 10px; }")
        doc_layout = QFormLayout(doc_group)
        doc_layout.setSpacing(8)
        
        noa_layout = QHBoxLayout()
        self.noa_lbl = QLabel("<i>No NOA PDF Uploaded</i>")
        self.noa_lbl.setStyleSheet("color: #aaaaaa; font-size: 11px;")
        noa_btn = QPushButton("Browse...")
        noa_btn.clicked.connect(self.browse_noa)
        noa_layout.addWidget(self.noa_lbl)
        noa_layout.addWidget(noa_btn)
        doc_layout.addRow("Notice of Award (NOA) PDF:", noa_layout)
        
        contract_layout = QHBoxLayout()
        self.contract_lbl = QLabel("<i>No Signed Contract PDF Uploaded</i>")
        self.contract_lbl.setStyleSheet("color: #aaaaaa; font-size: 11px;")
        contract_btn = QPushButton("Browse...")
        contract_btn.clicked.connect(self.browse_contract)
        contract_layout.addWidget(self.contract_lbl)
        contract_layout.addWidget(contract_btn)
        doc_layout.addRow("Signed Contract PDF:", contract_layout)
        
        self.reso_check = QCheckBox("BAC Reso (IF PRIMARY SUPPLIER IS NOT AVAILABLE)")
        self.reso_check.stateChanged.connect(self.toggle_reso_upload)
        doc_layout.addRow("", self.reso_check)
        
        self.reso_upload_widget = QWidget()
        reso_layout = QHBoxLayout(self.reso_upload_widget)
        reso_layout.setContentsMargins(0, 0, 0, 0)
        self.reso_lbl = QLabel("<i>No BAC Reso PDF Uploaded</i>")
        self.reso_lbl.setStyleSheet("color: #aaaaaa; font-size: 11px;")
        reso_btn = QPushButton("Browse...")
        reso_btn.clicked.connect(self.browse_reso)
        reso_layout.addWidget(self.reso_lbl)
        reso_layout.addWidget(reso_btn)
        doc_layout.addRow("BAC Resolution PDF:", self.reso_upload_widget)
        self.reso_upload_widget.setVisible(False)
        
        rq_layout = QHBoxLayout()
        self.rq_lbl = QLabel("<i>No RQ PDF Uploaded</i>")
        self.rq_lbl.setStyleSheet("color: #aaaaaa; font-size: 11px;")
        rq_btn = QPushButton("Browse...")
        rq_btn.clicked.connect(self.browse_rq)
        rq_layout.addWidget(self.rq_lbl)
        rq_layout.addWidget(rq_btn)
        doc_layout.addRow("Request Order (RQ) PDF:", rq_layout)
        
        scroll_layout.addWidget(con_group)
        scroll_layout.addWidget(sec_group)
        scroll_layout.addWidget(doc_group)
        
        self.loading_data = False
        # Populate if editing
        if self.contract_data:
            self.loading_data = True
            supplier_id = self.contract_data.get("supplier_id")
            if supplier_id is not None:
                idx = self.supplier_combo.findData(supplier_id)
                if idx >= 0:
                    self.supplier_combo.setCurrentIndex(idx)
                    
            self.po_jo_no.setText(self.contract_data.get("po_jo_contract_no", ""))
            self.con_amount.setValue(self.contract_data.get("contract_amount", 0.0))
            self.f_capacity.setValue(self.contract_data.get("financial_capacity_amount", 0.0))
            
            a_date = self.contract_data.get("notice_of_award_date", "")
            if a_date:
                self.award_date.setDate(QDate.fromString(a_date, "yyyy-MM-dd"))
                
            c_date = self.contract_data.get("contract_date", "")
            if c_date:
                self.contract_date.setDate(QDate.fromString(c_date, "yyyy-MM-dd"))
                
            n_date = self.contract_data.get("notice_to_proceed_date", "")
            if n_date:
                self.ntp_date.setDate(QDate.fromString(n_date, "yyyy-MM-dd"))
                
            self.duration.setValue(self.contract_data.get("contract_duration_days", 30))
            self.calculate_end_date()
            
            nat = self.contract_data.get("nature_of_procurement", "")
            idx = self.nature.findText(nat)
            if idx >= 0:
                self.nature.setCurrentIndex(idx)
                
            self.sec_form.setText(self.contract_data.get("performance_security_form", ""))
            self.sec_amount.setValue(self.contract_data.get("performance_security_amount", 0.0))
            
            sv_date = self.contract_data.get("performance_security_validity", "")
            if sv_date:
                self.sec_valid.setDate(QDate.fromString(sv_date, "yyyy-MM-dd"))
            self.loading_data = False
                
        # Load existing docs
        if self.project_id:
            try:
                conn = database_config.get_db_connection()
                cur = conn.cursor()
                cur.execute("SELECT * FROM contracts WHERE project_id = ?", (self.project_id,))
                row = cur.fetchone()
                if row:
                    import os
                    if row["noa_pdf"]:
                        self.noa_file_path = row["noa_pdf"]
                        self.noa_lbl.setText("📄 " + os.path.basename(self.noa_file_path))
                        self.noa_lbl.setStyleSheet("color: #00ffcc; font-weight: bold;")
                    if row["signed_contract_pdf"]:
                        self.contract_file_path = row["signed_contract_pdf"]
                        self.contract_lbl.setText("📄 " + os.path.basename(self.contract_file_path))
                        self.contract_lbl.setStyleSheet("color: #00ffcc; font-weight: bold;")
                    if row["bac_resolution_pdf"]:
                        self.reso_file_path = row["bac_resolution_pdf"]
                        self.reso_lbl.setText("📄 " + os.path.basename(self.reso_file_path))
                        self.reso_lbl.setStyleSheet("color: #00ffcc; font-weight: bold;")
                        self.reso_check.setChecked(True)
                        self.reso_upload_widget.setVisible(True)
                    if row["request_order_pdf"]:
                        self.rq_file_path = row["request_order_pdf"]
                        self.rq_lbl.setText("📄 " + os.path.basename(self.rq_file_path))
                        self.rq_lbl.setStyleSheet("color: #00ffcc; font-weight: bold;")
                conn.close()
            except Exception as e:
                print(f"Error loading Phase 1 docs in AddContractDialog: {e}")
                
        scroll_content.setLayout(scroll_layout)
        scroll.setWidget(scroll_content)
        self.layout.addWidget(scroll)
        
        # Buttons
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(BUTTON_CANCEL_STYLE)
        cancel_btn.clicked.connect(self.reject)
        
        submit_btn_text = "Save Changes" if self.contract_data else "Save Contract details"
        submit_btn = QPushButton(submit_btn_text)
        submit_btn.setStyleSheet(BUTTON_SUBMIT_STYLE)
        submit_btn.clicked.connect(self.submit_data)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(submit_btn)
        self.layout.addLayout(btn_layout)
        
        # Initial validation highlight
        self.validate_inputs()
        
    def toggle_reso_upload(self, state):
        self.reso_upload_widget.setVisible(state == 2)
        
    def browse_noa(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Upload NOA Document (PDF)", "", "PDF Files (*.pdf);;All Files (*)")
        if file_path:
            import os
            self.noa_lbl.setText("📄 " + os.path.basename(file_path))
            self.noa_lbl.setStyleSheet("color: #00ffcc; font-weight: bold;")
            self.noa_file_path = file_path
            
    def browse_contract(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Upload Signed Contract (PDF)", "", "PDF Files (*.pdf);;All Files (*)")
        if file_path:
            import os
            self.contract_lbl.setText("📄 " + os.path.basename(file_path))
            self.contract_lbl.setStyleSheet("color: #00ffcc; font-weight: bold;")
            self.contract_file_path = file_path
            
    def browse_reso(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Upload BAC Resolution (PDF)", "", "PDF Files (*.pdf);;All Files (*)")
        if file_path:
            import os
            self.reso_lbl.setText("📄 " + os.path.basename(file_path))
            self.reso_lbl.setStyleSheet("color: #00ffcc; font-weight: bold;")
            self.reso_file_path = file_path

    def browse_rq(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Upload Request Order (RQ) (PDF)", "", "PDF Files (*.pdf);;All Files (*)")
        if file_path:
            import os
            self.rq_lbl.setText("📄 " + os.path.basename(file_path))
            self.rq_lbl.setStyleSheet("color: #00ffcc; font-weight: bold;")
            self.rq_file_path = file_path
        
    def validate_inputs(self):
        po_jo_valid = len(self.po_jo_no.text().strip()) > 0
        con_amount_valid = self.con_amount.value() > 0.0
        self.set_field_validation(self.po_jo_no, po_jo_valid)
        self.set_field_validation(self.con_amount, con_amount_valid)
        
        sup_valid = True
        if self.new_supplier_check.isChecked():
            sup_valid = len(self.s_name.text().strip()) > 0
            self.set_field_validation(self.s_name, sup_valid)
        else:
            self.clear_field_validation(self.s_name)
            
        return po_jo_valid and con_amount_valid and sup_valid
        
    def populate_suppliers(self):
        self.supplier_combo.clear()
        try:
            suppliers = database_config.get_suppliers()
            for s in suppliers:
                self.supplier_combo.addItem(s["supplier_name"], s["id"])
        except Exception as e:
            print(f"Error loading suppliers list: {e}")
            
    def toggle_new_supplier_form(self, state):
        self.supplier_frame.setVisible(state == 2)
        
    def calculate_security_default(self):
        if getattr(self, "loading_data", False):
            return
        self.sec_amount.setValue(self.con_amount.value() * 0.10)
        
    def calculate_end_date(self):
        start = self.ntp_date.date()
        days = self.duration.value()
        expected = start.addDays(days)
        self.end_date_lbl.setText(expected.toString("yyyy-MM-dd"))
        
    def submit_data(self):
        if not self.validate_inputs():
            if not self.po_jo_no.text().strip():
                self.po_jo_no.setFocus()
            elif self.con_amount.value() <= 0.0:
                self.con_amount.setFocus()
            else:
                self.s_name.setFocus()
            return
            
        po_jo = self.po_jo_no.text().strip()
        amount = self.con_amount.value()
        
        supplier_id = None
        if self.new_supplier_check.isChecked():
            # Add supplier first
            s_name_txt = self.s_name.text().strip()
            success, s_res = database_config.add_supplier(
                s_name_txt, self.s_tin.text().strip(), self.s_address.text().strip(),
                self.s_contact.text().strip(), self.s_bank_name.text().strip(),
                self.s_bank_branch.text().strip(), self.s_bank_no.text().strip()
            )
            if success:
                supplier_id = s_res
            else:
                QMessageBox.critical(self, "Error", f"Failed to save Supplier details:\n{s_res}")
                return
        else:
            supplier_id = self.supplier_combo.currentData()
            if supplier_id is None:
                QMessageBox.warning(self, "Validation Error", "Please select a supplier from the list or add a new one.")
                return
                
        # Financial cap default
        f_cap = self.f_capacity.value()
        if f_cap == 0:
            f_cap = amount
            
        sec_amt = self.sec_amount.value()
        if sec_amt == 0:
            sec_amt = amount * 0.1 # default 10%
            
        expected_end = self.end_date_lbl.text()
        
        if self.contract_data:
            success, result = database_config.update_contract(
                self.contract_data["id"], supplier_id, f_cap,
                self.award_date.date().toString("yyyy-MM-dd"), self.sec_form.text().strip(),
                sec_amt, self.sec_valid.date().toString("yyyy-MM-dd"),
                self.contract_date.date().toString("yyyy-MM-dd"), po_jo, amount,
                self.ntp_date.date().toString("yyyy-MM-dd"), self.duration.value(),
                expected_end, self.nature.currentText()
            )
            action_name = "updated"
        else:
            success, result = database_config.add_contract(
                self.project_id, self.bid_id, supplier_id, f_cap,
                self.award_date.date().toString("yyyy-MM-dd"), self.sec_form.text().strip(),
                sec_amt, self.sec_valid.date().toString("yyyy-MM-dd"),
                self.contract_date.date().toString("yyyy-MM-dd"), po_jo, amount,
                self.ntp_date.date().toString("yyyy-MM-dd"), self.duration.value(),
                expected_end, self.nature.currentText()
            )
            action_name = "saved"
            
        if success:
            # Save files
            if self.noa_file_path and not self.noa_file_path.startswith("uploaded_documents/"):
                database_config.save_project_document(self.project_id, "NOA", self.noa_file_path)
            if self.contract_file_path and not self.contract_file_path.startswith("uploaded_documents/"):
                database_config.save_project_document(self.project_id, "Contract", self.contract_file_path)
            if self.reso_check.isChecked() and self.reso_file_path and not self.reso_file_path.startswith("uploaded_documents/"):
                database_config.save_project_document(self.project_id, "BAC_Reso", self.reso_file_path)
            elif not self.reso_check.isChecked():
                try:
                    conn = database_config.get_db_connection()
                    cur = conn.cursor()
                    cur.execute("UPDATE contracts SET bac_resolution_pdf = NULL, bac_resolution_pdf_data = NULL WHERE project_id = ?", (self.project_id,))
                    conn.commit()
                    conn.close()
                except Exception:
                    pass
            if self.rq_file_path and not self.rq_file_path.startswith("uploaded_documents/"):
                database_config.save_project_document(self.project_id, "RQ", self.rq_file_path)
                    
            QMessageBox.information(self, "Success", f"Contract and Supplier details successfully {action_name}!")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", f"Failed to save contract details:\n{result}")

class AddDeliverableDialog(BaseFormDialog):
    def __init__(self, contract_id, parent=None, deliverable_data=None):
        super().__init__(parent)
        self.contract_id = contract_id
        self.deliverable_data = deliverable_data
        
        self.iar_file_path = None
        self.po_file_path = None
        self.abstract_file_path = None
        
        self.project_id = None
        self.contract_amount = 0.0
        try:
            conn = database_config.get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT project_id, contract_amount FROM contracts WHERE contract_id = ?", (self.contract_id,))
            row = cur.fetchone()
            if row:
                self.project_id = row["project_id"]
                self.contract_amount = row["contract_amount"] if row["contract_amount"] is not None else 0.0
            conn.close()
        except Exception as e:
            print(f"Error resolving project_id and contract_amount in AddDeliverableDialog: {e}")
            
        if self.deliverable_data:
            self.setWindowTitle("Phase 3: Edit Deliverable Milestone")
        else:
            self.setWindowTitle("Phase 3: Add Deliverable Milestone")
        self.resize(700, 680)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        title_text = "Edit Deliverable / Milestone Details" if self.deliverable_data else "Add Deliverable / Milestone Details"
        title = QLabel(title_text)
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #00ffcc; margin-bottom: 10px;")
        layout.addWidget(title)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        form = QFormLayout()
        form.setSpacing(8)
        
        self.milestone = QLineEdit()
        self.milestone.setPlaceholderText("e.g. Delivery of office tables and partitions")
        self.milestone.textChanged.connect(self.validate_inputs)
        form.addRow("Milestone Description *:", self.milestone)
        
        self.start_date = QDateEdit(QDate.currentDate())
        self.start_date.setCalendarPopup(True)
        form.addRow("Expected Start Date:", self.start_date)
        
        self.expect_date = QDateEdit(QDate.currentDate().addDays(30))
        self.expect_date.setCalendarPopup(True)
        form.addRow("Expected Delivery Date *:", self.expect_date)
        
        self.duration = QSpinBox()
        self.duration.setRange(1, 365)
        self.duration.setValue(30)
        self.duration.setSuffix(" days")
        form.addRow("Delivery Period:", self.duration)
        
        self.revised_date_check = QCheckBox("Revised Expected Delivery Date")
        self.revised_date = QDateEdit(QDate.currentDate().addDays(30))
        self.revised_date.setCalendarPopup(True)
        self.revised_date.setEnabled(False)
        self.revised_date_check.stateChanged.connect(lambda state: self.revised_date.setEnabled(state == 2))
        form.addRow(self.revised_date_check, self.revised_date)
        
        self.actual_date_check = QCheckBox("Actual Delivery Date (If delivered)")
        self.actual_date = QDateEdit(QDate.currentDate())
        self.actual_date.setCalendarPopup(True)
        self.actual_date.setEnabled(False)
        self.actual_date_check.stateChanged.connect(lambda state: self.actual_date.setEnabled(state == 2))
        form.addRow(self.actual_date_check, self.actual_date)
        
        self.status = QComboBox()
        self.status.addItems(["Pending", "Delivered", "Delayed", "Cancelled"])
        form.addRow("Status of Delivery:", self.status)
        
        self.delays = QSpinBox()
        self.delays.setRange(0, 100)
        self.delays.setValue(0)
        self.delays.setSuffix(" days")
        form.addRow("Days Delayed:", self.delays)
        
        self.ld_rate = QDoubleSpinBox()
        self.ld_rate.setRange(0, 1.0)
        self.ld_rate.setDecimals(4)
        self.ld_rate.setValue(0.0010) # 0.1% daily
        self.ld_rate.setSingleStep(0.0001)
        form.addRow("LD Daily Rate:", self.ld_rate)
        
        self.ld_amt = QDoubleSpinBox()
        self.ld_amt.setRange(0, 99999999.00)
        self.ld_amt.setPrefix("₱")
        form.addRow("Liquidated Damages Amt:", self.ld_amt)
        
        # Connect automatic calculations for delays and liquidated damages
        self.expect_date.dateChanged.connect(self.calculate_delays)
        self.revised_date.dateChanged.connect(self.calculate_delays)
        self.actual_date.dateChanged.connect(self.calculate_delays)
        self.revised_date_check.stateChanged.connect(lambda state: self.calculate_delays())
        self.actual_date_check.stateChanged.connect(lambda state: self.calculate_delays())
        self.delays.valueChanged.connect(lambda val: self.calculate_liquidated_damages())
        self.ld_rate.valueChanged.connect(lambda val: self.calculate_liquidated_damages())
        
        self.iar = QLineEdit()
        self.iar.setPlaceholderText("e.g. IAR-2026-0002")
        form.addRow("IAR Number:", self.iar)
        
        self.accept_date = QDateEdit(QDate.currentDate())
        self.accept_date.setCalendarPopup(True)
        form.addRow("Inspection & Acceptance:", self.accept_date)
        
        self.issues = QLineEdit("None")
        form.addRow("Issues & Concerns:", self.issues)
        
        self.remarks = QLineEdit("On-track")
        form.addRow("Remarks Status:", self.remarks)
        
        # Document Uploads for Phase 3
        # IAR
        iar_layout = QHBoxLayout()
        self.iar_lbl = QLabel("<i>No IAR PDF Uploaded</i>")
        self.iar_lbl.setStyleSheet("color: #aaaaaa; font-size: 11px;")
        iar_btn = QPushButton("Browse...")
        iar_btn.clicked.connect(self.browse_iar)
        iar_layout.addWidget(self.iar_lbl)
        iar_layout.addWidget(iar_btn)
        form.addRow("IAR Document PDF:", iar_layout)
        
        # Purchase Order
        po_layout = QHBoxLayout()
        self.po_lbl = QLabel("<i>No PO PDF Uploaded</i>")
        self.po_lbl.setStyleSheet("color: #aaaaaa; font-size: 11px;")
        po_btn = QPushButton("Browse...")
        po_btn.clicked.connect(self.browse_po)
        po_layout.addWidget(self.po_lbl)
        po_layout.addWidget(po_btn)
        form.addRow("Purchase Order (PO) PDF:", po_layout)
        
        # Abstract of Quotations
        abs_layout = QHBoxLayout()
        self.abs_lbl = QLabel("<i>No Abstract PDF Uploaded</i>")
        self.abs_lbl.setStyleSheet("color: #aaaaaa; font-size: 11px;")
        abs_btn = QPushButton("Browse...")
        abs_btn.clicked.connect(self.browse_abstract)
        abs_layout.addWidget(self.abs_lbl)
        abs_layout.addWidget(abs_btn)
        form.addRow("Abstract of Quotations PDF:", abs_layout)
        
        # Populate if editing
        if self.deliverable_data:
            self.milestone.setText(self.deliverable_data.get("milestone_deliverable", ""))
            
            s_date = self.deliverable_data.get("expected_start_date", "")
            if s_date:
                self.start_date.setDate(QDate.fromString(s_date, "yyyy-MM-dd"))
                
            e_date = self.deliverable_data.get("original_expected_delivery_date", "")
            if e_date:
                self.expect_date.setDate(QDate.fromString(e_date, "yyyy-MM-dd"))
                
            self.duration.setValue(self.deliverable_data.get("delivery_period_days", 30))
            
            r_date = self.deliverable_data.get("revised_delivery_date", "")
            if r_date:
                self.revised_date_check.setChecked(True)
                self.revised_date.setDate(QDate.fromString(r_date, "yyyy-MM-dd"))
                self.revised_date.setEnabled(True)
                
            a_date = self.deliverable_data.get("actual_delivery_date", "")
            if a_date:
                self.actual_date_check.setChecked(True)
                self.actual_date.setDate(QDate.fromString(a_date, "yyyy-MM-dd"))
                self.actual_date.setEnabled(True)
                
            idx = self.status.findText(self.deliverable_data.get("status_of_delivery", ""))
            if idx >= 0:
                self.status.setCurrentIndex(idx)
                
            self.delays.setValue(self.deliverable_data.get("days_delayed", 0))
            self.ld_rate.setValue(self.deliverable_data.get("rate_liquidated_damages", 0.0010))
            self.ld_amt.setValue(self.deliverable_data.get("liquidated_damages_amount", 0.0))
            self.iar.setText(self.deliverable_data.get("iar_no", ""))
            
            ac_date = self.deliverable_data.get("acceptance_date", "")
            if ac_date:
                self.accept_date.setDate(QDate.fromString(ac_date, "yyyy-MM-dd"))
                
            self.issues.setText(self.deliverable_data.get("issues_and_concerns", "None"))
            self.remarks.setText(self.deliverable_data.get("remarks_status", "On-track"))
            
        # Load existing documents if editing
        if self.project_id:
            try:
                import os
                conn = database_config.get_db_connection()
                cur = conn.cursor()
                
                if self.deliverable_data:
                    cur.execute("SELECT iar_pdf, po_pdf FROM deliveries_and_payments WHERE milestone_id = ?", (self.deliverable_data["id"],))
                    row = cur.fetchone()
                    if row:
                        if row["iar_pdf"]:
                            self.iar_file_path = row["iar_pdf"]
                            self.iar_lbl.setText("📄 " + os.path.basename(self.iar_file_path))
                            self.iar_lbl.setStyleSheet("color: #00ffcc; font-weight: bold;")
                        if row["po_pdf"]:
                            self.po_file_path = row["po_pdf"]
                            self.po_lbl.setText("📄 " + os.path.basename(self.po_file_path))
                            self.po_lbl.setStyleSheet("color: #00ffcc; font-weight: bold;")
                            
                cur.execute("SELECT abstract_quotations_pdf FROM projects WHERE project_id = ?", (self.project_id,))
                row = cur.fetchone()
                if row and row["abstract_quotations_pdf"]:
                    self.abstract_file_path = row["abstract_quotations_pdf"]
                    self.abs_lbl.setText("📄 " + os.path.basename(self.abstract_file_path))
                    self.abs_lbl.setStyleSheet("color: #00ffcc; font-weight: bold;")
                conn.close()
            except Exception as e:
                print(f"Error loading Phase 2 documents: {e}")
                
        scroll_layout.addLayout(form)
        scroll_content.setLayout(scroll_layout)
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(BUTTON_CANCEL_STYLE)
        cancel_btn.clicked.connect(self.reject)
        
        submit_btn_text = "Save Changes" if self.deliverable_data else "Save Deliverable"
        submit_btn = QPushButton(submit_btn_text)
        submit_btn.setStyleSheet(BUTTON_SUBMIT_STYLE)
        submit_btn.clicked.connect(self.submit_data)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(submit_btn)
        layout.addLayout(btn_layout)
        self.validate_inputs()
        
    def calculate_delays(self):
        if self.revised_date_check.isChecked():
            target_date = self.revised_date.date()
        else:
            target_date = self.expect_date.date()
            
        if self.actual_date_check.isChecked():
            current_date = self.actual_date.date()
        else:
            # For delay calculation while pending, compare against today
            current_date = QDate.currentDate()
            
        days = target_date.daysTo(current_date)
        if days > 0:
            self.delays.setValue(days)
        else:
            self.delays.setValue(0)
            
        self.calculate_liquidated_damages()

    def calculate_liquidated_damages(self):
        contract_amt = getattr(self, "contract_amount", 0.0)
        days = self.delays.value()
        rate = self.ld_rate.value()
        ld = contract_amt * days * rate
        self.ld_amt.setValue(ld)
        
    def browse_iar(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Upload IAR Document (PDF)", "", "PDF Files (*.pdf);;All Files (*)")
        if file_path:
            import os
            self.iar_lbl.setText("📄 " + os.path.basename(file_path))
            self.iar_lbl.setStyleSheet("color: #00ffcc; font-weight: bold;")
            self.iar_file_path = file_path
            
    def browse_po(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Upload Purchase Order (PDF)", "", "PDF Files (*.pdf);;All Files (*)")
        if file_path:
            import os
            self.po_lbl.setText("📄 " + os.path.basename(file_path))
            self.po_lbl.setStyleSheet("color: #00ffcc; font-weight: bold;")
            self.po_file_path = file_path
            
    def browse_abstract(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Upload Abstract of Quotations (PDF)", "", "PDF Files (*.pdf);;All Files (*)")
        if file_path:
            import os
            self.abs_lbl.setText("📄 " + os.path.basename(file_path))
            self.abs_lbl.setStyleSheet("color: #00ffcc; font-weight: bold;")
            self.abstract_file_path = file_path
            
    def validate_inputs(self):
        desc_valid = len(self.milestone.text().strip()) > 0
        self.set_field_validation(self.milestone, desc_valid)
        return desc_valid
        
    def submit_data(self):
        if not self.validate_inputs():
            self.milestone.setFocus()
            return
            
        desc = self.milestone.text().strip()
        actual = self.actual_date.date().toString("yyyy-MM-dd") if self.actual_date_check.isChecked() else None
        revised = self.revised_date.date().toString("yyyy-MM-dd") if self.revised_date_check.isChecked() else None
        
        if self.deliverable_data:
            success, result = database_config.update_deliverable(
                self.deliverable_data["id"], desc, self.start_date.date().toString("yyyy-MM-dd"),
                self.expect_date.date().toString("yyyy-MM-dd"), self.duration.value(),
                revised, actual, self.status.currentText(), self.delays.value(),
                self.ld_rate.value(), self.ld_amt.value(), self.iar.text().strip(),
                self.accept_date.date().toString("yyyy-MM-dd"), self.accept_date.date().toString("yyyy-MM-dd"),
                self.accept_date.date().toString("yyyy-MM-dd"), self.issues.text().strip(),
                self.remarks.text().strip()
            )
            action_name = "updated"
        else:
            success, result = database_config.add_deliverable(
                self.contract_id, desc, self.start_date.date().toString("yyyy-MM-dd"),
                self.expect_date.date().toString("yyyy-MM-dd"), self.duration.value(),
                revised, actual, self.status.currentText(), self.delays.value(),
                self.ld_rate.value(), self.ld_amt.value(), self.iar.text().strip(),
                self.accept_date.date().toString("yyyy-MM-dd"), self.accept_date.date().toString("yyyy-MM-dd"),
                self.accept_date.date().toString("yyyy-MM-dd"), self.issues.text().strip(),
                self.remarks.text().strip()
            )
            action_name = "saved"
            
        if success:
            if self.project_id:
                if self.iar_file_path and not self.iar_file_path.startswith("uploaded_documents/"):
                    database_config.save_project_document(self.project_id, "IAR", self.iar_file_path)
                if self.po_file_path and not self.po_file_path.startswith("uploaded_documents/"):
                    database_config.save_project_document(self.project_id, "PO_Phase3", self.po_file_path)
                if self.abstract_file_path and not self.abstract_file_path.startswith("uploaded_documents/"):
                    database_config.save_project_document(self.project_id, "Abstract", self.abstract_file_path)
                    
            QMessageBox.information(self, "Success", f"Deliverable milestone successfully {action_name}!")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", f"Failed to save deliverable:\n{result}")

class AddPaymentDialog(BaseFormDialog):
    def __init__(self, contract_id, contract_data, parent=None, payment_data=None):
        super().__init__(parent)
        self.contract_id = contract_id
        self.contract_data = contract_data
        self.payment_data = payment_data
        if self.payment_data:
            self.setWindowTitle("Phase 3: Edit Payment Record")
        else:
            self.setWindowTitle("Phase 3: Add Payment Record")
        self.resize(480, 520)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        title_text = "Edit Payment Disbursement" if self.payment_data else "Record Payment Disbursement"
        title = QLabel(title_text)
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #00ffcc; margin-bottom: 10px;")
        layout.addWidget(title)
        
        form = QFormLayout()
        form.setSpacing(8)
        
        # Deliverable Milestone Picker
        self.deliv_combo = QComboBox()
        for d in self.contract_data.get("deliverables", []):
            self.deliv_combo.addItem(d["milestone_deliverable"], d["id"])
        form.addRow("Milestone Deliverable *:", self.deliv_combo)
        
        self.pay_type = QComboBox()
        self.pay_type.addItems(["Progress Payment", "Advance Payment (15%)", "Final Payment", "One-Time Full Payment"])
        form.addRow("Type of Payment:", self.pay_type)
        
        self.terms = QLineEdit("100% upon inspection and acceptance")
        form.addRow("Payment Schedule / Terms:", self.terms)
        
        self.due_date = QDateEdit(QDate.currentDate())
        self.due_date.setCalendarPopup(True)
        form.addRow("Due for Submission:", self.due_date)
        
        # Gross Amount
        self.gross_amt = QDoubleSpinBox()
        self.gross_amt.setRange(0, 999999999.99)
        self.gross_amt.setSingleStep(10000.0)
        self.gross_amt.setPrefix("₱")
        c_amt = self.contract_data.get("contract_amount", 0.0)
        self.gross_amt.setValue(c_amt)
        self.gross_amt.valueChanged.connect(self.calculate_disbursement_net)
        self.gross_amt.valueChanged.connect(self.validate_inputs)
        form.addRow("Gross Payment Amount *:", self.gross_amt)
        
        # Savings / Rebates (Deductible)
        self.savings = QDoubleSpinBox()
        self.savings.setRange(0, 999999999.99)
        self.savings.setSingleStep(1000.0)
        self.savings.setPrefix("₱")
        self.savings.valueChanged.connect(self.calculate_disbursement_net)
        form.addRow("Savings / Rebates (Deductible):", self.savings)
        
        # Taxes & Retention calculations
        self.retention_check = QCheckBox("Apply 10% Retention Deduction")
        self.retention_check.setChecked(True)
        self.retention_check.stateChanged.connect(self.calculate_disbursement_net)
        
        self.tax_type = QComboBox()
        self.tax_type.addItems(["Goods (1% EWT + 5% Gov VAT)", "Services (2% EWT + 5% Gov VAT)", "No Tax Deductions"])
        self.tax_type.currentIndexChanged.connect(self.calculate_disbursement_net)
        form.addRow("Tax Treatment Setup:", self.tax_type)
        form.addRow("", self.retention_check)
        
        # Display Auto-Calculated items (read only UI hints)
        self.ewt_lbl = QLabel("₱0.00")
        self.vat_lbl = QLabel("₱0.00")
        self.ret_lbl = QLabel("₱0.00")
        self.net_lbl = QLabel("₱0.00")
        self.net_lbl.setStyleSheet("color: #00ffcc; font-weight: bold; font-size: 14px;")
        
        form.addRow("Calculated EWT (1% / 2%):", self.ewt_lbl)
        form.addRow("Calculated Withholding VAT (5%):", self.vat_lbl)
        form.addRow("Calculated Retention Fee (10%):", self.ret_lbl)
        form.addRow("Final Net Disbursement Amount:", self.net_lbl)
        
        self.status = QComboBox()
        self.status.addItems(["Complete", "Incomplete", "Pending Signature", "Transmitted to Bank"])
        form.addRow("Payment Documents Status:", self.status)
        
        self.dv_no = QLineEdit()
        self.dv_no.setPlaceholderText("e.g. DV-2026-04-0012")
        form.addRow("RCI / DV / ACIC No:", self.dv_no)
        
        self.ada_no = QLineEdit()
        self.ada_no.setPlaceholderText("e.g. ADA-2026-0800")
        form.addRow("Check / LDDAP-ADA No:", self.ada_no)
        
        self.check_date = QDateEdit(QDate.currentDate())
        self.check_date.setCalendarPopup(True)
        form.addRow("Check / ADA Date:", self.check_date)
        
        # Populate if editing
        if self.payment_data:
            idx = self.deliv_combo.findData(self.payment_data.get("deliverable_id"))
            if idx >= 0:
                self.deliv_combo.setCurrentIndex(idx)
                
            idx = self.pay_type.findText(self.payment_data.get("types_of_payment", ""))
            if idx >= 0:
                self.pay_type.setCurrentIndex(idx)
                
            self.terms.setText(self.payment_data.get("payment_schedule_terms", ""))
            
            dd_val = self.payment_data.get("due_for_submission", "")
            if dd_val:
                self.due_date.setDate(QDate.fromString(dd_val, "yyyy-MM-dd"))
                
            self.gross_amt.setValue(self.payment_data.get("payment_amount_gross", 0.0))
            self.savings.setValue(self.payment_data.get("savings_unperformed_rebates", 0.0))
            
            ewt1 = self.payment_data.get("ewt_1_goods", 0.0)
            ewt2 = self.payment_data.get("ewt_2_services", 0.0)
            if ewt1 > 0:
                self.tax_type.setCurrentIndex(0)
            elif ewt2 > 0:
                self.tax_type.setCurrentIndex(1)
            else:
                self.tax_type.setCurrentIndex(2)
                
            ret_f = self.payment_data.get("retention_fee", 0.0)
            self.retention_check.setChecked(ret_f > 0)
            
            idx = self.status.findText(self.payment_data.get("status_of_payment_documents", ""))
            if idx >= 0:
                self.status.setCurrentIndex(idx)
                
            self.dv_no.setText(self.payment_data.get("rci_dv_acic_no", ""))
            self.ada_no.setText(self.payment_data.get("check_lddap_ada_no", ""))
            
            c_date = self.payment_data.get("check_date_lddap_ada", "")
            if c_date:
                self.check_date.setDate(QDate.fromString(c_date, "yyyy-MM-dd"))
                
        layout.addLayout(form)
        layout.addSpacing(15)
        
        # Calculate initially
        self.calculate_disbursement_net()
        
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(BUTTON_CANCEL_STYLE)
        cancel_btn.clicked.connect(self.reject)
        
        submit_btn_text = "Save Changes" if self.payment_data else "Submit Payment"
        submit_btn = QPushButton(submit_btn_text)
        submit_btn.setStyleSheet(BUTTON_SUBMIT_STYLE)
        submit_btn.clicked.connect(self.submit_data)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(submit_btn)
        layout.addLayout(btn_layout)
        
        # Initial validation highlight
        self.validate_inputs()
        
    def validate_inputs(self):
        gross_valid = self.gross_amt.value() > 0.0
        self.set_field_validation(self.gross_amt, gross_valid)
        return gross_valid
        
    def calculate_disbursement_net(self):
        gross = self.gross_amt.value()
        tax_idx = self.tax_type.currentIndex()
        
        ewt_rate = 0.0
        vat_rate = 0.0
        if tax_idx == 0:
            ewt_rate = 0.01
            vat_rate = 0.05
        elif tax_idx == 1:
            ewt_rate = 0.02
            vat_rate = 0.05
            
        ret_rate = 0.1 if self.retention_check.isChecked() else 0.0
        
        ewt = gross * ewt_rate
        vat = gross * vat_rate
        retention = gross * ret_rate
        savings = self.savings.value()
        net = gross - (ewt + vat + retention) - savings
        
        self.ewt_lbl.setText(f"₱{ewt:,.2f}")
        self.vat_lbl.setText(f"₱{vat:,.2f}")
        self.ret_lbl.setText(f"₱{retention:,.2f}")
        self.net_lbl.setText(f"₱{net:,.2f}")
        
    def submit_data(self):
        if not self.validate_inputs():
            self.gross_amt.setFocus()
            return
            
        gross = self.gross_amt.value()
        deliv_id = self.deliv_combo.currentData()
        
        if deliv_id is None:
            QMessageBox.warning(self, "Validation Error", "Please select a deliverable milestone.")
            return
            
        tax_idx = self.tax_type.currentIndex()
        ewt_1 = gross * 0.01 if tax_idx == 0 else 0.0
        ewt_2 = gross * 0.02 if tax_idx == 1 else 0.0
        vat = gross * 0.05 if tax_idx in [0, 1] else 0.0
        ret_rate = 0.1 if self.retention_check.isChecked() else 0.0
        ret_fee = gross * ret_rate
        savings = self.savings.value()
        net = gross - (ewt_1 + ewt_2 + vat + ret_fee) - savings
        
        if self.payment_data:
            success, result = database_config.update_payment(
                self.payment_data["id"], self.pay_type.currentText(), self.terms.text().strip(),
                self.due_date.date().toString("yyyy-MM-dd"), gross, savings,
                ewt_1, ewt_2, 0.0, vat, ret_rate, ret_fee, net,
                self.status.currentText(), self.dv_no.text().strip(), self.ada_no.text().strip(),
                self.check_date.date().toString("yyyy-MM-dd"), net
            )
            action_name = "updated"
        else:
            success, result = database_config.add_payment(
                self.contract_id, deliv_id, self.pay_type.currentText(), self.terms.text().strip(),
                self.due_date.date().toString("yyyy-MM-dd"), gross, savings,
                ewt_1, ewt_2, 0.0, vat, ret_rate, ret_fee, net,
                self.status.currentText(), self.dv_no.text().strip(), self.ada_no.text().strip(),
                self.check_date.date().toString("yyyy-MM-dd"), net
            )
            action_name = "recorded"
            
        if success:
            QMessageBox.information(self, "Success", f"Disbursement payment of ₱{net:,.2f} successfully {action_name}!")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", f"Failed to save payment record:\n{result}")

class AddWarrantyDialog(BaseFormDialog):
    def __init__(self, contract_id, parent=None, warranty_data=None):
        super().__init__(parent)
        self.contract_id = contract_id
        self.warranty_data = warranty_data
        self.warranty_file_path = None
        
        self.project_id = None
        try:
            conn = database_config.get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT project_id FROM contracts WHERE contract_id = ?", (self.contract_id,))
            row = cur.fetchone()
            if row:
                self.project_id = row["project_id"]
            conn.close()
        except Exception as e:
            print(f"Error resolving project_id in AddWarrantyDialog: {e}")
            
        if self.warranty_data:
            self.setWindowTitle("Phase 4: Edit Warranty details")
        else:
            self.setWindowTitle("Phase 4: Add Warranty details")
        self.resize(440, 440)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title_text = "Edit Warranty & Retention Security Info" if self.warranty_data else "Warranty & Retention Security Info"
        title = QLabel(title_text)
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #00ffcc; margin-bottom: 10px;")
        layout.addWidget(title)
        
        form = QFormLayout()
        form.setSpacing(10)
        
        self.start_date = QDateEdit(QDate.currentDate())
        self.start_date.setCalendarPopup(True)
        self.start_date.dateChanged.connect(self.calculate_end_date)
        form.addRow("Start of Warranty Period:", self.start_date)
        
        self.months = QSpinBox()
        self.months.setRange(1, 60)
        self.months.setValue(12)
        self.months.setSuffix(" months")
        self.months.valueChanged.connect(self.calculate_end_date)
        form.addRow("Warranty Period Duration:", self.months)
        
        self.end_date_lbl = QLabel()
        self.calculate_end_date()
        form.addRow("Calculated Warranty End Date:", self.end_date_lbl)
        
        self.security = QLineEdit("Retention Money (10%, Cash)")
        self.security.textChanged.connect(self.validate_inputs)
        form.addRow("Retention Security Form *:", self.security)
        
        self.status = QComboBox()
        self.status.addItems(["Ongoing", "Released", "Pending Claims", "COA Disallowance Hold"])
        form.addRow("Warranty Retention Status:", self.status)
        
        self.release_date_check = QCheckBox("Actual Date Release Retention")
        self.release_date = QDateEdit(QDate.currentDate().addYears(1))
        self.release_date.setCalendarPopup(True)
        self.release_date.setEnabled(False)
        self.release_date_check.stateChanged.connect(lambda state: self.release_date.setEnabled(state == 2))
        form.addRow(self.release_date_check, self.release_date)
        
        self.coa_claim = QCheckBox("With Petition for COA Claims")
        self.coa_claim.setChecked(False)
        form.addRow("COA Claims Petition:", self.coa_claim)
        
        # Warranty Certificate PDF File Uploader layout
        self.warranty_lbl = QLabel("<i>No Warranty Certificate PDF Uploaded</i>")
        self.warranty_lbl.setStyleSheet("color: #aaaaaa; font-size: 11px;")
        w_btn = QPushButton("Browse...")
        w_btn.clicked.connect(self.browse_warranty)
        w_layout = QHBoxLayout()
        w_layout.addWidget(self.warranty_lbl)
        w_layout.addWidget(w_btn)
        form.addRow("Warranty Certificate PDF:", w_layout)
        
        # Populate if editing
        if self.warranty_data:
            s_date = self.warranty_data.get("start_of_warranty_period", "")
            if s_date:
                self.start_date.setDate(QDate.fromString(s_date, "yyyy-MM-dd"))
                
            self.months.setValue(self.warranty_data.get("warranty_retention_period_months", 12))
            self.calculate_end_date()
            
            self.security.setText(self.warranty_data.get("retention_security", ""))
            
            idx = self.status.findText(self.warranty_data.get("retention_period_warranty_status", ""))
            if idx >= 0:
                self.status.setCurrentIndex(idx)
                
            r_date = self.warranty_data.get("actual_date_release_retention", "")
            if r_date:
                self.release_date_check.setChecked(True)
                self.release_date.setDate(QDate.fromString(r_date, "yyyy-MM-dd"))
                self.release_date.setEnabled(True)
                
            self.coa_claim.setChecked(self.warranty_data.get("with_petition_for_coa_claims") == 1)
            
            # Load existing document from SQLite
            try:
                import os
                conn = database_config.get_db_connection()
                cur = conn.cursor()
                cur.execute("SELECT warranty_certificate_pdf FROM warranties WHERE contract_id = ?", (self.contract_id,))
                row = cur.fetchone()
                if row and row["warranty_certificate_pdf"]:
                    self.warranty_file_path = row["warranty_certificate_pdf"]
                    self.warranty_lbl.setText("📄 " + os.path.basename(self.warranty_file_path))
                    self.warranty_lbl.setStyleSheet("color: #00ffcc; font-weight: bold;")
                conn.close()
            except Exception as e:
                print(f"Error loading existing warranty document: {e}")
            
        layout.addLayout(form)
        layout.addSpacing(15)
        
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(BUTTON_CANCEL_STYLE)
        cancel_btn.clicked.connect(self.reject)
        
        submit_btn_text = "Save Changes" if self.warranty_data else "Save Warranty details"
        submit_btn = QPushButton(submit_btn_text)
        submit_btn.setStyleSheet(BUTTON_SUBMIT_STYLE)
        submit_btn.clicked.connect(self.submit_data)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(submit_btn)
        layout.addLayout(btn_layout)
        
        # Initial validation highlight
        self.validate_inputs()
        
    def validate_inputs(self):
        sec_valid = len(self.security.text().strip()) > 0
        self.set_field_validation(self.security, sec_valid)
        return sec_valid
        
    def calculate_end_date(self):
        start = self.start_date.date()
        m = self.months.value()
        expected = start.addMonths(m)
        self.end_date_lbl.setText(expected.toString("yyyy-MM-dd"))
        
    def browse_warranty(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Upload Warranty Certificate (PDF)", "", "PDF Files (*.pdf);;All Files (*)")
        if file_path:
            import os
            self.warranty_lbl.setText("📄 " + os.path.basename(file_path))
            self.warranty_lbl.setStyleSheet("color: #00ffcc; font-weight: bold;")
            self.warranty_file_path = file_path
            
    def submit_data(self):
        if not self.validate_inputs():
            self.security.setFocus()
            return
            
        end_date = self.end_date_lbl.text()
        rel_date = self.release_date.date().toString("yyyy-MM-dd") if self.release_date_check.isChecked() else None
        coa = 1 if self.coa_claim.isChecked() else 0
        
        if self.warranty_data:
            success, result = database_config.update_warranty(
                self.warranty_data["id"], self.start_date.date().toString("yyyy-MM-dd"),
                self.months.value(), end_date, self.security.text().strip(),
                rel_date, self.status.currentText(), coa
            )
            action_name = "updated"
        else:
            success, result = database_config.add_warranty(
                self.contract_id, self.start_date.date().toString("yyyy-MM-dd"),
                self.months.value(), end_date, self.security.text().strip(),
                rel_date, self.status.currentText(), coa
            )
            action_name = "saved"
            
        if success:
            if self.warranty_file_path and not self.warranty_file_path.startswith("uploaded_documents/"):
                if self.project_id:
                    database_config.save_project_document(self.project_id, "Warranty", self.warranty_file_path)
            QMessageBox.information(self, "Success", f"Warranty and retention security details successfully {action_name}!")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", f"Failed to save warranty details:\n{result}")



class AddSupplierDialog(BaseFormDialog):
    def __init__(self, parent=None, supplier_data=None):
        super().__init__(parent)
        self.supplier_data = supplier_data
        self.setWindowTitle("Edit Supplier Details" if self.supplier_data else "Add New Supplier")
        self.resize(420, 380)
        self.setup_ui()
        if self.supplier_data:
            self.load_supplier_data()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("Modify Supplier Registry" if self.supplier_data else "Register New Supplier")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #00ffcc; margin-bottom: 15px;")
        layout.addWidget(title)
        
        form = QFormLayout()
        form.setSpacing(10)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., ACME Corporate Solutions Inc.")
        self.name_input.textChanged.connect(self.validate_inputs)
        form.addRow("Supplier Name *:", self.name_input)
        
        self.tin_input = QLineEdit()
        self.tin_input.setPlaceholderText("e.g., 123-456-789-000")
        form.addRow("TIN Number:", self.tin_input)
        
        self.addr_input = QLineEdit()
        self.addr_input.setPlaceholderText("e.g., 456 Quezon Avenue, Quezon City")
        form.addRow("Business Address:", self.addr_input)
        
        self.contact_input = QLineEdit()
        self.contact_input.setPlaceholderText("e.g., contact@acme.com / (02) 8123-4567")
        form.addRow("Contact Details:", self.contact_input)
        
        self.branch_input = QLineEdit()
        self.branch_input.setPlaceholderText("e.g., Landbank - DICT Branch")
        form.addRow("Bank Branch Name:", self.branch_input)
        
        self.acct_input = QLineEdit()
        self.acct_input.setPlaceholderText("e.g., 0012-3456-78")
        form.addRow("Bank Account Number:", self.acct_input)
        
        layout.addLayout(form)
        layout.addSpacing(15)
        
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(BUTTON_CANCEL_STYLE)
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QPushButton("Save Supplier")
        save_btn.setStyleSheet(BUTTON_SUBMIT_STYLE)
        save_btn.clicked.connect(self.submit_data)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)
        
        # Initial validation highlight
        self.validate_inputs()
        
    def load_supplier_data(self):
        s = self.supplier_data
        self.name_input.setText(s.get("supplier_name", ""))
        self.tin_input.setText(s.get("supplier_tin_no", ""))
        self.addr_input.setText(s.get("supplier_address", ""))
        self.contact_input.setText(s.get("supplier_contact_details", ""))
        self.branch_input.setText(s.get("supplier_bank_branch", ""))
        self.acct_input.setText(s.get("supplier_bank_account_number", ""))
        
    def validate_inputs(self):
        name_valid = len(self.name_input.text().strip()) > 0
        self.set_field_validation(self.name_input, name_valid)
        return name_valid
        
    def submit_data(self):
        if not self.validate_inputs():
            self.name_input.setFocus()
            return
            
        name = self.name_input.text().strip()
        tin = self.tin_input.text().strip()
        address = self.addr_input.text().strip()
        contact = self.contact_input.text().strip()
        branch = self.branch_input.text().strip()
        acct = self.acct_input.text().strip()
        
        if self.supplier_data:
            supplier_id = self.supplier_data.get("id")
            success, result = database_config.update_supplier(supplier_id, name, tin, address, contact, branch, acct)
            msg = "Supplier details successfully updated!"
        else:
            success, result = database_config.add_supplier(name, tin, address, contact, branch, acct)
            msg = "Supplier details successfully added to directory registry!"
            
        if success:
            QMessageBox.information(self, "Success", msg)
            self.accept()
        else:
            QMessageBox.critical(self, "Error", f"Failed to save supplier details:\n{result}")
