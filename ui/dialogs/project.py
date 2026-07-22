import sys
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QDoubleSpinBox, QSpinBox, QDateEdit, QCheckBox, QPushButton,
    QFormLayout, QMessageBox, QFrame, QGroupBox, QRadioButton, QButtonGroup,
    QScrollArea, QWidget, QFileDialog
)
from PySide6.QtCore import Qt, QDate
from .base import BaseFormDialog, INPUT_STYLE, BUTTON_SUBMIT_STYLE, BUTTON_CANCEL_STYLE, database_config


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
        
        from ui.widgets import DragDropFileWidget

# SARO Document PDF
        self.saro_widget = DragDropFileWidget("📁 Drag & Drop SARO PDF here or Click to Browse")
        doc_layout.addRow("SARO PDF Document:", self.saro_widget)
        
        # PPMP Document PDF
        self.ppmp_widget = DragDropFileWidget("📁 Drag & Drop PPMP PDF here or Click to Browse")
        doc_layout.addRow("PPMP PDF Document:", self.ppmp_widget)
        
        # MS Document PDF
        self.ms_widget = DragDropFileWidget("📁 Drag & Drop Market Scoping PDF here or Click to Browse")
        doc_layout.addRow("Market Scoping PDF:", self.ms_widget)
        
        # TS Document PDF
        self.ts_widget = DragDropFileWidget("📁 Drag & Drop Tech Specs/TOR PDF here or Click to Browse")
        doc_layout.addRow("Tech Specs/TOR PDF:", self.ts_widget)
        
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
                conn = database_config.get_db_connection()
                cur = conn.cursor()
                
                cur.execute("SELECT saro_pdf, ppmp_pdf, market_scoping_pdf, tech_specs_pdf FROM projects WHERE project_id = ?", (pid,))
                row = cur.fetchone()
                if row:
                    if row["saro_pdf"]:
                        self.saro_widget.set_file_path(row["saro_pdf"])
                    if row["ppmp_pdf"]:
                        self.ppmp_widget.set_file_path(row["ppmp_pdf"])
                    if row["market_scoping_pdf"]:
                        self.ms_widget.set_file_path(row["market_scoping_pdf"])
                    if row["tech_specs_pdf"]:
                        self.ts_widget.set_file_path(row["tech_specs_pdf"])
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
            saro_path = self.saro_widget.get_file_path()
            ppmp_path = self.ppmp_widget.get_file_path()
            ms_path = self.ms_widget.get_file_path()
            ts_path = self.ts_widget.get_file_path()
            
            # Save files
            if saro_path and not saro_path.startswith("uploaded_documents/"):
                database_config.save_project_document(project_id, "SARO", saro_path)
            if ppmp_path and not ppmp_path.startswith("uploaded_documents/"):
                database_config.save_project_document(project_id, "PPMP", ppmp_path)
            if ms_path and not ms_path.startswith("uploaded_documents/"):
                database_config.save_project_document(project_id, "MS", ms_path)
            if ts_path and not ts_path.startswith("uploaded_documents/"):
                database_config.save_project_document(project_id, "TS", ts_path)
                
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

