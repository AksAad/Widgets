from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGraphicsBlurEffect, QGraphicsDropShadowEffect, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt, QTimer, QRectF, QPointF, QDateTime
from PyQt6.QtGui import QPainter, QColor, QFont, QPainterPath, QBrush, QLinearGradient, QPen
from PyQt6.QtWidgets import QApplication

class BaseWidget(QWidget):
    def __init__(self, size=(300, 200)):
        super().__init__()
        
        # Window setup
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(*size)
        
        # Movement tracking
        self.dragging = False
        self.drag_start = None
        self.start_pos = None
        self.velocity = QPointF(0, 0)
        self.last_pos = None
        self.last_time = None
        self.frame_time = 1000/120  # Target 120 FPS
        
        # Animation setup
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update_position)
        self.animation_timer.setInterval(int(self.frame_time))
        
        # Damping and edge bounce factors
        self.damping = 0.95  # Velocity damping
        self.bounce_damping = 0.5  # Edge bounce damping
        self.min_velocity = 0.1  # Minimum velocity before stopping
        self.edge_margin = 20  # Pixels from screen edge for snapping
        
        # Layout setup
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Title bar
        self.title_label = QLabel("Widget")
        self.title_label.setStyleSheet("""
            QLabel {
                color: rgba(180, 180, 180, 0.8);  /* Relaxed gray color */
                background: transparent;
                padding: 4px;
                font-family: Consolas;
            }
        """)
        self.layout.addWidget(self.title_label)
        
        # Get screen dimensions
        self.update_screen_bounds()
        
        # Define theme colors
        self.colors = {
            'background': QColor(20, 20, 25, 230),  # Slightly blue-black
            'grid': QColor(40, 45, 50, 15),  # Subtle dark grid
            'border': QColor(60, 65, 70, 40),  # Relaxed border
            'text': QColor(180, 180, 180, 230),  # Soft gray text
            'accent': {
                'green': QColor(40, 180, 120),  # Relaxed green
                'blue': QColor(65, 105, 170),   # Relaxed blue
                'purple': QColor(120, 90, 170),  # Relaxed purple
                'red': QColor(220, 70, 70)      # Keep red as is
            }
        }
    
    def update_screen_bounds(self):
        screen = QApplication.primaryScreen().geometry()
        self.screen_bounds = QRectF(
            screen.x(),
            screen.y(),
            screen.width() - self.width(),
            screen.height() - self.height()
        )
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_start = event.pos()
            self.start_pos = self.pos()
            self.velocity = QPointF(0, 0)
            self.last_pos = self.pos()
            self.last_time = QDateTime.currentMSecsSinceEpoch()
            self.animation_timer.stop()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
    
    def mouseMoveEvent(self, event):
        if self.dragging:
            current_pos = self.mapToGlobal(event.pos() - self.drag_start)
            
            # Calculate velocity
            current_time = QDateTime.currentMSecsSinceEpoch()
            dt = (current_time - self.last_time) / 1000.0  # Convert to seconds
            if dt > 0:
                self.velocity = QPointF(
                    (current_pos.x() - self.last_pos.x()) / dt,
                    (current_pos.y() - self.last_pos.y()) / dt
                )
            
            # Update position
            self.move(current_pos.x(), current_pos.y())
            
            # Store last position and time
            self.last_pos = QPointF(current_pos)
            self.last_time = current_time
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.dragging:
            self.dragging = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            
            # Start animation if velocity is significant
            if abs(self.velocity.x()) > self.min_velocity or abs(self.velocity.y()) > self.min_velocity:
                self.animation_timer.start()
    
    def update_position(self):
        if self.dragging:
            self.animation_timer.stop()
            return
        
        # Update position based on velocity
        new_pos = QPointF(self.pos()) + self.velocity * (self.frame_time / 1000.0)
        
        # Check screen bounds
        if new_pos.x() < self.screen_bounds.left() + self.edge_margin:
            new_pos.setX(self.screen_bounds.left())
            self.velocity.setX(-self.velocity.x() * self.bounce_damping)
        elif new_pos.x() > self.screen_bounds.right() - self.edge_margin:
            new_pos.setX(self.screen_bounds.right())
            self.velocity.setX(-self.velocity.x() * self.bounce_damping)
            
        if new_pos.y() < self.screen_bounds.top() + self.edge_margin:
            new_pos.setY(self.screen_bounds.top())
            self.velocity.setY(-self.velocity.y() * self.bounce_damping)
        elif new_pos.y() > self.screen_bounds.bottom() - self.edge_margin:
            new_pos.setY(self.screen_bounds.bottom())
            self.velocity.setY(-self.velocity.y() * self.bounce_damping)
        
        # Apply damping
        self.velocity *= self.damping
        
        # Stop animation if velocity is too low
        if abs(self.velocity.x()) < self.min_velocity and abs(self.velocity.y()) < self.min_velocity:
            self.animation_timer.stop()
            self.velocity = QPointF(0, 0)
            
            # Snap to edges if close
            if abs(new_pos.x() - self.screen_bounds.left()) < self.edge_margin:
                new_pos.setX(self.screen_bounds.left())
            elif abs(new_pos.x() - self.screen_bounds.right()) < self.edge_margin:
                new_pos.setX(self.screen_bounds.right())
                
            if abs(new_pos.y() - self.screen_bounds.top()) < self.edge_margin:
                new_pos.setY(self.screen_bounds.top())
            elif abs(new_pos.y() - self.screen_bounds.bottom()) < self.edge_margin:
                new_pos.setY(self.screen_bounds.bottom())
        
        # Update widget position
        self.move(int(new_pos.x()), int(new_pos.y()))
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Create background path
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 12, 12)
        
        # Draw main background
        painter.fillPath(path, self.colors['background'])
        
        # Add subtle gradient overlay
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(255, 255, 255, 5))
        gradient.setColorAt(1, QColor(0, 0, 0, 10))
        painter.fillPath(path, gradient)
        
        # Add subtle grid pattern
        painter.setPen(QPen(self.colors['grid'], 1, Qt.PenStyle.SolidLine))
        grid_spacing = 15
        for i in range(0, self.height(), grid_spacing):
            painter.drawLine(0, i, self.width(), i)
        for i in range(0, self.width(), grid_spacing):
            painter.drawLine(i, 0, i, self.height())
        
        # Draw border
        border_path = QPainterPath()
        border_path.addRoundedRect(1, 1, self.width()-2, self.height()-2, 12, 12)
        painter.strokePath(border_path, QPen(self.colors['border'], 1.5))
    
    def update_data(self):
        """Override this method in child classes to update widget data"""
        pass 