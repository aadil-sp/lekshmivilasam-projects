#!/usr/bin/env python3
"""
RoboNav-SLAM: Dynamic Window Approach (DWA) Local Planner Node
Evaluates velocity space (v, w) trajectory rollouts in real time,
optimizes for heading to global path waypoint, obstacle clearance, and speed,
and outputs /cmd_vel to the robot motor base.
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Path, Odometry
from sensor_msgs.msg import LaserScan
import math
import numpy as np

class LocalPlannerDWA(Node):
    def __init__(self):
        super().__init__('local_planner_dwa')
        
        # Kinematic limits
        self.max_speed = 0.6    # m/s
        self.min_speed = -0.1   # m/s
        self.max_yaw_rate = 2.0 # rad/s
        self.max_accel = 1.2    # m/s^2
        self.max_dyaw = 3.2     # rad/s^2
        
        self.v_reso = 0.05
        self.yaw_rate_reso = 0.1
        self.dt = 0.1
        self.predict_time = 1.5
        
        # Weights for objective function
        self.to_goal_cost_gain = 0.15
        self.speed_cost_gain = 1.0
        self.obstacle_cost_gain = 1.2
        self.robot_radius = 0.20 # meters
        
        # Current state
        self.current_v = 0.0
        self.current_omega = 0.0
        self.robot_x = 0.0
        self.robot_y = 0.0
        self.robot_yaw = 0.0
        self.global_path = []
        self.obstacles = [] # list of (x, y)
        
        # Subscriptions
        self.create_subscription(Odometry, '/odometry/filtered', self.odom_callback, 10)
        self.create_subscription(Path, '/plan', self.path_callback, 10)
        self.create_subscription(LaserScan, '/scan', self.scan_callback, 10)
        
        # Publisher
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        
        # Control Loop Timer (20 Hz = 50ms)
        self.timer = self.create_timer(0.05, self.control_loop)
        self.get_logger().info("Dynamic Window Approach (DWA) Local Planner Active @ 20Hz")

    def odom_callback(self, msg: Odometry):
        self.robot_x = msg.pose.pose.position.x
        self.robot_y = msg.pose.pose.position.y
        q = msg.pose.pose.orientation
        siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        self.robot_yaw = math.atan2(siny_cosp, cosy_cosp)
        self.current_v = msg.twist.twist.linear.x
        self.current_omega = msg.twist.twist.angular.z

    def path_callback(self, msg: Path):
        self.global_path = [(p.pose.position.x, p.pose.position.y) for p in msg.poses]

    def scan_callback(self, msg: LaserScan):
        obs = []
        angle = msg.angle_min
        for r in msg.ranges:
            if not math.isnan(r) and msg.range_min < r < msg.range_max:
                beam_a = self.robot_yaw + angle
                ox = self.robot_x + r * math.cos(beam_a)
                oy = self.robot_y + r * math.sin(beam_a)
                obs.append((ox, oy))
            angle += msg.angle_increment
        self.obstacles = obs

    def control_loop(self):
        if not self.global_path:
            return

        # Find target waypoint ~0.5m ahead
        goal = self.global_path[-1]
        target_wp = self.global_path[0]
        for wp in self.global_path:
            d = math.hypot(wp[0] - self.robot_x, wp[1] - self.robot_y)
            if d > 0.4:
                target_wp = wp
                break

        # Check goal distance
        dist_to_final = math.hypot(goal[0] - self.robot_x, goal[1] - self.robot_y)
        if dist_to_final < 0.15:
            # Reached goal!
            cmd = Twist()
            self.cmd_pub.publish(cmd)
            self.global_path = []
            self.get_logger().info("Target Goal Position Reached!")
            return

        # Compute DWA best (v, omega)
        best_u = self.dwa_compute(target_wp)
        cmd = Twist()
        cmd.linear.x = float(best_u[0])
        cmd.angular.z = float(best_u[1])
        self.cmd_pub.publish(cmd)

    def dwa_compute(self, target_wp):
        # Dynamic window: [Vs intersect Vd]
        dw = [
            max(self.min_speed, self.current_v - self.max_accel * self.dt),
            min(self.max_speed, self.current_v + self.max_accel * self.dt),
            max(-self.max_yaw_rate, self.current_omega - self.max_dyaw * self.dt),
            min(self.max_yaw_rate, self.current_omega + self.max_dyaw * self.dt)
        ]

        best_cost = float('inf')
        best_u = [0.0, 0.0]

        v_samples = np.arange(dw[0], dw[1] + 1e-4, self.v_reso)
        w_samples = np.arange(dw[2], dw[3] + 1e-4, self.yaw_rate_reso)

        for v in v_samples:
            for w in w_samples:
                traj = self.predict_trajectory(v, w)
                
                # Evaluation Metrics
                to_goal_cost = self.to_goal_cost_gain * self.calc_to_goal_cost(traj, target_wp)
                speed_cost = self.speed_cost_gain * (self.max_speed - traj[-1][3])
                ob_cost = self.obstacle_cost_gain * self.calc_obstacle_cost(traj)
                
                if ob_cost == float('inf'):
                    continue

                final_cost = to_goal_cost + speed_cost + ob_cost
                if final_cost < best_cost:
                    best_cost = final_cost
                    best_u = [v, w]

        return best_u

    def predict_trajectory(self, v, w):
        traj = []
        x = self.robot_x
        y = self.robot_y
        yaw = self.robot_yaw
        time = 0.0
        while time <= self.predict_time:
            x += v * math.cos(yaw) * self.dt
            y += v * math.sin(yaw) * self.dt
            yaw += w * self.dt
            time += self.dt
            traj.append((x, y, yaw, v, w))
        return traj

    def calc_to_goal_cost(self, traj, goal):
        dx = goal[0] - traj[-1][0]
        dy = goal[1] - traj[-1][1]
        error_angle = math.atan2(dy, dx)
        cost_angle = error_angle - traj[-1][2]
        cost = abs(math.atan2(math.sin(cost_angle), math.cos(cost_angle)))
        return cost

    def calc_obstacle_cost(self, traj):
        min_dist = float('inf')
        for px, py, _, _, _ in traj:
            for ox, oy in self.obstacles[::4]: # Subsample for speed
                d = math.hypot(px - ox, py - oy)
                if d <= self.robot_radius:
                    return float('inf') # Collision
                if d < min_dist:
                    min_dist = d
        return 1.0 / min_dist if min_dist > 0 else float('inf')

def main(args=None):
    rclpy.init(args=args)
    node = LocalPlannerDWA()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
