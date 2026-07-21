import sys
from PySide6.QtWidgets import QApplication
from ui.dashboard import PremiumSplashScreen, clean_temp_files, Dashboard

if __name__ == "__main__":
    clean_temp_files()
    app = QApplication(sys.argv)
    app.aboutToQuit.connect(clean_temp_files)
    
    # 1. Instantiate and display custom splash screen
    splash = PremiumSplashScreen()
    splash.show()
    
    # 2. Step 1: Scanning local folder
    splash.set_progress(20, "Scanning local cache and temporary files...")
    
    # 3. Step 2: Local Database initialization
    splash.set_progress(50, "Establishing database connection and verifying schemas...")
    
    # Let connection run updates
    from database import get_db_connection
    conn = get_db_connection()
    conn.close()
    
    # 4. Step 3: Main dashboard instantiation
    splash.set_progress(80, "Initializing main dashboard system...")
    main_win = Dashboard()
    
    # 5. Step 4: Finish splash and show main window
    splash.set_progress(100, "Ready!")
    splash.finish(main_win)
    main_win.show()
    
    sys.exit(app.exec())
