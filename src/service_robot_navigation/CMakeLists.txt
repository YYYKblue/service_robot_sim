cmake_minimum_required(VERSION 3.0.2)
project(service_robot_navigation)

find_package(catkin REQUIRED)
catkin_package()

install(PROGRAMS
  scripts/save_map.sh
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(DIRECTORY launch config maps rviz
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)
