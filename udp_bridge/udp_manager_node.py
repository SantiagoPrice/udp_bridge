#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import UInt8MultiArray
from rclpy.parameter import Parameter
from rcl_interfaces.srv import SetParameters
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.action import ActionClient
from nav2_msgs.action import NavigateToPose
from action_msgs.srv import CancelGoal
import argparse

class TimerManagerNode(Node):
    def __init__(self,debug=False):
        super().__init__('udp_manager_node')

        self.debug=debug

        self.subscription = self.create_subscription(
            UInt8MultiArray,
            '/udp/raw', 
            self.listener_callback,
            10
        )

        self.previous_bit = 0
        self.timer_phase = 0  # 0 = idle, 1 = first timer, 2 = second timer
        self.active_timer = None
        self.nav2_goal_handle = None  # Track the current goal handle

        # Parameters to reduce speed
        self.cont_pars_normal = {
            "FollowPath.vx_max": 0.5,
            "FollowPath.vx_min": -0.5,
            "FollowPath.vx_std": 0.3,
            "FollowPath.wz_max": 0.8,
            "FollowPath.wz_std": 0.6,}
        
        self.cont_pars_slow = {
            "FollowPath.vx_max": 0.25,
            "FollowPath.vx_min": -0.25,
            "FollowPath.vx_std": 0.15,
            "FollowPath.wz_max": 0.4,
            "FollowPath.wz_std": 0.3,}
        
        self.cont_par_cli = self.create_client(
            srv_type=SetParameters,
            srv_name='/controller_server/set_parameters',
            callback_group=ReentrantCallbackGroup()
        )

        self.cancel_cli = self.create_client(
            CancelGoal,
            '/navigate_to_pose/_action/cancel_goal',
            callback_group=ReentrantCallbackGroup()
        )

        # Nav2 action client
        self.nav2_client = ActionClient(
            self,
            NavigateToPose,
            'navigate_to_pose',
            callback_group=ReentrantCallbackGroup()
        )

    def listener_callback(self, msg):
        if not msg.data:
            return

        current_bit = msg.data[0]-48  # first bit
        if current_bit == 1 and self.previous_bit == 0:
            self.start_first_timer()

        elif current_bit == 0 and self.timer_phase != 0:
            self.cancel_and_reset_timer()

        self.previous_bit = current_bit

    def start_first_timer(self):
        self.cancel_active_timer()
        self.timer_phase = 1
        self.get_logger().info('First 5s timer started.')
        self.active_timer = self.create_timer(5.0, self.first_timer_callback)
        

    def first_timer_callback(self):
        if not self.debug:
            self.reload_nav2_conf(self.param_update_callback, self.cont_par_cli, self.cont_pars_slow)
        self.cancel_active_timer()
        self.get_logger().info('First timer concluded: starting second 5s timer.')
        self.timer_phase = 2
        self.active_timer = self.create_timer(5.0, self.second_timer_callback)

    def second_timer_callback(self):
        self.cancel_active_timer()
        self.get_logger().info('Second timer concluded: cancelling Nav2 goal.')
        self.timer_phase = 0
        self.cancel_nav2_goal()

    def cancel_nav2_goal(self):
        request = CancelGoal.Request()
        # Empty goal_info cancels ALL active goals
        future = self.cancel_cli.call_async(request)
        future.add_done_callback(self.cancel_nav2_goal_callback)

    def cancel_nav2_goal_callback(self, future):
        result = future.result()
        self.get_logger().info(f'Nav2 goals cancelled: {result}')

    def cancel_nav2_goal_callback(self, future):
        try:
            result = future.result()
            self.get_logger().info(f'Nav2 goal cancelled successfully: {result}')
            self.nav2_goal_handle = None
        except Exception as e:
            self.get_logger().error(f'Failed to cancel Nav2 goal: {e}')

    def cancel_and_reset_timer(self):
        if not self.debug:
            self.reload_nav2_conf(self.param_update_callback, self.cont_par_cli, self.cont_pars_normal)
        self.cancel_active_timer()
        self.timer_phase = 0
        self.get_logger().info('Timer cancelled and reset (bit went to 0).')

    def cancel_active_timer(self):
        if self.active_timer is not None:
            self.active_timer.cancel()
            self.destroy_timer(self.active_timer)
            self.active_timer = None

    def reload_nav2_conf(self, callbackFunc, client, param_dict):
        request = SetParameters.Request()
        request.parameters = [
            Parameter(name=k, value=v).to_parameter_msg()
            for k, v in param_dict.items()
        ]
        future = client.call_async(request)
        future.add_done_callback(callbackFunc)

    def param_update_callback(self, future):
        if future.result():
            self.get_logger().info('Controller parameters updated: slow displacement.')


def main(args=None):

    parser = argparse.ArgumentParser(description='Timer Manager Node')
    parser.add_argument('--debug', action='store_true', help='Boolean flag argument')
    parsed_args, remaining = parser.parse_known_args(args)

    rclpy.init(args=args)
    node = TimerManagerNode(debug=parsed_args.debug)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()