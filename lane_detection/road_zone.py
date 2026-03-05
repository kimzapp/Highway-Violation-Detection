"""
Road Zone Selection Module
Cho phép người dùng xác định thủ công vùng đường hợp lệ
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional


class RoadZoneSelector:
    """
    Công cụ chọn vùng đường hợp lệ bằng cách click chuột để tạo polygon
    
    Hướng dẫn sử dụng:
    - Click chuột trái: Thêm điểm vào polygon
    - Click chuột phải: Xóa điểm cuối cùng
    - Nhấn 'Enter': Xác nhận polygon và tiếp tục
    - Nhấn 'r': Reset tất cả điểm
    - Nhấn 'Esc': Hủy và thoát
    """
    
    WINDOW_NAME = "Select Road Zone - Click to add points, Enter to confirm"
    
    def __init__(self, zone_color: Tuple[int, int, int] = (0, 255, 0), 
                 zone_alpha: float = 0.3,
                 point_color: Tuple[int, int, int] = (0, 0, 255),
                 line_color: Tuple[int, int, int] = (255, 255, 0)):
        """
        Khởi tạo RoadZoneSelector
        
        Args:
            zone_color: Màu fill của vùng (BGR)
            zone_alpha: Độ trong suốt của vùng (0-1)
            point_color: Màu các điểm đã chọn
            line_color: Màu đường nối các điểm
        """
        self.zone_color = zone_color
        self.zone_alpha = zone_alpha
        self.point_color = point_color
        self.line_color = line_color
        
        self.points: List[Tuple[int, int]] = []
        self._current_frame: Optional[np.ndarray] = None
        self._selection_done = False
        self._cancelled = False
    
    def _mouse_callback(self, event, x, y, flags, param):
        """Callback xử lý sự kiện chuột"""
        if event == cv2.EVENT_LBUTTONDOWN:
            # Click trái - thêm điểm
            self.points.append((x, y))
            self._draw_preview()
        elif event == cv2.EVENT_RBUTTONDOWN:
            # Click phải - xóa điểm cuối
            if self.points:
                self.points.pop()
                self._draw_preview()
    
    def _draw_preview(self):
        """Vẽ preview polygon lên frame"""
        if self._current_frame is None:
            return
        
        preview = self._current_frame.copy()
        
        # Vẽ polygon fill nếu có >= 3 điểm
        if len(self.points) >= 3:
            overlay = preview.copy()
            pts = np.array(self.points, dtype=np.int32)
            cv2.fillPoly(overlay, [pts], self.zone_color)
            preview = cv2.addWeighted(overlay, self.zone_alpha, preview, 1 - self.zone_alpha, 0)
        
        # Vẽ đường nối các điểm
        if len(self.points) >= 2:
            pts = np.array(self.points, dtype=np.int32)
            cv2.polylines(preview, [pts], isClosed=True, color=self.line_color, thickness=2)
        
        # Vẽ các điểm
        for i, pt in enumerate(self.points):
            cv2.circle(preview, pt, 6, self.point_color, -1)
            cv2.circle(preview, pt, 8, self.line_color, 2)
            # Số thứ tự điểm
            cv2.putText(preview, str(i + 1), (pt[0] + 10, pt[1] - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Hướng dẫn
        instructions = [
            "Left click: Add point",
            "Right click: Remove last point",
            "Enter: Confirm",
            "R: Reset",
            "Esc: Cancel"
        ]
        y_offset = 30
        for text in instructions:
            cv2.putText(preview, text, (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            y_offset += 25
        
        # Số điểm đã chọn
        cv2.putText(preview, f"Points: {len(self.points)}", (10, y_offset + 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        cv2.imshow(self.WINDOW_NAME, preview)
    
    def select_zone(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """
        Hiển thị UI để người dùng chọn vùng đường
        
        Args:
            frame: Frame để hiển thị (BGR)
            
        Returns:
            Numpy array với các điểm polygon [(x1,y1), (x2,y2),...] hoặc None nếu hủy
        """
        self._current_frame = frame.copy()
        self.points = []
        self._selection_done = False
        self._cancelled = False
        
        cv2.namedWindow(self.WINDOW_NAME, cv2.WINDOW_NORMAL)
        cv2.setMouseCallback(self.WINDOW_NAME, self._mouse_callback)
        
        self._draw_preview()
        
        while not self._selection_done and not self._cancelled:
            key = cv2.waitKey(1) & 0xFF
            
            if key == 13 or key == 10:  # Enter
                if len(self.points) >= 3:
                    self._selection_done = True
                else:
                    print("Cần ít nhất 3 điểm để tạo vùng!")
            elif key == ord('r') or key == ord('R'):  # Reset
                self.points = []
                self._draw_preview()
            elif key == 27:  # Esc
                self._cancelled = True
        
        cv2.destroyWindow(self.WINDOW_NAME)
        
        if self._cancelled or len(self.points) < 3:
            return None
        
        return np.array(self.points, dtype=np.int32)
    
    def get_zone_polygon(self) -> Optional[np.ndarray]:
        """Lấy polygon đã chọn"""
        if len(self.points) < 3:
            return None
        return np.array(self.points, dtype=np.int32)


class RoadZoneOverlay:
    """
    Vẽ overlay vùng đường hợp lệ lên frame
    """
    
    def __init__(self, zone_polygon: np.ndarray,
                 fill_color: Tuple[int, int, int] = (0, 255, 0),
                 border_color: Tuple[int, int, int] = (255, 255, 0),
                 alpha: float = 0.2,
                 border_thickness: int = 2,
                 label: str = "Valid Lane"):
        """
        Khởi tạo RoadZoneOverlay
        
        Args:
            zone_polygon: Polygon định nghĩa vùng đường [(x1,y1), (x2,y2),...]
            fill_color: Màu fill (BGR)
            border_color: Màu viền (BGR)
            alpha: Độ trong suốt (0-1)
            border_thickness: Độ dày viền
            label: Nhãn hiển thị
        """
        self.zone_polygon = zone_polygon
        self.fill_color = fill_color
        self.border_color = border_color
        self.alpha = alpha
        self.border_thickness = border_thickness
        self.label = label
    
    def draw(self, frame: np.ndarray) -> np.ndarray:
        """
        Vẽ vùng đường lên frame
        
        Args:
            frame: Frame cần vẽ (BGR)
            
        Returns:
            Frame đã vẽ overlay
        """
        if self.zone_polygon is None or len(self.zone_polygon) < 3:
            return frame
        
        result = frame.copy()
        
        # Vẽ fill với transparency
        overlay = result.copy()
        cv2.fillPoly(overlay, [self.zone_polygon], self.fill_color)
        result = cv2.addWeighted(overlay, self.alpha, result, 1 - self.alpha, 0)
        
        # Vẽ viền
        cv2.polylines(result, [self.zone_polygon], isClosed=True, 
                     color=self.border_color, thickness=self.border_thickness)
        
        # Vẽ label ở góc trên của polygon
        if self.label:
            # Tìm điểm cao nhất (y nhỏ nhất)
            top_point = self.zone_polygon[np.argmin(self.zone_polygon[:, 1])]
            label_pos = (int(top_point[0]), int(top_point[1]) - 10)
            
            # Background cho text
            (text_w, text_h), _ = cv2.getTextSize(self.label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(result, 
                         (label_pos[0] - 2, label_pos[1] - text_h - 5),
                         (label_pos[0] + text_w + 2, label_pos[1] + 5),
                         self.border_color, -1)
            cv2.putText(result, self.label, label_pos,
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        
        return result
    
    def is_point_inside(self, point: Tuple[int, int]) -> bool:
        """
        Kiểm tra một điểm có nằm trong vùng đường không
        
        Args:
            point: Tọa độ điểm (x, y)
            
        Returns:
            True nếu điểm nằm trong vùng
        """
        if self.zone_polygon is None:
            return False
        result = cv2.pointPolygonTest(self.zone_polygon, point, False)
        return result >= 0
    
    def is_box_inside(self, box: Tuple[int, int, int, int], threshold: float = 0.5) -> bool:
        """
        Kiểm tra bounding box có nằm trong vùng đường không
        
        Args:
            box: Bounding box (x1, y1, x2, y2)
            threshold: Tỉ lệ diện tích overlap cần thiết (0-1)
            
        Returns:
            True nếu box overlap với vùng đường >= threshold
        """
        if self.zone_polygon is None:
            return False
        
        x1, y1, x2, y2 = box
        
        # Tạo mask cho box
        box_area = (x2 - x1) * (y2 - y1)
        if box_area <= 0:
            return False
        
        # Kiểm tra center point của bottom edge (vị trí xe trên đường)
        center_bottom = (int((x1 + x2) / 2), int(y2))
        return self.is_point_inside(center_bottom)
