#!/usr/bin/env python3

import sys
import time
import socket
import os
import yaml
from ament_index_python.packages import get_package_share_directory


# ── Entry point ───────────────────────────────────────────────────────────────

def main(args=None):

    pkg_path = get_package_share_directory('udp_bridge')
    IPs_PATH = os.path.join(pkg_path,'conf/ips.yaml')

    # Configuration
    with open(IPs_PATH, "r") as f:
                conf_handlr= yaml.safe_load(f)
                host = conf_handlr["host"]
                port = conf_handlr["port"]

    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    sp   = 0.5 #sampling period

    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    

    if mode == "stop":
        signal = [1,]*int(5/sp)
    elif mode == "partial_recovery":
        signal = [1,]*int(3/sp) + [0,]*int(3/sp) +[1,]*int(3/sp)
    elif mode == "full_recovery":
        signal = [1,]*int(3/sp) + [0,]*int(10/sp) 
    elif mode == "reset": #controller v is restored. Make sure to not have nav2 goals
        signal = [0,]*int(10/sp)
    elif mode == "text": 
        signal = [b"Go to the table"]
    elif not mode: 
        raise ValueError(f"mode arg is empty")
    else: 
        raise ValueError(f"Command cannot be recognized {mode}")

    for bit in signal:
        message = bytes([bit])
        try:
            sent = sock.sendto(message, (host, port))
            print(f"Sent {sent} bytes to {host}:{port}")
            print(f"Message (hex): {message.hex()}")
        except Exception as e:
            print(f"Error sending bit {bit}: {e}")
        time.sleep(sp)

    sock.close()


if __name__ == '__main__':
    main()