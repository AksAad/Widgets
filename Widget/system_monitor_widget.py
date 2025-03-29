from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QWidget
from PyQt6.QtCore import Qt, QTimer, QRectF, QPointF
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QPainterPath, QLinearGradient
from base_widget import BaseWidget
import psutil
from collections import deque

class GraphWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(280, 60)
        self.cpu_data = [0] * 50
        self.memory_data = [0] * 50
        
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
        
        # Draw CPU graph with smooth curve
        self.draw_graph(painter, self.cpu_data, QColor(40, 120, 180, 180))  # Relaxed blue for CPU
        
        # Draw memory graph with smooth curve
        self.draw_graph(painter, self.memory_data, QColor(120, 40, 180, 180))  # Relaxed purple for memory
    
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

class SystemMonitorWidget(BaseWidget):
    def __init__(self):
        super().__init__(size=(300, 120))
        self.title_label.setText("System Monitor")
        
        # Create main content layout
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(12, 8, 12, 12)
        content_layout.setSpacing(8)
        
        # System stats container
        stats_container = QWidget()
        stats_layout = QVBoxLayout(stats_container)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(4)
        
        # CPU stats
        cpu_layout = QHBoxLayout()
        cpu_layout.setSpacing(4)
        
        cpu_label = QLabel("CPU")
        cpu_label.setStyleSheet("color: rgba(180, 180, 180, 0.9);")
        cpu_layout.addWidget(cpu_label)
        
        self.cpu_value = QLabel("0%")
        self.cpu_value.setStyleSheet("color: rgba(40, 120, 180, 0.9);")  # Relaxed blue for CPU
        cpu_layout.addWidget(self.cpu_value, alignment=Qt.AlignmentFlag.AlignRight)
        
        stats_layout.addLayout(cpu_layout)
        
        # Memory stats
        memory_layout = QHBoxLayout()
        memory_layout.setSpacing(4)
        
        memory_label = QLabel("Memory")
        memory_label.setStyleSheet("color: rgba(180, 180, 180, 0.9);")
        memory_layout.addWidget(memory_label)
        
        self.memory_value = QLabel("0%")
        self.memory_value.setStyleSheet("color: rgba(120, 40, 180, 0.9);")  # Relaxed purple for memory
        memory_layout.addWidget(self.memory_value, alignment=Qt.AlignmentFlag.AlignRight)
        
        stats_layout.addLayout(memory_layout)
        
        content_layout.addWidget(stats_container)
        
        # System monitor graph
        self.graph = GraphWidget()
        content_layout.addWidget(self.graph)
        
        self.layout.addLayout(content_layout)
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_data)
        self.update_timer.start(1000)  # Update every second
        
        # Initial update
        self.update_data()
    
    def update_data(self):
        # Get CPU usage
        cpu_percent = psutil.cpu_percent()
        self.cpu_value.setText(f"{cpu_percent:.1f}%")
        self.graph.cpu_data.append(cpu_percent / 100)
        self.graph.cpu_data.pop(0)
        
        # Get memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        self.memory_value.setText(f"{memory_percent:.1f}%")
        self.graph.memory_data.append(memory_percent / 100)
        self.graph.memory_data.pop(0)
        
        # Update graph
        self.graph.update() 