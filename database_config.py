import sqlite3
import json
from pathlib import Path

DB_PATH = "procurement.db"


def seed():
    # 1. Back up system_settings if they exist
    settings_backup = {}
    db_file = Path(DB_PATH)
    if db_file.exists():
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("SELECT setting_key, setting_value FROM system_settings")
            for row in cur.fetchall():
                settings_backup[row[0]] = row[1]
            conn.close()
        except Exception:
            pass # Table or DB might not exist yet
            
    db_file.unlink(missing_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(Path(Path(__file__).parent / "schema_sqlite.sql").read_text())

    # 2. Restore system_settings backup
    if settings_backup:
        try:
            cur = conn.cursor()
            for key, val in settings_backup.items():
                cur.execute("INSERT OR REPLACE INTO system_settings (setting_key, setting_value) VALUES (?, ?)", (key, val))
            conn.commit()
        except Exception as e:
            print(f"Failed to restore settings backup: {e}")
            
    # Ensure all tables and seed settings are correctly up to date
    check_and_update_schema(conn)

    cur = conn.cursor()

    # Project 1: fully progressed to Under Warranty
    cur.execute("""
        INSERT INTO projects (
            project_id, project_name, bureau_division, focal_person, focal_contact_email,
            nature_of_procurement, mode_of_procurement, approved_budget_abc, source_of_funds,
            fund_source_type, app_cycle, saro_control_number, bid_reference_no, post_to_philgeps,
            abstract_of_quotations_no, bac_resolution_no, date_received_bacsec, date_received_pcmd,
            signatory_box_a, signatory_box_c, status, remarks
        ) VALUES (
            'PRJ-2026-0001', 'Supply of Office Equipment', 'Procurement Division', 'Juan Dela Cruz', 
            'juan.delacruz@agency.gov.ph', 'Goods', 'Shopping', 450000.0, 'General Fund', 'GAA', 2, 
            'SARO-2026-00123', 'BID-2026-0001', 1, 'Abstract-2026-0001', 'BAC-Reso-2026-0001', 
            '2026-02-01', '2026-02-03', 'Maria Santos', 'Pedro Reyes', 'Under Warranty', 'Fully progressed project.'
        )
    """)

    cur.execute("""
        INSERT INTO suppliers (
            supplier_id, supplier_name, tin, address, bank_account, branch, bank_name
        ) VALUES (
            1, 'ABC Trading Corp.', '123-456-789-000', '123 Rizal St., Manila', 
            'ABC Trading Corp.', 'BDO Ayala Branch', 'BDO'
        )
    """)

    cur.execute("""
        INSERT INTO contracts (
            contract_id, project_id, supplier_id, contract_amount, noa_date, ntp_date,
            contract_duration_days, expected_end_date, performance_security_form,
            performance_security_amount, performance_security_validity, contract_amendments
        ) VALUES (
            'CTR-2026-0001', 'PRJ-2026-0001', 1, 445000.0, '2026-02-10', '2026-02-20', 
            30, '2026-03-22', 'Surety Bond', 44500.0, '2026-05-10', '[]'
        )
    """)

    cur.execute("""
        INSERT INTO deliveries_and_payments (
            contract_id, milestone_description, expected_start_date, original_delivery_date,
            revised_delivery_date, actual_delivery_date, delivery_status, days_delayed,
            liquidated_damages_rate, liquidated_damages_amount, iar_number, inspection_date,
            acceptance_date, facc_date, payment_type, payment_terms, due_date_submission,
            payment_gross_amount, savings_rebates, ewt_1_percent, ewt_2_percent,
            withholding_vat_5_percent, retention_rate_applied, retention_fee, payment_net_amount,
            payment_status, dv_rci_serial_no, check_ada_no, check_date
        ) VALUES (
            'CTR-2026-0001', 'Delivery of office chairs and desks', '2026-02-20', '2026-03-22',
            '2026-04-01', '2026-03-30', 'Delivered', 0, 0.1, 0.0, 'IAR-2026-0001', '2026-03-31',
            '2026-04-01', '2026-04-02', 'Final', '100% upon acceptance', '2026-04-05',
            445000.0, 0.0, 4450.0, 0.0, 0.0, 1, 44500.0, 396050.0,
            'Complete', 'DV-2026-0456', 'ADA-2026-0789', '2026-04-10'
        )
    """)

    cur.execute("""
        INSERT INTO warranties (
            contract_id, warranty_start_date, retention_period_months, warranty_end_date,
            retention_security_details, warranty_status, actual_release_date, coa_petition_claims
        ) VALUES (
            'CTR-2026-0001', '2026-04-02', 12, '2027-04-02', 'Retention Money (10%, Cash)', 'Ongoing', NULL, 0
        )
    """)

    # Project 2: only reached Phase 1 Bidding stage
    cur.execute("""
        INSERT INTO projects (
            project_id, project_name, bureau_division, focal_person, focal_contact_email,
            nature_of_procurement, mode_of_procurement, approved_budget_abc, source_of_funds,
            fund_source_type, app_cycle, saro_control_number, bid_reference_no, post_to_philgeps,
            abstract_of_quotations_no, bac_resolution_no, date_received_bacsec, date_received_pcmd,
            signatory_box_a, signatory_box_c, status, remarks
        ) VALUES (
            'PRJ-2026-0002', 'Repair of Office Aircon Units', 'General Services Division', 'Ana Reyes',
            'ana.reyes@agency.gov.ph', 'Goods', 'Shopping', 85000.0, 'General Fund', 'GAA', 3,
            'SARO-2026-00187', 'BID-2026-0007', 0, NULL, NULL, '2026-03-05', NULL,
            'Maria Santos', NULL, 'Planning & Bidding', 'Initial bidding setup.'
        )
    """)

    conn.commit()
    conn.close()
    print(f"Seeded {DB_PATH} with 2 projects.")


def check_and_update_schema(conn):
    cur = conn.cursor()
    
    # Check if migration is needed (if projects table exists and has old schema column like 'proj_id_no')
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='projects'")
    table_exists = cur.fetchone()
    
    if table_exists:
        cur.execute("PRAGMA table_info(projects)")
        columns = [row["name"] for row in cur.fetchall()]
        if "proj_id_no" in columns:
            print("Detected legacy database schema. Initiating automatic migration...")
            
            # List of tables to rename if they exist
            tables_to_rename = ["projects", "suppliers", "contracts", "contract_amendments", "deliverables", "payments", "warranties", "project_documents"]
            for t in tables_to_rename:
                cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{t}'")
                if cur.fetchone():
                    cur.execute(f"ALTER TABLE {t} RENAME TO {t}_old")
            
            # Drop auxiliary tables we don't need anymore
            cur.execute("DROP TABLE IF EXISTS project_budgets")
            cur.execute("DROP TABLE IF EXISTS bids")
            
            # Recreate the schema
            schema_path = Path(__file__).parent / "schema_sqlite.sql"
            if schema_path.exists():
                cur.executescript(schema_path.read_text())
                
            # Perform table mappings
            try:
                # 1. Suppliers
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='suppliers_old'")
                if cur.fetchone():
                    cur.execute("SELECT * FROM suppliers_old")
                    for s in cur.fetchall():
                        cur.execute("""
                            INSERT INTO suppliers (supplier_id, supplier_name, tin, address, bank_account, branch, bank_name)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (s["id"], s["supplier_name"], s["supplier_tin_no"], s["supplier_address"], 
                              s["supplier_bank_account"], s["supplier_bank_branch"], s["supplier_bank_account_number"]))
                
                # 2. Projects
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='projects_old'")
                if cur.fetchone():
                    cur.execute("SELECT * FROM projects_old")
                    for p_row in cur.fetchall():
                        p = dict(p_row)
                        pid = p["id"]
                        pr_no = p["proj_id_no"]
                        
                        bid_ref = None; post_phil = 0; abstract_no = None; reso_no = None
                        date_bacsec = None; date_pcmd = None; sig_a = None; sig_c = None
                        
                        # Check old bids table
                        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bids_old'")
                        if cur.fetchone():
                            cur.execute("SELECT * FROM bids_old WHERE project_id = ?", (pid,))
                            bid_row = cur.fetchone()
                            if bid_row:
                                bid_ref = bid_row["bid_reference_no"]
                                post_phil = 1 if bid_row["post_to_philgeps"] == "Yes (Posted)" else 0
                                abstract_no = bid_row["abstract_of_quotations_no"]
                                reso_no = bid_row["bac_resolution_no"]
                                date_bacsec = bid_row["date_received_bacsec"]
                                date_pcmd = bid_row["date_received_pcmd_initial"]
                                sig_a = bid_row["signatory_box_a"]
                                sig_c = bid_row["signatory_box_c"]
                                
                        saro_path = None; saro_data = None
                        ppmp_path = None; ppmp_data = None
                        ms_path = None; ms_data = None
                        ts_path = None; ts_data = None
                        abs_path = None; abs_data = None
                        
                        # Check old docs table
                        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='project_documents_old'")
                        if cur.fetchone():
                            cur.execute("SELECT * FROM project_documents_old WHERE project_id = ?", (pid,))
                            for d in cur.fetchall():
                                dtype = d["document_type"]
                                ref = d["file_reference"]
                                content = d["file_content"]
                                if dtype == "SARO":
                                    saro_path = ref; saro_data = content
                                elif dtype == "PPMP":
                                    ppmp_path = ref; ppmp_data = content
                                elif dtype == "MS":
                                    ms_path = ref; ms_data = content
                                elif dtype == "TS":
                                    ts_path = ref; ts_data = content
                                elif dtype == "Abstract":
                                    abs_path = ref; abs_data = content
                                    
                        nature = "Goods"
                        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='contracts_old'")
                        if cur.fetchone():
                            cur.execute("SELECT nature_of_procurement FROM contracts_old WHERE project_id = ?", (pid,))
                            con_row = cur.fetchone()
                            if con_row:
                                nature = con_row["nature_of_procurement"] or "Goods"
                                
                        cur.execute("""
                            INSERT INTO projects (
                                project_id, project_name, bureau_division, focal_person, focal_contact_email,
                                nature_of_procurement, mode_of_procurement, approved_budget_abc, source_of_funds,
                                fund_source_type, app_cycle, saro_control_number, bid_reference_no, post_to_philgeps,
                                abstract_of_quotations_no, bac_resolution_no, date_received_bacsec, date_received_pcmd,
                                signatory_box_a, signatory_box_c, status, remarks,
                                saro_pdf, ppmp_pdf, market_scoping_pdf, tech_specs_pdf, abstract_quotations_pdf
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            pr_no, p["project_name"], p["bureau_division_name"], p["focal_person"], p["end_user_contact_details"],
                            nature, p["mode_of_procurement"], p["abc_amount"], p["source_of_funds"],
                            p["fund_source"], p["app_cycle"], p["saro_number"], bid_ref, post_phil,
                            abstract_no, reso_no, date_bacsec, date_pcmd,
                            sig_a, sig_c, p["status"], p.get("remarks", ""),
                            saro_path, ppmp_path, ms_path, ts_path, abs_path
                        ))
                
                # 3. Contracts
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='contracts_old'")
                if cur.fetchone():
                    cur.execute("SELECT * FROM contracts_old")
                    for c_row in cur.fetchall():
                        c = dict(c_row)
                        old_pid = c["project_id"]
                        cur.execute("SELECT proj_id_no FROM projects_old WHERE id = ?", (old_pid,))
                        p_row = cur.fetchone()
                        pr_no = p_row["proj_id_no"] if p_row else f"PRJ-UNKNOWN-{old_pid}"
                        
                        noa_path = None; noa_data = None
                        contract_path = None; contract_data = None
                        reso_path = None; reso_data = None
                        rq_path = None; rq_data = None
                        
                        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='project_documents_old'")
                        if cur.fetchone():
                            cur.execute("SELECT * FROM project_documents_old WHERE project_id = ?", (old_pid,))
                            for d in cur.fetchall():
                                dtype = d["document_type"]
                                ref = d["file_reference"]
                                content = d["file_content"]
                                if dtype == "NOA":
                                    noa_path = ref; noa_data = content
                                elif dtype == "Contract":
                                    contract_path = ref; contract_data = content
                                elif dtype == "BAC_Reso":
                                    reso_path = ref; reso_data = content
                                elif dtype == "RQ":
                                    rq_path = ref; rq_data = content
                                    
                        amend_list = []
                        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='contract_amendments_old'")
                        if cur.fetchone():
                            cur.execute("SELECT * FROM contract_amendments_old WHERE contract_id = ?", (c["id"],))
                            for a in cur.fetchall():
                                amend_list.append({
                                    "amendment_type": a["amendment_type"],
                                    "variation_order_amount": a["variation_order_amount"],
                                    "suspension_days": a["suspension_days"],
                                    "extension_days": a["extension_days"],
                                    "amendment_date": a.get("amendment_date", ""),
                                    "remarks": a["remarks"]
                                })
                        amend_str = json.dumps(amend_list)
                        
                        cur.execute("""
                            INSERT INTO contracts (
                                contract_id, project_id, supplier_id, contract_amount, noa_date, ntp_date,
                                contract_duration_days, expected_end_date, performance_security_form,
                                performance_security_amount, performance_security_validity, contract_amendments,
                                noa_pdf, signed_contract_pdf, request_order_pdf, bac_resolution_pdf
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            c["po_jo_contract_no"], pr_no, c["supplier_id"], c["contract_amount"],
                            c["notice_of_award_date"], c["notice_to_proceed_date"], c["contract_duration_days"],
                            c["expected_end_of_contract"], c["performance_security_form"], c["performance_security_amount"],
                            c["performance_security_validity"], amend_str,
                            noa_path, contract_path, rq_path, reso_path
                        ))
                        
                # 4. Deliveries and Payments
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='deliverables_old'")
                if cur.fetchone():
                    cur.execute("SELECT * FROM deliverables_old")
                    for d_row in cur.fetchall():
                        d = dict(d_row)
                        old_deliv_id = d["id"]
                        old_cid = d["contract_id"]
                        
                        cur.execute("SELECT po_jo_contract_no FROM contracts_old WHERE id = ?", (old_cid,))
                        c_row = cur.fetchone()
                        contract_id = c_row["po_jo_contract_no"] if c_row else f"CTR-UNKNOWN-{old_cid}"
                        
                        iar_path = None; iar_data = None
                        po_path = None; po_data = None
                        
                        cur.execute("SELECT project_id FROM contracts_old WHERE id = ?", (old_cid,))
                        proj_id_row = cur.fetchone()
                        if proj_id_row:
                            old_proj_id = proj_id_row["project_id"]
                            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='project_documents_old'")
                            if cur.fetchone():
                                cur.execute("SELECT * FROM project_documents_old WHERE project_id = ? AND document_type IN ('IAR', 'PO_Phase3')", (old_proj_id,))
                                for doc in cur.fetchall():
                                    if doc["document_type"] == "IAR":
                                        iar_path = doc["file_reference"]; iar_data = doc["file_content"]
                                    elif doc["document_type"] == "PO_Phase3":
                                        po_path = doc["file_reference"]; po_data = doc["file_content"]
                                        
                        p_type = None; p_terms = None; due_date = None; gross = 0.0; savings = 0.0
                        ewt1 = 0.0; ewt2 = 0.0; vat5 = 0.0; ret_applied = 0; ret_fee = 0.0; net = 0.0
                        p_status = "Pending"; dv_no = None; check_no = None; check_date = None
                        
                        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='payments_old'")
                        if cur.fetchone():
                            cur.execute("SELECT * FROM payments_old WHERE deliverable_id = ?", (old_deliv_id,))
                            p_row = cur.fetchone()
                            if p_row:
                                p_type = p_row["types_of_payment"]
                                p_terms = p_row["payment_schedule_terms"]
                                due_date = p_row["due_for_submission"]
                                gross = p_row["payment_amount_gross"] or 0.0
                                savings = p_row["savings_unperformed_rebates"] or 0.0
                                ewt1 = p_row["ewt_1_goods"] or 0.0
                                ewt2 = p_row["ewt_2_services"] or 0.0
                                vat5 = p_row["withholding_vat_5"] or 0.0
                                ret_applied = 1 if (p_row["retention_rate"] or 0.0) > 0 else 0
                                ret_fee = p_row["retention_fee"] or 0.0
                                net = p_row["payment_amount_net"] or 0.0
                                p_status = p_row["status_of_payment_documents"] or "Pending"
                                dv_no = p_row["rci_dv_acic_no"]
                                check_no = p_row["check_lddap_ada_no"]
                                check_date = p_row["check_date_lddap_ada"]
                                
                        cur.execute("""
                            INSERT INTO deliveries_and_payments (
                                contract_id, milestone_description, expected_start_date, original_delivery_date,
                                revised_delivery_date, actual_delivery_date, delivery_status, days_delayed,
                                liquidated_damages_rate, liquidated_damages_amount, iar_number, inspection_date,
                                acceptance_date, facc_date, payment_type, payment_terms, due_date_submission,
                                payment_gross_amount, savings_rebates, ewt_1_percent, ewt_2_percent,
                                withholding_vat_5_percent, retention_rate_applied, retention_fee, payment_net_amount,
                                payment_status, dv_rci_serial_no, check_ada_no, check_date,
                                iar_pdf, po_pdf
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            contract_id, d["milestone_deliverable"], d["expected_start_date"], d["original_expected_delivery_date"],
                            d["revised_delivery_date"], d["actual_delivery_date"], d["status_of_delivery"], d["days_delayed"],
                            d["rate_liquidated_damages"], d["liquidated_damages_amount"], d["iar_no"], d["inspection_date"],
                            d["acceptance_date"], d["facc_date"], p_type, p_terms, due_date,
                            gross, savings, ewt1, ewt2,
                            vat5, ret_applied, ret_fee, net,
                            p_status, dv_no, check_no, check_date,
                            iar_path, po_path
                        ))
                        
                # 5. Warranties
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='warranties_old'")
                if cur.fetchone():
                    cur.execute("SELECT * FROM warranties_old")
                    for w_row in cur.fetchall():
                        w = dict(w_row)
                        old_cid = w["contract_id"]
                        cur.execute("SELECT po_jo_contract_no FROM contracts_old WHERE id = ?", (old_cid,))
                        c_row = cur.fetchone()
                        contract_id = c_row["po_jo_contract_no"] if c_row else f"CTR-UNKNOWN-{old_cid}"
                        
                        w_path = None; w_data = None
                        cur.execute("SELECT project_id FROM contracts_old WHERE id = ?", (old_cid,))
                        proj_id_row = cur.fetchone()
                        if proj_id_row:
                            old_proj_id = proj_id_row["project_id"]
                            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='project_documents_old'")
                            if cur.fetchone():
                                cur.execute("SELECT * FROM project_documents_old WHERE project_id = ? AND document_type = 'Warranty'", (old_proj_id,))
                                doc = cur.fetchone()
                                if doc:
                                    w_path = doc["file_reference"]; w_data = doc["file_content"]
                                    
                        cur.execute("""
                            INSERT INTO warranties (
                                contract_id, warranty_start_date, retention_period_months, warranty_end_date,
                                retention_security_details, warranty_status, actual_release_date, coa_petition_claims,
                                warranty_certificate_pdf
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            contract_id, w["start_of_warranty_period"], w["warranty_retention_period_months"],
                            w["end_date_of_warranty_period"], w["retention_security"], w["retention_period_warranty_status"],
                            w["actual_date_release_retention"], w["with_petition_for_coa_claims"],
                            w_path
                        ))
                        
                # Drop all OLD tables
                for t in tables_to_rename:
                    cur.execute(f"DROP TABLE IF EXISTS {t}_old")
                cur.execute("DROP TABLE IF EXISTS contract_amendments_old")
                
                conn.commit()
                print("Database migration successful!")
            except Exception as e:
                conn.rollback()
                print(f"Error during database migration: {e}")
    else:
        # DB doesn't exist or is empty, execute standard table creation
        schema_path = Path(__file__).parent / "schema_sqlite.sql"
        if schema_path.exists():
            cur.executescript(schema_path.read_text())
            conn.commit()

    # Ensure 'contact' column exists in suppliers
    try:
        cur.execute("ALTER TABLE suppliers ADD COLUMN contact TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # Already exists

    default_creds = ""
    creds_file = Path(__file__).parent / "procurement_credentials.json"
    if creds_file.exists():
        default_creds = str(creds_file.resolve())

    # Ensure system_settings table exists and is seeded
    cur.execute("""
        CREATE TABLE IF NOT EXISTS system_settings (
            setting_key TEXT PRIMARY KEY,
            setting_value TEXT
        )
    """)
    cur.execute("INSERT OR IGNORE INTO system_settings (setting_key, setting_value) VALUES ('theme', 'dark')")
    cur.execute("INSERT OR IGNORE INTO system_settings (setting_key, setting_value) VALUES ('google_credentials_path', ?)", (default_creds,))
    cur.execute("INSERT OR IGNORE INTO system_settings (setting_key, setting_value) VALUES ('google_spreadsheet_id', '')")
    cur.execute("INSERT OR IGNORE INTO system_settings (setting_key, setting_value) VALUES ('google_drive_folder_id', '')")
    
    if default_creds:
        cur.execute("SELECT setting_value FROM system_settings WHERE setting_key = 'google_credentials_path'")
        row = cur.fetchone()
        if not row or not row[0]:
            cur.execute("INSERT OR REPLACE INTO system_settings (setting_key, setting_value) VALUES ('google_credentials_path', ?)", (default_creds,))
            
    conn.commit()


def get_db_connection():
    db_file = Path(__file__).parent / DB_PATH
    conn = sqlite3.connect(db_file, timeout=20.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    check_and_update_schema(conn)
    return conn


def get_stats():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM projects")
    total_projects = cur.fetchone()[0] or 0
    
    cur.execute("SELECT SUM(approved_budget_abc) FROM projects")
    total_budget = cur.fetchone()[0] or 0.0
    
    cur.execute("SELECT SUM(contract_amount) FROM contracts")
    total_contracted = cur.fetchone()[0] or 0.0
    
    cur.execute("SELECT SUM(payment_net_amount) FROM deliveries_and_payments")
    total_paid = cur.fetchone()[0] or 0.0
    
    conn.close()
    return {
        "total_projects": total_projects,
        "total_budget": total_budget,
        "total_contracted": total_contracted,
        "total_paid": total_paid
    }


def get_projects():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.project_id AS id, p.project_id AS proj_id_no, p.project_name, p.bureau_division AS bureau_division_name, 
               p.focal_person, p.approved_budget_abc AS abc_amount, p.status, p.mode_of_procurement,
               p.saro_control_number AS saro_number, p.fund_source_type AS fund_source, p.source_of_funds,
               NULL AS ors_serial_no, NULL AS ors_amount,
               s.supplier_name, c.contract_id AS po_jo_contract_no, c.contract_amount,
               COALESCE(c.ntp_date, p.date_received_bacsec, '2026-01-01') AS project_date,
               p.remarks
        FROM projects p
        LEFT JOIN contracts c ON p.project_id = c.project_id
        LEFT JOIN suppliers s ON c.supplier_id = s.supplier_id
        ORDER BY p.project_id DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_suppliers():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM suppliers ORDER BY supplier_id DESC")
    rows = cur.fetchall()
    conn.close()
    
    # Map back to old supplier names for UI compatibility
    result = []
    for r in rows:
        d = dict(r)
        d["id"] = d["supplier_id"]
        d["supplier_tin_no"] = d["tin"]
        d["supplier_address"] = d["address"]
        d["supplier_contact_details"] = d["contact"] if d.get("contact") else ""
        d["supplier_bank_account"] = d["bank_account"]
        d["supplier_bank_branch"] = d["branch"]
        d["supplier_bank_account_number"] = d["bank_name"]
        result.append(d)
    return result


def get_project_detail(project_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM projects WHERE project_id = ?", (project_id,))
    project_row = cur.fetchone()
    if not project_row:
        conn.close()
        return None
    project = dict(project_row)
    
    # Map back to legacy project details for UI compatibility
    project["id"] = project["project_id"]
    project["proj_id_no"] = project["project_id"]
    project["bureau_division_name"] = project["bureau_division"]
    project["end_user_contact_details"] = project["focal_contact_email"]
    project["abc_amount"] = project["approved_budget_abc"]
    project["fund_source"] = project["fund_source_type"]
    project["saro_number"] = project["saro_control_number"]
    
    # Budgets
    project["budgets"] = [{
        "budget_type": "MOOE",
        "app_amount": project["approved_budget_abc"],
        "ors_amount": 0.0,
        "ors_serial_no": ""
    }]
    
    # Documents
    docs = []
    doc_types = [
        ("SARO", project["saro_pdf"]),
        ("PPMP", project["ppmp_pdf"]),
        ("MS", project["market_scoping_pdf"]),
        ("TS", project["tech_specs_pdf"]),
        ("Abstract", project["abstract_quotations_pdf"])
    ]
    for dtype, ref in doc_types:
        if ref:
            docs.append({
                "document_type": dtype,
                "file_reference": ref,
                "date_prepared": "",
                "prepared_by": "System"
            })
    project["documents"] = docs
    
    # Bids
    bids = []
    if project["bid_reference_no"]:
        bids.append({
            "id": project["project_id"],
            "bid_reference_no": project["bid_reference_no"],
            "purchase_request_no": project["project_id"],
            "post_to_philgeps": "Yes (Posted)" if project["post_to_philgeps"] else "No (Not Posted)",
            "abstract_of_quotations_no": project["abstract_of_quotations_no"],
            "bac_resolution_no": project["bac_resolution_no"],
            "date_received_bacsec": project["date_received_bacsec"],
            "date_received_pcmd_initial": project["date_received_pcmd"],
            "signatory_box_a": project["signatory_box_a"],
            "signatory_box_c": project["signatory_box_c"]
        })
    project["bids"] = bids
    
    # Contracts
    cur.execute("""
        SELECT c.*, s.supplier_name, s.tin AS supplier_tin_no, s.address AS supplier_address, 
               s.tin AS supplier_contact_details, s.bank_account AS supplier_bank_account, 
               s.branch AS supplier_bank_branch, s.bank_name AS supplier_bank_account_number
        FROM contracts c
        LEFT JOIN suppliers s ON c.supplier_id = s.supplier_id
        WHERE c.project_id = ?
    """, (project_id,))
    contracts_rows = cur.fetchall()
    project["contracts"] = []
    for c_row in contracts_rows:
        contract = dict(c_row)
        contract["id"] = contract["contract_id"]
        contract["po_jo_contract_no"] = contract["contract_id"]
        contract["notice_of_award_date"] = contract["noa_date"]
        contract["notice_to_proceed_date"] = contract["ntp_date"]
        contract["expected_end_of_contract"] = contract["expected_end_date"]
        
        # Budget ORS updating
        project["budgets"][0]["ors_amount"] = contract["contract_amount"]
        project["budgets"][0]["ors_serial_no"] = f"ORS-{contract['contract_id']}"
        
        con_doc_types = [
            ("NOA", contract["noa_pdf"]),
            ("Contract", contract["signed_contract_pdf"]),
            ("RQ", contract["request_order_pdf"]),
            ("BAC_Reso", contract["bac_resolution_pdf"])
        ]
        for dtype, ref in con_doc_types:
            if ref:
                project["documents"].append({
                    "document_type": dtype,
                    "file_reference": ref,
                    "date_prepared": "",
                    "prepared_by": "System"
                })
                
        try:
            contract["amendments"] = json.loads(contract["contract_amendments"] or "[]")
        except Exception:
            contract["amendments"] = []
            
        # Deliverables & Payments
        cur.execute("SELECT * FROM deliveries_and_payments WHERE contract_id = ?", (contract["contract_id"],))
        deliv_rows = cur.fetchall()
        contract["deliverables"] = []
        for d_row in deliv_rows:
            d = dict(d_row)
            d["id"] = d["milestone_id"]
            d["milestone_deliverable"] = d["milestone_description"]
            d["status_of_delivery"] = d["delivery_status"]
            d["original_expected_delivery_date"] = d["original_delivery_date"]
            d["rate_liquidated_damages"] = d["liquidated_damages_rate"]
            d["iar_no"] = d["iar_number"]
            
            if d["iar_pdf"]:
                project["documents"].append({
                    "document_type": "IAR",
                    "file_reference": d["iar_pdf"],
                    "date_prepared": "",
                    "prepared_by": "System"
                })
            if d["po_pdf"]:
                project["documents"].append({
                    "document_type": "PO_Phase3",
                    "file_reference": d["po_pdf"],
                    "date_prepared": "",
                    "prepared_by": "System"
                })
                
            d["payments"] = []
            if d["payment_type"]:
                d["payments"].append({
                    "id": d["milestone_id"],
                    "types_of_payment": d["payment_type"],
                    "payment_schedule_terms": d["payment_terms"],
                    "due_for_submission": d["due_date_submission"],
                    "payment_amount_gross": d["payment_gross_amount"],
                    "savings_unperformed_rebates": d["savings_rebates"],
                    "ewt_1_goods": d["ewt_1_percent"],
                    "ewt_2_services": d["ewt_2_percent"],
                    "withholding_vat_5": d["withholding_vat_5_percent"],
                    "retention_rate": 0.1 if d["retention_rate_applied"] else 0.0,
                    "retention_fee": d["retention_fee"],
                    "payment_amount_net": d["payment_net_amount"],
                    "status_of_payment_documents": d["payment_status"],
                    "rci_dv_acic_no": d["dv_rci_serial_no"],
                    "check_lddap_ada_no": d["check_ada_no"],
                    "check_date_lddap_ada": d["check_date"]
                })
            contract["deliverables"].append(d)
            
        # Warranties
        cur.execute("SELECT * FROM warranties WHERE contract_id = ?", (contract["contract_id"],))
        warr_rows = cur.fetchall()
        contract["warranties"] = []
        for w_row in warr_rows:
            w = dict(w_row)
            w["id"] = w["warranty_id"]
            w["start_of_warranty_period"] = w["warranty_start_date"]
            w["warranty_retention_period_months"] = w["retention_period_months"]
            w["end_date_of_warranty_period"] = w["warranty_end_date"]
            w["retention_security"] = w["retention_security_details"]
            w["retention_period_warranty_status"] = w["warranty_status"]
            w["actual_date_release_retention"] = w["actual_release_date"]
            w["with_petition_for_coa_claims"] = w["coa_petition_claims"]
            
            if w["warranty_certificate_pdf"]:
                project["documents"].append({
                    "document_type": "Warranty",
                    "file_reference": w["warranty_certificate_pdf"],
                    "date_prepared": "",
                    "prepared_by": "System"
                })
            contract["warranties"].append(w)
            
        project["contracts"].append(contract)
        
    conn.close()
    return project


def create_project(project_id, project_name, saro_control_number, bureau_division, focal_person, 
                   focal_contact_email, mode_of_procurement, approved_budget_abc, 
                   source_of_funds, fund_source_type, app_cycle, remarks=None):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO projects (
                project_id, project_name, bureau_division, focal_person, focal_contact_email,
                mode_of_procurement, approved_budget_abc, source_of_funds, fund_source_type, 
                app_cycle, status, remarks, saro_control_number
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Planning & Bidding', ?, ?)
        """, (project_id, project_name, bureau_division, focal_person, focal_contact_email,
              mode_of_procurement, approved_budget_abc, source_of_funds, fund_source_type, 
              app_cycle, remarks, saro_control_number))
        conn.commit()
        return True, project_id
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()


def update_project(project_id, new_project_id, project_name, saro_control_number, bureau_division, focal_person, 
                   focal_contact_email, mode_of_procurement, approved_budget_abc, 
                   source_of_funds, fund_source_type, app_cycle, remarks=None):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE projects 
            SET project_id = ?, project_name = ?, saro_control_number = ?, bureau_division = ?, focal_person = ?, 
                focal_contact_email = ?, mode_of_procurement = ?, approved_budget_abc = ?, 
                source_of_funds = ?, fund_source_type = ?, app_cycle = ?, remarks = ?
            WHERE project_id = ?
        """, (new_project_id, project_name, saro_control_number, bureau_division, focal_person, 
              focal_contact_email, mode_of_procurement, approved_budget_abc, 
              source_of_funds, fund_source_type, app_cycle, remarks, project_id))
        conn.commit()
        return True, None
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()


def add_bid(project_id, bid_reference_no, date_received_bacsec, date_received_pcmd, 
            signatory_box_a, signatory_box_c, purchase_request_no=None, post_to_philgeps=None,
            abstract_of_quotations_no=None, bac_resolution_no=None):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        post_val = 0
        if post_to_philgeps == "Yes (Posted)":
            post_val = 1
        elif post_to_philgeps and "Auto-detect" in str(post_to_philgeps):
            cur.execute("SELECT approved_budget_abc FROM projects WHERE project_id = ?", (project_id,))
            proj_row = cur.fetchone()
            abc_val = proj_row[0] if proj_row and proj_row[0] is not None else 0.0
            post_val = 1 if abc_val >= 200000.0 else 0
        cur.execute("""
            UPDATE projects 
            SET bid_reference_no = ?, date_received_bacsec = ?, date_received_pcmd = ?, 
                signatory_box_a = ?, signatory_box_c = ?, post_to_philgeps = ?, 
                abstract_of_quotations_no = ?, bac_resolution_no = ?, status = 'Planning & Bidding'
            WHERE project_id = ?
        """, (bid_reference_no, date_received_bacsec, date_received_pcmd, 
              signatory_box_a, signatory_box_c, post_val, 
              abstract_of_quotations_no, bac_resolution_no, project_id))
        conn.commit()
        return True, project_id
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()


def update_bid(bid_id, bid_reference_no, date_received_bacsec, date_received_pcmd, 
               signatory_box_a, signatory_box_c, purchase_request_no=None, post_to_philgeps=None,
               abstract_of_quotations_no=None, bac_resolution_no=None):
    return add_bid(bid_id, bid_reference_no, date_received_bacsec, date_received_pcmd,
                   signatory_box_a, signatory_box_c, purchase_request_no, post_to_philgeps,
                   abstract_of_quotations_no, bac_resolution_no)


def add_supplier(name, tin, address, contact, branch, account_no):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO suppliers (supplier_name, tin, address, contact, bank_account, branch, bank_name)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, tin, address, contact, name, branch, account_no))
        conn.commit()
        return True, cur.lastrowid
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()


def update_supplier(supplier_id, name, tin, address, contact, branch, account_no):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE suppliers 
            SET supplier_name = ?, tin = ?, address = ?, contact = ?, bank_account = ?, branch = ?, bank_name = ?
            WHERE supplier_id = ?
        """, (name, tin, address, contact, name, branch, account_no, supplier_id))
        conn.commit()
        return True, "Supplier successfully updated."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()


