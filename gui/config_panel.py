"""
Configuration Panel Widget
Widget cho phép người dùng cấu hình các tham số của hệ thống
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
import os

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QPushButton, QLineEdit, QComboBox,
    QSpinBox, QDoubleSpinBox, QCheckBox, QSlider,
    QFileDialog, QScrollArea, QFrame, QTabWidget,
    QGridLayout, QSizePolicy, QMessageBox
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont


@dataclass 
class ProcessingConfig:
    """Cấu hình xử lý video"""
    # Model settings
    model_path: str = "yolov8n.pt"
    device: str = "cpu"
    img_size: int = 640
    
    # Detection settings
    conf_threshold: float = 0.25
    iou_threshold: float = 0.5
    classes: List[int] = field(default_factory=list)  # Empty = detect all classes (compatible with custom models)
    
    # Tracker settings  
    max_age: int = 90
    trace_length: int = 50
    
    # Visualization settings
    show_boxes: bool = True
    show_labels: bool = True
    show_traces: bool = True
    
    # BEV settings
    enable_bev: bool = True
    bev_width: int = 400
    bev_height: int = 600
    bev_method: str = "ipm"
    camera_height: float = 1.5
    
    # Output settings
    output_path: str = "output.mp4"
    save_video: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'model_path': self.model_path,
            'device': self.device,
            'img_size': self.img_size,
            'conf_threshold': self.conf_threshold,
            'iou_threshold': self.iou_threshold,
            'classes': self.classes,
            'max_age': self.max_age,
            'trace_length': self.trace_length,
            'show_boxes': self.show_boxes,
            'show_labels': self.show_labels,
            'show_traces': self.show_traces,
            'enable_bev': self.enable_bev,
            'bev_width': self.bev_width,
            'bev_height': self.bev_height,
            'bev_method': self.bev_method,
            'camera_height': self.camera_height,
            'output_path': self.output_path,
            'save_video': self.save_video
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessingConfig':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# COCO class names cho vehicle classes
VEHICLE_CLASSES = {
    2: "Car",
    3: "Motorcycle", 
    5: "Bus",
    7: "Truck",
    0: "Person",
    1: "Bicycle"
}


class ConfigPanel(QWidget):
    """
    Panel cấu hình các tham số xử lý
    
    Signals:
        config_changed: Phát ra khi cấu hình thay đổi
        config_confirmed: Phát ra khi người dùng xác nhận cấu hình
    """
    
    config_changed = pyqtSignal(object)  # ProcessingConfig
    config_confirmed = pyqtSignal(object)  # ProcessingConfig
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._config = ProcessingConfig()
        self._setup_ui()
        self._connect_signals()
        self._load_config_to_ui()
        
    def _setup_ui(self):
        """Thiết lập giao diện"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Title
        title_label = QLabel("Cấu Hình Tham Số")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Create scroll area for settings
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(15)
        
        # Tab widget for organized settings
        tab_widget = QTabWidget()
        
        # Model tab
        model_tab = self._create_model_tab()
        tab_widget.addTab(model_tab, "🤖 Model")
        
        # Detection tab
        detection_tab = self._create_detection_tab()
        tab_widget.addTab(detection_tab, "🎯 Detection")
        
        # Tracking tab
        tracking_tab = self._create_tracking_tab()
        tab_widget.addTab(tracking_tab, "📍 Tracking")
        
        # Visualization tab
        viz_tab = self._create_visualization_tab()
        tab_widget.addTab(viz_tab, "👁️ Hiển thị")
        
        # Output tab
        output_tab = self._create_output_tab()
        tab_widget.addTab(output_tab, "💾 Output")
        
        scroll_layout.addWidget(tab_widget)
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area, 1)
        
        # Button row
        button_layout = QHBoxLayout()
        
        self._reset_btn = QPushButton("🔄 Reset Mặc Định")
        self._reset_btn.setMinimumHeight(40)
        button_layout.addWidget(self._reset_btn)
        
        button_layout.addStretch()
        
        self._back_btn = QPushButton("← Quay Lại")
        self._back_btn.setMinimumHeight(40)
        button_layout.addWidget(self._back_btn)
        
        self._confirm_btn = QPushButton("Tiếp Tục →")
        self._confirm_btn.setMinimumHeight(40)
        self._confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 13px;
                font-weight: bold;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        button_layout.addWidget(self._confirm_btn)
        
        main_layout.addLayout(button_layout)
        
    def _create_model_tab(self) -> QWidget:
        """Tạo tab cấu hình model"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Model file selection
        model_group = QGroupBox("Model File")
        model_layout = QGridLayout(model_group)
        
        model_layout.addWidget(QLabel("Model:"), 0, 0)
        
        self._model_path_edit = QLineEdit()
        self._model_path_edit.setPlaceholderText("Đường dẫn đến file model (.pt, .onnx)")
        self._model_path_edit.setMinimumHeight(35)
        model_layout.addWidget(self._model_path_edit, 0, 1)
        
        self._browse_model_btn = QPushButton("Duyệt...")
        self._browse_model_btn.setMinimumHeight(35)
        model_layout.addWidget(self._browse_model_btn, 0, 2)
        
        # Preset models
        model_layout.addWidget(QLabel("Preset:"), 1, 0)
        self._model_preset_combo = QComboBox()
        self._model_preset_combo.addItem("YOLOv8n (Nhanh)", "yolov8n.pt")
        self._model_preset_combo.addItem("YOLOv8s (Cân bằng)", "yolov8s.pt")
        self._model_preset_combo.addItem("YOLOv8m (Chính xác)", "yolov8m.pt")
        self._model_preset_combo.addItem("Custom Model", "")
        self._model_preset_combo.setMinimumHeight(35)
        model_layout.addWidget(self._model_preset_combo, 1, 1, 1, 2)
        
        layout.addWidget(model_group)
        
        # Device selection
        device_group = QGroupBox("Thiết Bị Xử Lý")
        device_layout = QHBoxLayout(device_group)
        
        device_layout.addWidget(QLabel("Device:"))
        
        self._device_combo = QComboBox()
        self._device_combo.addItem("CPU", "cpu")
        self._device_combo.addItem("GPU (CUDA)", "cuda")
        self._device_combo.addItem("GPU 0", "cuda:0")
        self._device_combo.addItem("GPU 1", "cuda:1")
        self._device_combo.setMinimumHeight(35)
        device_layout.addWidget(self._device_combo)
        
        self._detect_gpu_btn = QPushButton("Kiểm tra GPU")
        self._detect_gpu_btn.setMinimumHeight(35)
        device_layout.addWidget(self._detect_gpu_btn)
        
        self._gpu_info_label = QLabel("")
        self._gpu_info_label.setStyleSheet("color: #666666;")
        device_layout.addWidget(self._gpu_info_label)
        
        device_layout.addStretch()
        
        layout.addWidget(device_group)
        
        # Image size
        size_group = QGroupBox("Kích Thước Input")
        size_layout = QHBoxLayout(size_group)
        
        size_layout.addWidget(QLabel("Image Size:"))
        
        self._img_size_combo = QComboBox()
        self._img_size_combo.addItem("320 (Nhanh)", 320)
        self._img_size_combo.addItem("416", 416)
        self._img_size_combo.addItem("512", 512)
        self._img_size_combo.addItem("640 (Mặc định)", 640)
        self._img_size_combo.addItem("832", 832)
        self._img_size_combo.addItem("1024 (Chính xác)", 1024)
        self._img_size_combo.setCurrentIndex(3)  # Default 640
        self._img_size_combo.setMinimumHeight(35)
        size_layout.addWidget(self._img_size_combo)
        
        size_layout.addStretch()
        
        layout.addWidget(size_group)
        
        layout.addStretch()
        
        return widget
        
    def _create_detection_tab(self) -> QWidget:
        """Tạo tab cấu hình detection"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Thresholds
        thresh_group = QGroupBox("Ngưỡng Phát Hiện")
        thresh_layout = QGridLayout(thresh_group)
        
        # Confidence threshold
        thresh_layout.addWidget(QLabel("Confidence:"), 0, 0)
        
        self._conf_slider = QSlider(Qt.Horizontal)
        self._conf_slider.setRange(5, 95)
        self._conf_slider.setValue(25)
        thresh_layout.addWidget(self._conf_slider, 0, 1)
        
        self._conf_spin = QDoubleSpinBox()
        self._conf_spin.setRange(0.05, 0.95)
        self._conf_spin.setSingleStep(0.05)
        self._conf_spin.setValue(0.25)
        self._conf_spin.setMinimumWidth(80)
        thresh_layout.addWidget(self._conf_spin, 0, 2)
        
        # IOU threshold
        thresh_layout.addWidget(QLabel("IOU:"), 1, 0)
        
        self._iou_slider = QSlider(Qt.Horizontal)
        self._iou_slider.setRange(10, 90)
        self._iou_slider.setValue(50)
        thresh_layout.addWidget(self._iou_slider, 1, 1)
        
        self._iou_spin = QDoubleSpinBox()
        self._iou_spin.setRange(0.1, 0.9)
        self._iou_spin.setSingleStep(0.05)
        self._iou_spin.setValue(0.5)
        self._iou_spin.setMinimumWidth(80)
        thresh_layout.addWidget(self._iou_spin, 1, 2)
        
        layout.addWidget(thresh_group)
        
        # Class selection
        class_group = QGroupBox("Loại Đối Tượng Phát Hiện")
        class_layout = QVBoxLayout(class_group)
        
        class_hint = QLabel("Chọn các loại đối tượng cần theo dõi:")
        class_hint.setStyleSheet("color: #666666;")
        class_layout.addWidget(class_hint)
        
        self._class_checkboxes = {}
        class_grid = QGridLayout()
        
        for i, (class_id, class_name) in enumerate(VEHICLE_CLASSES.items()):
            checkbox = QCheckBox(f"{class_name} (ID: {class_id})")
            checkbox.setChecked(True)  # Default: detect all classes (compatible with custom models)
            self._class_checkboxes[class_id] = checkbox
            class_grid.addWidget(checkbox, i // 3, i % 3)
            
        class_layout.addLayout(class_grid)
        
        # Quick select buttons
        quick_layout = QHBoxLayout()
        
        self._select_vehicles_btn = QPushButton("Chọn Xe Cộ")
        self._select_vehicles_btn.clicked.connect(self._select_vehicle_classes)
        quick_layout.addWidget(self._select_vehicles_btn)
        
        self._select_all_btn = QPushButton("Chọn Tất Cả")
        self._select_all_btn.clicked.connect(self._select_all_classes)
        quick_layout.addWidget(self._select_all_btn)
        
        self._select_none_btn = QPushButton("Bỏ Chọn")
        self._select_none_btn.clicked.connect(self._clear_all_classes)
        quick_layout.addWidget(self._select_none_btn)
        
        quick_layout.addStretch()
        class_layout.addLayout(quick_layout)
        
        layout.addWidget(class_group)
        
        layout.addStretch()
        
        return widget
        
    def _create_tracking_tab(self) -> QWidget:
        """Tạo tab cấu hình tracking"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Tracker settings
        tracker_group = QGroupBox("ByteTrack Settings")
        tracker_layout = QGridLayout(tracker_group)
        
        # Max age
        tracker_layout.addWidget(QLabel("Max Age (frames):"), 0, 0)
        self._max_age_spin = QSpinBox()
        self._max_age_spin.setRange(10, 300)
        self._max_age_spin.setValue(90)
        self._max_age_spin.setMinimumHeight(35)
        self._max_age_spin.setToolTip("Số frame tối đa giữ track khi không có detection")
        tracker_layout.addWidget(self._max_age_spin, 0, 1)
        
        # Trace length
        tracker_layout.addWidget(QLabel("Trace Length:"), 1, 0)
        self._trace_length_spin = QSpinBox()
        self._trace_length_spin.setRange(10, 200)
        self._trace_length_spin.setValue(50)
        self._trace_length_spin.setMinimumHeight(35)
        self._trace_length_spin.setToolTip("Độ dài của vệt theo dõi hiển thị")
        tracker_layout.addWidget(self._trace_length_spin, 1, 1)
        
        tracker_layout.setColumnStretch(2, 1)
        
        layout.addWidget(tracker_group)
        
        # Info box
        info_label = QLabel(
            "💡 <b>Gợi ý:</b><br>"
            "• <b>Max Age</b>: Tăng nếu xe bị che khuất lâu<br>"
            "• <b>Trace Length</b>: Tăng để thấy quỹ đạo dài hơn"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("""
            QLabel {
                background-color: #e3f2fd;
                padding: 15px;
                border-radius: 5px;
            }
        """)
        layout.addWidget(info_label)
        
        layout.addStretch()
        
        return widget
        
    def _create_visualization_tab(self) -> QWidget:
        """Tạo tab cấu hình hiển thị"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Display options
        display_group = QGroupBox("Tùy Chọn Hiển Thị")
        display_layout = QVBoxLayout(display_group)
        
        self._show_boxes_check = QCheckBox("Hiển thị bounding boxes")
        self._show_boxes_check.setChecked(True)
        display_layout.addWidget(self._show_boxes_check)
        
        self._show_labels_check = QCheckBox("Hiển thị nhãn (class, ID)")
        self._show_labels_check.setChecked(True)
        display_layout.addWidget(self._show_labels_check)
        
        self._show_traces_check = QCheckBox("Hiển thị vệt di chuyển")
        self._show_traces_check.setChecked(True)
        display_layout.addWidget(self._show_traces_check)
        
        layout.addWidget(display_group)
        
        # BEV options
        bev_group = QGroupBox("Bird's Eye View (BEV)")
        bev_layout = QGridLayout(bev_group)
        
        self._enable_bev_check = QCheckBox("Bật Bird's Eye View")
        self._enable_bev_check.setChecked(True)
        bev_layout.addWidget(self._enable_bev_check, 0, 0, 1, 2)
        
        bev_layout.addWidget(QLabel("Phương pháp:"), 1, 0)
        self._bev_method_combo = QComboBox()
        self._bev_method_combo.addItem("IPM (Inverse Perspective Mapping)", "ipm")
        self._bev_method_combo.addItem("Homography", "homography")
        self._bev_method_combo.setMinimumHeight(35)
        bev_layout.addWidget(self._bev_method_combo, 1, 1)
        
        bev_layout.addWidget(QLabel("Chiều rộng BEV:"), 2, 0)
        self._bev_width_spin = QSpinBox()
        self._bev_width_spin.setRange(200, 800)
        self._bev_width_spin.setValue(400)
        self._bev_width_spin.setMinimumHeight(35)
        bev_layout.addWidget(self._bev_width_spin, 2, 1)
        
        bev_layout.addWidget(QLabel("Chiều cao BEV:"), 3, 0)
        self._bev_height_spin = QSpinBox()
        self._bev_height_spin.setRange(300, 1000)
        self._bev_height_spin.setValue(600)
        self._bev_height_spin.setMinimumHeight(35)
        bev_layout.addWidget(self._bev_height_spin, 3, 1)
        
        bev_layout.addWidget(QLabel("Chiều cao camera (m):"), 4, 0)
        self._camera_height_spin = QDoubleSpinBox()
        self._camera_height_spin.setRange(0.5, 10.0)
        self._camera_height_spin.setValue(1.5)
        self._camera_height_spin.setSingleStep(0.1)
        self._camera_height_spin.setMinimumHeight(35)
        self._camera_height_spin.setToolTip("Chiều cao camera so với mặt đường (cho IPM)")
        bev_layout.addWidget(self._camera_height_spin, 4, 1)
        
        layout.addWidget(bev_group)
        
        layout.addStretch()
        
        return widget
        
    def _create_output_tab(self) -> QWidget:
        """Tạo tab cấu hình output"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Output settings
        output_group = QGroupBox("Cấu Hình Output")
        output_layout = QGridLayout(output_group)
        
        self._save_video_check = QCheckBox("Lưu video output")
        self._save_video_check.setChecked(True)
        output_layout.addWidget(self._save_video_check, 0, 0, 1, 3)
        
        output_layout.addWidget(QLabel("Output path:"), 1, 0)
        
        self._output_path_edit = QLineEdit()
        self._output_path_edit.setPlaceholderText("Đường dẫn lưu video output")
        self._output_path_edit.setText("output.mp4")
        self._output_path_edit.setMinimumHeight(35)
        output_layout.addWidget(self._output_path_edit, 1, 1)
        
        self._browse_output_btn = QPushButton("Duyệt...")
        self._browse_output_btn.setMinimumHeight(35)
        output_layout.addWidget(self._browse_output_btn, 1, 2)
        
        layout.addWidget(output_group)
        
        layout.addStretch()
        
        return widget
        
    def _connect_signals(self):
        """Kết nối các signals"""
        # Model
        self._browse_model_btn.clicked.connect(self._browse_model_file)
        self._model_preset_combo.currentIndexChanged.connect(self._on_model_preset_changed)
        self._detect_gpu_btn.clicked.connect(self._detect_gpu)
        
        # Threshold sliders and spinboxes
        self._conf_slider.valueChanged.connect(lambda v: self._conf_spin.setValue(v / 100))
        self._conf_spin.valueChanged.connect(lambda v: self._conf_slider.setValue(int(v * 100)))
        
        self._iou_slider.valueChanged.connect(lambda v: self._iou_spin.setValue(v / 100))
        self._iou_spin.valueChanged.connect(lambda v: self._iou_slider.setValue(int(v * 100)))
        
        # Output
        self._browse_output_btn.clicked.connect(self._browse_output_file)
        
        # Buttons
        self._reset_btn.clicked.connect(self._reset_to_defaults)
        self._confirm_btn.clicked.connect(self._on_confirm)
        
    def _browse_model_file(self):
        """Mở dialog chọn model file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Chọn Model File",
            "",
            "Model Files (*.pt *.pth *.onnx);;All Files (*.*)"
        )
        if file_path:
            self._model_path_edit.setText(file_path)
            self._model_preset_combo.setCurrentIndex(
                self._model_preset_combo.count() - 1  # Select "Custom Model"
            )
            
    def _on_model_preset_changed(self, index: int):
        """Xử lý khi chọn preset model"""
        model_path = self._model_preset_combo.currentData()
        if model_path:
            self._model_path_edit.setText(model_path)
            
    def _detect_gpu(self):
        try:
            import torch

            if torch.cuda.is_available():
                prop = torch.cuda.get_device_properties(0)
                name = prop.name
                mem = prop.total_memory / 1e9
                text = f"✅ {name} ({mem:.1f}GB)"
                color = "#4CAF50"
            else:
                text = "⚠️ Đang chạy bằng CPU"
                color = "#ff9800"

        except Exception:
            text = "❌ Không thể kiểm tra GPU"
            color = "#f44336"

        self._gpu_info_label.setText(text)
        self._gpu_info_label.setStyleSheet(f"color: {color};")
            
    def _select_vehicle_classes(self):
        """Chọn các class xe cộ"""
        vehicle_ids = [2, 3, 5, 7]  # car, motorcycle, bus, truck
        for class_id, checkbox in self._class_checkboxes.items():
            checkbox.setChecked(class_id in vehicle_ids)
            
    def _select_all_classes(self):
        """Chọn tất cả classes"""
        for checkbox in self._class_checkboxes.values():
            checkbox.setChecked(True)
            
    def _clear_all_classes(self):
        """Bỏ chọn tất cả classes"""
        for checkbox in self._class_checkboxes.values():
            checkbox.setChecked(False)
            
    def _browse_output_file(self):
        """Mở dialog chọn output file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Chọn Đường Dẫn Output",
            "output.mp4",
            "Video Files (*.mp4 *.avi);;All Files (*.*)"
        )
        if file_path:
            self._output_path_edit.setText(file_path)
            
    def _reset_to_defaults(self):
        """Reset về giá trị mặc định"""
        reply = QMessageBox.question(
            self,
            "Xác Nhận Reset",
            "Bạn có chắc muốn reset tất cả cấu hình về mặc định?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self._config = ProcessingConfig()
            self._load_config_to_ui()
            
    def _load_config_to_ui(self):
        """Load config vào UI"""
        # Model
        self._model_path_edit.setText(self._config.model_path)
        
        # Device
        device_index = self._device_combo.findData(self._config.device)
        if device_index >= 0:
            self._device_combo.setCurrentIndex(device_index)
            
        # Image size
        size_index = self._img_size_combo.findData(self._config.img_size)
        if size_index >= 0:
            self._img_size_combo.setCurrentIndex(size_index)
            
        # Thresholds
        self._conf_spin.setValue(self._config.conf_threshold)
        self._iou_spin.setValue(self._config.iou_threshold)
        
        # Classes
        for class_id, checkbox in self._class_checkboxes.items():
            checkbox.setChecked(class_id in self._config.classes)
            
        # Tracker
        self._max_age_spin.setValue(self._config.max_age)
        self._trace_length_spin.setValue(self._config.trace_length)
        
        # Visualization
        self._show_boxes_check.setChecked(self._config.show_boxes)
        self._show_labels_check.setChecked(self._config.show_labels)
        self._show_traces_check.setChecked(self._config.show_traces)
        
        # BEV
        self._enable_bev_check.setChecked(self._config.enable_bev)
        self._bev_width_spin.setValue(self._config.bev_width)
        self._bev_height_spin.setValue(self._config.bev_height)
        self._camera_height_spin.setValue(self._config.camera_height)
        
        bev_method_index = self._bev_method_combo.findData(self._config.bev_method)
        if bev_method_index >= 0:
            self._bev_method_combo.setCurrentIndex(bev_method_index)
            
        # Output
        self._save_video_check.setChecked(self._config.save_video)
        self._output_path_edit.setText(self._config.output_path)
        
    def _save_ui_to_config(self):
        """Lưu UI vào config"""
        self._config.model_path = self._model_path_edit.text().strip() or "yolov8n.pt"
        self._config.device = self._device_combo.currentData() or "cpu"
        self._config.img_size = self._img_size_combo.currentData() or 640
        
        self._config.conf_threshold = self._conf_spin.value()
        self._config.iou_threshold = self._iou_spin.value()
        
        self._config.classes = [
            class_id for class_id, checkbox in self._class_checkboxes.items()
            if checkbox.isChecked()
        ]
        
        self._config.max_age = self._max_age_spin.value()
        self._config.trace_length = self._trace_length_spin.value()
        
        self._config.show_boxes = self._show_boxes_check.isChecked()
        self._config.show_labels = self._show_labels_check.isChecked()
        self._config.show_traces = self._show_traces_check.isChecked()
        
        self._config.enable_bev = self._enable_bev_check.isChecked()
        self._config.bev_width = self._bev_width_spin.value()
        self._config.bev_height = self._bev_height_spin.value()
        self._config.bev_method = self._bev_method_combo.currentData() or "ipm"
        self._config.camera_height = self._camera_height_spin.value()
        
        self._config.save_video = self._save_video_check.isChecked()
        self._config.output_path = self._output_path_edit.text().strip() or "output.mp4"
        
    def _on_confirm(self):
        """Xử lý khi nhấn xác nhận"""
        self._save_ui_to_config()
        self.config_confirmed.emit(self._config)
        
    def get_config(self) -> ProcessingConfig:
        """Lấy cấu hình hiện tại"""
        self._save_ui_to_config()
        return self._config
        
    def set_config(self, config: ProcessingConfig):
        """Đặt cấu hình"""
        self._config = config
        self._load_config_to_ui()
