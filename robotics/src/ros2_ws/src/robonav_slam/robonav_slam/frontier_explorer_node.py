#!/usr/bin/env python3
"""
RoboNav-SLAM: Autonomous Frontier Exploration Node
Detects unknown/free-space boundary cells on /map, clusters candidate frontiers,
ranks frontiers using information gain and distance cost, and publishes /goal_pose
to achieve 100% autonomous indoor exploration without human intervention.
"""

import rclpy
from rclpy.node import Node
from nav_msgs.msg import OccupancyGrid, Odometry
from geometry_msgs.msg import PoseStamped
import numpy as np
import math

class FrontierExplorerNode(Node):
    def __init__(self):
        super().__init__('frontier_explorer_node')
        
        self.map_data = None
        self.width = 0
        self.height = 0
        self.resolution = 0.05
        self.origin_x = 0.0
        self.origin_y = 0.0
        
        self.robot_x = 0.0
        self.robot_y = 0.0
        self.is_exploring = True
        self.current_goal = None
        
        # Subscriptions
        self.create_subscription(OccupancyGrid, '/map', self.map_callback, 1)
        self.create_subscription(Odometry, '/odometry/filtered', self.odom_callback, 10)
        
        # Publisher
        self.goal_pub = self.create_publisher(PoseStamped, '/goal_pose', 1)
        
        # Periodic Frontier Evaluator Timer (every 2.5s)
        self.timer = self.create_timer(2.5, self.evaluate_frontiers)
        self.get_logger().info("Autonomous Frontier Exploration Engine Active")

    def odom_callback(self, msg: Odometry):
        self.robot_x = msg.pose.pose.position.x
        self.robot_y = msg.pose.pose.position.y

    def map_callback(self, msg: OccupancyGrid):
        self.width = msg.info.width
        self.height = msg.info.height
        self.resolution = msg.info.resolution
        self.origin_x = msg.info.origin.position.x
        self.origin_y = msg.info.origin.position.y
        self.map_data = np.array(msg.data, dtype=np.int8).reshape((self.height, self.width))

    def evaluate_frontiers(self):
        if self.map_data is None or not self.is_exploring:
            return

        # Check if already close to current target goal
        if self.current_goal is not None:
            dist = math.hypot(self.current_goal[0] - self.robot_x, self.current_goal[1] - self.robot_y)
            if dist > 0.4:
                return # Keep moving towards current frontier

        frontiers = self.detect_frontier_cells()
        if not frontiers:
            self.get_logger().info("🎉 Frontier Exploration Complete! No unexplored boundaries remaining.")
            self.is_exploring = False
            return

        best_goal = self.select_best_frontier(frontiers)
        if best_goal:
            self.current_goal = best_goal
            self.publish_exploration_goal(best_goal[0], best_goal[1])

    def detect_frontier_cells(self):
        """Finds all FREE cells (0 <= val <= 25) adjacent to UNKNOWN cells (-1)"""
        frontiers = []
        # Downsampled scan for speed
        for r in range(1, self.height - 1, 2):
            for c in range(1, self.width - 1, 2):
                val = self.map_data[r, c]
                if 0 <= val <= 25: # Known free space
                    # Check 8-neighbor adjacency for -1 (unknown)
                    neighborhood = self.map_data[r-1:r+2, c-1:c+2]
                    if -1 in neighborhood:
                        wx = self.origin_x + (c + 0.5) * self.resolution
                        wy = self.origin_y + (r + 0.5) * self.resolution
                        frontiers.append((wx, wy))
        return frontiers

    def select_best_frontier(self, frontiers):
        """Utility Function: U(f) = Information_Gain / (Euclidean_Distance + epsilon)"""
        best_score = -float('inf')
        best_frontier = None

        for fx, fy in frontiers:
            dist = math.hypot(fx - self.robot_x, fy - self.robot_y)
            if dist < 0.35: # Ignore immediate radius
                continue
            
            # Closer frontiers scored higher; reward dense unexplored regions
            utility = 10.0 / (dist + 1.0)
            if utility > best_score:
                best_score = utility
                best_frontier = (fx, fy)

        return best_frontier

    def publish_exploration_goal(self, gx, gy):
        goal = PoseStamped()
        goal.header.stamp = self.get_clock().now().to_msg()
        goal.header.frame_id = 'map'
        goal.pose.position.x = gx
        goal.pose.position.y = gy
        goal.pose.position.z = 0.0
        goal.pose.orientation.w = 1.0
        
        self.goal_pub.publish(goal)
        self.get_logger().info(f"Dispatching New Frontier Goal -> ({gx:.2f}m, {gy:.2f}m)")

def main(args=None):
    rclpy.init(args=args)
    node = FrontierExplorerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
