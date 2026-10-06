from setuptools import setup
import os
from glob import glob

package_name = 'robonav_slam'

setup(
    name=package_name,
    version='2.4.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Lekshmivilasam Labs',
    maintainer_email='labs@lekshmivilasam.edu',
    description='RoboNav-SLAM: Autonomous LiDAR & RGB-D Navigation Package',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'lidar_node = robonav_slam.lidar_node:main',
            'camera_vision_node = robonav_slam.camera_vision_node:main',
            'ekf_fusion_node = robonav_slam.ekf_fusion_node:main',
            'slam_occupancy_node = robonav_slam.slam_occupancy_node:main',
            'global_planner_astar = robonav_slam.global_planner_astar:main',
            'local_planner_dwa = robonav_slam.local_planner_dwa:main',
            'frontier_explorer_node = robonav_slam.frontier_explorer_node:main',
            'nav_master_node = robonav_slam.nav_master_node:main',
        ],
    },
)
