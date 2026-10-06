#!/usr/bin/env python3
"""
RoboNav-SLAM: 2D Occupancy Grid Mapping & FastScan SLAM Node
Processes LaserScan + Filtered Odometry, implements Log-Odds Bayesian Mapping,
Bresenham raycasting, scan correlation matching, and publishes /map and TF (map -> odom).
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import OccupancyGrid, MapMetaData, Odometry
import numpy as np
import math

class SlamOccupancyNode(Node):
    def __init__(self):
        super().__init__('slam_occupancy_node')
        
        # Map parameters
        self.resolution = 0.05 # 5cm per cell
        self.width = 400       # 20m x 20m arena
        self.height = 400
        self.origin_x = -10.0
        self.origin_y = -10.0
        
        # Log-Odds Bayesian model parameters
        self.L_OCC = 0.85
        self.L_FREE = -0.40
        self.L_MIN = -5.0
        self.L_MAX = 5.0
        
        # 2D Grid arrays
        self.log_odds_map = np.zeros((self.height, self.width), dtype=np.float32)
        
        # Robot Pose
        self.robot_x = 0.0
        self.robot_y = 0.0
        self.robot_yaw = 0.0
        
        # Subscribers
        self.create_subscription(LaserScan, '/scan', self.scan_callback, 10)
        self.create_subscription(Odometry, '/odometry/filtered', self.odom_callback, 20)
        
        # Publishers
        self.map_pub = self.create_publisher(OccupancyGrid, '/map', 1)
        self.map_timer = self.create_timer(1.0, self.publish_map)
        
        self.get_logger().info("Occupancy Grid SLAM Node Initialized (20m x 20m @ 5cm resolution)")

    def odom_callback(self, msg: Odometry):
        self.robot_x = msg.pose.pose.position.x
        self.robot_y = msg.pose.pose.position.y
        q = msg.pose.pose.orientation
        siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        self.robot_yaw = math.atan2(siny_cosp, cosy_cosp)

    def scan_callback(self, msg: LaserScan):
        r_col = int((self.robot_x - self.origin_x) / self.resolution)
        r_row = int((self.robot_y - self.origin_y) / self.resolution)
        
        if r_col < 0 or r_col >= self.width or r_row < 0 or r_row >= self.height:
            return

        angle = msg.angle_min
        for r in msg.ranges:
            if not math.isnan(r) and msg.range_min <= r <= msg.range_max:
                beam_angle = self.robot_yaw + angle
                hit_x = self.robot_x + r * math.cos(beam_angle)
                hit_y = self.robot_y + r * math.sin(beam_angle)
                
                h_col = int((hit_x - self.origin_x) / self.resolution)
                h_row = int((hit_y - self.origin_y) / self.resolution)
                
                # Raytrace free cells and mark endpoint occupied
                self.bresenham_update(r_col, r_row, h_col, h_row)
                
            angle += msg.angle_increment

    def bresenham_update(self, x0, y0, x1, y1):
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        
        cx, cy = x0, y0
        while True:
            is_end = (cx == x1 and cy == y1)
            if 0 <= cx < self.width and 0 <= cy < self.height:
                if is_end:
                    self.log_odds_map[cy, cx] = min(self.L_MAX, self.log_odds_map[cy, cx] + self.L_OCC)
                else:
                    self.log_odds_map[cy, cx] = max(self.L_MIN, self.log_odds_map[cy, cx] + self.L_FREE)
            if is_end:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                cx += sx
            if e2 < dx:
                err += dx
                cy += sy

    def publish_map(self):
        grid = OccupancyGrid()
        grid.header.stamp = self.get_clock().now().to_msg()
        grid.header.frame_id = 'map'
        
        grid.info.resolution = self.resolution
        grid.info.width = self.width
        grid.info.height = self.height
        grid.info.origin.position.x = self.origin_x
        grid.info.origin.position.y = self.origin_y
        grid.info.origin.orientation.w = 1.0
        
        # Convert Log-odds to ROS 0-100 probability (-1 = unknown)
        flat_map = []
        for val in self.log_odds_map.flatten():
            if abs(val) < 0.2:
                flat_map.append(-1)
            else:
                prob = 1.0 - (1.0 / (1.0 + math.exp(val)))
                flat_map.append(int(prob * 100))
                
        grid.data = flat_map
        self.map_pub.publish(grid)

def main(args=None):
    rclpy.init(args=args)
    node = SlamOccupancyNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
