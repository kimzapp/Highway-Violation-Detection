"""
Video Preview Widget
Widget hiển thị video preview trong GUI
"""

import cv2
import numpy as np
from typing import Optional, Callable

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QSlider, QSizePolicy, QFrame
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QColor


class VideoPreviewWidget(QWidget):
    """
    Widget hiển thị video preview
    
    Signals:
        frame_changed: Phát ra khi frame thay đổi (frame_number)
        video_loaded: Phát ra khi video được load thành công
        video_ended: Phát ra khi video kết thúc
    """
    
    frame_changed = pyqtSignal(int)
    video_loaded = pyqtSignal(dict)  # Video info
    video_ended = pyqtSignal()
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self._cap: Optional[cv2.VideoCapture] = None
        self._current_frame: Optional[np.ndarray] = None
        self._current_frame_number: int = 0
        self._total_frames: int = 0
        self._fps: float = 30.0
        self._video_width: int = 0
        self._video_height: int = 0
        
        self._is_playing: bool = False
        self._playback_timer: Optional[QTimer] = None
        
        self._setup_ui()
        self._connect_signals()
        
    def _setup_ui(self):
        """Thiết lập giao diện"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Video display area
        self._video_label = QLabel()
        self._video_label.setAlignment(Qt.AlignCenter)
        self._video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._video_label.setMinimumSize(400, 300)
        self._video_label.setStyleSheet("""
            QLabel {
                background-color: #1a1a1a;
                border: 1px solid #333333;
                border-radius: 5px;
            }
        """)
        self._video_label.setText("Chưa có video")
        layout.addWidget(self._video_label, 1)
        
        # Controls
        controls_frame = QFrame()
        controls_frame.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        controls_layout = QVBoxLayout(controls_frame)
        controls_layout.setContentsMargins(10, 5, 10, 5)
        controls_layout.setSpacing(5)
        
        # Progress slider
        slider_layout = QHBoxLayout()
        
        self._time_label = QLabel("00:00")
        self._time_label.setStyleSheet("color: white; font-size: 11px;")
        self._time_label.setMinimumWidth(45)
        slider_layout.addWidget(self._time_label)
        
        self._progress_slider = QSlider(Qt.Horizontal)
        self._progress_slider.setRange(0, 100)
        self._progress_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #999999;
                height: 8px;
                background: #404040;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #4CAF50;
                border: 1px solid #45a049;
                width: 14px;
                margin: -3px 0;
                border-radius: 7px;
            }
            QSlider::sub-page:horizontal {
                background: #4CAF50;
                border-radius: 4px;
            }
        """)
        slider_layout.addWidget(self._progress_slider)
        
        self._duration_label = QLabel("00:00")
        self._duration_label.setStyleSheet("color: white; font-size: 11px;")
        self._duration_label.setMinimumWidth(45)
        slider_layout.addWidget(self._duration_label)
        
        controls_layout.addLayout(slider_layout)
        
        # Playback buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        btn_style = """
            QPushButton {
                background-color: #404040;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:pressed {
                background-color: #353535;
            }
            QPushButton:disabled {
                background-color: #2a2a2a;
                color: #666666;
            }
        """
        
        self._prev_frame_btn = QPushButton("⏮ Prev")
        self._prev_frame_btn.setStyleSheet(btn_style)
        buttons_layout.addWidget(self._prev_frame_btn)
        
        self._play_btn = QPushButton("▶ Play")
        self._play_btn.setStyleSheet(btn_style)
        self._play_btn.setMinimumWidth(80)
        buttons_layout.addWidget(self._play_btn)
        
        self._next_frame_btn = QPushButton("Next ⏭")
        self._next_frame_btn.setStyleSheet(btn_style)
        buttons_layout.addWidget(self._next_frame_btn)
        
        buttons_layout.addStretch()
        
        self._frame_info_label = QLabel("Frame: 0 / 0")
        self._frame_info_label.setStyleSheet("color: #aaaaaa; font-size: 11px;")
        buttons_layout.addWidget(self._frame_info_label)
        
        controls_layout.addLayout(buttons_layout)
        
        layout.addWidget(controls_frame)
        
    def _connect_signals(self):
        """Kết nối signals"""
        self._play_btn.clicked.connect(self._toggle_play)
        self._prev_frame_btn.clicked.connect(self._prev_frame)
        self._next_frame_btn.clicked.connect(self._next_frame)
        self._progress_slider.sliderPressed.connect(self._on_slider_pressed)
        self._progress_slider.sliderReleased.connect(self._on_slider_released)
        self._progress_slider.valueChanged.connect(self._on_slider_changed)
        
    def load_video(self, video_path: str) -> bool:
        """Load video từ đường dẫn"""
        if self._cap is not None:
            self._cap.release()
            
        self._cap = cv2.VideoCapture(video_path)
        
        if not self._cap.isOpened():
            self._video_label.setText("❌ Không thể mở video")
            return False
            
        # Get video info
        self._video_width = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self._video_height = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self._fps = self._cap.get(cv2.CAP_PROP_FPS)
        self._total_frames = int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Update UI
        self._progress_slider.setRange(0, max(1, self._total_frames - 1))
        duration = self._total_frames / self._fps if self._fps > 0 else 0
        self._duration_label.setText(self._format_time(duration))
        
        # Read first frame
        self._seek_to_frame(0)
        
        # Emit video loaded signal
        video_info = {
            'width': self._video_width,
            'height': self._video_height,
            'fps': self._fps,
            'total_frames': self._total_frames,
            'duration': duration
        }
        self.video_loaded.emit(video_info)
        
        return True
        
    def _seek_to_frame(self, frame_number: int):
        """Seek đến frame cụ thể"""
        if self._cap is None:
            return
            
        frame_number = max(0, min(frame_number, self._total_frames - 1))
        self._cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        
        ret, frame = self._cap.read()
        if ret:
            self._current_frame = frame
            self._current_frame_number = frame_number
            self._display_frame(frame)
            self._update_ui_state()
            self.frame_changed.emit(frame_number)
            
    def _display_frame(self, frame: np.ndarray):
        """Hiển thị frame lên widget"""
        if frame is None:
            return
            
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Scale frame to fit label while maintaining aspect ratio
        label_size = self._video_label.size()
        h, w = rgb_frame.shape[:2]
        
        scale = min(label_size.width() / w, label_size.height() / h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        if new_w > 0 and new_h > 0:
            scaled_frame = cv2.resize(rgb_frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
            
            # Create QImage and QPixmap
            h, w, ch = scaled_frame.shape
            bytes_per_line = ch * w
            q_image = QImage(scaled_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image)
            
            self._video_label.setPixmap(pixmap)
            
    def _update_ui_state(self):
        """Cập nhật trạng thái UI"""
        # Update slider
        self._progress_slider.blockSignals(True)
        self._progress_slider.setValue(self._current_frame_number)
        self._progress_slider.blockSignals(False)
        
        # Update time label
        current_time = self._current_frame_number / self._fps if self._fps > 0 else 0
        self._time_label.setText(self._format_time(current_time))
        
        # Update frame info
        self._frame_info_label.setText(f"Frame: {self._current_frame_number + 1} / {self._total_frames}")
        
    def _format_time(self, seconds: float) -> str:
        """Format thời gian thành mm:ss"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
        
    def _toggle_play(self):
        """Toggle play/pause"""
        if self._is_playing:
            self._pause()
        else:
            self._play()
            
    def _play(self):
        """Bắt đầu phát video"""
        if self._cap is None or self._is_playing:
            return
            
        self._is_playing = True
        self._play_btn.setText("⏸ Pause")
        
        # Create timer for playback
        if self._playback_timer is None:
            self._playback_timer = QTimer(self)
            self._playback_timer.timeout.connect(self._read_next_frame)
            
        interval = int(1000 / self._fps) if self._fps > 0 else 33
        self._playback_timer.start(interval)
        
    def _pause(self):
        """Tạm dừng video"""
        self._is_playing = False
        self._play_btn.setText("▶ Play")
        
        if self._playback_timer is not None:
            self._playback_timer.stop()
            
    def _read_next_frame(self):
        """Đọc frame tiếp theo"""
        if self._cap is None:
            return
            
        ret, frame = self._cap.read()
        if ret:
            self._current_frame = frame
            self._current_frame_number = int(self._cap.get(cv2.CAP_PROP_POS_FRAMES)) - 1
            self._display_frame(frame)
            self._update_ui_state()
            self.frame_changed.emit(self._current_frame_number)
        else:
            # Video ended
            self._pause()
            self.video_ended.emit()
            
    def _prev_frame(self):
        """Đến frame trước"""
        if self._current_frame_number > 0:
            self._seek_to_frame(self._current_frame_number - 1)
            
    def _next_frame(self):
        """Đến frame tiếp theo"""
        if self._current_frame_number < self._total_frames - 1:
            self._seek_to_frame(self._current_frame_number + 1)
            
    def _on_slider_pressed(self):
        """Xử lý khi bắt đầu kéo slider"""
        if self._is_playing:
            self._pause()
            
    def _on_slider_released(self):
        """Xử lý khi thả slider"""
        pass  # Do nothing special
        
    def _on_slider_changed(self, value: int):
        """Xử lý khi slider thay đổi"""
        if abs(value - self._current_frame_number) > 1:
            self._seek_to_frame(value)
            
    def get_current_frame(self) -> Optional[np.ndarray]:
        """Lấy frame hiện tại"""
        return self._current_frame.copy() if self._current_frame is not None else None
        
    def get_current_frame_number(self) -> int:
        """Lấy số frame hiện tại"""
        return self._current_frame_number
        
    def get_video_info(self) -> dict:
        """Lấy thông tin video"""
        return {
            'width': self._video_width,
            'height': self._video_height,
            'fps': self._fps,
            'total_frames': self._total_frames
        }
        
    def resizeEvent(self, event):
        """Xử lý khi widget resize"""
        super().resizeEvent(event)
        if self._current_frame is not None:
            self._display_frame(self._current_frame)
            
    def release(self):
        """Giải phóng tài nguyên"""
        if self._playback_timer is not None:
            self._playback_timer.stop()
            
        if self._cap is not None:
            self._cap.release()
            self._cap = None
