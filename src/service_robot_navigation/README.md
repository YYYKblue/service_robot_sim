# service_robot_navigation

ROS Noetic navigation package for the existing `service_robot_sim` omnidirectional robot simulation.

## 1. Install dependencies

```bash
sudo apt update
sudo apt install ros-noetic-navigation ros-noetic-slam-gmapping ros-noetic-map-server
```

## 2. Build

Place this package directly under `~/service_rebot/src/`, then:

```bash
cd ~/service_rebot
rosdep install --from-paths src --ignore-src -r -y
catkin_make
source devel/setup.bash
```

## 3. Build a map

```bash
roslaunch service_robot_navigation sim_mapping.launch
```

Use teleoperation or `/cmd_vel` commands to cover the whole map. Avoid excessive spinning and move through every test area.

Save the map:

```bash
rosrun service_robot_navigation save_map.sh indoor
```

Stop the mapping launch after `indoor.pgm` and `indoor.yaml` appear under `maps/`.

## 4. Start localization and navigation

```bash
roslaunch service_robot_navigation sim_navigation.launch
```

In RViz:

1. Use **2D Pose Estimate** to set the robot pose if AMCL does not initialize at the correct pose.
2. Use **2D Nav Goal** to issue a navigation goal.

## 5. Important omnidirectional settings

- AMCL uses `odom_model_type: omni`.
- DWA uses nonzero `max_vel_y`, `min_vel_y`, and `vy_samples > 1`.
- DWAPlannerROS does not require a `holonomic_robot` parameter.
- The robot is circular, so costmaps use `robot_radius: 0.27`.
