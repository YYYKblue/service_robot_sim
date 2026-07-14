cmake_minimum_required(VERSION 3.0.2)
project(sweeper_robot_omni4_base_ros)

find_package(catkin REQUIRED COMPONENTS
  rospy
  std_msgs
  geometry_msgs
  sensor_msgs
  robot_state_publisher
  joint_state_publisher
  gazebo_ros
)

catkin_package()

catkin_install_python(PROGRAMS
  scripts/velocity_interface_node.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(DIRECTORY
  launch
  meshes
  rviz
  urdf
  worlds
  config
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)