def delete_supplier(supplier_id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM suppliers WHERE supplier_id = ?", (supplier_id,))
        conn.commit()
        return True, "Supplier successfully deleted."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()


def add_contract(project_id, bid_id, supplier_id, financial_capacity_amount, notice_of_award_date, 
                 performance_security_form, performance_security_amount, performance_security_validity, 
                 contract_date, po_jo_contract_no, contract_amount, notice_to_proceed_date, 
                 contract_duration_days, expected_end_of_contract, nature_of_procurement):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO contracts (
                contract_id, project_id, supplier_id, contract_amount, noa_date, ntp_date,
                contract_duration_days, expected_end_date, performance_security_form,
                performance_security_amount, performance_security_validity, contract_amendments
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '[]')
        """, (po_jo_contract_no, project_id, supplier_id, contract_amount, notice_of_award_date,
              notice_to_proceed_date, contract_duration_days, expected_end_of_contract,
              performance_security_form, performance_security_amount, performance_security_validity))
              
        cur.execute("UPDATE projects SET status = 'Contract Awarded', nature_of_procurement = ? WHERE project_id = ?", 
                    (nature_of_procurement, project_id))
        conn.commit()
        return True, po_jo_contract_no
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()


def update_contract(contract_id, supplier_id, financial_capacity_amount, notice_of_award_date, 
                    performance_security_form, performance_security_amount, performance_security_validity, 
                    contract_date, po_jo_contract_no, contract_amount, notice_to_proceed_date, 
                    contract_duration_days, expected_end_of_contract, nature_of_procurement):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE contracts 
            SET contract_id = ?, supplier_id = ?, contract_amount = ?, noa_date = ?, ntp_date = ?, 
                contract_duration_days = ?, expected_end_date = ?, performance_security_form = ?, 
                performance_security_amount = ?, performance_security_validity = ?
            WHERE contract_id = ?
        """, (po_jo_contract_no, supplier_id, contract_amount, notice_of_award_date, notice_to_proceed_date, 
              contract_duration_days, expected_end_of_contract, performance_security_form, 
              performance_security_amount, performance_security_validity, contract_id))
              
        cur.execute("SELECT project_id FROM contracts WHERE contract_id = ?", (po_jo_contract_no,))
        proj_row = cur.fetchone()
        if proj_row:
            cur.execute("UPDATE projects SET nature_of_procurement = ? WHERE project_id = ?", (nature_of_procurement, proj_row["project_id"]))
            
        conn.commit()
        return True, None
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()


