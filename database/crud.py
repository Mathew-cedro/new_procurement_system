import sqlite3
from pathlib import Path
from PySide6.QtCore import QDate
from .connection import get_db_connection, set_system_setting

def mark_database_modified():
    """Updates the last_modified_at system setting timestamp whenever local data changes."""
    from datetime import datetime
    try:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        set_system_setting("last_modified_at", now_str)
    except Exception as e:
        print(f"Failed to mark database modified: {e}")

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
        from .connection import ROOT_DIR
        dest_dir = ROOT_DIR / "uploaded_documents"
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
            cur.execute(f"UPDATE contracts SET {pdf_col} = ? WHERE project_id = ? OR contract_id = ?", (rel_path, target_id, target_id))
            
        elif document_type in ["IAR", "PO_Phase3"]:
            cur.execute("SELECT contract_id FROM contracts WHERE project_id = ? OR contract_id = ?", (target_id, target_id))
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
            cur.execute("SELECT contract_id FROM contracts WHERE project_id = ? OR contract_id = ?", (target_id, target_id))
            con_row = cur.fetchone()
            cid = con_row["contract_id"] if con_row else target_id
            cur.execute("UPDATE warranties SET warranty_certificate_pdf = ? WHERE contract_id = ?", (rel_path, cid))
                
        conn.commit()
        conn.close()
        mark_database_modified()
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


def get_upcoming_alerts(days=90):
    """Returns upcoming warranty expirations and pending payment/milestone deadlines within specified days."""
    from datetime import datetime, timedelta
    conn = get_db_connection()
    cur = conn.cursor()
    
    today = datetime.now().date()
    cutoff = today + timedelta(days=days)
    cutoff_str = cutoff.strftime("%Y-%m-%d")
    
    alerts = []
    
    # 1. Warranty Expirations
    cur.execute("""
        SELECT w.warranty_id, p.proj_id_no, p.project_name, w.warranty_end_date, w.warranty_status
        FROM warranties w
        JOIN contracts c ON w.contract_id = c.contract_id
        JOIN projects p ON c.project_id = p.project_id
        WHERE w.warranty_end_date IS NOT NULL AND w.warranty_end_date != ''
          AND w.warranty_end_date <= ? AND w.warranty_status != 'Expired'
    """, (cutoff_str,))
    for r in cur.fetchall():
        w_date_str = r[3]
        try:
            w_date = datetime.strptime(w_date_str, "%Y-%m-%d").date()
            diff_days = (w_date - today).days
        except Exception:
            diff_days = 0
            
        severity = "urgent" if diff_days <= 14 else ("warning" if diff_days <= 30 else "info")
        alerts.append({
            "id": r[0],
            "proj_id": r[1],
            "project_name": r[2],
            "title": f"Warranty Expiration ({r[1]})",
            "date": w_date_str,
            "days_remaining": diff_days,
            "severity": severity,
            "type": "warranty"
        })

    # 2. Payment/Milestone Deadlines
    cur.execute("""
        SELECT d.milestone_id, p.proj_id_no, p.project_name, d.payment_type, d.due_date_submission, d.payment_status
        FROM deliveries_and_payments d
        JOIN contracts c ON d.contract_id = c.contract_id
        JOIN projects p ON c.project_id = p.project_id
        WHERE d.due_date_submission IS NOT NULL AND d.due_date_submission != ''
          AND d.due_date_submission <= ? AND d.payment_status != 'Complete'
    """, (cutoff_str,))
    for r in cur.fetchall():
        d_date_str = r[4]
        try:
            d_date = datetime.strptime(d_date_str, "%Y-%m-%d").date()
            diff_days = (d_date - today).days
        except Exception:
            diff_days = 0
            
        severity = "urgent" if diff_days < 0 else ("warning" if diff_days <= 14 else "info")
        title_prefix = "OVERDUE Milestone" if diff_days < 0 else "Upcoming Milestone"
        alerts.append({
            "id": r[0],
            "proj_id": r[1],
            "project_name": r[2],
            "title": f"{title_prefix}: {r[3]} ({r[1]})",
            "date": d_date_str,
            "days_remaining": diff_days,
            "severity": severity,
            "type": "payment"
        })

    conn.close()
    alerts.sort(key=lambda x: x["days_remaining"])
    return alerts

def global_search(query):
    """Searches across projects, contracts, suppliers, payments, and warranties."""
    if not query or len(query.strip()) < 2:
        return []
        
    q = f"%{query.strip()}%"
    conn = get_db_connection()
    cur = conn.cursor()
    results = []
    
    # 1. Search Projects
    cur.execute("""
        SELECT project_id, proj_id_no, project_name, status, total_budget 
        FROM projects 
        WHERE proj_id_no LIKE ? OR project_name LIKE ? OR particulars LIKE ?
    """, (q, q, q))
    for r in cur.fetchall():
        results.append({
            "category": "Project",
            "title": f"Project: {r[1]} - {r[2]}",
            "subtitle": f"Status: {r[3]} | Budget: ₱{r[4]:,.2f}",
            "item_id": r[0],
            "type": "project"
        })
        
    # 2. Search Contracts
    cur.execute("""
        SELECT contract_id, contract_no, contract_amount, winner_supplier 
        FROM contracts 
        WHERE contract_no LIKE ? OR winner_supplier LIKE ?
    """, (q, q))
    for r in cur.fetchall():
        results.append({
            "category": "Contract",
            "title": f"Contract #{r[1]}",
            "subtitle": f"Supplier: {r[3]} | Amount: ₱{r[2]:,.2f}",
            "item_id": r[0],
            "type": "contract"
        })
        
    # 3. Search Suppliers
    cur.execute("""
        SELECT supplier_id, name, line_of_business, contact 
        FROM suppliers 
        WHERE name LIKE ? OR line_of_business LIKE ? OR contact LIKE ?
    """, (q, q, q))
    for r in cur.fetchall():
        results.append({
            "category": "Supplier",
            "title": f"Supplier: {r[1]}",
            "subtitle": f"Business: {r[2] or 'N/A'} | Contact: {r[3] or 'N/A'}",
            "item_id": r[0],
            "type": "supplier"
        })
        
    # 4. Search Deliveries / Payments
    cur.execute("""
        SELECT milestone_id, payment_type, po_no, iar_no, amount 
        FROM deliveries_and_payments 
        WHERE po_no LIKE ? OR iar_no LIKE ? OR payment_type LIKE ?
    """, (q, q, q))
    for r in cur.fetchall():
        results.append({
            "category": "Payment",
            "title": f"Payment: {r[1]} (PO #{r[2] or 'N/A'})",
            "subtitle": f"IAR #{r[3] or 'N/A'} | Amount: ₱{r[4]:,.2f}",
            "item_id": r[0],
            "type": "payment"
        })

    conn.close()
    return results


