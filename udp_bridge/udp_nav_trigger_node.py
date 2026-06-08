#!/usr/bin/env python3
import os
import rclpy
from rclpy.node import Node
from std_msgs.msg import UInt8MultiArray
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.action import ActionClient
from nav2_msgs.action import NavigateToPose
from ament_index_python.packages import get_package_share_directory

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

        self.previous_bit = 0

        self.nav2_client = ActionClient(
            self,
            NavigateToPose,
            'navigate_to_pose',
            callback_group=ReentrantCallbackGroup()
        )

    def listener_callback(self, msg):
        if not msg.data:
            return

        if self.previous_bit:
            return

        self.previous_bit = msg.data[0] - 48  # first bit

        if self.previous_bit:
            goal = NavigateToPose.Goal()
            goal.behavior_tree = os.path.join(bt_path,"udp_test.xml")
            self.nav2_client.send_goal_async(goal)


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