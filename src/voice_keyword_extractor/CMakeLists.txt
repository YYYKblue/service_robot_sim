cmake_minimum_required(VERSION 3.0.2)
project(voice_keyword_extractor)

find_package(catkin REQUIRED COMPONENTS
  message_generation
  rospy
  std_msgs
)

add_service_files(
  FILES
  ExtractKeyword.srv
)

generate_messages(
  DEPENDENCIES
  std_msgs
)

catkin_package(
  CATKIN_DEPENDS
  message_runtime
  rospy
  std_msgs
)

include_directories(
  ${catkin_INCLUDE_DIRS}
)

catkin_install_python(
  PROGRAMS scripts/keyword_service_node.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)
