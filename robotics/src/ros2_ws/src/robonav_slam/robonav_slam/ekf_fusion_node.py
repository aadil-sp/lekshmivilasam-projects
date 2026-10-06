#!/usr/bin/env python3
"""
RoboNav-SLAM: Extended Kalman Filter (EKF) Sensor Fusion Node
Combines:
  1. Wheel Encoder Odometry (/odom_raw)
  2. MPU-6050 6-DOF IMU Angular Velocities (/imu/data)
  3. RGB-D Visual Odometry (/camera/visual_odom)
Publishes optimal state estimate [x, y, theta, v, omega] on /odometry/filtered.
"""

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Imu
from geometry_msgs.msg import Quaternion, TransformStamped
import tf2_ros
import numpy as np
import math

class EKFSensorFusionNode(Node):
    def __init__(self):
        super().__init__('ekf_fusion_node')
        
        # State Vector: x = [x, y, theta, v, omega]^T
        self.x = np.zeros((5, 1))
        
        # State Covariance Matrix P (5x5)
        self.P = np.diag([0.1, 0.1, 0.05, 0.2, 0.1])
        
        # Process Noise Covariance Q (5x5)
        self.Q = np.diag([0.02, 0.02, 0.01, 0.05, 0.02])
        
        # Measurement Noise Covariances
        self.R_odom = np.diag([0.1, 0.1, 0.05, 0.1, 0.1]) # Wheel odom
        self.R_imu  = np.diag([0.02])                     # IMU yaw rate
        self.R_vo   = np.diag([0.05, 0.05, 0.03])         # Visual odom
        
        # Subscribers
        self.create_subscription(Odometry, '/odom_raw', self.odom_callback, 20)
        self.create_subscription(Imu, '/imu/data', self.imu_callback, 50)
        self.create_subscription(Odometry, '/camera/visual_odom', self.vo_callback, 10)
        
        # Publisher
        self.fused_pub = self.create_publisher(Odometry, '/odometry/filtered', 20)
        self.tf_broadcaster = tf2_ros.TransformBroadcaster(self)
        
        self.last_time = self.get_clock().now()
        self.get_logger().info("EKF Multi-Sensor Fusion Node Active")

    def predict(self, dt):
        """Non-linear Kinematic State Transition Function f(x, u)"""
        theta = self.x[2, 0]
        v = self.x[3, 0]
        omega = self.x[4, 0]
        
        # Integrate forward kinematics
        self.x[0, 0] += v * math.cos(theta) * dt
        self.x[1, 0] += v * math.sin(theta) * dt
        self.x[2, 0] = self.normalize_angle(theta + omega * dt)
        
        # Jacobian Matrix F = df / dx
        F = np.eye(5)
        F[0, 2] = -v * math.sin(theta) * dt
        F[0, 3] = math.cos(theta) * dt
        F[1, 2] = v * math.cos(theta) * dt
        F[1, 3] = math.sin(theta) * dt
        F[2, 4] = dt
        
        # Propagate covariance P = F * P * F^T + Q
        self.P = F @ self.P @ F.T + self.Q * dt

    def update_measurement(self, z, H, R):
        """Standard Kalman Measurement Update"""
        y = z - (H @ self.x) # Innovation / Residual
        
        # Normalize angle residual if measurement includes theta
        if H.shape[0] >= 3:
            y[2, 0] = self.normalize_angle(y[2, 0])
            
        S = H @ self.P @ H.T + R # Innovation covariance
        K = self.P @ H.T @ np.linalg.inv(S) # Optimal Kalman Gain
        
        # State and Covariance Update
        self.x = self.x + K @ y
        self.x[2, 0] = self.normalize_angle(self.x[2, 0])
        I = np.eye(5)
        self.P = (I - K @ H) @ self.P

    def odom_callback(self, msg: Odometry):
        now = self.get_clock().now()
        dt = (now - self.last_time).nanoseconds / 1e9
        self.last_time = now
        
        if dt <= 0 or dt > 0.5:
            dt = 0.05
            
        # 1. Prediction step
        self.predict(dt)
        
        # 2. Measurement update from wheel encoders
        z_odom = np.array([
            [msg.pose.pose.position.x],
            [msg.pose.pose.position.y],
            [self.quat_to_yaw(msg.pose.pose.orientation)],
            [msg.twist.twist.linear.x],
            [msg.twist.twist.angular.z]
        ])
        H_odom = np.eye(5)
        self.update_measurement(z_odom, H_odom, self.R_odom)
        
        self.publish_fused_odometry()

    def imu_callback(self, msg: Imu):
        # Update gyroscope yaw rate
        z_imu = np.array([[msg.angular_velocity.z]])
        H_imu = np.zeros((1, 5))
        H_imu[0, 4] = 1.0 # measures omega
        self.update_measurement(z_imu, H_imu, self.R_imu)

    def vo_callback(self, msg: Odometry):
        # Update visual pose
        z_vo = np.array([
            [msg.pose.pose.position.x],
            [msg.pose.pose.position.y],
            [self.quat_to_yaw(msg.pose.pose.orientation)]
        ])
        H_vo = np.zeros((3, 5))
        H_vo[0, 0] = 1.0
        H_vo[1, 1] = 1.0
        H_vo[2, 2] = 1.0
        self.update_measurement(z_vo, H_vo, self.R_vo)

    def publish_fused_odometry(self):
        msg = Odometry()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'odom'
        msg.child_frame_id = 'base_link'
        
        msg.pose.pose.position.x = float(self.x[0, 0])
        msg.pose.pose.position.y = float(self.x[1, 0])
        msg.pose.pose.position.z = 0.0
        
        yaw = float(self.x[2, 0])
        msg.pose.pose.orientation.z = math.sin(yaw / 2.0)
        msg.pose.pose.orientation.w = math.cos(yaw / 2.0)
        
        msg.twist.twist.linear.x = float(self.x[3, 0])
        msg.twist.twist.angular.z = float(self.x[4, 0])
        
        self.fused_pub.publish(msg)

    @staticmethod
    def normalize_angle(angle):
        while angle > math.pi:
            angle -= 2.0 * math.pi
        while angle < -math.pi:
            angle += 2.0 * math.pi
        return angle

    @staticmethod
    def quat_to_yaw(q: Quaternion):
        siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        return math.atan2(siny_cosp, cosy_cosp)

def main(args=None):
    rclpy.init(args=args)
    node = EKFSensorFusionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
