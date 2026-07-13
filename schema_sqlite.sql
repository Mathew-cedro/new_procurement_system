-- SQL Schema for Procurement and Payment Tracking Database

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proj_id_no TEXT UNIQUE NOT NULL,
    project_name TEXT NOT NULL,
    saro_number TEXT,
    bureau_division_name TEXT,
    focal_person TEXT,
    end_user_contact_details TEXT,
    mode_of_procurement TEXT,
    abc_amount REAL,
    source_of_funds TEXT,
    fund_source TEXT,
    app_cycle INTEGER,
    status TEXT
);

CREATE TABLE IF NOT EXISTS project_budgets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    budget_type TEXT,
    app_amount REAL,
    ors_amount REAL,
    ors_serial_no TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS project_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    document_type TEXT,
    file_reference TEXT,
    date_prepared TEXT,
    prepared_by TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS bids (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    bid_reference_no TEXT,
    date_received_bacsec TEXT,
    date_received_pcmd_initial TEXT,
    signatory_box_a TEXT,
    signatory_box_c TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_name TEXT NOT NULL,
    supplier_tin_no TEXT,
    supplier_address TEXT,
    supplier_contact_details TEXT,
    supplier_bank_account TEXT,
    supplier_bank_branch TEXT,
    supplier_bank_account_number TEXT
);

CREATE TABLE IF NOT EXISTS contracts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    bid_id INTEGER,
    supplier_id INTEGER,
    financial_capacity_amount REAL,
    notice_of_award_date TEXT,
    performance_security_form TEXT,
    performance_security_amount REAL,
    performance_security_validity TEXT,
    contract_date TEXT,
    po_jo_contract_no TEXT,
    contract_amount REAL,
    notice_to_proceed_date TEXT,
    contract_duration_days INTEGER,
    expected_end_of_contract TEXT,
    nature_of_procurement TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (bid_id) REFERENCES bids(id) ON DELETE SET NULL,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS contract_amendments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    amendment_type TEXT,
    variation_order_amount REAL,
    suspension_days INTEGER,
    extension_days INTEGER,
    amendment_date TEXT,
    remarks TEXT,
    FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS deliverables (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    milestone_deliverable TEXT,
    expected_start_date TEXT,
    original_expected_delivery_date TEXT,
    delivery_period_days INTEGER,
    revised_delivery_date TEXT,
    actual_delivery_date TEXT,
    status_of_delivery TEXT,
    days_delayed INTEGER,
    rate_liquidated_damages REAL,
    liquidated_damages_amount REAL,
    iar_no TEXT,
    inspection_date TEXT,
    acceptance_date TEXT,
    facc_date TEXT,
    issues_and_concerns TEXT,
    remarks_status TEXT,
    FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    deliverable_id INTEGER,
    types_of_payment TEXT,
    payment_schedule_terms TEXT,
    due_for_submission TEXT,
    payment_amount_gross REAL,
    savings_unperformed_rebates REAL,
    ewt_1_goods REAL,
    ewt_2_services REAL,
    tax_5_rent_lease_prof REAL,
    withholding_vat_5 REAL,
    retention_rate REAL,
    retention_fee REAL,
    payment_amount_net REAL,
    status_of_payment_documents TEXT,
    rci_dv_acic_no TEXT,
    check_lddap_ada_no TEXT,
    check_date_lddap_ada TEXT,
    lddap_ada_amount REAL,
    FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE CASCADE,
    FOREIGN KEY (deliverable_id) REFERENCES deliverables(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS warranties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    start_of_warranty_period TEXT,
    warranty_retention_period_months INTEGER,
    end_date_of_warranty_period TEXT,
    retention_security TEXT,
    actual_date_release_retention TEXT,
    retention_period_warranty_status TEXT,
    with_petition_for_coa_claims INTEGER,
    FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE CASCADE
);