def add_deliverable(contract_id, milestone_deliverable, expected_start_date, 
                    original_expected_delivery_date, delivery_period_days, revised_delivery_date, 
                    actual_delivery_date, status_of_delivery, days_delayed, rate_liquidated_damages, 
                    liquidated_damages_amount, iar_no, inspection_date, acceptance_date, facc_date, 
                    issues_and_concerns, remarks_status):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO deliveries_and_payments (
                contract_id, milestone_description, expected_start_date, original_delivery_date, 
                revised_delivery_date, actual_delivery_date, delivery_status, days_delayed, 
                liquidated_damages_rate, liquidated_damages_amount, iar_number, inspection_date, 
                acceptance_date, facc_date, payment_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending')
        """, (contract_id, milestone_deliverable, expected_start_date, original_expected_delivery_date, 
              revised_delivery_date, actual_delivery_date, status_of_delivery, days_delayed, 
              rate_liquidated_damages, liquidated_damages_amount, iar_no, inspection_date, 
              acceptance_date, facc_date))
        milestone_id = cur.lastrowid
        
        cur.execute("""
            UPDATE projects SET status = 'Deliveries & Payments' 
            WHERE project_id = (SELECT project_id FROM contracts WHERE contract_id = ?)
        """, (contract_id,))
        conn.commit()
        return True, milestone_id
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()


def update_deliverable(deliverable_id, milestone_deliverable, expected_start_date, 
                       original_expected_delivery_date, delivery_period_days, revised_delivery_date, 
                       actual_delivery_date, status_of_delivery, days_delayed, rate_liquidated_damages, 
                       liquidated_damages_amount, iar_no, inspection_date, acceptance_date, facc_date, 
                       issues_and_concerns, remarks_status):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE deliveries_and_payments 
            SET milestone_description = ?, expected_start_date = ?, original_delivery_date = ?, 
                revised_delivery_date = ?, actual_delivery_date = ?, delivery_status = ?, 
                days_delayed = ?, liquidated_damages_rate = ?, liquidated_damages_amount = ?, 
                iar_number = ?, inspection_date = ?, acceptance_date = ?, facc_date = ?
            WHERE milestone_id = ?
        """, (milestone_deliverable, expected_start_date, original_expected_delivery_date, 
              revised_delivery_date, actual_delivery_date, status_of_delivery, 
              days_delayed, rate_liquidated_damages, liquidated_damages_amount, 
              iar_no, inspection_date, acceptance_date, facc_date, deliverable_id))
        conn.commit()
        return True, None
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()


