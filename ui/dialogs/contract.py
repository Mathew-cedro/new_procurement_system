import sys
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QDoubleSpinBox, QSpinBox, QDateEdit, QCheckBox, QPushButton,
    QFormLayout, QMessageBox, QFrame, QGroupBox, QRadioButton, QButtonGroup,
    QScrollArea, QWidget, QFileDialog
)
from PySide6.QtCore import Qt, QDate
from .base import BaseFormDialog, INPUT_STYLE, BUTTON_SUBMIT_STYLE, BUTTON_CANCEL_STYLE, database_config


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
        
        self.abc_amount = 0.0
        try:
            conn = database_config.get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT approved_budget_abc FROM projects WHERE project_id = ?", (self.project_id,))
            r = cur.fetchone()
            if r and r["approved_budget_abc"]:
                self.abc_amount = r["approved_budget_abc"]
            conn.close()
        except Exception:
            pass

        self.con_amount = QDoubleSpinBox()
        self.con_amount.setRange(0, 999999999.99)
        self.con_amount.setSingleStep(10000.0)
        self.con_amount.setPrefix("₱")
        self.con_amount.valueChanged.connect(self.validate_inputs)
        self.con_amount.valueChanged.connect(self.update_budget_feedback)
        con_layout.addRow("Contract Award Amount *:", self.con_amount)
        
        self.budget_feedback_lbl = QLabel()
        con_layout.addRow("", self.budget_feedback_lbl)
        self.update_budget_feedback()
        
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
        
        from ui.widgets import DragDropFileWidget
        
        # Document Upload Group
        doc_group = QGroupBox("Contract & Award Documents")
        doc_group.setStyleSheet("QGroupBox { color: #00ffcc; font-weight: bold; border: 1px solid #3a3a4a; padding-top: 10px; }")
        doc_layout = QFormLayout(doc_group)
        doc_layout.setSpacing(8)
        
        self.noa_widget = DragDropFileWidget("📁 Drag & Drop Notice of Award (NOA) PDF here or Click to Browse")
        doc_layout.addRow("Notice of Award (NOA) PDF:", self.noa_widget)
        
        self.contract_widget = DragDropFileWidget("📁 Drag & Drop Signed Contract PDF here or Click to Browse")
        doc_layout.addRow("Signed Contract PDF:", self.contract_widget)
        
        self.reso_check = QCheckBox("BAC Reso (IF PRIMARY SUPPLIER IS NOT AVAILABLE)")
        self.reso_check.stateChanged.connect(self.toggle_reso_upload)
        doc_layout.addRow("", self.reso_check)
        
        self.reso_widget = DragDropFileWidget("📁 Drag & Drop BAC Resolution PDF here or Click to Browse")
        doc_layout.addRow("BAC Resolution PDF:", self.reso_widget)
        self.reso_widget.setVisible(False)
        
        self.rq_widget = DragDropFileWidget("📁 Drag & Drop Request Order (RQ) PDF here or Click to Browse")
        doc_layout.addRow("Request Order (RQ) PDF:", self.rq_widget)
        
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
            
            idx = self.nature.findText(self.contract_data.get("nature_of_procurement", ""))
            if idx >= 0:
                self.nature.setCurrentIndex(idx)
                
            self.sec_form.setText(self.contract_data.get("performance_security_form", "Surety Bond"))
            self.sec_amount.setValue(self.contract_data.get("performance_security_amount", 0.0))
            
            v_date = self.contract_data.get("performance_security_validity", "")
            if v_date:
                self.sec_valid.setDate(QDate.fromString(v_date, "yyyy-MM-dd"))
                
            self.loading_data = False
                
        # Load existing docs
        if self.project_id:
            try:
                conn = database_config.get_db_connection()
                cur = conn.cursor()
                cur.execute("SELECT * FROM contracts WHERE project_id = ?", (self.project_id,))
                row = cur.fetchone()
                if row:
                    if row["noa_pdf"]:
                        self.noa_widget.set_file_path(row["noa_pdf"])
                    if row["signed_contract_pdf"]:
                        self.contract_widget.set_file_path(row["signed_contract_pdf"])
                    if row["bac_resolution_pdf"]:
                        self.reso_widget.set_file_path(row["bac_resolution_pdf"])
                        self.reso_check.setChecked(True)
                        self.reso_widget.setVisible(True)
                    if row["request_order_pdf"]:
                        self.rq_widget.set_file_path(row["request_order_pdf"])
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
        self.reso_widget.setVisible(state == 2)
        
    def browse_noa(self): pass
    def browse_contract(self): pass
    def browse_reso(self): pass
    def browse_rq(self): pass

    def update_budget_feedback(self):
        val = self.con_amount.value()
        if self.abc_amount <= 0:
            self.budget_feedback_lbl.setText("")
            return
        if val <= self.abc_amount:
            savings = self.abc_amount - val
            pct = (savings / self.abc_amount) * 100 if self.abc_amount > 0 else 0.0
            self.budget_feedback_lbl.setText(f"🟢 Savings: ₱{savings:,.2f} ({pct:.1f}% under ABC ₱{self.abc_amount:,.2f})")
            self.budget_feedback_lbl.setStyleSheet("color: #1F9D55; font-size: 11px; font-weight: bold;")
        else:
            overrun = val - self.abc_amount
            self.budget_feedback_lbl.setText(f"⚠️ BUDGET OVERRUN: Exceeds ABC (₱{self.abc_amount:,.2f}) by ₱{overrun:,.2f}!")
            self.budget_feedback_lbl.setStyleSheet("color: #C9282D; font-size: 11px; font-weight: bold;")

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
                
        f_cap = self.f_capacity.value()
        if f_cap == 0:
            f_cap = amount
            
        sec_amt = self.sec_amount.value()
        if sec_amt == 0:
            sec_amt = amount * 0.1
            
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
            target_id = self.project_id if self.project_id else po_jo
            noa_p = self.noa_widget.get_file_path()
            con_p = self.contract_widget.get_file_path()
            reso_p = self.reso_widget.get_file_path()
            rq_p = self.rq_widget.get_file_path()
            
            # Save files
            if noa_p and not noa_p.startswith("uploaded_documents/"):
                database_config.save_project_document(target_id, "NOA", noa_p)
            if con_p and not con_p.startswith("uploaded_documents/"):
                database_config.save_project_document(target_id, "Contract", con_p)
            if self.reso_check.isChecked() and reso_p and not reso_p.startswith("uploaded_documents/"):
                database_config.save_project_document(target_id, "BAC_Reso", reso_p)
            elif not self.reso_check.isChecked():
                try:
                    conn = database_config.get_db_connection()
                    cur = conn.cursor()
                    cur.execute("UPDATE contracts SET bac_resolution_pdf = NULL, bac_resolution_pdf_data = NULL WHERE project_id = ? OR contract_id = ?", (target_id, po_jo))
                    conn.commit()
                    conn.close()
                except Exception:
                    pass
            if rq_p and not rq_p.startswith("uploaded_documents/"):
                database_config.save_project_document(target_id, "RQ", rq_p)
                    
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

