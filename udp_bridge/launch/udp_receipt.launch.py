from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration , PythonExpression
from launch_ros.actions import Node



def generate_launch_description():

    log_level = LaunchConfiguration('log_level', default='info')
    isolated  = PythonExpression(["'",LaunchConfiguration('isolated', default='false'), "' == 'true'"])

    return LaunchDescription([
        Node(
            package='udp_bridge',
            executable='udp_manager_node',
            name='udp_manager_node',
            output='log',
            parameters=[{'isolated':isolated}],
            arguments=['--ros-args', '--log-level', log_level]
        ),
        Node(
            package='udp_bridge',
            executable='udp_receiver_node',
            name='udp_receiver_node',
            output='screen',
            arguments=['--ros-args', '--log-level', log_level]
        ),
    ])
