import os
import sqlite3
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file'
]

def col_index_to_letter(col_idx):
    """Converts a 0-based column index to an A1-style column letter (e.g. 0 -> A, 25 -> Z, 26 -> AA)."""
    letter = ""
    while col_idx >= 0:
        letter = chr(col_idx % 26 + ord('A')) + letter
        col_idx = col_idx // 26 - 1
    return letter

def get_google_services():
    """Authenticates the user and returns Sheets and Drive API services."""
    import database as database_config
    from database.connection import ROOT_DIR, SCHEMA_DIR
    creds_path = database_config.get_system_setting("google_credentials_path", "")
    
    # Check if creds_path exists directly or relative to ROOT_DIR / SCHEMA_DIR
    if creds_path:
        target = Path(creds_path)
        if target.exists():
            creds_path = str(target.resolve())
        elif (ROOT_DIR / creds_path).exists():
            creds_path = str((ROOT_DIR / creds_path).resolve())
            database_config.set_system_setting("google_credentials_path", creds_path)
        elif (SCHEMA_DIR / creds_path).exists():
            creds_path = str((SCHEMA_DIR / creds_path).resolve())
            database_config.set_system_setting("google_credentials_path", creds_path)
            
    # If still not found, auto-discover in ROOT_DIR or SCHEMA_DIR
    if not creds_path or not os.path.exists(creds_path):
        for candidate in ["procurement_credentials.json", "credentials.json"]:
            p1 = ROOT_DIR / candidate
            p2 = SCHEMA_DIR / candidate
            if p1.exists():
                creds_path = str(p1.resolve())
                database_config.set_system_setting("google_credentials_path", creds_path)
                break
            elif p2.exists():
                creds_path = str(p2.resolve())
                database_config.set_system_setting("google_credentials_path", creds_path)
                break

    if not creds_path or not os.path.exists(creds_path):
        raise Exception("Google credentials.json path is empty or the file does not exist. Please configure it in the Settings tab.")
        
    creds = None
    token_path = os.path.join(os.path.dirname(creds_path), 'token.json')
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        
    try:
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
    except Exception as err:
        err_str = str(err)
        if any(net_err in err_str.lower() for net_err in ["nameresolutionerror", "getaddrinfo failed", "failed to resolve", "max retries exceeded", "connectionrefused", "timed out", "timeout"]):
            raise Exception("NETWORK_ERROR: Unable to connect to Google servers. Please check your internet connection and try again.")
        raise err
            
    sheets_service = build('sheets', 'v4', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)
    return sheets_service, drive_service

def get_connected_email():
    """Retrieves the email address of the authenticated Google account, or None if not logged in."""
    try:
        import database as database_config
        creds_path = database_config.get_system_setting("google_credentials_path", "")
        if not creds_path or not os.path.exists(creds_path):
            return None
        token_path = os.path.join(os.path.dirname(creds_path), 'token.json')
        if not os.path.exists(token_path):
            return None
            
        sheets_service, drive_service = get_google_services()
        if not drive_service:
            return None
        about = drive_service.about().get(fields="user").execute()
        user_info = about.get('user', {})
        return user_info.get('emailAddress')
    except Exception as e:
        print(f"Failed to get connected email: {e}")
        return None

