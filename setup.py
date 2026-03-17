#!/usr/bin/env python3
from setuptools import setup , find_packages
import glob
 
package_name = "udp_bridge"
 
setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
        (f"share/{package_name}/conf", glob.glob(f"{package_name}/conf/*")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    entry_points={
        "console_scripts": [
            "udp_receiver_node = udp_bridge.udp_receiver_node:main",
            "udp_manager_node = udp_bridge.udp_manager_node:main",
        ],
    },
)