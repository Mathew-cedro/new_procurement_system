import sys
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QDoubleSpinBox, QSpinBox, QDateEdit, QCheckBox, QPushButton,
    QFormLayout, QMessageBox, QFrame, QGroupBox, QRadioButton, QButtonGroup,
    QScrollArea, QWidget, QFileDialog
)
from PySide6.QtCore import Qt, QDate
from .base import BaseFormDialog, INPUT_STYLE, BUTTON_SUBMIT_STYLE, BUTTON_CANCEL_STYLE, database_config


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
