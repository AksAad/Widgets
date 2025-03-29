from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QWidget
from PyQt6.QtCore import Qt, QTimer, QRectF, QPointF
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QPainterPath, QLinearGradient
from base_widget import BaseWidget
import psutil
from collections import deque

class NetworkGraphWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(280, 60)
        self.upload_data = [0] * 50
        self.download_data = [0] * 50
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw background
        painter.fillRect(self.rect(), QColor(30, 30, 35, 100))
        
        # Draw grid lines
        painter.setPen(QPen(QColor(255, 255, 255, 15), 1, Qt.PenStyle.DotLine))
        
        # Horizontal grid lines
        for i in range(1, 4):
            y = int(self.height() * (i / 4))
            painter.drawLine(0, y, self.width(), y)
        
        # Vertical grid lines
        step = self.width() / 10
        for i in range(1, 10):
            x = int(step * i)
            painter.drawLine(x, 0, x, self.height())
        
        # Draw upload graph with smooth curve
        self.draw_graph(painter, self.upload_data, QColor(220, 70, 70, 180))  # Keep red for upload
        
        # Draw download graph with smooth curve
        self.draw_graph(painter, self.download_data, QColor(40, 180, 120, 180))  # Relaxed green for download
    
    def draw_graph(self, painter, data, color):
        if not data:
            return
        
        # Calculate points
        points = []
        w = self.width()
        h = self.height()
        dx = w / (len(data) - 1)
        
        for i, value in enumerate(data):
            x = i * dx
            y = h * (1 - value)
            points.append(QPointF(x, y))
        
        # Create smooth curve path
        path = QPainterPath()
        path.moveTo(points[0])
        
        # Use cubic bezier curves to create smooth lines
        for i in range(1, len(points) - 2):
            p1 = points[i]
            p2 = points[i + 1]
            
            # Calculate control points
            ctrl1 = QPointF((p1.x() + p2.x()) / 2, p1.y())
            ctrl2 = QPointF((p1.x() + p2.x()) / 2, p2.y())
            
            path.cubicTo(ctrl1, ctrl2, p2)
        
        # Add last segment
        if len(points) > 2:
            path.lineTo(points[-1])
        
        # Draw line
        pen = QPen(color, 1.5)
        painter.setPen(pen)
        painter.drawPath(path)
        
        # Create fill path
        fill_path = QPainterPath(path)
        fill_path.lineTo(w, h)
        fill_path.lineTo(0, h)
        fill_path.closeSubpath()
        
        # Create and apply gradient fill
        gradient = QLinearGradient(0, 0, 0, h)
        gradient.setColorAt(0, QColor(color.red(), color.green(), color.blue(), 40))
        gradient.setColorAt(1, QColor(color.red(), color.green(), color.blue(), 10))
        painter.fillPath(fill_path, gradient)
        
        # Add highlight effect on the line
        highlight = QPen(QColor(color.red(), color.green(), color.blue(), 100), 3)
        painter.setPen(highlight)
        painter.drawPath(path)

