import sqlite3
from pathlib import Path

DB_PATH = "procurement.db"


def seed():
    Path(DB_PATH).unlink(missing_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(Path("schema_sqlite.sql").read_text())

    cur = conn.cursor()

    # ------------------------------------------------------------
    # Project 1: PRJ-2026-0001 — fully progressed through Phase 6
    # ------------------------------------------------------------
    cur.execute("""
        INSERT INTO projects (proj_id_no, project_name, saro_number, bureau_division_name,
            focal_person, end_user_contact_details, mode_of_procurement, abc_amount,
            source_of_funds, fund_source, app_cycle, status)
        VALUES ('PRJ-2026-0001', 'Supply of Office Equipment', 'SARO-2026-00123',
            'Procurement Division', 'Juan Dela Cruz', 'juan.delacruz@agency.gov.ph',
            'Shopping', 450000, 'General Fund', 'GAA', 2, 'Under Warranty')
    """)
    p1 = cur.lastrowid

    cur.execute("""INSERT INTO project_budgets (project_id, budget_type, app_amount, ors_amount, ors_serial_no)
                   VALUES (?, 'MOOE', 450000, 448000, 'ORS-2026-0088')""", (p1,))
    cur.execute("""INSERT INTO project_documents (project_id, document_type, file_reference, date_prepared, prepared_by)
                   VALUES (?, 'RFQ', 'RFQ-2026-0001.pdf', '2026-01-20', 'Juan Dela Cruz')""", (p1,))
    cur.execute("""INSERT INTO bids (project_id, bid_reference_no, date_received_bacsec,
            date_received_pcmd_initial, signatory_box_a, signatory_box_c)
        VALUES (?, 'BID-2026-0001', '2026-02-01', '2026-02-03', 'Maria Santos', 'Pedro Reyes')""", (p1,))
    b1 = cur.lastrowid

    cur.execute("""INSERT INTO suppliers (supplier_name, supplier_tin_no, supplier_address,
            supplier_contact_details, supplier_bank_account, supplier_bank_branch, supplier_bank_account_number)
        VALUES ('ABC Trading Corp.', '123-456-789-000', '123 Rizal St., Manila',
            'abc@trading.com / 0917-123-4567', 'ABC Trading Corp.', 'BDO Ayala Branch', '001234567890')""")
    s1 = cur.lastrowid

    cur.execute("""INSERT INTO contracts (project_id, bid_id, supplier_id, financial_capacity_amount,
            notice_of_award_date, performance_security_form, performance_security_amount,
            performance_security_validity, contract_date, po_jo_contract_no, contract_amount,
            notice_to_proceed_date, contract_duration_days, expected_end_of_contract, nature_of_procurement)
        VALUES (?, ?, ?, 460000, '2026-02-10', 'Surety Bond', 46000, '2026-05-10', '2026-02-15',
            'CTR-2026-0001', 445000, '2026-02-20', 30, '2026-03-22', 'Goods')""", (p1, b1, s1))
    c1 = cur.lastrowid

    cur.execute("""INSERT INTO contract_amendments (contract_id, amendment_type, variation_order_amount,
            suspension_days, extension_days, amendment_date, remarks)
        VALUES (?, 'Extension', 0, 0, 10, '2026-03-15', 'Extended due to supplier logistics delay')""", (c1,))

    cur.execute("""INSERT INTO deliverables (contract_id, milestone_deliverable, expected_start_date,
            original_expected_delivery_date, delivery_period_days, revised_delivery_date,
            actual_delivery_date, status_of_delivery, days_delayed, rate_liquidated_damages,
            liquidated_damages_amount, iar_no, inspection_date, acceptance_date, facc_date,
            issues_and_concerns, remarks_status)
        VALUES (?, 'Delivery of office chairs and desks', '2026-02-20', '2026-03-22', 30,
            '2026-04-01', '2026-03-30', 'Delivered', 0, 0.1, 0, 'IAR-2026-0001', '2026-03-31',
            '2026-04-01', '2026-04-02', 'None', 'Accepted, no defects noted')""", (c1,))
    d1 = cur.lastrowid

    cur.execute("""INSERT INTO payments (contract_id, deliverable_id, types_of_payment,
            payment_schedule_terms, due_for_submission, payment_amount_gross,
            savings_unperformed_rebates, ewt_1_goods, ewt_2_services, tax_5_rent_lease_prof,
            withholding_vat_5, retention_rate, retention_fee, payment_amount_net,
            status_of_payment_documents, rci_dv_acic_no, check_lddap_ada_no,
            check_date_lddap_ada, lddap_ada_amount)
        VALUES (?, ?, 'Final', '100% upon acceptance', '2026-04-05', 445000, 0, 4450, 0, 0, 0,
            0.1, 44500, 396050, 'Complete', 'DV-2026-0456', 'ADA-2026-0789', '2026-04-10', 396050)""",
        (c1, d1))

    cur.execute("""INSERT INTO warranties (contract_id, start_of_warranty_period,
            warranty_retention_period_months, end_date_of_warranty_period, retention_security,
            actual_date_release_retention, retention_period_warranty_status, with_petition_for_coa_claims)
        VALUES (?, '2026-04-02', 12, '2027-04-02', 'Retention Money (10%25, Cash)', NULL, 'Ongoing', 0)""",
        (c1,))

    # ------------------------------------------------------------
    # Project 2: PRJ-2026-0002 — only reached Phase 2 (Bidding)
    # No documents, no contract, no downstream data yet.
    # ------------------------------------------------------------
    cur.execute("""
        INSERT INTO projects (proj_id_no, project_name, saro_number, bureau_division_name,
            focal_person, end_user_contact_details, mode_of_procurement, abc_amount,
            source_of_funds, fund_source, app_cycle, status)
        VALUES ('PRJ-2026-0002', 'Repair of Office Aircon Units', 'SARO-2026-00187',
            'General Services Division', 'Ana Reyes', 'ana.reyes@agency.gov.ph',
            'Shopping', 85000, 'General Fund', 'GAA', 3, 'Bidding')
    """)
    p2 = cur.lastrowid

    cur.execute("""INSERT INTO project_budgets (project_id, budget_type, app_amount, ors_amount, ors_serial_no)
                   VALUES (?, 'MOOE', 85000, 85000, 'ORS-2026-0104')""", (p2,))
    cur.execute("""INSERT INTO bids (project_id, bid_reference_no, date_received_bacsec,
            date_received_pcmd_initial, signatory_box_a, signatory_box_c)
        VALUES (?, 'BID-2026-0007', '2026-03-05', NULL, 'Maria Santos', NULL)""", (p2,))

    conn.commit()
    conn.close()
    print(f"Seeded {DB_PATH} with 2 projects.")



def check_and_update_schema(conn):
    cur = conn.cursor()
    columns_to_add = [
        ("purchase_request_no", "TEXT"),
        ("post_to_philgeps", "TEXT"),
        ("abstract_of_quotations_no", "TEXT"),
        ("bac_resolution_no", "TEXT")
    ]
    for col, col_type in columns_to_add:
        try:
            cur.execute(f"ALTER TABLE bids ADD COLUMN {col} {col_type}")
        except sqlite3.OperationalError:
            pass
            
    # Add BLOB column to project_documents table
    try:
        cur.execute("ALTER TABLE project_documents ADD COLUMN file_content BLOB")
    except sqlite3.OperationalError:
        pass
        
    # Perform Migration of physical PDF documents to BLOBs
    try:
        cur.execute("SELECT id, file_reference, file_content FROM project_documents WHERE file_reference IS NOT NULL")
        rows = cur.fetchall()
        
        base_dir = Path(__file__).parent
        for doc_id, ref, blob in rows:
            if not blob and ref:
                file_path = base_dir / ref
                if file_path.exists():
                    try:
                        with open(file_path, "rb") as f:
                            data = f.read()
                        cur.execute("UPDATE project_documents SET file_content = ? WHERE id = ?", (data, doc_id))
                        print(f"Migrated physical file {ref} to SQLite BLOB!")
                    except Exception as e:
                        print(f"Error migrating file {ref}: {e}")
        conn.commit()
    except Exception as e:
        print(f"Migration error: {e}")

def get_db_connection():
    db_file = Path(__file__).parent / DB_PATH
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    check_and_update_schema(conn)
    return conn

def get_stats():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM projects")
    total_projects = cur.fetchone()[0] or 0
    
    cur.execute("SELECT SUM(abc_amount) FROM projects")
    total_budget = cur.fetchone()[0] or 0.0
    
    cur.execute("SELECT SUM(contract_amount) FROM contracts")
    total_contracted = cur.fetchone()[0] or 0.0
    
    cur.execute("SELECT SUM(payment_amount_net) FROM payments")
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
        SELECT p.id, p.proj_id_no, p.project_name, p.bureau_division_name, 
               p.focal_person, p.abc_amount, p.status, p.mode_of_procurement,
               p.saro_number, p.fund_source, p.source_of_funds,
               pb.ors_serial_no, pb.ors_amount,
               s.supplier_name, c.po_jo_contract_no, c.contract_amount,
               COALESCE(c.contract_date, 
                        (SELECT MIN(d.date_prepared) FROM project_documents d WHERE d.project_id = p.id),
                        (SELECT MIN(b.date_received_bacsec) FROM bids b WHERE b.project_id = p.id),
                        '2026-01-01') AS project_date
        FROM projects p
        LEFT JOIN project_budgets pb ON p.id = pb.project_id
        LEFT JOIN contracts c ON p.id = c.project_id
        LEFT JOIN suppliers s ON c.supplier_id = s.id
        ORDER BY p.id DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_suppliers():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM suppliers ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_project_detail(project_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    project_row = cur.fetchone()
    if not project_row:
        conn.close()
        return None
    project = dict(project_row)
    
    cur.execute("SELECT * FROM project_budgets WHERE project_id = ?", (project_id,))
    project["budgets"] = [dict(r) for r in cur.fetchall()]
    
    cur.execute("SELECT * FROM project_documents WHERE project_id = ?", (project_id,))
    project["documents"] = [dict(r) for r in cur.fetchall()]
    
    cur.execute("SELECT * FROM bids WHERE project_id = ?", (project_id,))
    project["bids"] = [dict(r) for r in cur.fetchall()]
    
    cur.execute("""
        SELECT c.*, s.supplier_name, s.supplier_tin_no, s.supplier_address, 
               s.supplier_contact_details, s.supplier_bank_account, 
               s.supplier_bank_branch, s.supplier_bank_account_number
        FROM contracts c
        LEFT JOIN suppliers s ON c.supplier_id = s.id
        WHERE c.project_id = ?
    """, (project_id,))
    contracts_rows = cur.fetchall()
    project["contracts"] = []
    for c_row in contracts_rows:
        contract = dict(c_row)
        contract_id = contract["id"]
        
        cur.execute("SELECT * FROM contract_amendments WHERE contract_id = ?", (contract_id,))
        contract["amendments"] = [dict(r) for r in cur.fetchall()]
        
        cur.execute("SELECT * FROM deliverables WHERE contract_id = ?", (contract_id,))
        deliverables_rows = cur.fetchall()
        contract["deliverables"] = []
        for d_row in deliverables_rows:
            deliverable = dict(d_row)
            deliverable_id = deliverable["id"]
            
            cur.execute("SELECT * FROM payments WHERE deliverable_id = ?", (deliverable_id,))
            deliverable["payments"] = [dict(r) for r in cur.fetchall()]
            
            contract["deliverables"].append(deliverable)
            
        cur.execute("SELECT * FROM warranties WHERE contract_id = ?", (contract_id,))
        contract["warranties"] = [dict(r) for r in cur.fetchall()]
        
        project["contracts"].append(contract)
        
    conn.close()
    return project

def create_project(proj_id_no, project_name, saro_number, bureau_division_name, focal_person, 
                   end_user_contact_details, mode_of_procurement, abc_amount, 
                   source_of_funds, fund_source, app_cycle):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO projects (proj_id_no, project_name, saro_number, bureau_division_name, focal_person, 
                                  end_user_contact_details, mode_of_procurement, abc_amount, 
                                  source_of_funds, fund_source, app_cycle, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Initiated')
        """, (proj_id_no, project_name, saro_number, bureau_division_name, focal_person, 
              end_user_contact_details, mode_of_procurement, abc_amount, 
              source_of_funds, fund_source, app_cycle))
        project_id = cur.lastrowid
        
        cur.execute("""
            INSERT INTO project_budgets (project_id, budget_type, app_amount, ors_amount, ors_serial_no)
            VALUES (?, 'MOOE', ?, 0, '')
        """, (project_id, abc_amount))
        
        cur.execute("""
            INSERT INTO project_documents (project_id, document_type, file_reference, date_prepared, prepared_by)
            VALUES (?, 'PR/RFQ', 'RFQ-' || ?, date('now'), ?)
        """, (project_id, proj_id_no, focal_person))
        
        conn.commit()
        return True, project_id
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def add_bid(project_id, bid_reference_no, date_received_bacsec, date_received_pcmd_initial, 
            signatory_box_a, signatory_box_c, purchase_request_no=None, post_to_philgeps=None,
            abstract_of_quotations_no=None, bac_resolution_no=None):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO bids (project_id, bid_reference_no, date_received_bacsec, 
                              date_received_pcmd_initial, signatory_box_a, signatory_box_c,
                              purchase_request_no, post_to_philgeps, abstract_of_quotations_no, bac_resolution_no)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (project_id, bid_reference_no, date_received_bacsec, 
              date_received_pcmd_initial, signatory_box_a, signatory_box_c,
              purchase_request_no, post_to_philgeps, abstract_of_quotations_no, bac_resolution_no))
        bid_id = cur.lastrowid
        
        cur.execute("UPDATE projects SET status = 'Bidding' WHERE id = ?", (project_id,))
        conn.commit()
        return True, bid_id
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def add_supplier(supplier_name, supplier_tin_no, supplier_address, supplier_contact_details, 
                 supplier_bank_account, supplier_bank_branch, supplier_bank_account_number):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO suppliers (supplier_name, supplier_tin_no, supplier_address, 
                                   supplier_contact_details, supplier_bank_account, 
                                   supplier_bank_branch, supplier_bank_account_number)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (supplier_name, supplier_tin_no, supplier_address, 
              supplier_contact_details, supplier_bank_account, 
              supplier_bank_branch, supplier_bank_account_number))
        supplier_id = cur.lastrowid
        conn.commit()
        return True, supplier_id
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
            INSERT INTO contracts (project_id, bid_id, supplier_id, financial_capacity_amount, 
                                   notice_of_award_date, performance_security_form, performance_security_amount, 
                                   performance_security_validity, contract_date, po_jo_contract_no, contract_amount, 
                                   notice_to_proceed_date, contract_duration_days, expected_end_of_contract, nature_of_procurement)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (project_id, bid_id, supplier_id, financial_capacity_amount, notice_of_award_date, 
              performance_security_form, performance_security_amount, performance_security_validity, 
              contract_date, po_jo_contract_no, contract_amount, notice_to_proceed_date, 
              contract_duration_days, expected_end_of_contract, nature_of_procurement))
        contract_id = cur.lastrowid
        
        cur.execute("UPDATE project_budgets SET ors_amount = ?, ors_serial_no = 'ORS-' || ? WHERE project_id = ?", 
                    (contract_amount, po_jo_contract_no, project_id))
        
        cur.execute("UPDATE projects SET status = 'Contract Awarded' WHERE id = ?", (project_id,))
        conn.commit()
        return True, contract_id
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
            INSERT INTO deliverables (contract_id, milestone_deliverable, expected_start_date, 
                                      original_expected_delivery_date, delivery_period_days, 
                                      revised_delivery_date, actual_delivery_date, status_of_delivery, 
                                      days_delayed, rate_liquidated_damages, liquidated_damages_amount, 
                                      iar_no, inspection_date, acceptance_date, facc_date, 
                                      issues_and_concerns, remarks_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (contract_id, milestone_deliverable, expected_start_date, original_expected_delivery_date, 
              delivery_period_days, revised_delivery_date, actual_delivery_date, status_of_delivery, 
              days_delayed, rate_liquidated_damages, liquidated_damages_amount, iar_no, inspection_date, 
              acceptance_date, facc_date, issues_and_concerns, remarks_status))
        deliverable_id = cur.lastrowid
        
        cur.execute("""
            UPDATE projects SET status = 'Delivering' 
            WHERE id = (SELECT project_id FROM contracts WHERE id = ?)
        """, (contract_id,))
        conn.commit()
        return True, deliverable_id
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
        cur.execute("""
            INSERT INTO payments (contract_id, deliverable_id, types_of_payment, 
                                  payment_schedule_terms, due_for_submission, payment_amount_gross, 
                                  savings_unperformed_rebates, ewt_1_goods, ewt_2_services, 
                                  tax_5_rent_lease_prof, withholding_vat_5, retention_rate, 
                                  retention_fee, payment_amount_net, status_of_payment_documents, 
                                  rci_dv_acic_no, check_lddap_ada_no, check_date_lddap_ada, 
                                  lddap_ada_amount)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (contract_id, deliverable_id, types_of_payment, payment_schedule_terms, due_for_submission, 
              payment_amount_gross, savings_unperformed_rebates, ewt_1_goods, ewt_2_services, 
              tax_5_rent_lease_prof, withholding_vat_5, retention_rate, retention_fee, 
              payment_amount_net, status_of_payment_documents, rci_dv_acic_no, check_lddap_ada_no, 
              check_date_lddap_ada, lddap_ada_amount))
        payment_id = cur.lastrowid
        
        cur.execute("UPDATE deliverables SET status_of_delivery = 'Delivered' WHERE id = ?", (deliverable_id,))
        conn.commit()
        return True, payment_id
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def add_warranty(contract_id, start_of_warranty_period, warranty_retention_period_months, 
                 end_date_of_warranty_period, retention_security, actual_date_release_retention, 
                 retention_period_warranty_status, with_petition_for_coa_claims):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO warranties (contract_id, start_of_warranty_period, 
                                    warranty_retention_period_months, end_date_of_warranty_period, 
                                    retention_security, actual_date_release_retention, 
                                    retention_period_warranty_status, with_petition_for_coa_claims)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (contract_id, start_of_warranty_period, warranty_retention_period_months, 
              end_date_of_warranty_period, retention_security, actual_date_release_retention, 
              retention_period_warranty_status, with_petition_for_coa_claims))
        warranty_id = cur.lastrowid
        
        cur.execute("""
            UPDATE projects SET status = 'Under Warranty' 
            WHERE id = (SELECT project_id FROM contracts WHERE id = ?)
        """, (contract_id,))
        conn.commit()
        return True, warranty_id
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()


def update_project(project_id, proj_id_no, project_name, saro_number, bureau_division_name, focal_person, 
                   end_user_contact_details, mode_of_procurement, abc_amount, 
                   source_of_funds, fund_source, app_cycle):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE projects 
            SET proj_id_no = ?, project_name = ?, saro_number = ?, bureau_division_name = ?, focal_person = ?, 
                end_user_contact_details = ?, mode_of_procurement = ?, abc_amount = ?, 
                source_of_funds = ?, fund_source = ?, app_cycle = ?
            WHERE id = ?
        """, (proj_id_no, project_name, saro_number, bureau_division_name, focal_person, 
              end_user_contact_details, mode_of_procurement, abc_amount, 
              source_of_funds, fund_source, app_cycle, project_id))
        
        cur.execute("""
            UPDATE project_budgets 
            SET app_amount = ? 
            WHERE project_id = ? AND budget_type = 'MOOE'
        """, (abc_amount, project_id))
        
        conn.commit()
        return True, None
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def update_bid(bid_id, bid_reference_no, date_received_bacsec, date_received_pcmd_initial, 
               signatory_box_a, signatory_box_c, purchase_request_no=None, post_to_philgeps=None,
               abstract_of_quotations_no=None, bac_resolution_no=None):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE bids 
            SET bid_reference_no = ?, date_received_bacsec = ?, 
                date_received_pcmd_initial = ?, signatory_box_a = ?, signatory_box_c = ?,
                purchase_request_no = ?, post_to_philgeps = ?, 
                abstract_of_quotations_no = ?, bac_resolution_no = ?
            WHERE id = ?
        """, (bid_reference_no, date_received_bacsec, date_received_pcmd_initial, 
              signatory_box_a, signatory_box_c, purchase_request_no, post_to_philgeps,
              abstract_of_quotations_no, bac_resolution_no, bid_id))
        conn.commit()
        return True, None
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
            SET supplier_id = ?, financial_capacity_amount = ?, notice_of_award_date = ?, 
                performance_security_form = ?, performance_security_amount = ?, 
                performance_security_validity = ?, contract_date = ?, po_jo_contract_no = ?, 
                contract_amount = ?, notice_to_proceed_date = ?, contract_duration_days = ?, 
                expected_end_of_contract = ?, nature_of_procurement = ?
            WHERE id = ?
        """, (supplier_id, financial_capacity_amount, notice_of_award_date, 
              performance_security_form, performance_security_amount, performance_security_validity, 
              contract_date, po_jo_contract_no, contract_amount, notice_to_proceed_date, 
              contract_duration_days, expected_end_of_contract, nature_of_procurement, contract_id))
        
        cur.execute("SELECT project_id FROM contracts WHERE id = ?", (contract_id,))
        project_id = cur.fetchone()[0]
        
        cur.execute("""
            UPDATE project_budgets 
            SET ors_amount = ?, ors_serial_no = 'ORS-' || ? 
            WHERE project_id = ?
        """, (contract_amount, po_jo_contract_no, project_id))
        
        conn.commit()
        return True, None
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
            UPDATE deliverables 
            SET milestone_deliverable = ?, expected_start_date = ?, original_expected_delivery_date = ?, 
                delivery_period_days = ?, revised_delivery_date = ?, actual_delivery_date = ?, 
                status_of_delivery = ?, days_delayed = ?, rate_liquidated_damages = ?, 
                liquidated_damages_amount = ?, iar_no = ?, inspection_date = ?, 
                acceptance_date = ?, facc_date = ?, issues_and_concerns = ?, remarks_status = ?
            WHERE id = ?
        """, (milestone_deliverable, expected_start_date, original_expected_delivery_date, 
              delivery_period_days, revised_delivery_date, actual_delivery_date, 
              status_of_delivery, days_delayed, rate_liquidated_damages, 
              liquidated_damages_amount, iar_no, inspection_date, 
              acceptance_date, facc_date, issues_and_concerns, remarks_status, deliverable_id))
        conn.commit()
        return True, None
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
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE payments 
            SET types_of_payment = ?, payment_schedule_terms = ?, due_for_submission = ?, 
                payment_amount_gross = ?, savings_unperformed_rebates = ?, ewt_1_goods = ?, 
                ewt_2_services = ?, tax_5_rent_lease_prof = ?, withholding_vat_5 = ?, 
                retention_rate = ?, retention_fee = ?, payment_amount_net = ?, 
                status_of_payment_documents = ?, rci_dv_acic_no = ?, check_lddap_ada_no = ?, 
                check_date_lddap_ada = ?, lddap_ada_amount = ?
            WHERE id = ?
        """, (types_of_payment, payment_schedule_terms, due_for_submission, 
              payment_amount_gross, savings_unperformed_rebates, ewt_1_goods, 
              ewt_2_services, tax_5_rent_lease_prof, withholding_vat_5, 
              retention_rate, retention_fee, payment_amount_net, 
              status_of_payment_documents, rci_dv_acic_no, check_lddap_ada_no, 
              check_date_lddap_ada, lddap_ada_amount, payment_id))
        conn.commit()
        return True, None
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
            SET start_of_warranty_period = ?, warranty_retention_period_months = ?, 
                end_date_of_warranty_period = ?, retention_security = ?, 
                actual_date_release_retention = ?, retention_period_warranty_status = ?, 
                with_petition_for_coa_claims = ?
            WHERE id = ?
        """, (start_of_warranty_period, warranty_retention_period_months, 
              end_date_of_warranty_period, retention_security, 
              actual_date_release_retention, retention_period_warranty_status, 
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
        
        # 1. Fetch Projects financial baseline
        cur.execute("SELECT SUM(abc_amount) FROM projects")
        val = cur.fetchone()[0]
        analytics["total_abc"] = val if val is not None else 0.0
        
        # 2. Fetch total contract values
        cur.execute("SELECT SUM(contract_amount) FROM contracts")
        val = cur.fetchone()[0]
        analytics["total_contracted"] = val if val is not None else 0.0
        
        # 3. Fetch total payments paid (net)
        cur.execute("SELECT SUM(payment_amount_net) FROM payments WHERE status_of_payment_documents = 'Complete' OR rci_dv_acic_no IS NOT NULL")
        val = cur.fetchone()[0]
        analytics["total_paid"] = val if val is not None else 0.0
        
        # Calculate savings
        cur.execute("""
            SELECT SUM(p.abc_amount - c.contract_amount) 
            FROM projects p
            JOIN contracts c ON p.id = c.project_id
        """)
        val = cur.fetchone()[0]
        analytics["savings_amount"] = val if val is not None else 0.0
        
        if analytics["total_contracted"] > 0:
            cur.execute("""
                SELECT SUM(p.abc_amount) 
                FROM projects p
                JOIN contracts c ON p.id = c.project_id
            """)
            abc_contracted = cur.fetchone()[0] or 0.0
            if abc_contracted > 0:
                analytics["savings_percent"] = (analytics["savings_amount"] / abc_contracted) * 100.0
                
        analytics["unpaid_balance"] = max(0.0, analytics["total_contracted"] - analytics["total_paid"])
        
        # 4. Critical Alerts
        # A) Delayed Deliverables
        cur.execute("""
            SELECT p.proj_id_no, p.project_name, d.milestone_deliverable, 
                   COALESCE(d.revised_delivery_date, d.original_expected_delivery_date) as expected_date
            FROM deliverables d
            JOIN contracts c ON d.contract_id = c.id
            JOIN projects p ON c.project_id = p.id
            WHERE d.status_of_delivery != 'Delivered' 
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
                
        # B) Pending Payments
        cur.execute("""
            SELECT p.proj_id_no, d.milestone_deliverable, pm.types_of_payment, pm.due_for_submission, pm.payment_amount_gross
            FROM payments pm
            JOIN deliverables d ON pm.deliverable_id = d.id
            JOIN contracts c ON d.contract_id = c.id
            JOIN projects p ON c.project_id = p.id
            WHERE pm.status_of_payment_documents != 'Complete'
              AND pm.rci_dv_acic_no IS NULL
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
                
        # C) Warranty Expirations
        cur.execute("""
            SELECT p.proj_id_no, w.end_date_of_warranty_period
            FROM warranties w
            JOIN contracts c ON w.contract_id = c.id
            JOIN projects p ON c.project_id = p.id
            WHERE w.retention_period_warranty_status = 'Ongoing'
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
                
        # 5. Top Suppliers
        cur.execute("""
            SELECT s.supplier_name, COUNT(c.id) as contract_count, SUM(c.contract_amount) as total_val
            FROM contracts c
            JOIN suppliers s ON c.supplier_id = s.id
            GROUP BY s.id
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

def add_supplier(name, tin, address, contact, branch, account_no):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO suppliers (supplier_name, supplier_tin_no, supplier_address,
                                   supplier_contact_details, supplier_bank_account, 
                                   supplier_bank_branch, supplier_bank_account_number)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, tin, address, contact, name, branch, account_no))
        conn.commit()
        return True, cur.lastrowid
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

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

def save_project_document(project_id, document_type, file_path):
    if not file_path:
        return True, None
    
    import shutil
    from pathlib import Path
    
    try:
        # Read the file content as binary BLOB
        with open(file_path, "rb") as f:
            file_data = f.read()
            
        dest_dir = Path(__file__).parent / "uploaded_documents"
        dest_dir.mkdir(exist_ok=True)
        
        src_path = Path(file_path)
        filename = f"proj_{project_id}_{document_type}{src_path.suffix}"
        dest_path = dest_dir / filename
        shutil.copy(file_path, dest_path)
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id FROM project_documents 
            WHERE project_id = ? AND document_type = ?
        """, (project_id, document_type))
        row = cur.fetchone()
        
        rel_path = f"uploaded_documents/{filename}"
        
        if row:
            cur.execute("""
                UPDATE project_documents 
                SET file_reference = ?, file_content = ?, date_prepared = date('now')
                WHERE id = ?
            """, (rel_path, file_data, row[0]))
        else:
            cur.execute("""
                INSERT INTO project_documents (project_id, document_type, file_reference, file_content, date_prepared, prepared_by)
                VALUES (?, ?, ?, ?, date('now'), 'System')
            """, (project_id, document_type, rel_path, file_data))
            
        conn.commit()
        conn.close()
        return True, rel_path
    except Exception as e:
        return False, str(e)

def delete_project(project_id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM projects WHERE id = ?", (project_id,))
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
        SELECT p.proj_id_no, p.project_name, c.notice_to_proceed_date 
        FROM contracts c
        JOIN projects p ON c.project_id = p.id
        WHERE c.notice_to_proceed_date IS NOT NULL AND c.notice_to_proceed_date != ''
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
        SELECT p.proj_id_no, p.project_name, d.milestone_deliverable, 
               COALESCE(d.revised_delivery_date, d.original_expected_delivery_date) as deliv_date
        FROM deliverables d
        JOIN contracts c ON d.contract_id = c.id
        JOIN projects p ON c.project_id = p.id
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
        SELECT p.proj_id_no, p.project_name, pm.types_of_payment, pm.due_for_submission
        FROM payments pm
        JOIN contracts c ON pm.contract_id = c.id
        JOIN projects p ON c.project_id = p.id
        WHERE pm.due_for_submission IS NOT NULL AND pm.due_for_submission != '' AND pm.status_of_payment_documents != 'Complete'
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
        SELECT p.proj_id_no, p.project_name, w.end_date_of_warranty_period
        FROM warranties w
        JOIN contracts c ON w.contract_id = c.id
        JOIN projects p ON c.project_id = p.id
        WHERE w.end_date_of_warranty_period IS NOT NULL AND w.end_date_of_warranty_period != '' AND w.retention_period_warranty_status = 'Ongoing'
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
    
    # Sort events by date ascending (chronological order)
    events.sort(key=lambda x: x["date"])
    return events

if __name__ == "__main__":
    seed()


