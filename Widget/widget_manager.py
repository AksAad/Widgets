import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QPoint
from system_monitor_widget import SystemMonitorWidget
from network_widget import NetworkWidget
from battery_widget import BatteryWidget
from music_widget import MusicWidget

class WidgetManager:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.widgets = []
        self.screen = self.app.primaryScreen().geometry()
        self._widget_spacing = 20  # Space between widgets
        
    def add_widget(self, widget_class, position='top-right'):
        """Add a new widget at the specified position"""
        widget = widget_class()
        
        # Calculate position
        if position == 'top-right':
            x = self.screen.width() - widget.width() - self._widget_spacing
            y = self._widget_spacing
        elif position == 'top-left':
            x = self._widget_spacing
            y = self._widget_spacing
        elif position == 'bottom-right':
            x = self.screen.width() - widget.width() - self._widget_spacing
            y = self.screen.height() - widget.height() - self._widget_spacing
        elif position == 'bottom-left':
            x = self._widget_spacing
            y = self.screen.height() - widget.height() - self._widget_spacing
        elif position == 'center-top':
            x = (self.screen.width() - widget.width()) // 2
            y = self._widget_spacing
        elif position == 'center-bottom':
            x = (self.screen.width() - widget.width()) // 2
            y = self.screen.height() - widget.height() - self._widget_spacing
        else:  # Custom position as QPoint
            x, y = position.x(), position.y()
            
        widget.move(x, y)
        widget.show()
        self.widgets.append(widget)
        return widget
    
    def run(self):
        """Start the widget manager"""
        # Add system monitor widget at the top right
        self.add_widget(SystemMonitorWidget, 'top-right')
        
        # Add network widget at the top left
        self.add_widget(NetworkWidget, 'top-left')
        
        # Add battery widget at the center right
        battery_pos = QPoint(
            self.screen.width() - 200,
            (self.screen.height() - 160) // 2
        )
        self.add_widget(BatteryWidget, battery_pos)
        
        # Add music widget at the bottom center
        music_pos = QPoint(
            (self.screen.width() - 380) // 2,  # Center horizontally
            self.screen.height() - 130  # Position from bottom
        )
        self.add_widget(MusicWidget, music_pos)
        
        return self.app.exec()

def main():
    # Set application name and organization
    QApplication.setApplicationName("Desktop Widgets")
    QApplication.setOrganizationName("Widget System")
    
    manager = WidgetManager()
    sys.exit(manager.run())

if __name__ == "__main__":
    main() 