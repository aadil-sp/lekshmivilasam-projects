#!/usr/bin/env python3
"""
RoboNav-SLAM: Navigation Master State Machine Node
Coordinates autonomous states:
  - IDLE
  - MAPPING_FRONTIER
  - GOAL_NAVIGATION
  - OBSTACLE_RECOVERY
  - EMERGENCY_STOP
Interfaces with ESP32 Serial driver, ROS2 actions, and diagnostic telemetry.
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Bool
from geometry_msgs.msg import Twist, PoseStamped
from nav_msgs.msg import Odometry

class NavMasterNode(Node):
    def __init__(self):
        super().__init__('nav_master_node')
        
        self.state = 'IDLE' # IDLE, MAPPING, NAVIGATING, RECOVERY, STOPPED
        
        # Publishers
        self.state_pub = self.create_publisher(String, '/robonav/system_state', 10)
        self.cmd_override_pub = self.create_publisher(Twist, '/cmd_vel_override', 10)
        
        # Subscribers
        self.create_subscription(String, '/robonav/set_mode', self.mode_callback, 10)
        self.create_subscription(Bool, '/robonav/emergency_stop', self.estop_callback, 10)
        self.create_subscription(PoseStamped, '/goal_pose', self.goal_received_callback, 10)
        
        self.status_timer = self.create_timer(1.0, self.publish_status)
        self.get_logger().info("RoboNav Master Navigation Coordinator Initialized")

    def mode_callback(self, msg: String):
        req = msg.data.upper()
        if req in ['IDLE', 'MAPPING', 'NAVIGATING', 'STOPPED']:
            self.state = req
            self.get_logger().info(f"System State Changed to: {self.state}")

    def estop_callback(self, msg: Bool):
        if msg.data:
            self.state = 'STOPPED'
            stop_twist = Twist()
            self.cmd_override_pub.publish(stop_twist)
            self.get_logger().error("EMERGENCY STOP TRIGGERED!")

    def goal_received_callback(self, msg: PoseStamped):
        if self.state != 'STOPPED':
            self.state = 'NAVIGATING'
            self.get_logger().info(f"New Waypoint Accepted at ({msg.pose.position.x:.2f}, {msg.pose.position.y:.2f})")

    def publish_status(self):
        msg = String()
        msg.data = f'{{"state":"{self.state}","health":"NOMINAL"}}'
        self.state_pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = NavMasterNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