def add_payment(contract_id, deliverable_id, types_of_payment, payment_schedule_terms, 
                due_for_submission, payment_amount_gross, savings_unperformed_rebates, 
                ewt_1_goods, ewt_2_services, tax_5_rent_lease_prof, withholding_vat_5, 
                retention_rate, retention_fee, payment_amount_net, status_of_payment_documents, 
                rci_dv_acic_no, check_lddap_ada_no, check_date_lddap_ada, lddap_ada_amount):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        ret_applied = 1 if (retention_rate or 0.0) > 0 else 0
        cur.execute("""
            UPDATE deliveries_and_payments 
            SET payment_type = ?, payment_terms = ?, due_date_submission = ?, 
                payment_gross_amount = ?, savings_rebates = ?, ewt_1_percent = ?, 
                ewt_2_percent = ?, withholding_vat_5_percent = ?, retention_rate_applied = ?, 
                retention_fee = ?, payment_net_amount = ?, payment_status = ?, 
                dv_rci_serial_no = ?, check_ada_no = ?, check_date = ?, delivery_status = 'Delivered'
            WHERE milestone_id = ?
        """, (types_of_payment, payment_schedule_terms, due_for_submission, 
              payment_amount_gross, savings_unperformed_rebates, ewt_1_goods, 
              ewt_2_services, withholding_vat_5, ret_applied, retention_fee, 
              payment_amount_net, status_of_payment_documents, rci_dv_acic_no, 
              check_lddap_ada_no, check_date_lddap_ada, deliverable_id))
        conn.commit()
        return True, deliverable_id
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()


