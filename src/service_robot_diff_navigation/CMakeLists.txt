cmake_minimum_required(VERSION 3.0.2)
project(service_robot_diff_navigation)

find_package(catkin REQUIRED)
catkin_package()

catkin_install_python(
  PROGRAMS scripts/run_task_tests.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(DIRECTORY launch config maps rviz
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)
