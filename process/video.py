"""
Video Processing Module
Xử lý video với YOLO detection và ByteTrack tracking
"""

import cv2
import numpy as np
import supervision as sv
from typing import Optional, Callable, Dict, Any
from ultralytics import YOLO

from tracking.bytetrack import ByteTracker


class VideoProcessor:
    """
    Video Processor với YOLO detection và ByteTrack tracking
    
    Attributes:
        model: YOLO model
        tracker: ByteTracker instance
        model_names: Dict mapping class_id to class name
    """
    
    def __init__(
        self,
        model_path: str,
        device: str = "cpu",
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.5,
        max_age: int = 90,
        img_size: int = 640,
        classes: Optional[list] = None,
        show_boxes: bool = True,
        show_labels: bool = True,
        show_traces: bool = True,
        trace_length: int = 50
    ):
        """
        Khởi tạo VideoProcessor
        
        Args:
            model_path: Đường dẫn tới YOLO model
            device: Device để chạy model ('cpu' hoặc 'cuda')
            conf_threshold: Ngưỡng confidence cho detections
            iou_threshold: Ngưỡng IoU cho tracking matching
            max_age: Số frames tối đa giữ track khi không có detection
            img_size: Kích thước ảnh input cho model
            classes: List class IDs cần track (None = tất cả)
            show_boxes: Hiển thị bounding boxes
            show_labels: Hiển thị labels
            show_traces: Hiển thị traces
            trace_length: Độ dài trace
        """
        self.model = YOLO(model_path)
        self.model.to(device)
        self.model_names = self.model.names
        
        self.device = device
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.max_age = max_age
        self.img_size = img_size
        self.classes = classes
        
        self.show_boxes = show_boxes
        self.show_labels = show_labels
        self.show_traces = show_traces
        self.trace_length = trace_length
        
        # Tracker sẽ được khởi tạo khi biết fps
        self.tracker: Optional[ByteTracker] = None
        
        # Callback functions
        self._on_frame_callback: Optional[Callable] = None
        self._on_detection_callback: Optional[Callable] = None
    
    def _init_tracker(self, fps: int = 30):
        """Khởi tạo tracker với fps thực tế"""
        self.tracker = ByteTracker(
            track_activation_threshold=self.conf_threshold,
            lost_track_buffer=self.max_age,
            minimum_matching_threshold=self.iou_threshold,
            frame_rate=fps,
            box_viz=self.show_boxes,
            label_viz=self.show_labels,
            trace_viz=self.show_traces,
            trace_length=self.trace_length
        )
    
    def set_on_frame_callback(self, callback: Callable[[np.ndarray, sv.Detections, int], np.ndarray]):
        """
        Đặt callback được gọi sau mỗi frame
        
        Args:
            callback: Function(frame, detections, frame_count) -> processed_frame
        """
        self._on_frame_callback = callback
    
    def set_on_detection_callback(self, callback: Callable[[sv.Detections, int], None]):
        """
        Đặt callback được gọi khi có detections
        
        Args:
            callback: Function(detections, frame_count) -> None
        """
        self._on_detection_callback = callback
    
    def process_frame(self, frame: np.ndarray) -> tuple[np.ndarray, sv.Detections]:
        """
        Xử lý một frame: detect và track
        
        Args:
            frame: Input frame (BGR)
            
        Returns:
            annotated_frame: Frame đã được annotate
            tracked_detections: Detections với tracker IDs
        """
        # Run YOLO detection
        results = self.model(frame, verbose=False, conf=self.conf_threshold, imgsz=self.img_size)
        
        # Convert to supervision Detections
        detections = sv.Detections.from_ultralytics(results[0])
        
        # Filter by classes if specified
        if self.classes is not None:
            detections = detections[np.isin(detections.class_id, self.classes)]
        
        # Update tracker and annotate
        annotated_frame, tracked_detections = self.tracker.update_and_annotate(
            scene=frame,
            detections=detections,
            labels=None
        )
        
        # Add labels with tracker IDs
        if self.show_labels and tracked_detections.tracker_id is not None and len(tracked_detections) > 0:
            labels = [
                f"#{tracker_id} {self.model_names[class_id]} {conf:.2f}"
                for tracker_id, class_id, conf in zip(
                    tracked_detections.tracker_id,
                    tracked_detections.class_id,
                    tracked_detections.confidence
                )
            ]
            if self.tracker.label_annotator:
                annotated_frame = self.tracker.label_annotator.annotate(
                    scene=annotated_frame,
                    detections=tracked_detections,
                    labels=labels
                )
        
        return annotated_frame, tracked_detections
    
    def process_video(
        self,
        video_path: str,
        output_path: Optional[str] = None,
        display: bool = False,
        show_progress: bool = True
    ) -> Dict[str, Any]:
        """
        Xử lý video file
        
        Args:
            video_path: Đường dẫn video input
            output_path: Đường dẫn lưu video output (None = không lưu)
            display: Hiển thị video trong quá trình xử lý
            show_progress: In tiến trình xử lý
            
        Returns:
            Dict với thông tin xử lý (frames_processed, etc.)
        """
        # Open video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        
        # Get video properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Initialize tracker với fps thực tế
        self._init_tracker(fps)
        
        if show_progress:
            print(f"Video: {video_path}")
            print(f"Resolution: {width}x{height}, FPS: {fps}, Total frames: {total_frames}")
        
        # Video writer
        writer = None
        if output_path:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            if show_progress:
                print(f"Output will be saved to: {output_path}")
        
        frame_count = 0
        stopped_by_user = False
        
        if show_progress:
            print("Processing... Press 'q' to quit")
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Process frame
                annotated_frame, tracked_detections = self.process_frame(frame)
                
                # Call detection callback if set
                if self._on_detection_callback and len(tracked_detections) > 0:
                    self._on_detection_callback(tracked_detections, frame_count)
                
                # Call frame callback if set
                if self._on_frame_callback:
                    annotated_frame = self._on_frame_callback(
                        annotated_frame, tracked_detections, frame_count
                    )
                
                # Add frame info overlay
                info_text = f"Frame: {frame_count}/{total_frames} | Tracks: {len(tracked_detections)}"
                cv2.putText(annotated_frame, info_text, (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                
                # Display if enabled
                if display:
                    cv2.imshow("ByteTrack - Object Tracking", annotated_frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        stopped_by_user = True
                        if show_progress:
                            print("Stopped by user")
                        break
                
                # Save frame
                if writer:
                    writer.write(annotated_frame)
                
                frame_count += 1
                
                # Print progress
                if show_progress and frame_count % 100 == 0:
                    progress = 100 * frame_count / total_frames if total_frames > 0 else 0
                    print(f"Processed {frame_count}/{total_frames} frames ({progress:.1f}%)")
        
        finally:
            # Cleanup
            cap.release()
            if writer:
                writer.release()
            cv2.destroyAllWindows()
        
        if show_progress:
            print(f"\nDone! Processed {frame_count} frames")
            if output_path:
                print(f"Output saved to: {output_path}")
        
        return {
            "frames_processed": frame_count,
            "total_frames": total_frames,
            "stopped_by_user": stopped_by_user,
            "output_path": output_path
        }
    
    def reset_tracker(self):
        """Reset tracker state (useful khi chuyển sang video mới)"""
        if self.tracker:
            self.tracker.tracker.reset()
