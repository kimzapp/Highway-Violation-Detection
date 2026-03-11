"""
GUI Styles Module
Định nghĩa các styles chung cho ứng dụng
"""

# Color palette
COLORS = {
    'primary': '#2196F3',
    'primary_dark': '#1976D2',
    'primary_light': '#BBDEFB',
    
    'success': '#4CAF50',
    'success_dark': '#45a049',
    
    'warning': '#FF9800',
    'warning_dark': '#F57C00',
    
    'error': '#f44336',
    'error_dark': '#d32f2f',
    
    'background': '#ffffff',
    'background_dark': '#f5f5f5',
    'surface': '#ffffff',
    
    'text_primary': '#212121',
    'text_secondary': '#666666',
    'text_disabled': '#9e9e9e',
    
    'border': '#e0e0e0',
    'divider': '#bdbdbd',
}

# Global stylesheet
GLOBAL_STYLESHEET = """
    QMainWindow {
        background-color: #f5f5f5;
    }
    
    QWidget {
        font-family: 'Segoe UI', 'Arial', sans-serif;
        font-size: 13px;
    }
    
    QGroupBox {
        font-weight: bold;
        border: 1px solid #ddd;
        border-radius: 5px;
        margin-top: 10px;
        padding-top: 10px;
    }
    
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px;
    }
    
    QLineEdit {
        padding: 8px;
        border: 1px solid #ddd;
        border-radius: 4px;
        background-color: white;
    }
    
    QLineEdit:focus {
        border: 2px solid #2196F3;
    }
    
    QComboBox {
        padding: 8px;
        border: 1px solid #ddd;
        border-radius: 4px;
        background-color: white;
    }
    
    QComboBox:focus {
        border: 2px solid #2196F3;
    }
    
    QComboBox::drop-down {
        border: none;
        padding-right: 10px;
    }
    
    QSpinBox, QDoubleSpinBox {
        padding: 8px;
        border: 1px solid #ddd;
        border-radius: 4px;
        background-color: white;
    }
    
    QSpinBox:focus, QDoubleSpinBox:focus {
        border: 2px solid #2196F3;
    }
    
    QPushButton {
        padding: 10px 20px;
        border: none;
        border-radius: 4px;
        background-color: #e0e0e0;
        color: #333;
    }
    
    QPushButton:hover {
        background-color: #d0d0d0;
    }
    
    QPushButton:pressed {
        background-color: #c0c0c0;
    }
    
    QPushButton:disabled {
        background-color: #f0f0f0;
        color: #999;
    }
    
    QCheckBox {
        spacing: 8px;
    }
    
    QCheckBox::indicator {
        width: 18px;
        height: 18px;
    }
    
    QRadioButton {
        spacing: 8px;
    }
    
    QRadioButton::indicator {
        width: 18px;
        height: 18px;
    }
    
    QSlider::groove:horizontal {
        border: 1px solid #bbb;
        background: #e0e0e0;
        height: 8px;
        border-radius: 4px;
    }
    
    QSlider::handle:horizontal {
        background: #2196F3;
        border: 1px solid #1976D2;
        width: 14px;
        margin: -4px 0;
        border-radius: 7px;
    }
    
    QSlider::sub-page:horizontal {
        background: #2196F3;
        border-radius: 4px;
    }
    
    QTabWidget::pane {
        border: 1px solid #ddd;
        border-radius: 5px;
        background-color: white;
    }
    
    QTabBar::tab {
        background-color: #f0f0f0;
        padding: 10px 20px;
        margin-right: 2px;
        border-top-left-radius: 5px;
        border-top-right-radius: 5px;
    }
    
    QTabBar::tab:selected {
        background-color: white;
        border-bottom: 2px solid #2196F3;
    }
    
    QTabBar::tab:hover {
        background-color: #e8e8e8;
    }
    
    QScrollArea {
        border: none;
        background-color: transparent;
    }
    
    QListWidget {
        border: 1px solid #ddd;
        border-radius: 4px;
        background-color: white;
    }
    
    QListWidget::item {
        padding: 8px;
    }
    
    QListWidget::item:selected {
        background-color: #e3f2fd;
        color: #1976D2;
    }
    
    QListWidget::item:hover {
        background-color: #f5f5f5;
    }
    
    QProgressBar {
        border: 1px solid #ddd;
        border-radius: 5px;
        text-align: center;
        background-color: #f0f0f0;
    }
    
    QProgressBar::chunk {
        background-color: #4CAF50;
        border-radius: 4px;
    }
    
    QStatusBar {
        background-color: #f5f5f5;
        border-top: 1px solid #ddd;
    }
    
    QToolTip {
        background-color: #333;
        color: white;
        border: none;
        padding: 5px 10px;
        border-radius: 3px;
    }
"""

# Button styles
BUTTON_PRIMARY = """
    QPushButton {
        background-color: #2196F3;
        color: white;
        border: none;
        border-radius: 5px;
        font-weight: bold;
        padding: 12px 24px;
    }
    QPushButton:hover {
        background-color: #1976D2;
    }
    QPushButton:pressed {
        background-color: #1565C0;
    }
    QPushButton:disabled {
        background-color: #BDBDBD;
        color: #757575;
    }
"""

BUTTON_SUCCESS = """
    QPushButton {
        background-color: #4CAF50;
        color: white;
        border: none;
        border-radius: 5px;
        font-weight: bold;
        padding: 12px 24px;
    }
    QPushButton:hover {
        background-color: #45a049;
    }
    QPushButton:pressed {
        background-color: #388E3C;
    }
    QPushButton:disabled {
        background-color: #BDBDBD;
        color: #757575;
    }
"""

BUTTON_DANGER = """
    QPushButton {
        background-color: #f44336;
        color: white;
        border: none;
        border-radius: 5px;
        font-weight: bold;
        padding: 12px 24px;
    }
    QPushButton:hover {
        background-color: #d32f2f;
    }
    QPushButton:pressed {
        background-color: #c62828;
    }
    QPushButton:disabled {
        background-color: #BDBDBD;
        color: #757575;
    }
"""

BUTTON_OUTLINE = """
    QPushButton {
        background-color: transparent;
        color: #2196F3;
        border: 2px solid #2196F3;
        border-radius: 5px;
        font-weight: bold;
        padding: 10px 22px;
    }
    QPushButton:hover {
        background-color: #e3f2fd;
    }
    QPushButton:pressed {
        background-color: #BBDEFB;
    }
    QPushButton:disabled {
        border-color: #BDBDBD;
        color: #757575;
    }
"""


def apply_stylesheet(app):
    """Áp dụng stylesheet toàn cục cho ứng dụng"""
    app.setStyleSheet(GLOBAL_STYLESHEET)
