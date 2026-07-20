-- SQL Schema for Procurement and Payment Tracking Database (Consolidated 5-Table Layout)

CREATE TABLE IF NOT EXISTS projects (
    project_id TEXT PRIMARY KEY, -- matches PR No
    project_name TEXT NOT NULL,
    bureau_division TEXT,
    focal_person TEXT,
    focal_contact_email TEXT,
    nature_of_procurement TEXT, -- Goods, Civil Works, Consulting
    mode_of_procurement TEXT,
    approved_budget_abc REAL,
    source_of_funds TEXT,
    fund_source_type TEXT,
    app_cycle INTEGER,
    saro_control_number TEXT,
    bid_reference_no TEXT,
    post_to_philgeps INTEGER, -- Boolean (0 or 1)
    abstract_of_quotations_no TEXT,
    bac_resolution_no TEXT,
    date_received_bacsec TEXT, -- Date (yyyy-MM-dd)
    date_received_pcmd TEXT, -- Date (yyyy-MM-dd)
    signatory_box_a TEXT,
    signatory_box_c TEXT,
    status TEXT,
    remarks TEXT,
    -- Document path references
    saro_pdf TEXT,
    ppmp_pdf TEXT,
    market_scoping_pdf TEXT,
    tech_specs_pdf TEXT,
    abstract_quotations_pdf TEXT
);

CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_name TEXT NOT NULL,
    tin TEXT,
    address TEXT,
    bank_account TEXT,
    branch TEXT,
    bank_name TEXT
);

CREATE TABLE IF NOT EXISTS contracts (
    contract_id TEXT PRIMARY KEY, -- matches PO/JO No
    project_id TEXT,
    supplier_id INTEGER,
    contract_amount REAL,
    noa_date TEXT, -- Date (yyyy-MM-dd)
    ntp_date TEXT, -- Date (yyyy-MM-dd)
    contract_duration_days INTEGER,
    expected_end_date TEXT, -- Auto-calculated Date
    performance_security_form TEXT,
    performance_security_amount REAL,
    performance_security_validity TEXT,
    contract_amendments TEXT, -- JSON/Text
    -- Document paths
    noa_pdf TEXT,
    signed_contract_pdf TEXT,
    request_order_pdf TEXT,
    bac_resolution_pdf TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS deliveries_and_payments (
    milestone_id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id TEXT,
    milestone_description TEXT,
    expected_start_date TEXT,
    original_delivery_date TEXT,
    revised_delivery_date TEXT,
    actual_delivery_date TEXT,
    delivery_status TEXT,
    days_delayed INTEGER,
    liquidated_damages_rate REAL,
    liquidated_damages_amount REAL,
    iar_number TEXT,
    inspection_date TEXT,
    acceptance_date TEXT,
    facc_date TEXT,
    payment_type TEXT, -- Advance, Progress, Final
    payment_terms TEXT,
    due_date_submission TEXT,
    payment_gross_amount REAL,
    savings_rebates REAL,
    ewt_1_percent REAL,
    ewt_2_percent REAL,
    withholding_vat_5_percent REAL,
    retention_rate_applied INTEGER, -- Boolean (0 or 1)
    retention_fee REAL,
    payment_net_amount REAL,
    payment_status TEXT, -- In Process, Approved, Disbursed, Held
    dv_rci_serial_no TEXT,
    check_ada_no TEXT,
    check_date TEXT,
    -- Document paths
    iar_pdf TEXT,
    po_pdf TEXT,
    FOREIGN KEY (contract_id) REFERENCES contracts(contract_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS warranties (
    warranty_id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id TEXT,
    warranty_start_date TEXT,
    retention_period_months INTEGER,
    warranty_end_date TEXT, -- Auto-calculated Date
    retention_security_details TEXT,
    warranty_status TEXT,
    actual_release_date TEXT,
    coa_petition_claims INTEGER, -- Boolean (0 or 1)
    -- Document path
    warranty_certificate_pdf TEXT,
    FOREIGN KEY (contract_id) REFERENCES contracts(contract_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS system_settings (
    setting_key TEXT PRIMARY KEY,
    setting_value TEXT
);
