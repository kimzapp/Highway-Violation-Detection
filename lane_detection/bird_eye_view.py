"""
Bird's Eye View (BEV) Transformation Module
Chuyển đổi vùng làn đường sang góc nhìn từ trên xuống để giám sát chính xác hơn
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
import supervision as sv


class BirdEyeViewTransformer:
    """
    Chuyển đổi perspective từ camera view sang bird's eye view
    
    Sử dụng 4 điểm từ polygon làn đường để tính ma trận transform.
    Điểm được sắp xếp theo thứ tự: top-left, top-right, bottom-right, bottom-left
    """
    
    def __init__(
        self, 
        source_polygon: np.ndarray,
        bev_width: int = 400,
        bev_height: int = 600,
        margin: int = 50
    ):
        """
        Khởi tạo BEV Transformer
        
        Args:
            source_polygon: Polygon vùng làn đường từ camera view
            bev_width: Chiều rộng của BEV output
            bev_height: Chiều cao của BEV output
            margin: Margin xung quanh BEV
        """
        self.source_polygon = source_polygon
        self.bev_width = bev_width
        self.bev_height = bev_height
        self.margin = margin
        
        # Sắp xếp các điểm polygon theo thứ tự chuẩn
        self.source_points = self._order_points(source_polygon)
        
        # Tạo điểm đích cho BEV (hình chữ nhật)
        self.dest_points = np.array([
            [margin, margin],                           # top-left
            [bev_width - margin, margin],               # top-right
            [bev_width - margin, bev_height - margin],  # bottom-right
            [margin, bev_height - margin]               # bottom-left
        ], dtype=np.float32)
        
        # Tính ma trận perspective transform
        self.transform_matrix = cv2.getPerspectiveTransform(
            self.source_points.astype(np.float32), 
            self.dest_points
        )
        
        # Tính ma trận inverse để chuyển ngược từ BEV -> camera view
        self.inverse_matrix = cv2.getPerspectiveTransform(
            self.dest_points,
            self.source_points.astype(np.float32)
        )
    
    def _order_points(self, pts: np.ndarray) -> np.ndarray:
        """
        Sắp xếp 4 điểm theo thứ tự: top-left, top-right, bottom-right, bottom-left
        
        Nếu polygon có nhiều hơn 4 điểm, chọn 4 điểm góc (bounding box corners)
        """
        if len(pts) == 4:
            # Sắp xếp 4 điểm
            rect = np.zeros((4, 2), dtype=np.float32)
            
            # Top-left có tổng x+y nhỏ nhất
            # Bottom-right có tổng x+y lớn nhất
            s = pts.sum(axis=1)
            rect[0] = pts[np.argmin(s)]
            rect[2] = pts[np.argmax(s)]
            
            # Top-right có hiệu y-x nhỏ nhất
            # Bottom-left có hiệu y-x lớn nhất
            diff = np.diff(pts, axis=1)
            rect[1] = pts[np.argmin(diff)]
            rect[3] = pts[np.argmax(diff)]
            
            return rect
        else:
            # Với polygon nhiều hơn 4 điểm, tìm bounding quadrilateral
            # Lấy 4 điểm cực: trên cùng, dưới cùng, trái nhất, phải nhất
            hull = cv2.convexHull(pts)
            hull = hull.reshape(-1, 2)
            
            # Tìm 4 điểm góc dựa trên vị trí
            top_idx = np.argmin(hull[:, 1])
            bottom_idx = np.argmax(hull[:, 1])
            left_idx = np.argmin(hull[:, 0])
            right_idx = np.argmax(hull[:, 0])
            
            # Xác định 4 góc
            # Top side: điểm có y nhỏ nhất ở bên trái và bên phải
            top_points = hull[hull[:, 1] < np.median(hull[:, 1])]
            if len(top_points) >= 2:
                top_left = top_points[np.argmin(top_points[:, 0])]
                top_right = top_points[np.argmax(top_points[:, 0])]
            else:
                top_left = hull[top_idx]
                top_right = hull[top_idx]
            
            # Bottom side: điểm có y lớn nhất ở bên trái và bên phải  
            bottom_points = hull[hull[:, 1] >= np.median(hull[:, 1])]
            if len(bottom_points) >= 2:
                bottom_left = bottom_points[np.argmin(bottom_points[:, 0])]
                bottom_right = bottom_points[np.argmax(bottom_points[:, 0])]
            else:
                bottom_left = hull[bottom_idx]
                bottom_right = hull[bottom_idx]
            
            return np.array([top_left, top_right, bottom_right, bottom_left], dtype=np.float32)
    
    def transform_point(self, point: Tuple[int, int]) -> Tuple[int, int]:
        """
        Chuyển đổi một điểm từ camera view sang BEV
        
        Args:
            point: Tọa độ (x, y) trong camera view
            
        Returns:
            Tọa độ (x, y) trong BEV
        """
        pt = np.array([[[point[0], point[1]]]], dtype=np.float32)
        transformed = cv2.perspectiveTransform(pt, self.transform_matrix)
        return (int(transformed[0][0][0]), int(transformed[0][0][1]))
    
    def transform_points(self, points: np.ndarray) -> np.ndarray:
        """
        Chuyển đổi nhiều điểm từ camera view sang BEV
        
        Args:
            points: Mảng điểm shape (N, 2)
            
        Returns:
            Mảng điểm đã transform shape (N, 2)
        """
        if len(points) == 0:
            return np.array([])
        
        pts = points.reshape(-1, 1, 2).astype(np.float32)
        transformed = cv2.perspectiveTransform(pts, self.transform_matrix)
        return transformed.reshape(-1, 2).astype(np.int32)
    
    def transform_box_to_point(self, box: Tuple[int, int, int, int]) -> Tuple[int, int]:
        """
        Chuyển đổi bounding box thành điểm đại diện trên BEV
        Sử dụng điểm giữa cạnh dưới của box (vị trí xe trên mặt đường)
        
        Args:
            box: Bounding box (x1, y1, x2, y2)
            
        Returns:
            Tọa độ điểm trên BEV
        """
        x1, y1, x2, y2 = box
        # Điểm giữa cạnh dưới
        center_bottom = (int((x1 + x2) / 2), int(y2))
        return self.transform_point(center_bottom)
    
    def inverse_transform_point(self, point: Tuple[int, int]) -> Tuple[int, int]:
        """
        Chuyển đổi điểm từ BEV ngược về camera view
        """
        pt = np.array([[[point[0], point[1]]]], dtype=np.float32)
        transformed = cv2.perspectiveTransform(pt, self.inverse_matrix)
        return (int(transformed[0][0][0]), int(transformed[0][0][1]))


class BirdEyeViewVisualizer:
    """
    Hiển thị Bird's Eye View với các xe được tracking
    """
    
    def __init__(
        self,
        transformer: BirdEyeViewTransformer,
        bg_color: Tuple[int, int, int] = (40, 40, 40),
        lane_color: Tuple[int, int, int] = (100, 100, 100),
        lane_border_color: Tuple[int, int, int] = (255, 255, 0),
        vehicle_colors: Optional[dict] = None
    ):
        """
        Khởi tạo BEV Visualizer
        
        Args:
            transformer: BEV transformer đã được khởi tạo
            bg_color: Màu nền BEV
            lane_color: Màu của làn đường
            lane_border_color: Màu viền làn đường
            vehicle_colors: Dict mapping class_id -> color
        """
        self.transformer = transformer
        self.bg_color = bg_color
        self.lane_color = lane_color
        self.lane_border_color = lane_border_color
        
        # Màu mặc định cho các loại xe
        self.vehicle_colors = vehicle_colors or {
            0: (0, 255, 0),     # person - xanh lá
            1: (255, 165, 0),   # bicycle - cam
            2: (0, 0, 255),     # car - đỏ
            3: (255, 0, 255),   # motorcycle - tím
            5: (0, 255, 255),   # bus - vàng
            7: (255, 0, 0),     # truck - xanh dương
        }
        self.default_color = (255, 255, 255)  # Trắng cho các class khác
        
        # Tạo base BEV image với làn đường
        self._create_base_image()
    
    def _create_base_image(self):
        """Tạo ảnh nền BEV với làn đường"""
        self.base_image = np.full(
            (self.transformer.bev_height, self.transformer.bev_width, 3),
            self.bg_color,
            dtype=np.uint8
        )
        
        # Vẽ làn đường (hình chữ nhật đã transform)
        lane_pts = self.transformer.dest_points.astype(np.int32)
        cv2.fillPoly(self.base_image, [lane_pts], self.lane_color)
        cv2.polylines(self.base_image, [lane_pts], True, self.lane_border_color, 2)
        
        # Vẽ line chia làn (giữa)
        mid_top = ((lane_pts[0][0] + lane_pts[1][0]) // 2, lane_pts[0][1])
        mid_bottom = ((lane_pts[3][0] + lane_pts[2][0]) // 2, lane_pts[2][1])
        
        # Vẽ line đứt đoạn
        self._draw_dashed_line(self.base_image, mid_top, mid_bottom, (255, 255, 255), 2, 20, 10)
        
        # Thêm label
        cv2.putText(self.base_image, "Bird's Eye View", (10, 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    def _draw_dashed_line(self, img, pt1, pt2, color, thickness, dash_length, gap_length):
        """Vẽ đường đứt đoạn"""
        dist = np.sqrt((pt2[0] - pt1[0])**2 + (pt2[1] - pt1[1])**2)
        if dist == 0:
            return
            
        dx = (pt2[0] - pt1[0]) / dist
        dy = (pt2[1] - pt1[1]) / dist
        
        current = 0
        while current < dist:
            start = (int(pt1[0] + dx * current), int(pt1[1] + dy * current))
            end_dist = min(current + dash_length, dist)
            end = (int(pt1[0] + dx * end_dist), int(pt1[1] + dy * end_dist))
            cv2.line(img, start, end, color, thickness)
            current += dash_length + gap_length
    
    def get_vehicle_color(self, class_id: int, tracker_id: int = None) -> Tuple[int, int, int]:
        """Lấy màu cho xe dựa trên class hoặc tracker ID"""
        if tracker_id is not None:
            # Tạo màu unique dựa trên tracker ID
            np.random.seed(tracker_id * 10)
            return tuple(np.random.randint(100, 255, 3).tolist())
        return self.vehicle_colors.get(class_id, self.default_color)
    
    def draw(
        self,
        detections: sv.Detections,
        class_names: Optional[dict] = None,
        show_ids: bool = True,
        show_labels: bool = True
    ) -> np.ndarray:
        """
        Vẽ BEV với các xe từ detections
        
        Args:
            detections: Supervision Detections object với tracker IDs
            class_names: Dict mapping class_id -> class name
            show_ids: Hiển thị tracker IDs
            show_labels: Hiển thị class labels
            
        Returns:
            BEV image với các xe được vẽ
        """
        bev_image = self.base_image.copy()
        
        if detections is None or len(detections) == 0:
            return bev_image
        
        # Lấy thông tin detections
        boxes = detections.xyxy
        class_ids = detections.class_id
        tracker_ids = detections.tracker_id if detections.tracker_id is not None else [None] * len(boxes)
        confidences = detections.confidence if detections.confidence is not None else [1.0] * len(boxes)
        
        # Vẽ từng xe lên BEV
        for i, (box, class_id, tracker_id, conf) in enumerate(zip(boxes, class_ids, tracker_ids, confidences)):
            # Transform điểm xe sang BEV
            try:
                bev_point = self.transformer.transform_box_to_point(box)
            except:
                continue
            
            # Kiểm tra điểm có nằm trong vùng BEV không
            if not (0 <= bev_point[0] < self.transformer.bev_width and 
                    0 <= bev_point[1] < self.transformer.bev_height):
                continue
            
            # Lấy màu
            color = self.get_vehicle_color(class_id, tracker_id)
            
            # Vẽ hình đại diện xe (hình chữ nhật nhỏ)
            vehicle_width = 20
            vehicle_height = 35
            x, y = bev_point
            
            # Vẽ xe như hình chữ nhật
            pt1 = (x - vehicle_width // 2, y - vehicle_height // 2)
            pt2 = (x + vehicle_width // 2, y + vehicle_height // 2)
            cv2.rectangle(bev_image, pt1, pt2, color, -1)
            cv2.rectangle(bev_image, pt1, pt2, (255, 255, 255), 1)
            
            # Vẽ mũi tên chỉ hướng (giả sử hướng xuống)
            arrow_start = (x, y - vehicle_height // 4)
            arrow_end = (x, y + vehicle_height // 4)
            cv2.arrowedLine(bev_image, arrow_start, arrow_end, (255, 255, 255), 2, tipLength=0.4)
            
            # Vẽ label
            label_parts = []
            if show_ids and tracker_id is not None:
                label_parts.append(f"#{tracker_id}")
            if show_labels and class_names and class_id in class_names:
                label_parts.append(class_names[class_id])
            
            if label_parts:
                label = " ".join(label_parts)
                label_pos = (x - vehicle_width // 2, y - vehicle_height // 2 - 5)
                
                # Background cho label
                (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
                cv2.rectangle(bev_image,
                             (label_pos[0] - 2, label_pos[1] - text_h - 2),
                             (label_pos[0] + text_w + 2, label_pos[1] + 2),
                             color, -1)
                cv2.putText(bev_image, label, label_pos,
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        # Thêm thống kê
        vehicle_count = len(detections)
        cv2.putText(bev_image, f"Vehicles: {vehicle_count}", 
                   (10, self.transformer.bev_height - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return bev_image


def create_combined_view(
    camera_frame: np.ndarray,
    bev_frame: np.ndarray,
    layout: str = "horizontal"
) -> np.ndarray:
    """
    Kết hợp camera view và BEV thành một frame
    
    Args:
        camera_frame: Frame từ camera
        bev_frame: Frame BEV
        layout: "horizontal" hoặc "vertical"
        
    Returns:
        Combined frame
    """
    cam_h, cam_w = camera_frame.shape[:2]
    bev_h, bev_w = bev_frame.shape[:2]
    
    if layout == "horizontal":
        # Scale BEV để có cùng chiều cao với camera frame
        scale = cam_h / bev_h
        new_bev_w = int(bev_w * scale)
        bev_resized = cv2.resize(bev_frame, (new_bev_w, cam_h))
        
        # Ghép ngang
        combined = np.hstack([camera_frame, bev_resized])
    else:
        # Scale BEV để có cùng chiều rộng với camera frame
        scale = cam_w / bev_w
        new_bev_h = int(bev_h * scale)
        bev_resized = cv2.resize(bev_frame, (cam_w, new_bev_h))
        
        # Ghép dọc
        combined = np.vstack([camera_frame, bev_resized])
    
    return combined
