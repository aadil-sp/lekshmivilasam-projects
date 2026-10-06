"""
========================================================================================
AI Vision Color & Shape Sorting Controller for Dobot Magician Lite
Hardware: Mac Webcam / USB Camera + Dobot Magician Lite + Magic Box
Features:
- Real-time HSV Color Detection (Red, Green, Blue, Yellow)
- Contour analysis and Centroid extraction
- Pixel-to-Robot Cartesian Coordinate Calibration Matrix
- Automatic trajectory dispatching via Serial / Deployer
========================================================================================
"""

import cv2
import numpy as np
import time
import os

# HSV Color Thresholds
COLOR_RANGES = {
    "RED": [
        (np.array([0, 120, 70]), np.array([10, 255, 255])),
        (np.array([170, 120, 70]), np.array([180, 255, 255]))
    ],
    "GREEN": [
        (np.array([36, 100, 70]), np.array([89, 255, 255]))
    ],
    "BLUE": [
        (np.array([90, 100, 70]), np.array([128, 255, 255]))
    ],
    "YELLOW": [
        (np.array([20, 100, 100]), np.array([35, 255, 255]))
    ]
}

# Designated Sorting Target Locations (X, Y, Z, R) in mm
BIN_LOCATIONS = {
    "RED":    (260.0, -120.0, -25.0, 0.0),
    "GREEN":  (260.0,  -60.0, -25.0, 0.0),
    "BLUE":   (260.0,   60.0, -25.0, 0.0),
    "YELLOW": (260.0,  120.0, -25.0, 0.0)
}

class VisionSorter:
    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        # 4-Point Homography Matrix Calibration Points (Camera Pixels -> Robot mm)
        self.cam_pts = np.float32([[100, 100], [540, 100], [540, 380], [100, 380]])
        self.robot_pts = np.float32([[200, -100], [200, 100], [320, 100], [320, -100]])
        self.transform_matrix = cv2.getPerspectiveTransform(self.cam_pts, self.robot_pts)

    def pixel_to_robot(self, px, py):
        """Transform camera image pixels (px, py) to Dobot Cartesian coordinates (rx, ry)"""
        point = np.array([[[px, py]]], dtype=np.float32)
        transformed = cv2.perspectiveTransform(point, self.transform_matrix)
        rx = float(transformed[0][0][0])
        ry = float(transformed[0][0][1])
        return rx, ry

    def detect_colored_objects(self, frame):
        """Analyze frame and identify target objects by color and centroid"""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        detected_items = []

        for color_name, ranges in COLOR_RANGES.items():
            mask = np.zeros(hsv.shape[:2], dtype="uint8")
            for lower, upper in ranges:
                mask |= cv2.inRange(hsv, lower, upper)
            
            # Morphological noise cleanup
            kernel = np.ones((5, 5), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area > 400: # Minimum size threshold
                    M = cv2.moments(cnt)
                    if M["m00"] != 0:
                        cx = int(M["m10"] / M["m00"])
                        cy = int(M["m01"] / M["m00"])
                        rx, ry = self.pixel_to_robot(cx, cy)
                        detected_items.append({
                            "color": color_name,
                            "pixel": (cx, cy),
                            "robot_coord": (rx, ry, -25.0, 0.0),
                            "contour": cnt,
                            "target_bin": BIN_LOCATIONS[color_name]
                        })
        return detected_items

if __name__ == "__main__":
    print("[INFO] AI Vision Sorter initialized.")
    print("[INFO] Ready for camera calibration and coordinate mapping.")
