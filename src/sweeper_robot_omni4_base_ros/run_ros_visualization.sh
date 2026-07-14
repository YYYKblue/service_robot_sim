#!/usr/bin/env bash
set -e
source /opt/ros/noetic/setup.bash
PKG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export ROS_PACKAGE_PATH="$(dirname "$PKG_DIR"):${ROS_PACKAGE_PATH}"
VIEW="${1:-iso}"
roslaunch sweeper_robot_omni4_base_ros display.launch view:="$VIEW"
