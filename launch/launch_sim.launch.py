import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command
from launch_ros.actions import Node


def generate_launch_description():

    package_name = 'smart_navigation_robot'

    pkg_share = get_package_share_directory(package_name)
    ros_gz_sim = get_package_share_directory('ros_gz_sim')

    robot_description_file = os.path.join(
        pkg_share,
        'description',
        'robot.urdf.xacro'
    )

    gz_launch = os.path.join(
        ros_gz_sim,
        'launch',
        'gz_sim.launch.py'
    )

    robot_description = Command([
        'xacro ',
        robot_description_file
    ])

    return LaunchDescription([

        # Start Gazebo Harmonic
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(gz_launch),
            launch_arguments={
                'gz_args': '-r /home/yamini/smart_robot_ws/src/smart-navigation-robot/worlds/empty_with_sensors.sdf'
            }.items()
        ),

        # Bridge Gazebo simulation clock to ROS 2
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            name='clock_bridge',
            arguments=[
                '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'
            ],
            output='screen'
        ),

        # Bridge Gazebo LiDAR scan to ROS 2
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            name='lidar_bridge',
            arguments=[
                '/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan'
            ],
            output='screen'
        ),

        # Publish robot description and TF
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[
                {
                    'robot_description': robot_description,
                    'use_sim_time': True
                }
            ]
        ),

        # Spawn robot into Gazebo
        Node(
            package='ros_gz_sim',
            executable='create',
            arguments=[
                '-name', 'smart_robot',
                '-topic', 'robot_description',
                '-z', '0.15'
            ],
            output='screen'
        ),

        # Start controllers after the robot has spawned
        TimerAction(
            period=10.0,
            actions=[

                Node(
                    package='controller_manager',
                    executable='spawner',
                    arguments=[
                        'joint_state_broadcaster'
                    ],
                    output='screen'
                ),

                Node(
                    package='controller_manager',
                    executable='spawner',
                    arguments=[
                        'diff_drive_controller'
                    ],
                    output='screen'
                ),
            ]
        ),
    ])
