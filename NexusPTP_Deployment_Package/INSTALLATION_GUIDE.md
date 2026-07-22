# NexusPTP — Official DICT Application Deployment Guide

## 📋 Overview
**NexusPTP** (Payment & Contract Tracking Program) is a standalone, portable desktop application designed for DICT procurement and financial tracking. It operates with a local SQLite database for fast offline performance and integrates with Google Sheets & Google Drive for multi-user synchronization.

---

## 📂 Deployment Package Contents

| File | Description |
| :--- | :--- |
| **`NexusPTP.exe`** | Standalone pre-compiled application executable (No Python installation required). |
| **`procurement_credentials.json`** | Google OAuth Client Secrets configuration file. |
| **`Setup_NexusPTP.bat`** | 1-Click script to automatically create a Desktop Shortcut. |
| **`INSTALLATION_GUIDE.md`** | Step-by-step user setup and deployment instructions. |

---

## 🚀 How to Deploy & Install on Other Computers

### Step 1: Copy & Extract
1. Copy `NexusPTP_v2.0_Deployment.zip` or the `NexusPTP_Deployment_Package` folder onto a USB flash drive or shared network drive.
2. Paste the folder onto the target computer (e.g. `C:\DICT_Programs\NexusPTP` or inside `Documents`).
3. If using a ZIP file, right-click and select **Extract All...**.

### Step 2: Create Desktop Shortcut (Optional)
* Double-click **`Setup_NexusPTP.bat`**.
* A shortcut named **NexusPTP** will instantly appear on the user's Windows Desktop.

### Step 3: Run NexusPTP
* Double-click **`NexusPTP.exe`** (or the Desktop Shortcut).
* The application will launch with a splash screen, initialize local database tables, and present the system dashboard.

---

## ☁️ Google Sheets & Drive Account Authorization

To enable cloud synchronization on a new computer:
1. Open **NexusPTP** ➔ Go to **Settings & Tools** ➔ **☁️ Google Sync & Account**.
2. Click **🔑 Connect Account**.
3. A web browser window will open automatically. Log in with your authorized DICT Google Account and click **Allow**.
4. Once authorized, click **🔄 Push SQLite to Sheets** or **📥 Pull Sheets to SQLite** to synchronize projects, contracts, payments, and PDF documents.

---

## 🔒 Security & Data Preservation
* **Offline Resiliency:** The app stores data in `procurement.db` inside the program directory. If offline, all work is saved locally and can be synced once reconnected to the internet.
* **Snapshot Backups:** Automated snapshot backups are saved in the `backups/` folder prior to major sync operations.