def ensure_spreadsheet():
    """Ensures a Google Spreadsheet exists, creating a new one if necessary."""
    import database as database_config
    spreadsheet_id = database_config.get_system_setting("google_spreadsheet_id", "")
    sheets_service, drive_service = get_google_services()
    
    if spreadsheet_id and len(spreadsheet_id.strip()) > 0:
        try:
            # Query Drive metadata to check if the spreadsheet has been trashed or deleted
            meta = drive_service.files().get(fileId=spreadsheet_id, fields="trashed").execute()
            if meta.get('trashed', False):
                print("Google Spreadsheet is in trash. Resetting ID.")
                spreadsheet_id = ""
                database_config.set_system_setting("google_spreadsheet_id", "")
            else:
                sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        except Exception as e:
            from googleapiclient.errors import HttpError
            if isinstance(e, HttpError) and e.resp.status == 404:
                print("Google Spreadsheet was deleted. Resetting ID.")
                spreadsheet_id = ""
                database_config.set_system_setting("google_spreadsheet_id", "")
            else:
                raise e
    
    if not spreadsheet_id or len(spreadsheet_id.strip()) == 0:
        spreadsheet = {
            'properties': {
                'title': 'Nexus Procurement Master Database'
            }
        }
        spreadsheet = sheets_service.spreadsheets().create(
            body=spreadsheet, fields='spreadsheetId'
        ).execute()
        spreadsheet_id = spreadsheet['spreadsheetId']
        database_config.set_system_setting("google_spreadsheet_id", spreadsheet_id)
        
    return spreadsheet_id

def ensure_drive_folder():
    """Ensures a Google Drive folder exists, creating a new one if necessary."""
    import database as database_config
    folder_id = database_config.get_system_setting("google_drive_folder_id", "")
    sheets_service, drive_service = get_google_services()
    
    if folder_id and len(folder_id.strip()) > 0:
        try:
            # Query Drive metadata to check if the folder has been trashed or deleted
            meta = drive_service.files().get(fileId=folder_id, fields="trashed").execute()
            if meta.get('trashed', False):
                print("Google Drive Folder is in trash. Resetting ID.")
                folder_id = ""
                database_config.set_system_setting("google_drive_folder_id", "")
            else:
                drive_service.files().get(fileId=folder_id).execute()
        except Exception as e:
            from googleapiclient.errors import HttpError
            if isinstance(e, HttpError) and e.resp.status == 404:
                print("Google Drive Folder was deleted. Resetting ID.")
                folder_id = ""
                database_config.set_system_setting("google_drive_folder_id", "")
            else:
                raise e
    
    if not folder_id or len(folder_id.strip()) == 0:
        file_metadata = {
            'name': 'Nexus Procurement Documents',
            'mimeType': 'application/vnd.google-apps.folder'
        }
        file = drive_service.files().create(body=file_metadata, fields='id').execute()
        folder_id = file.get('id')
        database_config.set_system_setting("google_drive_folder_id", folder_id)
        
    return folder_id

