#!/usr/bin/env bash
set -euo pipefail

MAP_NAME="${1:-indoor}"
PKG_PATH="$(rospack find service_robot_navigation)"
mkdir -p "${PKG_PATH}/maps"

rosrun map_server map_saver -f "${PKG_PATH}/maps/${MAP_NAME}"
echo "Saved map to ${PKG_PATH}/maps/${MAP_NAME}.pgm and .yaml"
