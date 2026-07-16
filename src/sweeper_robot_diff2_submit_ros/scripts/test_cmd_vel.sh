#!/usr/bin/env bash
set -e
MODE="${1:-forward}"
case "$MODE" in
  forward) MSG='{linear: {x: 0.20, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}' ;;
  back)    MSG='{linear: {x: -0.20, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}' ;;
  left)    MSG='{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.55}}' ;;
  right)   MSG='{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: -0.55}}' ;;
  stop)    MSG='{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}' ;;
  *) echo "用法: $0 [forward|back|left|right|stop]"; exit 1 ;;
esac
rostopic pub -r 10 /cmd_vel geometry_msgs/Twist "$MSG"
