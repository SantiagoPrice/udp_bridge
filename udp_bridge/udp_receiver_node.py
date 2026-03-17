#!/usr/bin/env python3
"""
ROS2 Node — UDP Binary Receiver
Listens on a UDP socket and publishes incoming binary data to a ROS2 topic.

Topic published : /udp/raw   (std_msgs/msg/UInt8MultiArray)
Topic published : /udp/info  (std_msgs/msg/String)  ← sender address + byte count

Usage
-----
  ros2 run <your_package> udp_receiver_node
  ros2 run <your_package> udp_receiver_node --ros-args -p udp_port:=9000 -p udp_host:=0.0.0.0
"""
import os
import socket
import threading

import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
from std_msgs.msg import UInt8MultiArray, MultiArrayDimension, String
from ament_index_python.packages import get_package_share_directory
import yaml

pkg_path = get_package_share_directory('udp_bridge')
API_PATH = os.path.join(pkg_path,'conf/ips.yaml')
PROMPT_PATH = os.path.join(pkg_path,'others/prompts.yaml')






class UdpReceiverNode(Node):
    """ROS2 node that receives binary UDP datagrams and publishes them."""

    def __init__(self):
        super().__init__("udp_receiver_node")

        with open(API_PATH, "r") as f:
            conf_handlr= yaml.safe_load(f)
            host = conf_handlr["host"]
            port = conf_handlr["port"]
        
        # ── Parameters ────────────────────────────────────────────────────────
        self.declare_parameter("udp_host", host)
        self.declare_parameter("udp_port", port)
        self.declare_parameter("buffer_size", 4096)
        self.declare_parameter("raw_topic", "/udp/raw")
        self.declare_parameter("info_topic", "/udp/info")

        host        = self.get_parameter("udp_host").value
        port        = self.get_parameter("udp_port").value
        self._buf   = self.get_parameter("buffer_size").value
        raw_topic   = self.get_parameter("raw_topic").value
        info_topic  = self.get_parameter("info_topic").value

        # ── Publishers ────────────────────────────────────────────────────────
        self._raw_pub  = self.create_publisher(UInt8MultiArray, raw_topic,  10)
        self._info_pub = self.create_publisher(String,          info_topic, 10)

        # ── UDP socket ────────────────────────────────────────────────────────
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind((host, port))
        self._sock.settimeout(1.0)          # allows clean shutdown

        self.get_logger().info(
            f"UDP receiver listening on {host}:{port}  "
            f"→  publishing to '{raw_topic}' and '{info_topic}'"
        )

        # ── Background receive thread ─────────────────────────────────────────
        self._running = True
        self._thread  = threading.Thread(target=self._recv_loop, daemon=True)
        self._thread.start()

    # ── Core receive loop ─────────────────────────────────────────────────────

    def _recv_loop(self) -> None:
        """Blocking receive loop running in a daemon thread."""
        while self._running and rclpy.ok():
            try:
                data, addr = self._sock.recvfrom(self._buf)
            except socket.timeout:
                continue
            except OSError:
                break

            self._publish(data, addr)

    def _publish(self, data: bytes, addr: tuple) -> None:
        """Build and publish ROS2 messages from a received datagram."""
        # -- UInt8MultiArray (raw bytes) --------------------------------------
        raw_msg                        = UInt8MultiArray()
        raw_msg.layout.data_offset     = 0
        dim                            = MultiArrayDimension()
        dim.label                      = "bytes"
        dim.size                       = len(data)
        dim.stride                     = len(data)
        raw_msg.layout.dim             = [dim]
        raw_msg.data                   = list(data)
        self._raw_pub.publish(raw_msg)

        # -- String info message ---------------------------------------------
        info_msg      = String()
        info_msg.data = (
            f"from={addr[0]}:{addr[1]}  "
            f"bytes={len(data)}  "
            f"hex={data.hex()}"
        )
        self._info_pub.publish(info_msg)

        self.get_logger().debug(info_msg.data)

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def destroy_node(self) -> None:
        self.get_logger().info("Shutting down UDP receiver…")
        self._running = False
        self._thread.join(timeout=2.0)
        self._sock.close()
        super().destroy_node()


# ── Entry point ───────────────────────────────────────────────────────────────

def main(args=None):
    rclpy.init(args=args)
    node = UdpReceiverNode()

    executor = MultiThreadedExecutor()
    executor.add_node(node)

    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()