# sweeper_robot_omni4_base_ros

Integrated ROS Noetic package for a 0.5 m four-omni-wheel sweeper robot model.

## What was integrated

- Standard ROS package files: package.xml and CMakeLists.txt.
- Portable mesh paths: URDF uses package://sweeper_robot_omni4_base_ros/meshes/.
- base_footprint frame for navigation-friendly TF.
- RViz display launch: launch/display.launch.
- Gazebo simulation launch: launch/gazebo.launch.
- Gazebo planar motion plugin: subscribe /cmd_vel and publish /odom + /tf.
- Gazebo 2D lidar plugin on lidar_link: publish /scan.
- Inertial and simplified collision parameters for stable Gazebo loading.
- Velocity interface node: subscribe /cmd_vel and publish wheel /joint_states.

## RViz

```bash
cd ~/catkin_ws/src
unzip sweeper_robot_omni4_gazebo_integrated.zip
cd ~/catkin_ws
catkin_make
source devel/setup.bash
roslaunch sweeper_robot_omni4_base_ros display.launch
```

## Gazebo

```bash
source ~/catkin_ws/devel/setup.bash
roslaunch sweeper_robot_omni4_base_ros gazebo.launch
```

## Motion tests

```bash
rosrun sweeper_robot_omni4_base_ros test_cmd_vel.sh forward
rosrun sweeper_robot_omni4_base_ros test_cmd_vel.sh lateral
rosrun sweeper_robot_omni4_base_ros test_cmd_vel.sh rotate
```

Expected ROS topics include /cmd_vel, /odom, /tf, /scan, /joint_states, and /robot_description.
