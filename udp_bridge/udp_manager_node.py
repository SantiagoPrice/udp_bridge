#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import UInt8MultiArray , Header
from rclpy.parameter import Parameter
from rcl_interfaces.srv import SetParameters
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.action import ActionClient
from nav2_msgs.action import NavigateToPose
from action_msgs.srv import CancelGoal
import argparse

class TimerManagerNode(Node):
    def __init__(self):
        super().__init__('udp_manager_node')


        self.subscription = self.create_subscription(
            UInt8MultiArray,
            '/udp/raw', 
            self.listener_callback,
            10
        )

        self.publisher = self.create_publisher(Header, '/udp/response', 10)

        self.declare_parameter('debug', False)
        self.debug = self.get_parameter('debug').value

        self.previous_bit = 0
        self.active_timer = None
        self.nav2_goal_handle = None  # Track the current goal handle

        # Parameters to reduce speed
        self.cont_pars_normal = {
            "FollowPath.vx_max": 0.5,
            "FollowPath.vx_min": -0.5,
            "FollowPath.vx_std": 0.3,
            "FollowPath.wz_max": 0.8,
            "FollowPath.wz_std": 0.6,}
        
        self.vm     = self.cont_pars_normal["FollowPath.vx_max"] #max speed
        self.delt_v = self.vm / 5  #0.1  discrete v reductions
        
        
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

        self.active_timer = self.create_timer(0.5, self.timer_callback)

    def listener_callback(self, msg):
        if not msg.data:
            return

        current_bit = msg.data[0]-48  # first bit

        msg = Header()
        msg.frame_id = str(current_bit)
        msg.stamp = self.get_clock().now().to_msg()
        self.publisher.publish(msg)

        self.delt_v = abs(self.delt_v) * (-1) ** current_bit # positive when signal is 0 , negative otherwise
      
      
    def timer_callback(self):
        if self.delt_v < 0:
            if self.cont_pars_normal["FollowPath.vx_max"] >  (self.delt_v+0.01):
                self.cont_pars_normal["FollowPath.vx_max"] += self.delt_v
            else:
                if not self.debug:
                    self.cancel_nav2_goal()
                return

        else:
            if self.cont_pars_normal["FollowPath.vx_max"] <  (self.vm - self.delt_v):
                self.cont_pars_normal["FollowPath.vx_max"] += self.delt_v
            else:
                pass
  
        if not self.debug:
            self.reload_nav2_conf(self.param_update_callback, self.cont_par_cli, self.cont_pars_normal)
        else:
            self.get_logger().info("New speed: {}".format(self.cont_pars_normal["FollowPath.vx_max"]))

    def cancel_nav2_goal(self):
        request = CancelGoal.Request()
        # Empty goal_info cancels ALL active goals
        future = self.cancel_cli.call_async(request)
        future.add_done_callback(self.cancel_nav2_goal_callback)


    def cancel_nav2_goal_callback(self, future):
        try:
            result = future.result()
            self.get_logger().info(f'Nav2 goal cancelled successfully: {result}')
            self.nav2_goal_handle = None
        except Exception as e:
            self.get_logger().error(f'Failed to cancel Nav2 goal: {e}')


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