class NetworkWidget(BaseWidget):
    def __init__(self):
        super().__init__(size=(300, 120))
        self.title_label.setText("Network")
        
        # Initialize network counters
        net = psutil.net_io_counters()
        self.prev_bytes_sent = net.bytes_sent
        self.prev_bytes_recv = net.bytes_recv
        
        # Create main content layout
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(12, 8, 12, 12)
        content_layout.setSpacing(8)
        
        # Network stats container
        stats_container = QWidget()
        stats_layout = QVBoxLayout(stats_container)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(4)
        
        # Upload stats
        upload_layout = QHBoxLayout()
        upload_layout.setSpacing(4)
        
        upload_label = QLabel("Upload")
        upload_label.setStyleSheet("color: rgba(180, 180, 180, 0.9);")
        upload_layout.addWidget(upload_label)
        
        self.upload_value = QLabel("0 KB/s")
        self.upload_value.setStyleSheet("color: rgba(220, 70, 70, 0.9);")  # Keep red for upload
        upload_layout.addWidget(self.upload_value, alignment=Qt.AlignmentFlag.AlignRight)
        
        self.upload_total = QLabel("Total: 0 MB")
        self.upload_total.setStyleSheet("color: rgba(180, 180, 180, 0.7);")
        upload_layout.addWidget(self.upload_total, alignment=Qt.AlignmentFlag.AlignRight)
        
        stats_layout.addLayout(upload_layout)
        
        # Download stats
        download_layout = QHBoxLayout()
        download_layout.setSpacing(4)
        
        download_label = QLabel("Download")
        download_label.setStyleSheet("color: rgba(180, 180, 180, 0.9);")
        download_layout.addWidget(download_label)
        
        self.download_value = QLabel("0 KB/s")
        self.download_value.setStyleSheet("color: rgba(40, 180, 120, 0.9);")  # Relaxed green for download
        download_layout.addWidget(self.download_value, alignment=Qt.AlignmentFlag.AlignRight)
        
        self.download_total = QLabel("Total: 0 MB")
        self.download_total.setStyleSheet("color: rgba(180, 180, 180, 0.7);")
        download_layout.addWidget(self.download_total, alignment=Qt.AlignmentFlag.AlignRight)
        
        stats_layout.addLayout(download_layout)
        
        content_layout.addWidget(stats_container)
        
        # Network graph
        self.graph = NetworkGraphWidget()
        content_layout.addWidget(self.graph)
        
        self.layout.addLayout(content_layout)
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_data)
        self.update_timer.start(1000)  # Update every second
    
    def update_data(self):
        try:
            # Get current network I/O stats
            net_io = psutil.net_io_counters()
            
            # Calculate speeds
            bytes_sent = net_io.bytes_sent - self.prev_bytes_sent
            bytes_recv = net_io.bytes_recv - self.prev_bytes_recv
            
            # Update previous values
            self.prev_bytes_sent = net_io.bytes_sent
            self.prev_bytes_recv = net_io.bytes_recv
            
            # Update graph
            self.graph.upload_data.append(bytes_sent / 1024)
            self.graph.download_data.append(bytes_recv / 1024)
            
            # Format and update labels
            self.upload_value.setText(f"{bytes_sent / 1024:.1f} KB/s")
            self.download_value.setText(f"{bytes_recv / 1024:.1f} KB/s")
            
            # Format total transferred data
            self.upload_total.setText(f"Total: {net_io.bytes_sent / (1024*1024):.1f} MB")
            self.download_total.setText(f"Total: {net_io.bytes_recv / (1024*1024):.1f} MB")
            
        except Exception as e:
            print(f"Error updating network data: {e}")

    def format_speed(self, bytes_per_sec):
        if bytes_per_sec >= 1024 * 1024:  # MB/s
            return f"{bytes_per_sec / (1024 * 1024):.1f} MB/s"
        else:  # KB/s
            return f"{bytes_per_sec / 1024:.1f} KB/s"
    
    def format_total(self, bytes_total):
        if bytes_total >= 1024 * 1024 * 1024:  # GB
            return f"Total: {bytes_total / (1024 * 1024 * 1024):.1f} GB"
        else:  # MB
            return f"Total: {bytes_total / (1024 * 1024):.1f} MB"
    
    def update_data(self):
        net_io = psutil.net_io_counters()
        
        # Calculate speeds
        bytes_sent = net_io.bytes_sent
        bytes_recv = net_io.bytes_recv
        
        upload_speed = bytes_sent - self.prev_bytes_sent
        download_speed = bytes_recv - self.prev_bytes_recv
        
        # Update previous values
        self.prev_bytes_sent = bytes_sent
        self.prev_bytes_recv = bytes_recv
        
        # Update upload indicators
        self.upload_value.setText(self.format_speed(upload_speed))
        self.upload_total.setText(self.format_total(bytes_sent))
        self.graph.upload_data.append(upload_speed / 1024)
        
        # Update download indicators
        self.download_value.setText(self.format_speed(download_speed))
        self.download_total.setText(self.format_total(bytes_recv))
        self.graph.download_data.append(download_speed / 1024) 