def update_payment(payment_id, types_of_payment, payment_schedule_terms, due_for_submission, 
                   payment_amount_gross, savings_unperformed_rebates, ewt_1_goods, ewt_2_services, 
                   tax_5_rent_lease_prof, withholding_vat_5, retention_rate, retention_fee, 
                   payment_amount_net, status_of_payment_documents, rci_dv_acic_no, 
                   check_lddap_ada_no, check_date_lddap_ada, lddap_ada_amount):
    return add_payment(None, payment_id, types_of_payment, payment_schedule_terms, due_for_submission,
                       payment_amount_gross, savings_unperformed_rebates, ewt_1_goods, ewt_2_services,
                       tax_5_rent_lease_prof, withholding_vat_5, retention_rate, retention_fee,
                       payment_amount_net, status_of_payment_documents, rci_dv_acic_no,
                       check_lddap_ada_no, check_date_lddap_ada, lddap_ada_amount)


def add_warranty(contract_id, start_of_warranty_period, warranty_retention_period_months, 
                 end_date_of_warranty_period, retention_security, actual_date_release_retention, 
                 retention_period_warranty_status, with_petition_for_coa_claims):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO warranties (
                contract_id, warranty_start_date, retention_period_months, warranty_end_date, 
                retention_security_details, warranty_status, actual_release_date, coa_petition_claims
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (contract_id, start_of_warranty_period, warranty_retention_period_months, 
              end_date_of_warranty_period, retention_security, retention_period_warranty_status, 
              actual_date_release_retention, with_petition_for_coa_claims))
        warranty_id = cur.lastrowid
        
        cur.execute("""
            UPDATE projects SET status = 'Under Warranty' 
            WHERE project_id = (SELECT project_id FROM contracts WHERE contract_id = ?)
        """, (contract_id,))
        conn.commit()
        return True, warranty_id
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()


