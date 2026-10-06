#!/usr/bin/env python3
"""
RoboNav-SLAM: A* (A-Star) Global Path Planner Node
Consumes /map, computes obstacle costmap inflation, solves shortest collision-free path
from robot position to /goal_pose, and publishes /plan (nav_msgs/Path).
"""

import rclpy
from rclpy.node import Node
from nav_msgs.msg import OccupancyGrid, Path, Odometry
from geometry_msgs.msg import PoseStamped
import heapq
import math
import numpy as np

class GlobalPlannerAStar(Node):
    def __init__(self):
        super().__init__('global_planner_astar')
        
        self.map_data = None
        self.costmap = None
        self.resolution = 0.05
        self.origin_x = 0.0
        self.origin_y = 0.0
        self.width = 0
        self.height = 0
        
        self.robot_x = 0.0
        self.robot_y = 0.0
        
        # Subscriptions
        self.create_subscription(OccupancyGrid, '/map', self.map_callback, 1)
        self.create_subscription(Odometry, '/odometry/filtered', self.odom_callback, 10)
        self.create_subscription(PoseStamped, '/goal_pose', self.goal_callback, 10)
        
        # Publisher
        self.path_pub = self.create_publisher(Path, '/plan', 1)
        self.get_logger().info("A* Global Path Planner Node Ready")

    def odom_callback(self, msg: Odometry):
        self.robot_x = msg.pose.pose.position.x
        self.robot_y = msg.pose.pose.position.y

    def map_callback(self, msg: OccupancyGrid):
        self.resolution = msg.info.resolution
        self.origin_x = msg.info.origin.position.x
        self.origin_y = msg.info.origin.position.y
        self.width = msg.info.width
        self.height = msg.info.height
        
        raw_grid = np.array(msg.data, dtype=np.int8).reshape((self.height, self.width))
        self.compute_costmap_inflation(raw_grid)

    def compute_costmap_inflation(self, raw_grid):
        # 0.25m robot inflation radius (5 cells)
        inflation_cells = int(0.25 / self.resolution)
        costmap = np.zeros_like(raw_grid, dtype=np.uint8)
        
        occ_y, occ_x = np.where(raw_grid > 50)
        for y, x in zip(occ_y, occ_x):
            y_min = max(0, y - inflation_cells)
            y_max = min(self.height, y + inflation_cells + 1)
            x_min = max(0, x - inflation_cells)
            x_max = min(self.width, x + inflation_cells + 1)
            costmap[y_min:y_max, x_min:x_max] = 254 # Lethal obstacle boundary
            
        self.costmap = costmap

    def goal_callback(self, goal_msg: PoseStamped):
        if self.costmap is None:
            self.get_logger().warn("Cannot plan path: No costmap received yet!")
            return

        gx = goal_msg.pose.position.x
        gy = goal_msg.pose.position.y
        
        start_c = int((self.robot_x - self.origin_x) / self.resolution)
        start_r = int((self.robot_y - self.origin_y) / self.resolution)
        goal_c = int((gx - self.origin_x) / self.resolution)
        goal_r = int((gy - self.origin_y) / self.resolution)
        
        path_cells = self.astar_search(start_c, start_r, goal_c, goal_r)
        if path_cells:
            self.publish_path(path_cells)
        else:
            self.get_logger().warn("A* Search: No feasible path to goal found!")

    def astar_search(self, start_c, start_r, goal_c, goal_r):
        if not (0 <= goal_c < self.width and 0 <= goal_r < self.height):
            return []

        open_set = []
        heapq.heappush(open_set, (0, (start_c, start_r)))
        came_from = {}
        g_score = { (start_c, start_r): 0 }
        
        neighbors = [(1,0,1.0), (-1,0,1.0), (0,1,1.0), (0,-1,1.0),
                     (1,1,1.414), (-1,1,1.414), (1,-1,1.414), (-1,-1,1.414)]
        
        while open_set:
            _, current = heapq.heappop(open_set)
            
            if current == (goal_c, goal_r):
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                path.reverse()
                return path
            
            for dc, dr, cost in neighbors:
                nc, nr = current[0] + dc, current[1] + dr
                if 0 <= nc < self.width and 0 <= nr < self.height:
                    if self.costmap[nr, nc] > 200:
                        continue # Lethal obstacle
                        
                    tentative_g = g_score[current] + cost + (self.costmap[nr, nc] / 50.0)
                    neighbor = (nc, nr)
                    if tentative_g < g_score.get(neighbor, float('inf')):
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g
                        f_score = tentative_g + math.hypot(nc - goal_c, nr - goal_r)
                        heapq.heappush(open_set, (f_score, neighbor))
                        
        return []

    def publish_path(self, cells):
        path_msg = Path()
        path_msg.header.stamp = self.get_clock().now().to_msg()
        path_msg.header.frame_id = 'map'
        
        for c, r in cells:
            pose = PoseStamped()
            pose.header = path_msg.header
            pose.pose.position.x = self.origin_x + (c + 0.5) * self.resolution
            pose.pose.position.y = self.origin_y + (r + 0.5) * self.resolution
            pose.pose.position.z = 0.0
            pose.pose.orientation.w = 1.0
            path_msg.poses.append(pose)
            
        self.path_pub.publish(path_msg)

def main(args=None):
    rclpy.init(args=args)
    node = GlobalPlannerAStar()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
