#!/usr/bin/env python3
import os
import rclpy
from rclpy.node import Node
from std_msgs.msg import UInt8MultiArray
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.action import ActionClient
from nav2_msgs.action import NavigateToPose
from ament_index_python.packages import get_package_share_directory
from geometry_msgs.msg import PoseStamped

bt_path = os.path.join(get_package_share_directory('bts'),'behavior_trees')

class TimerManagerNode(Node):
    def __init__(self):
        super().__init__('udp_nav_trigger_node')

        self.subscription = self.create_subscription(
            UInt8MultiArray,
            '/udp/raw',
            self.listener_callback,
            10
        )

        self.declare_parameter('isolated', False)
        self.isolated = self.get_parameter('isolated').value

        self.command = 0

        self.nav2_client = ActionClient(
            self,
            NavigateToPose,
            'navigate_to_pose',
            callback_group=ReentrantCallbackGroup()
        )

    def listener_callback(self, msg):
        if not msg.data:
            return


        self.command =bytes(msg.data).decode("utf-8") # first bit

        self.get_logger().info(f"Received data {self.command}")

        g_msg = NavigateToPose.Goal()
        g_msg.pose = PoseStamped()
        g_msg.pose.header.frame_id = 'map'
        g_msg.pose.header.stamp = self.get_clock().now().to_msg()

        if "fridge" in self.command:
            g_msg.pose.pose.position.x = 0.18
            g_msg.pose.pose.position.y = 0.73
            g_msg.pose.pose.position.z = 0.0
            g_msg.pose.pose.orientation.x = 0.0
            g_msg.pose.pose.orientation.y = 0.0
            g_msg.pose.pose.orientation.z = 0.691915
            g_msg.pose.pose.orientation.w = 0.721979
        else:
            g_msg.pose.pose.position.x = 1.65
            g_msg.pose.pose.position.y = 0.35
            g_msg.pose.pose.position.z = 0.0
            g_msg.pose.pose.orientation.x = 0.0
            g_msg.pose.pose.orientation.y = 0.0
            g_msg.pose.pose.orientation.z = 0.688395
            g_msg.pose.pose.orientation.w = 0.725336

        future = self.nav2_client.send_goal_async(g_msg)

        future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().info('Goal rejected :(')
            return
        self.get_logger().info('Goal accepted :)')

def main(args=None):
    rclpy.init(args=args)
    node = TimerManagerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()