def update_warranty(warranty_id, start_of_warranty_period, warranty_retention_period_months, 
                    end_date_of_warranty_period, retention_security, actual_date_release_retention, 
                    retention_period_warranty_status, with_petition_for_coa_claims):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE warranties 
            SET warranty_start_date = ?, retention_period_months = ?, 
                warranty_end_date = ?, retention_security_details = ?, 
                warranty_status = ?, actual_release_date = ?, 
                coa_petition_claims = ?
            WHERE warranty_id = ?
        """, (start_of_warranty_period, warranty_retention_period_months, 
              end_date_of_warranty_period, retention_security, 
              retention_period_warranty_status, actual_date_release_retention, 
              with_petition_for_coa_claims, warranty_id))
        conn.commit()
        return True, None
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()


def get_dashboard_analytics():
    conn = get_db_connection()
    cur = conn.cursor()
    
    analytics = {
        "alerts": [],
        "total_abc": 0.0,
        "total_contracted": 0.0,
        "total_paid": 0.0,
        "savings_amount": 0.0,
        "savings_percent": 0.0,
        "unpaid_balance": 0.0,
        "suppliers_leaderboard": []
    }
    
    try:
        from datetime import datetime, date
        current_date_str = date.today().strftime("%Y-%m-%d")
        current_date = date.today()
        
        cur.execute("SELECT SUM(approved_budget_abc) FROM projects")
        val = cur.fetchone()[0]
        analytics["total_abc"] = val if val is not None else 0.0
        
        cur.execute("SELECT SUM(contract_amount) FROM contracts")
        val = cur.fetchone()[0]
        analytics["total_contracted"] = val if val is not None else 0.0
        
        cur.execute("""
            SELECT SUM(payment_net_amount) FROM deliveries_and_payments 
            WHERE payment_status = 'Complete' OR dv_rci_serial_no IS NOT NULL
        """)
        val = cur.fetchone()[0]
        analytics["total_paid"] = val if val is not None else 0.0
        
        cur.execute("""
            SELECT SUM(p.approved_budget_abc - c.contract_amount) 
            FROM projects p
            JOIN contracts c ON p.project_id = c.project_id
        """)
        val = cur.fetchone()[0]
        analytics["savings_amount"] = val if val is not None else 0.0
        
        if analytics["total_contracted"] > 0:
            cur.execute("""
                SELECT SUM(p.approved_budget_abc) 
                FROM projects p
                JOIN contracts c ON p.project_id = c.project_id
            """)
            abc_contracted = cur.fetchone()[0] or 0.0
            if abc_contracted > 0:
                analytics["savings_percent"] = (analytics["savings_amount"] / abc_contracted) * 100.0
                
        analytics["unpaid_balance"] = max(0.0, analytics["total_contracted"] - analytics["total_paid"])
        
        # Alerts
        cur.execute("""
            SELECT p.project_id, p.project_name, d.milestone_description, 
                   COALESCE(d.revised_delivery_date, d.original_delivery_date) as expected_date
            FROM deliveries_and_payments d
            JOIN contracts c ON d.contract_id = c.contract_id
            JOIN projects p ON c.project_id = p.project_id
            WHERE d.delivery_status != 'Delivered' 
              AND expected_date IS NOT NULL 
              AND expected_date != ''
        """)
        for row in cur.fetchall():
            proj_id, proj_name, milestone, expected_str = row
            try:
                expected_date = datetime.strptime(expected_str, "%Y-%m-%d").date()
                if expected_date < current_date:
                    days = (current_date - expected_date).days
                    analytics["alerts"].append({
                        "type": "error",
                        "text": f"🔴 {proj_id}: '{milestone}' is delayed by {days} days! (Expected: {expected_str})"
                    })
            except Exception:
                pass
                
        cur.execute("""
            SELECT p.project_id, d.milestone_description, d.payment_type, d.due_date_submission, d.payment_gross_amount
            FROM deliveries_and_payments d
            JOIN contracts c ON d.contract_id = c.contract_id
            JOIN projects p ON c.project_id = p.project_id
            WHERE d.payment_status != 'Complete'
              AND d.dv_rci_serial_no IS NULL
              AND d.payment_type IS NOT NULL
        """)
        for row in cur.fetchall():
            proj_id, milestone, pay_type, due_str, gross = row
            try:
                if due_str:
                    due_date = datetime.strptime(due_str, "%Y-%m-%d").date()
                    days = (due_date - current_date).days
                    if days < 0:
                        analytics["alerts"].append({
                            "type": "warning",
                            "text": f"🟡 {proj_id}: {pay_type} Payment of ₱{gross:,.2f} is OVERDUE by {abs(days)} days!"
                        })
                    elif days <= 7:
                        analytics["alerts"].append({
                            "type": "info",
                            "text": f"ℹ️ {proj_id}: {pay_type} Payment of ₱{gross:,.2f} is due in {days} days."
                        })
            except Exception:
                pass
                
        cur.execute("""
            SELECT p.project_id, w.warranty_end_date
            FROM warranties w
            JOIN contracts c ON w.contract_id = c.contract_id
            JOIN projects p ON c.project_id = p.project_id
            WHERE w.warranty_status = 'Ongoing'
        """)
        for row in cur.fetchall():
            proj_id, end_str = row
            try:
                if end_str:
                    end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
                    days = (end_date - current_date).days
                    if 0 <= days <= 30:
                        analytics["alerts"].append({
                            "type": "info",
                            "text": f"🛡️ {proj_id}: Warranty period ending in {days} days (Exp: {end_str})."
                        })
            except Exception:
                pass
                
        cur.execute("""
            SELECT s.supplier_name, COUNT(c.contract_id) as contract_count, SUM(c.contract_amount) as total_val
            FROM contracts c
            JOIN suppliers s ON c.supplier_id = s.supplier_id
            GROUP BY s.supplier_id
            ORDER BY total_val DESC
            LIMIT 5
        """)
        for row in cur.fetchall():
            s_name, count, total = row
            analytics["suppliers_leaderboard"].append({
                "supplier_name": s_name,
                "contract_count": count,
                "total_value": total
            })
            
    except Exception as e:
        print(f"Error compiling dashboard analytics: {e}")
        
    return analytics


def generate_next_project_id():
    import datetime
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM projects")
        count = cur.fetchone()[0] or 0
        conn.close()
    except Exception:
        count = 0
    year = datetime.datetime.now().year
    return f"PRJ-{year}-{count+1:04d}"


def save_project_document(target_id, document_type, file_path):
    if not file_path:
        return True, None
        
    import os
    import shutil
    from pathlib import Path
    
    try:
        dest_dir = Path(__file__).parent / "uploaded_documents"
        dest_dir.mkdir(exist_ok=True)
        
        src_path = Path(file_path)
        filename = f"doc_{target_id}_{document_type}{src_path.suffix}"
        dest_path = dest_dir / filename
        shutil.copy(file_path, dest_path)
        
        rel_path = f"uploaded_documents/{filename}"
        
        # Synchronous Drive upload removed; offloaded to background worker threads during sheet push
        conn = get_db_connection()
        cur = conn.cursor()
        
        if document_type in ["SARO", "PPMP", "MS", "TS", "Abstract"]:
            col_map = {
                "SARO": "saro_pdf",
                "PPMP": "ppmp_pdf",
                "MS": "market_scoping_pdf",
                "TS": "tech_specs_pdf",
                "Abstract": "abstract_quotations_pdf"
            }
            pdf_col = col_map[document_type]
            cur.execute(f"UPDATE projects SET {pdf_col} = ? WHERE project_id = ?", (rel_path, target_id))
            
        elif document_type in ["NOA", "Contract", "BAC_Reso", "RQ"]:
            col_map = {
                "NOA": "noa_pdf",
                "Contract": "signed_contract_pdf",
                "BAC_Reso": "bac_resolution_pdf",
                "RQ": "request_order_pdf"
            }
            pdf_col = col_map[document_type]
            cur.execute(f"UPDATE contracts SET {pdf_col} = ? WHERE project_id = ?", (rel_path, target_id))
            
        elif document_type in ["IAR", "PO_Phase3"]:
            cur.execute("SELECT contract_id FROM contracts WHERE project_id = ?", (target_id,))
            con_row = cur.fetchone()
            if con_row:
                cid = con_row["contract_id"]
                col_map = {
                    "IAR": "iar_pdf",
                    "PO_Phase3": "po_pdf"
                }
                pdf_col = col_map[document_type]
                cur.execute(f"""
                    UPDATE deliveries_and_payments 
                    SET {pdf_col} = ? 
                    WHERE contract_id = ? 
                      AND milestone_id = (SELECT MAX(milestone_id) FROM deliveries_and_payments WHERE contract_id = ?)
                """, (rel_path, cid, cid))
                
        elif document_type == "Warranty":
            cur.execute("SELECT contract_id FROM contracts WHERE project_id = ?", (target_id,))
            con_row = cur.fetchone()
            if con_row:
                cid = con_row["contract_id"]
                cur.execute("UPDATE warranties SET warranty_certificate_pdf = ? WHERE contract_id = ?", (rel_path, cid))
                
        conn.commit()
        conn.close()
        return True, rel_path
    except Exception as e:
        return False, str(e)


def get_document_data(project_id, doc_type):
    conn = get_db_connection()
    cur = conn.cursor()
    ref_path = None
    
    try:
        if doc_type in ["SARO", "PPMP", "MS", "TS", "Abstract"]:
            col_map = {
                "SARO": "saro_pdf",
                "PPMP": "ppmp_pdf",
                "MS": "market_scoping_pdf",
                "TS": "tech_specs_pdf",
                "Abstract": "abstract_quotations_pdf"
            }
            pdf_col = col_map[doc_type]
            cur.execute(f"SELECT {pdf_col} FROM projects WHERE project_id = ?", (project_id,))
            row = cur.fetchone()
            if row:
                ref_path = row[0]
                
        elif doc_type in ["NOA", "Contract", "BAC_Reso", "RQ"]:
            col_map = {
                "NOA": "noa_pdf",
                "Contract": "signed_contract_pdf",
                "BAC_Reso": "bac_resolution_pdf",
                "RQ": "request_order_pdf"
            }
            pdf_col = col_map[doc_type]
            cur.execute(f"SELECT {pdf_col} FROM contracts WHERE project_id = ?", (project_id,))
            row = cur.fetchone()
            if row:
                ref_path = row[0]
                
        elif doc_type in ["IAR", "PO_Phase3"]:
            cur.execute("SELECT contract_id FROM contracts WHERE project_id = ?", (project_id,))
            con_row = cur.fetchone()
            if con_row:
                cid = con_row[0]
                col_map = {
                    "IAR": "iar_pdf",
                    "PO_Phase3": "po_pdf"
                }
                pdf_col = col_map[doc_type]
                cur.execute(f"""
                    SELECT {pdf_col} FROM deliveries_and_payments 
                    WHERE contract_id = ? 
                      AND {pdf_col} IS NOT NULL 
                    ORDER BY milestone_id DESC LIMIT 1
                """, (cid,))
                row = cur.fetchone()
                if row:
                    ref_path = row[0]
                    
        elif doc_type == "Warranty":
            cur.execute("SELECT contract_id FROM contracts WHERE project_id = ?", (project_id,))
            con_row = cur.fetchone()
            if con_row:
                cid = con_row[0]
                cur.execute("SELECT warranty_certificate_pdf FROM warranties WHERE contract_id = ?", (cid,))
                row = cur.fetchone()
                if row:
                    ref_path = row[0]
    except Exception as e:
        print(f"Error fetching document path: {e}")
    finally:
        conn.close()
        
    return None, ref_path


def delete_project(project_id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM projects WHERE project_id = ?", (project_id,))
        conn.commit()
        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def get_upcoming_timeline_events():
    conn = get_db_connection()
    cur = conn.cursor()
    events = []
    
    # 1. NTP Dates
    cur.execute("""
        SELECT p.project_id, p.project_name, c.ntp_date 
        FROM contracts c
        JOIN projects p ON c.project_id = p.project_id
        WHERE c.ntp_date IS NOT NULL AND c.ntp_date != ''
    """)
    for row in cur.fetchall():
        events.append({
            "proj_id": row[0],
            "project_name": row[1],
            "event_name": "Notice to Proceed (NTP)",
            "date": row[2],
            "type": "ntp"
        })
        
    # 2. Deliverables Expected Delivery
    cur.execute("""
        SELECT p.project_id, p.project_name, d.milestone_description, 
               COALESCE(d.revised_delivery_date, d.original_delivery_date) as deliv_date
        FROM deliveries_and_payments d
        JOIN contracts c ON d.contract_id = c.contract_id
        JOIN projects p ON c.project_id = p.project_id
        WHERE deliv_date IS NOT NULL AND deliv_date != '' AND d.actual_delivery_date IS NULL
    """)
    for row in cur.fetchall():
        events.append({
            "proj_id": row[0],
            "project_name": row[1],
            "event_name": f"Delivery: {row[2][:30]}...",
            "date": row[3],
            "type": "delivery"
        })
        
    # 3. Payments Due Dates
    cur.execute("""
        SELECT p.project_id, p.project_name, d.payment_type, d.due_date_submission
        FROM deliveries_and_payments d
        JOIN contracts c ON d.contract_id = c.contract_id
        JOIN projects p ON c.project_id = p.project_id
        WHERE d.due_date_submission IS NOT NULL AND d.due_date_submission != '' AND d.payment_status != 'Complete'
    """)
    for row in cur.fetchall():
        events.append({
            "proj_id": row[0],
            "project_name": row[1],
            "event_name": f"Payment: {row[2]}",
            "date": row[3],
            "type": "payment"
        })
        
    # 4. Warranty Expiry Dates
    cur.execute("""
        SELECT p.project_id, p.project_name, w.warranty_end_date
        FROM warranties w
        JOIN contracts c ON w.contract_id = c.contract_id
        JOIN projects p ON c.project_id = p.project_id
        WHERE w.warranty_end_date IS NOT NULL AND w.warranty_end_date != '' AND w.warranty_status = 'Ongoing'
    """)
    for row in cur.fetchall():
        events.append({
            "proj_id": row[0],
            "project_name": row[1],
            "event_name": "Warranty Expiration",
            "date": row[2],
            "type": "warranty"
        })
        
    conn.close()
    events.sort(key=lambda x: x["date"])
    return events


def get_system_setting(key, default_value=""):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT setting_value FROM system_settings WHERE setting_key = ?", (key,))
        row = cur.fetchone()
        return row[0] if (row and row[0] is not None) else default_value
    except Exception:
        return default_value
    finally:
        conn.close()


def set_system_setting(key, value):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT OR REPLACE INTO system_settings (setting_key, setting_value) VALUES (?, ?)", (key, value))
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        conn.close()


def get_theme_setting():
    return get_system_setting("theme", "dark")


def update_theme_setting(theme_name):
    return set_system_setting("theme", theme_name)


if __name__ == "__main__":
    seed()
