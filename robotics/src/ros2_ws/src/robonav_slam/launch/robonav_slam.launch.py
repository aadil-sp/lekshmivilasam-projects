#!/usr/bin/env python3
"""
RoboNav-SLAM Master Launch File
Launches:
 1. LiDAR Interface Node
 2. RGB-D Camera Visual Odometry Node
 3. EKF Sensor Fusion Node
 4. Occupancy Grid SLAM Node
 5. A* Global Path Planner Node
 6. DWA Local Collision Evasion Planner Node
 7. Autonomous Frontier Explorer Node
 8. Navigation Master State Machine Node
"""

from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # 1. LiDAR Driver Node
        Node(
            package='robonav_slam',
            executable='lidar_node',
            name='lidar_node',
            output='screen',
            parameters=[{'serial_port': '/dev/ttyUSB0', 'baud_rate': 115200}]
        ),
        
        # 2. Camera Vision Node
        Node(
            package='robonav_slam',
            executable='camera_vision_node',
            name='camera_vision_node',
            output='screen',
            parameters=[{'enable_apriltags': True}]
        ),

        # 3. EKF Sensor Fusion Node
        Node(
            package='robonav_slam',
            executable='ekf_fusion_node',
            name='ekf_fusion_node',
            output='screen'
        ),

        # 4. 2D Occupancy Grid SLAM Node
        Node(
            package='robonav_slam',
            executable='slam_occupancy_node',
            name='slam_occupancy_node',
            output='screen'
        ),

        # 5. Global Path Planner (A*)
        Node(
            package='robonav_slam',
            executable='global_planner_astar',
            name='global_planner_astar',
            output='screen'
        ),

        # 6. Local Planner (DWA)
        Node(
            package='robonav_slam',
            executable='local_planner_dwa',
            name='local_planner_dwa',
            output='screen'
        ),

        # 7. Frontier Exploration Engine
        Node(
            package='robonav_slam',
            executable='frontier_explorer_node',
            name='frontier_explorer_node',
            output='screen'
        ),

        # 8. Master Navigation Coordinator
        Node(
            package='robonav_slam',
            executable='nav_master_node',
            name='nav_master_node',
            output='screen'
        )
    ])
