Windows Desktop Widgets
A customizable widget system for Windows that displays widgets on your desktop with real-time updates.

Features
Semi-transparent, always-on-top widgets
Real-time updates
Modular design for easy widget creation
Sample system monitor widget included
Installation
Install Python 3.8 or higher
Install the required dependencies:
pip install -r requirements.txt
Usage
Run the widget manager:
python widget_manager.py
The system monitor widget will appear in the top-right corner of your screen.
Creating New Widgets
To create a new widget:

Create a new Python file (e.g., my_widget.py)
Inherit from BaseWidget:
from base_widget import BaseWidget

class MyWidget(BaseWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.title_label.setText("My Widget")
        self.setFixedSize(200, 100)
    
    def update_data(self):
        # Update your widget's data here
        self.content_label.setText("Your content here")
Add your widget to the WidgetManager class in widget_manager.py
Widget Properties
All widgets are frameless and stay on top of other windows
Semi-transparent black background
White text
Auto-updates every second
Customizable size and position