def migrate_local_files_to_drive():
    """Finds any local file paths in the database, uploads them to Drive, and updates database records."""
    import database as database_config
    from pathlib import Path
    
    conn = database_config.get_db_connection()
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = OFF")
    
    from database.connection import ROOT_DIR, SCHEMA_DIR
    base_dir = ROOT_DIR

    def resolve_local_file(val):
        if not val or str(val).startswith("http"):
            return None
        p = Path(val)
        if p.is_absolute() and p.exists():
            return p
        for root in [ROOT_DIR, SCHEMA_DIR, Path(__file__).parent, Path(__file__).parent.parent]:
            cand = root / val
            if cand.exists():
                return cand
        return None

    # 1. Projects
    try:
        cur.execute("SELECT project_id, saro_pdf, ppmp_pdf, market_scoping_pdf, tech_specs_pdf, abstract_quotations_pdf FROM projects")
        for row in cur.fetchall():
            pid = row["project_id"]
            updates = {}
            for col in ["saro_pdf", "ppmp_pdf", "market_scoping_pdf", "tech_specs_pdf", "abstract_quotations_pdf"]:
                val = row[col]
                local_path = resolve_local_file(val)
                if local_path:
                    try:
                        filename = f"doc_{pid}_{col.replace('_pdf', '').upper()}{local_path.suffix}"
                        url = upload_file_to_drive(str(local_path), filename)
                        updates[col] = url
                    except Exception as e:
                        print(f"Failed to migrate project file {val}: {e}")
            if updates:
                cols = ", ".join(f"{k} = ?" for k in updates.keys())
                params = list(updates.values()) + [pid]
                cur.execute(f"UPDATE projects SET {cols} WHERE project_id = ?", tuple(params))
    except Exception as e:
        print(f"Failed to scan project files for migration: {e}")
            
    # 2. Contracts
    try:
        cur.execute("SELECT contract_id, project_id, noa_pdf, signed_contract_pdf, request_order_pdf, bac_resolution_pdf FROM contracts")
        for row in cur.fetchall():
            cid = row["contract_id"]
            pid = row["project_id"]
            updates = {}
            for col in ["noa_pdf", "signed_contract_pdf", "request_order_pdf", "bac_resolution_pdf"]:
                val = row[col]
                local_path = resolve_local_file(val)
                if local_path:
                    try:
                        filename = f"doc_{pid}_{col.replace('_pdf', '').upper()}{local_path.suffix}"
                        url = upload_file_to_drive(str(local_path), filename)
                        updates[col] = url
                    except Exception as e:
                        print(f"Failed to migrate contract file {val}: {e}")
            if updates:
                cols = ", ".join(f"{k} = ?" for k in updates.keys())
                params = list(updates.values()) + [cid]
                cur.execute(f"UPDATE contracts SET {cols} WHERE contract_id = ?", tuple(params))
    except Exception as e:
        print(f"Failed to scan contract files for migration: {e}")
            
    # 3. Deliveries
    try:
        cur.execute("SELECT milestone_id, contract_id, iar_pdf, po_pdf FROM deliveries_and_payments")
        for row in cur.fetchall():
            mid = row["milestone_id"]
            cid = row["contract_id"]
            cur.execute("SELECT project_id FROM contracts WHERE contract_id = ?", (cid,))
            proj_row = cur.fetchone()
            pid = proj_row["project_id"] if proj_row else cid
            
            updates = {}
            for col in ["iar_pdf", "po_pdf"]:
                val = row[col]
                local_path = resolve_local_file(val)
                if local_path:
                    try:
                        filename = f"doc_{pid}_{col.replace('_pdf', '').upper()}_{mid}{local_path.suffix}"
                        url = upload_file_to_drive(str(local_path), filename)
                        updates[col] = url
                    except Exception as e:
                        print(f"Failed to migrate delivery file {val}: {e}")
            if updates:
                cols = ", ".join(f"{k} = ?" for k in updates.keys())
                params = list(updates.values()) + [mid]
                cur.execute(f"UPDATE deliveries_and_payments SET {cols} WHERE milestone_id = ?", tuple(params))
    except Exception as e:
        print(f"Failed to scan delivery files for migration: {e}")
            
    # 4. Warranties
    try:
        cur.execute("SELECT warranty_id, contract_id, warranty_certificate_pdf FROM warranties")
        for row in cur.fetchall():
            wid = row["warranty_id"]
            cid = row["contract_id"]
            cur.execute("SELECT project_id FROM contracts WHERE contract_id = ?", (cid,))
            proj_row = cur.fetchone()
            pid = proj_row["project_id"] if proj_row else cid
            
            val = row["warranty_certificate_pdf"]
            local_path = resolve_local_file(val)
            if local_path:
                try:
                    filename = f"doc_{pid}_WARRANTY{local_path.suffix}"
                    url = upload_file_to_drive(str(local_path), filename)
                    cur.execute("UPDATE warranties SET warranty_certificate_pdf = ? WHERE warranty_id = ?", (url, wid))
                except Exception as e:
                    print(f"Failed to migrate warranty file {val}: {e}")
    except Exception as e:
        print(f"Failed to scan warranty files for migration: {e}")
                    
    conn.commit()
    cur.execute("PRAGMA foreign_keys = ON")
    conn.close()

