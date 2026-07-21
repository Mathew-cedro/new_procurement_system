import sys
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QDoubleSpinBox, QSpinBox, QDateEdit, QCheckBox, QPushButton,
    QFormLayout, QMessageBox, QFrame, QGroupBox, QRadioButton, QButtonGroup,
    QScrollArea, QWidget, QFileDialog
)
from PySide6.QtCore import Qt, QDate
from .base import BaseFormDialog, INPUT_STYLE, BUTTON_SUBMIT_STYLE, BUTTON_CANCEL_STYLE, database_config


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

