from PyQt6.QtWidgets import QVBoxLayout, QLabel, QWidget, QHBoxLayout, QProgressBar
from PyQt6.QtCore import Qt, QRectF, QTimer, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QPainterPath, QLinearGradient, QConicalGradient
from base_widget import BaseWidget
import psutil
from PyQt6.QtGui import QFont

class BatteryWidget(BaseWidget):
    def __init__(self):
        super().__init__(size=(200, 200))
        self.title_label.setText("Battery")
        self.title_label.setFont(QFont("Segoe UI Variable", 10))
        self.title_label.setStyleSheet("color: rgba(255, 255, 255, 0.9);")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.title_label.setContentsMargins(20, 15, 0, 0)
        
        # Create main layout
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(15, 15, 15, 15)
        content_layout.setSpacing(5)
        
        # Create a container for percentage and status
        text_container = QWidget()
        text_layout = QVBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(4)
        
        # Battery percentage
        self.percentage_label = QLabel("100%")
        self.percentage_label.setFont(QFont("Segoe UI Variable", 22))
        self.percentage_label.setStyleSheet("color: rgba(255, 255, 255, 0.95);")
        self.percentage_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text_layout.addWidget(self.percentage_label)
        
        # Battery status
        self.status_label = QLabel("Plugged In")
        self.status_label.setFont(QFont("Segoe UI Variable", 9))
        self.status_label.setStyleSheet("color: rgba(255, 255, 255, 0.8);")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text_layout.addWidget(self.status_label)
        
        # Add text container to main layout
        content_layout.addStretch(1)
        content_layout.addWidget(text_container)
        content_layout.addStretch(1)
        
        self.layout.addLayout(content_layout)
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_data)
        self.update_timer.start(2000)  # Update every 2 seconds
        
        # Initial update
        self.update_data()
    
    def update_data(self):
        battery = psutil.sensors_battery()
        if battery:
            percent = int(battery.percent)
            plugged = battery.power_plugged
            
            # Update percentage
            self.percentage_label.setText(f"{percent}%")
            
            # Update status
            status = "Plugged In" if plugged else "On Battery"
            self.status_label.setText(status)
            
            # Update widget to trigger repaint
            self.update()
        else:
            self.percentage_label.setText("N/A")
            self.status_label.setText("No Battery")
    
    def paintEvent(self, event):
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Get battery info
        battery = psutil.sensors_battery()
        if not battery:
            return
            
        percent = battery.percent
        plugged = battery.power_plugged
        
        # Calculate circle dimensions
        center = QPointF(self.width() / 2, self.height() / 2)
        outer_radius = min(self.width(), self.height()) / 2 - 30
        
        # Draw background circle
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(30, 30, 35, 200))
        painter.drawEllipse(center, outer_radius, outer_radius)
        
        # Draw battery level arc
        if percent > 0:
            # Choose color based on battery state
            if plugged:
                color = QColor("#063D08")  # New specified green color
            elif percent <= 20:
                color = QColor(255, 50, 50, 200)  # Red for low battery
            else:
                color = QColor(200, 200, 200, 200)  # Gray for normal battery
            
            # Draw the arc
            pen = QPen(color, 15, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            
            # Calculate start and span angles
            start_angle = 90 * 16
            span_angle = -int(360 * (percent / 100) * 16)
            
            painter.drawArc(QRectF(center.x() - outer_radius, center.y() - outer_radius,
                                 outer_radius * 2, outer_radius * 2),
                          start_angle, span_angle)
            
            # Draw charging indicator if plugged in
            if plugged:
                painter.setPen(QPen(color, 2.5))
                painter.setBrush(color)
                bolt_path = QPainterPath()
                bolt_size = outer_radius * 0.15
                
                # Position the bolt above the percentage text
                bolt_y_offset = 20  # Adjust this value to move the bolt up/down
                bolt_path.moveTo(center.x(), center.y() - bolt_size - bolt_y_offset)
                bolt_path.lineTo(center.x() - bolt_size/2, center.y() - bolt_y_offset)
                bolt_path.lineTo(center.x(), center.y() + bolt_size/3 - bolt_y_offset)
                bolt_path.lineTo(center.x() + bolt_size/2, center.y() - bolt_y_offset)
                bolt_path.lineTo(center.x(), center.y() - bolt_size - bolt_y_offset)
                painter.drawPath(bolt_path) 