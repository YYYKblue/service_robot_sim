#!/usr/bin/env bash
set -e
source /opt/ros/noetic/setup.bash
MODE="${1:-forward}"
case "$MODE" in
  forward)
    MSG='{linear: {x: 0.2, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}'
    ;;
  lateral|side)
    MSG='{linear: {x: 0.0, y: 0.2, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}'
    ;;
  rotate)
    MSG='{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.5}}'
    ;;
  stop)
    MSG='{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}'
    ;;
  *)
    echo "usage: $0 [forward|lateral|rotate|stop]"
    exit 1
    ;;
esac
rostopic pub -r 10 /cmd_vel geometry_msgs/Twist "$MSG"