def push_sqlite_to_sheets(progress_callback=None, force_full=False):
    """Pushes local SQLite tables to Google Sheets using incremental delta sync."""
    def p(pct, msg):
        if progress_callback:
            progress_callback(pct, msg)

    import database as database_config
    from datetime import datetime

    last_synced = database_config.get_system_setting("last_synced_at", "")
    last_modified = database_config.get_system_setting("last_modified_at", "")

    if not force_full and last_synced and last_modified and last_synced >= last_modified:
        p(100, "No new local changes detected. Google Sheets is already up to date!")
        spreadsheet_id = database_config.get_system_setting("google_spreadsheet_id", "")
        return spreadsheet_id

    p(5, "Scanning and migrating local PDF files to Google Drive...")
    try:
        migrate_local_files_to_drive()
    except Exception as e:
        print(f"File migration skip/failed during sheet push: {e}")

    p(20, "Authenticating Google Services...")
    sheets_service, drive_service = get_google_services()
    spreadsheet_id = ensure_spreadsheet()
    
    conn = database_config.get_db_connection()
    cur = conn.cursor()
    
    tables = ["projects", "suppliers", "contracts", "deliveries_and_payments", "warranties"]
    
    sheet_metadata = sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheets = sheet_metadata.get('sheets', [])
    sheet_titles = [s['properties']['title'] for s in sheets]
    
    for idx, table in enumerate(tables):
        pct = 25 + int((idx / len(tables)) * 50)
        p(pct, f"Pushing table '{table}' ({idx+1}/{len(tables)}) to Google Sheets...")
        if table not in sheet_titles:
            body = {
                'requests': [{
                    'addSheet': {
                        'properties': {
                            'title': table
                        }
                    }
                }]
            }
            sheets_service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()
            
        # Filter out columns ending with _data (raw binary columns) for sheets export
        cur.execute(f"PRAGMA table_info({table})")
        columns_info = cur.fetchall()
        select_cols = [c[1] for c in columns_info if not c[1].endswith("_data")]
        
        cols_str = ", ".join(f'"{c}"' for c in select_cols)
        cur.execute(f"SELECT {cols_str} FROM {table}")
        rows = cur.fetchall()
        colnames = select_cols
        
        values = [colnames]
        for r in rows:
            row_values = []
            for val in r:
                if isinstance(val, bytes):
                    row_values.append("[Binary Document Data]")
                elif val is None:
                    row_values.append("")
                else:
                    row_values.append(str(val))
            values.append(row_values)
            
        sheets_service.spreadsheets().values().clear(
            spreadsheetId=spreadsheet_id, range=f"'{table}'!A1:Z1000"
        ).execute()
        
        body = {'values': values}
        sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id, range=f"'{table}'!A1",
            valueInputOption='RAW', body=body
        ).execute()
        
    p(80, "Formatting Google Drive PDF Smart Chips...")
    # Apply styling & auto-fit column widths to each sheet
    try:
        sheet_metadata_new = sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheets_new = sheet_metadata_new.get('sheets', [])
        sheet_id_map = {s['properties']['title']: s['properties']['sheetId'] for s in sheets_new}
        
        for table in tables:
            grid_id = sheet_id_map.get(table)
            if grid_id is not None:
                cur.execute(f"SELECT * FROM {table} LIMIT 1")
                colnames_all = [desc[0] for desc in cur.description]
                num_cols = len(colnames_all)
                
                format_requests = [
                    # Header format (Dark blue background, white bold text, centered)
                    {
                        'repeatCell': {
                            'range': {
                                'sheetId': grid_id,
                                'startRowIndex': 0,
                                'endRowIndex': 1,
                                'startColumnIndex': 0,
                                'endColumnIndex': num_cols
                            },
                            'cell': {
                                'userEnteredFormat': {
                                    'backgroundColor': {
                                        'red': 0.12,
                                        'green': 0.31,
                                        'blue': 0.47
                                    },
                                    'textFormat': {
                                        'foregroundColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0},
                                        'bold': True,
                                        'fontFamily': 'Arial',
                                        'fontSize': 10
                                    },
                                    'horizontalAlignment': 'CENTER',
                                    'verticalAlignment': 'MIDDLE'
                                }
                            },
                            'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)'
                        }
                    },
                    # Column widths auto-resize
                    {
                        'autoResizeDimensions': {
                            'dimensions': {
                                'sheetId': grid_id,
                                'dimension': 'COLUMNS',
                                'startIndex': 0,
                                'endIndex': num_cols
                            }
                        }
                    }
                ]
                
                # Fetch row data to generate smart chips for PDF columns
                cur.execute(f"PRAGMA table_info({table})")
                columns_info = cur.fetchall()
                select_cols = [c[1] for c in columns_info if not c[1].endswith("_data")]
                cols_str = ", ".join(f'"{c}"' for c in select_cols)
                
                cur.execute(f"SELECT {cols_str} FROM {table}")
                rows_data = cur.fetchall()
                
                for r_idx, row_record in enumerate(rows_data, 1): # row index 0 is header
                    for c_idx, col_name in enumerate(select_cols):
                        if col_name.endswith("_pdf"):
                            val = row_record[c_idx]
                            if val and str(val).startswith("http") and "drive.google.com" in str(val):
                                format_requests.append({
                                    'updateCells': {
                                        'rows': [{
                                            'values': [{
                                                'userEnteredValue': {'stringValue': '@'},
                                                'chipRuns': [{
                                                    'startIndex': 0,
                                                    'chip': {
                                                        'richLinkProperties': {
                                                            'uri': str(val)
                                                        }
                                                    }
                                                }]
                                            }]
                                        }],
                                        'fields': 'userEnteredValue,chipRuns',
                                        'range': {
                                            'sheetId': grid_id,
                                            'startRowIndex': r_idx,
                                            'endRowIndex': r_idx + 1,
                                            'startColumnIndex': c_idx,
                                            'endColumnIndex': c_idx + 1
                                        }
                                    }
                                })
                
                # Chunk format_requests into batches of 500 to avoid payload size limit issues
                chunk_size = 500
                for i in range(0, len(format_requests), chunk_size):
                    chunk = format_requests[i:i + chunk_size]
                    sheets_service.spreadsheets().batchUpdate(
                        spreadsheetId=spreadsheet_id,
                        body={'requests': chunk}
                    ).execute()
    except Exception as e:
        print(f"Failed to style sheets: {e}")

    # Delete default "Sheet1" or "Sheet 1" if it exists, so the first populated table sheet displays automatically
    try:
        sheet_metadata_new = sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheets_new = sheet_metadata_new.get('sheets', [])
        if len(sheets_new) > 1:
            for s in sheets_new:
                title = s['properties']['title']
                if title in ["Sheet1", "Sheet 1"]:
                    sheet_id_to_delete = s['properties']['sheetId']
                    body = {
                        'requests': [{
                            'deleteSheet': {
                                'sheetId': sheet_id_to_delete
                            }
                        }]
                    }
                    sheets_service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()
    except Exception as e:
        print(f"Skipped deleting default Sheet1: {e}")

    p(95, "Finalizing sync & updating timestamps...")
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    database_config.set_system_setting("last_synced_at", now_str)
    database_config.set_system_setting("last_modified_at", now_str)
    conn.close()
    p(100, "Google Sheets Sync Completed!")
    return spreadsheet_id

