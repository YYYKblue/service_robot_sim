# service_robot_sim

This catkin package starts the `my_world` indoor Gazebo world and spawns the
`sweeper_robot_omni4_base_ros` robot into the same Gazebo process.

## Workspace layout

Place these three packages directly under `~/catkin_ws/src/`:

```text
catkin_ws/src/
├── my_world/
├── sweeper_robot_omni4_base_ros/
└── service_robot_sim/
```

## Build

```bash
cd ~/catkin_ws/src
chmod +x sweeper_robot_omni4_base_ros/scripts/velocity_interface_node.py
chmod +x sweeper_robot_omni4_base_ros/scripts/test_cmd_vel.sh

cd ~/catkin_ws
rosdep install --from-paths src --ignore-src -r -y
catkin_make
source devel/setup.bash
```

## Start

```bash
roslaunch service_robot_sim omni4_indoor.launch
```

Useful optional arguments:

```bash
roslaunch service_robot_sim omni4_indoor.launch rviz:=true
roslaunch service_robot_sim omni4_indoor.launch x:=2.0 y:=8.05 yaw:=0.0
```

Do not launch `my_world indoor.launch` and
`sweeper_robot_omni4_base_ros gazebo.launch` at the same time: both original
launch files start a Gazebo server. The integrated launch starts Gazebo only
once.

## Basic checks

```bash
rostopic list | grep -E '^/(cmd_vel|odom|scan|joint_states|tf)$'
rostopic echo -n 1 /scan
rostopic echo -n 1 /odom
```

Lateral movement test:

```bash
rostopic pub -r 10 /cmd_vel geometry_msgs/Twist \
"{linear: {x: 0.0, y: 0.20, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"
```

Press `Ctrl+C` to stop the command.
