from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='udp_bridge',
            executable='udp_manager_node',
            name='udp_manager_node',
            output='log',
            arguments=['--ros-args', '--log-level', 'warn']
        ),
        Node(
            package='udp_bridge',
            executable='udp_receiver_node',
            name='udp_receiver_node',
            output='screen',
            arguments=['--ros-args', '--log-level', 'info']
        ),
    ])
