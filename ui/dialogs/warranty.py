import sys
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QDoubleSpinBox, QSpinBox, QDateEdit, QCheckBox, QPushButton,
    QFormLayout, QMessageBox, QFrame, QGroupBox, QRadioButton, QButtonGroup,
    QScrollArea, QWidget, QFileDialog
)
from PySide6.QtCore import Qt, QDate
from .base import BaseFormDialog, INPUT_STYLE, BUTTON_SUBMIT_STYLE, BUTTON_CANCEL_STYLE, database_config


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



