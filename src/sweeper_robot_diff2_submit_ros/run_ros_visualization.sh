#!/usr/bin/env bash
set -e
source /opt/ros/noetic/setup.bash
PKG="sweeper_robot_diff2_submit_ros"
SRC="$HOME/catkin_ws/src"
SELF="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$SRC"
rm -rf "$SRC/$PKG"
cp -a "$SELF" "$SRC/$PKG"
chmod +x "$SRC/$PKG/scripts/"*.py "$SRC/$PKG/scripts/"*.sh 2>/dev/null || true
cd "$HOME/catkin_ws"
catkin_make
source devel/setup.bash
roslaunch "$PKG" display.launch