def pull_sheets_to_sqlite(progress_callback=None):
    """Pulls online changes from Google Sheets back into the local SQLite database, resolving smart chips if present."""
    def p(pct, msg):
        if progress_callback:
            progress_callback(pct, msg)

    p(10, "Connecting to Google Sheets API...")
    sheets_service, drive_service = get_google_services()
    spreadsheet_id = ensure_spreadsheet()
    
    import database as database_config
    conn = database_config.get_db_connection()
    cur = conn.cursor()
    
    tables = ["projects", "suppliers", "contracts", "deliveries_and_payments", "warranties"]
    
    primary_keys = {
        "projects": "project_id",
        "suppliers": "supplier_id",
        "contracts": "contract_id",
        "deliveries_and_payments": "milestone_id",
        "warranties": "warranty_id"
    }
    
    try:
        cur.execute("PRAGMA foreign_keys = OFF")
        
        for idx, table in enumerate(tables):
            pct = 20 + int((idx / len(tables)) * 70)
            p(pct, f"Pulling and merging table '{table}' ({idx+1}/{len(tables)})...")
            try:
                # 1. Fetch raw values first (very fast, handles thousands of rows in milliseconds)
                res = sheets_service.spreadsheets().values().get(
                    spreadsheetId=spreadsheet_id, range=f"'{table}'!A1:Z10000"
                ).execute()
                values = res.get('values', [])
                if not values or len(values) < 2:
                    continue
                    
                headers = values[0]
                pk = primary_keys.get(table)
                
                # Exclude header row and build a list of row dicts
                row_dicts = []
                for row in values[1:]:
                    if len(row) < len(headers):
                        row.extend([""] * (len(headers) - len(row)))
                    row_dicts.append(dict(zip(headers, row)))
                    
                # 2. Identify PDF columns to fetch their smart chip URLs
                pdf_columns = [col for col in headers if col.endswith("_pdf")]
                if pdf_columns:
                    pdf_ranges = []
                    col_to_letter = {}
                    for col in pdf_columns:
                        c_idx = headers.index(col)
                        # Convert column index to A1 letter
                        col_letter = col_index_to_letter(c_idx)
                        col_to_letter[col] = col_letter
                        pdf_ranges.append(f"'{table}'!{col_letter}:{col_letter}")
                        
                    # Fetch formats/chipRuns only for those columns
                    try:
                        res_chips = sheets_service.spreadsheets().get(
                            spreadsheetId=spreadsheet_id,
                            ranges=pdf_ranges,
                            includeGridData=True,
                            fields="sheets(data(rowData(values(chipRuns))))"
                        ).execute()
                        
                        # Parse the chip runs
                        sheets_list = res_chips.get('sheets', [])
                        if sheets_list:
                            grid_data_list = sheets_list[0].get('data', [])
                            # Map each range back to the PDF column name
                            for range_idx, data_entry in enumerate(grid_data_list):
                                if range_idx < len(pdf_columns):
                                    col_name = pdf_columns[range_idx]
                                    row_data_list = data_entry.get('rowData', [])
                                    # Update URLs in row_dicts (offset by 1 due to header row)
                                    for r_idx in range(1, len(row_data_list)):
                                        row_cell_list = row_data_list[r_idx].get('values', [])
                                        if row_cell_list:
                                            cell = row_cell_list[0] # range is single column, so index 0
                                            if 'chipRuns' in cell:
                                                for run in cell['chipRuns']:
                                                    chip = run.get('chip', {})
                                                    rich_link = chip.get('richLinkProperties', {})
                                                    if 'uri' in rich_link:
                                                        uri_val = rich_link['uri']
                                                        # Update the value in row_dicts (r_idx - 1 mapping)
                                                        if r_idx - 1 < len(row_dicts):
                                                            row_dicts[r_idx - 1][col_name] = uri_val
                                                        break
                    except Exception as chip_err:
                        print(f"Skipped formatting fetch for '{table}': {chip_err}")
                
                # 3. Save records to local SQLite database
                for row_dict in row_dicts:
                    if pk not in row_dict or not row_dict[pk] or str(row_dict[pk]).strip() == "":
                        continue
                        
                    cur.execute(f"PRAGMA table_info({table})")
                    columns_info = cur.fetchall()
                    db_columns = [col[1] for col in columns_info]
                    
                    final_row_dict = {}
                    for col in db_columns:
                        if col in row_dict:
                            val = row_dict[col]
                            if val == "" or val is None:
                                final_row_dict[col] = None
                            else:
                                col_type = next((c[2] for c in columns_info if c[1] == col), "TEXT")
                                if "INT" in col_type.upper():
                                    try:
                                        final_row_dict[col] = int(val)
                                    except ValueError:
                                        final_row_dict[col] = None
                                elif "REAL" in col_type.upper() or "NUM" in col_type.upper():
                                    try:
                                        final_row_dict[col] = float(val)
                                    except ValueError:
                                        final_row_dict[col] = None
                                else:
                                    final_row_dict[col] = val
                                    
                    if final_row_dict:
                        cols = ", ".join(final_row_dict.keys())
                        placeholders = ", ".join(["?"] * len(final_row_dict))
                        
                        update_cols = [c for c in final_row_dict.keys() if c != pk]
                        update_str = ", ".join(f"{c} = excluded.{c}" for c in update_cols)
                        
                        q = f"""
                            INSERT INTO {table} ({cols}) 
                            VALUES ({placeholders})
                            ON CONFLICT({pk}) DO UPDATE SET {update_str}
                        """
                        cur.execute(q, tuple(final_row_dict.values()))
                        
            except Exception as e:
                print(f"Error syncing table '{table}': {e}")
                
        conn.commit()
    finally:
        try:
            cur.execute("PRAGMA foreign_keys = ON")
        except Exception:
            pass
        conn.close()

