from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor, QPen, QFont
import database as database_config

class SimpleChart(QWidget):
    """A custom chart widget drawn using QPainter showing project budgets."""
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(250)
        self.data = []
        self.labels = []
        self.theme = "dark"
        self.load_data()

    def set_theme(self, theme):
        self.theme = theme
        self.update()

    def load_data(self):
        try:
            self.theme = database_config.get_theme_setting()
            projects = database_config.get_projects()
            if projects:
                # Take up to last 7 projects for display, chronological
                projects = projects[:7]
                projects.reverse()
                self.data = [p.get("abc_amount", 0.0) or 0.0 for p in projects]
                self.labels = [p.get("proj_id_no", "N/A") for p in projects]
            else:
                self.data = [0]
                self.labels = ["None"]
        except Exception as e:
            self.data = [0]
            self.labels = ["Error"]
            print(f"Error loading chart data: {e}")

    def paintEvent(self, event):
        if not self.data:
            return
            
        theme = getattr(self, "theme", "dark")
        if theme == "light":
            grid_color = QColor("#cbd5e1")
            text_color = QColor("#475569")
            accent_color = QColor("#002C76")
        else:
            grid_color = QColor("#253454")
            text_color = QColor("#94a3b8")
            accent_color = QColor("#FFDE15")

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background grid
        painter.setPen(QPen(grid_color, 1, Qt.DashLine))
        for i in range(1, 4):
            y = int(self.height() * (i / 4))
            painter.drawLine(40, y, self.width() - 20, y)
            
        padding = 60
        width_step = (self.width() - padding - 40) / (len(self.data) - 1) if len(self.data) > 1 else self.width() - padding - 40
        points = []
        
        max_val = max(self.data) if max(self.data) > 0 else 1

        for i, val in enumerate(self.data):
            x = int(padding + (i * width_step))
            y = int(self.height() - 50 - (val / max_val * (self.height() - 80)))
            points.append((x, y))
            
            # X Labels
            painter.setPen(text_color)
            painter.setFont(QFont("Arial", 8))
            painter.drawText(x - 20, self.height() - 15, self.labels[i])

            # Y value label
            painter.setPen(accent_color)
            painter.setFont(QFont("Arial", 8))
            
            if val >= 1000000:
                val_str = f"{val/1000000:.1f}M"
            elif val >= 1000:
                val_str = f"{val/1000:.0f}K"
            else:
                val_str = f"{val:.0f}"
            painter.drawText(x - 15, y - 10, val_str)

        # Draw trend line
        if len(points) > 1:
            painter.setPen(QPen(accent_color, 2, Qt.SolidLine))
            for i in range(len(points) - 1):
                painter.drawLine(points[i][0], points[i][1], points[i+1][0], points[i+1][1])

        # Draw data points
        painter.setBrush(accent_color)
        painter.setPen(Qt.NoPen)
        for pt in points:
            painter.drawEllipse(pt[0] - 4, pt[1] - 4, 8, 8)
