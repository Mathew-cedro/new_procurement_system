import sys
import sqlite3
import json
from pathlib import Path

# Resolve directories dynamically for both standard python launch and PyInstaller frozen bundle
if getattr(sys, 'frozen', False):
    SCHEMA_DIR = Path(sys._MEIPASS)
    ROOT_DIR = Path(sys.executable).parent
else:
    SCHEMA_DIR = Path(__file__).parent.parent
    ROOT_DIR = Path(__file__).parent.parent

DB_PATH = "procurement.db"

def seed():
    # 1. Back up system_settings if they exist
    settings_backup = {}
    db_file = ROOT_DIR / DB_PATH
    if db_file.exists():
        try:
            conn = sqlite3.connect(db_file)
            cur = conn.cursor()
            cur.execute("SELECT setting_key, setting_value FROM system_settings")
            for row in cur.fetchall():
                settings_backup[row[0]] = row[1]
            conn.close()
        except Exception:
            pass # Table or DB might not exist yet
            
    db_file.unlink(missing_ok=True)
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(Path(SCHEMA_DIR / "schema_sqlite.sql").read_text())

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
    db_file = ROOT_DIR / DB_PATH
    conn = sqlite3.connect(db_file, timeout=20.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    check_and_update_schema(conn)
    return conn




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


