import sqlite3
from pathlib import Path
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

def create_formatted_sheet(sheet, headers, rows):
    # Styling configurations
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    left_align = Alignment(horizontal="left", vertical="center")
    right_align = Alignment(horizontal="right", vertical="center")
    
    thin_border = Border(
        left=Side(style='thin', color='D9D9D9'),
        right=Side(style='thin', color='D9D9D9'),
        top=Side(style='thin', color='D9D9D9'),
        bottom=Side(style='thin', color='D9D9D9')
    )
    
    # Write header columns
    for col_idx, header in enumerate(headers, 1):
        cell = sheet.cell(row=1, column=col_idx, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = thin_border
        
    # Freeze panes below headers
    sheet.freeze_panes = "A2"
    
    # Data row style
    data_font = Font(name="Calibri", size=10)
    
    # Write row records
    for row_idx, row_val in enumerate(rows, 2):
        for col_idx, val in enumerate(row_val, 1):
            cell = sheet.cell(row=row_idx, column=col_idx, value=val)
            cell.font = data_font
            cell.border = thin_border
            
            # Align and format based on column headers
            h_name = headers[col_idx - 1]
            if "(₱)" in h_name or "Allocation" in h_name or "Amount" in h_name or "Gross" in h_name or "Net" in h_name:
                cell.alignment = right_align
                if val is not None:
                    try:
                        cell.value = float(val)
                    except (ValueError, TypeError):
                        pass
                    cell.number_format = '"₱"#,##0.00'
            elif "Date" in h_name or "ID" in h_name or "Serial" in h_name or "Status" in h_name or "No" in h_name:
                cell.alignment = center_align
            else:
                cell.alignment = left_align
                
    # Row Heights
    sheet.row_dimensions[1].height = 28
    for r in range(2, len(rows) + 2):
        sheet.row_dimensions[r].height = 20
        
    # Auto-fit column widths
    for col in sheet.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            val = str(cell.value or "")
            if cell.number_format == '"₱"#,##0.00' and isinstance(cell.value, (int, float)):
                val = f"₱{cell.value:,.2f}"
            max_len = max(max_len, len(val))
        sheet.column_dimensions[col_letter].width = max(max_len + 4, 12)

def export_master_data(output_path, filters=None):
    """
    Queries all tables from procurement.db, joins them into a flat format,
    applies optional filters (status, division, date range), and exports
    them to a styled native Excel worksheet (.xlsx).
    """
    db_file = Path(__file__).parent / "procurement.db"
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    
    query = """
        SELECT 
            p.proj_id_no, p.project_name, p.bureau_division_name, p.focal_person, p.mode_of_procurement, p.abc_amount, p.status,
            pb.budget_type, pb.app_amount, pb.ors_amount, pb.ors_serial_no,
            s.supplier_name,
            c.po_jo_contract_no, c.contract_amount,
            d.milestone_deliverable, d.status_of_delivery, d.actual_delivery_date,
            pm.types_of_payment, pm.payment_amount_gross, pm.payment_amount_net, pm.rci_dv_acic_no, pm.check_date_lddap_ada,
            w.retention_period_warranty_status,
            COALESCE(c.contract_date, 
                     (SELECT MIN(d.date_prepared) FROM project_documents d WHERE d.project_id = p.id),
                     (SELECT MIN(b.date_received_bacsec) FROM bids b WHERE b.project_id = p.id),
                     '2026-01-01') AS project_date
        FROM projects p
        LEFT JOIN project_budgets pb ON p.id = pb.project_id
        LEFT JOIN contracts c ON p.id = c.project_id
        LEFT JOIN suppliers s ON c.supplier_id = s.id
        LEFT JOIN deliverables d ON c.id = d.contract_id
        LEFT JOIN payments pm ON d.id = pm.deliverable_id
        LEFT JOIN warranties w ON c.id = w.contract_id
        ORDER BY p.proj_id_no
    """
    
    try:
        cur.execute(query)
        rows = cur.fetchall()
        
        # Apply filters programmatically
        filtered_rows = []
        if filters:
            from datetime import datetime, date
            status_filter = filters.get("status", "All Statuses")
            division_filter = filters.get("division", "All Divisions")
            date_filter = filters.get("date", "All Dates")
            current_date = date.today()
            
            for row in rows:
                row_status = row[6]
                row_division = row[2]
                row_date_str = row[23]  # COALESCE project_date is the 24th column
                
                # Status Filter
                if status_filter != "All Statuses" and row_status != status_filter:
                    continue
                    
                # Division Filter
                if division_filter != "All Divisions" and (row_division is None or row_division.strip() != division_filter.strip()):
                    continue
                    
                # Date Presets Filter
                if date_filter != "All Dates" and row_date_str:
                    try:
                        proj_date = datetime.strptime(row_date_str, "%Y-%m-%d").date()
                        days_diff = (current_date - proj_date).days
                        if date_filter == "Within 24 hours only" and not (0 <= days_diff <= 1):
                            continue
                        elif date_filter == "Within a week only" and not (0 <= days_diff <= 7):
                            continue
                        elif date_filter == "Within a month only" and not (0 <= days_diff <= 30):
                            continue
                    except Exception:
                        pass
                        
                filtered_rows.append(row[:23])
        else:
            for row in rows:
                filtered_rows.append(row[:23])
                
        headers = [
            "Project ID", "Project Name", "Bureau/Division", "Focal Person", "Mode of Procurement", "ABC Budget (₱)", "Project Status",
            "Budget Type", "App Allocation (₱)", "ORS Amount (₱)", "ORS Serial No",
            "Supplier Name", "PO/JO Contract No", "Contract Amount (₱)",
            "Milestone Deliverable", "Delivery Status", "Actual Delivery Date",
            "Payment Type", "Payment Gross (₱)", "Payment Net (₱)", "DV / RCI No", "Check Date",
            "Warranty Status"
        ]
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Procurement Registry"
        
        # Grid lines visibility
        ws.views.sheetView[0].showGridLines = True
        
        create_formatted_sheet(ws, headers, filtered_rows)
        wb.save(output_path)
        
        return True, len(filtered_rows)
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def export_project_timeline(project_id, output_path):
    """
    Queries all timeline data related to a specific project and exports it to a styled native Excel worksheet (.xlsx).
    """
    db_file = Path(__file__).parent / "procurement.db"
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    
    query = """
        SELECT 
            p.proj_id_no, p.project_name, p.bureau_division_name, p.focal_person, p.mode_of_procurement, p.abc_amount, p.status,
            pb.budget_type, pb.app_amount, pb.ors_amount, pb.ors_serial_no,
            s.supplier_name,
            c.po_jo_contract_no, c.contract_amount,
            d.milestone_deliverable, d.status_of_delivery, d.actual_delivery_date,
            pm.types_of_payment, pm.payment_amount_gross, pm.payment_amount_net, pm.rci_dv_acic_no, pm.check_date_lddap_ada,
            w.retention_period_warranty_status
        FROM projects p
        LEFT JOIN project_budgets pb ON p.id = pb.project_id
        LEFT JOIN contracts c ON p.id = c.project_id
        LEFT JOIN suppliers s ON c.supplier_id = s.id
        LEFT JOIN deliverables d ON c.id = d.contract_id
        LEFT JOIN payments pm ON d.id = pm.deliverable_id
        LEFT JOIN warranties w ON c.id = w.contract_id
        WHERE p.id = ?
        ORDER BY p.proj_id_no
    """
    
    try:
        cur.execute(query, (project_id,))
        rows = cur.fetchall()
        
        headers = [
            "Project ID", "Project Name", "Bureau/Division", "Focal Person", "Mode of Procurement", "ABC Budget (₱)", "Project Status",
            "Budget Type", "App Allocation (₱)", "ORS Amount (₱)", "ORS Serial No",
            "Supplier Name", "PO/JO Contract No", "Contract Amount (₱)",
            "Milestone Deliverable", "Delivery Status", "Actual Delivery Date",
            "Payment Type", "Payment Gross (₱)", "Payment Net (₱)", "DV / RCI No", "Check Date",
            "Warranty Status"
        ]
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Project Timeline"
        
        # Grid lines visibility
        ws.views.sheetView[0].showGridLines = True
        
        create_formatted_sheet(ws, headers, rows)
        wb.save(output_path)
        
        return True, len(rows)
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()