def upload_file_to_drive(local_path, filename):
    """Uploads a local file to the synced Google Drive folder and returns the view link."""
    sheets_service, drive_service = get_google_services()
    folder_id = ensure_drive_folder()
    
    file_metadata = {
        'name': filename,
        'parents': [folder_id]
    }
    
    media = MediaFileUpload(
        local_path,
        mimetype='application/pdf',
        resumable=True
    )
    
    file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, webViewLink'
    ).execute()
    
    file_id = file.get('id')
    web_link = file.get('webViewLink')
    
    # Set public link reader access permissions
    permission = {
        'type': 'anyone',
        'role': 'reader',
    }
    drive_service.permissions().create(
        fileId=file_id,
        body=permission
    ).execute()
    
    return web_link

from PySide6.QtCore import QThread, Signal

class GoogleSyncWorker(QThread):
    finished = Signal(bool, str) # (success, message)
    progress = Signal(int, str)  # (percent, status_text)
    
    def __init__(self, action_type="push", local_path=None, filename=None):
        super().__init__()
        self.action_type = action_type # "push", "pull", "upload"
        self.local_path = local_path
        self.filename = filename
        self.result_url = None
        
    def run(self):
        def cb(pct, msg):
            self.progress.emit(pct, msg)

        try:
            if self.action_type == "push":
                sid = push_sqlite_to_sheets(progress_callback=cb)
                self.finished.emit(True, sid)
            elif self.action_type == "pull":
                pull_sheets_to_sqlite(progress_callback=cb)
                self.finished.emit(True, "Pull completed successfully.")
            elif self.action_type == "upload":
                url = upload_file_to_drive(self.local_path, self.filename)
                self.result_url = url
                self.finished.emit(True, url)
        except Exception as e:
            err_msg = str(e)
            if any(net_err in err_msg.lower() for net_err in ["nameresolutionerror", "getaddrinfo failed", "failed to resolve", "max retries exceeded", "connectionrefused", "timed out", "timeout"]):
                err_msg = "NETWORK_ERROR: Unable to connect to Google servers. Please check your internet connection and try again."
            self.finished.emit(False, err_msg)


import socket
import time

class NetworkMonitorThread(QThread):
    status_changed = Signal(bool) # Emits True if connected, False if offline
    
    def __init__(self, interval_seconds=10):
        super().__init__()
        self.interval_seconds = interval_seconds
        self._running = True
        self._last_state = None
        
    def stop(self):
        self._running = False
        
    def check_connection(self):
        try:
            s = socket.create_connection(("8.8.8.8", 53), timeout=2.0)
            s.close()
            return True
        except Exception:
            try:
                s = socket.create_connection(("oauth2.googleapis.com", 443), timeout=2.0)
                s.close()
                return True
            except Exception:
                return False
                
    def run(self):
        while self._running:
            is_online = self.check_connection()
            if is_online != self._last_state:
                self._last_state = is_online
                self.status_changed.emit(is_online)
            for _ in range(self.interval_seconds):
                if not self._running:
                    break
                time.sleep(1)
