# service_robot_diff_navigation

这是与 `service_robot_navigation` 对照使用的两驱差速轮导航包。它复用全向轮的室内 world、地图、五项任务和主要 move_base 参数，只将底盘运动学、AMCL 里程计模型和 DWA 横向速度约束改为差速轮版本。

## 启动

在 ROS Noetic 工作空间中：

```bash
source /opt/ros/noetic/setup.bash
source devel/setup.bash
roslaunch service_robot_diff_navigation diff_navigation.launch
```

无图形界面运行：

```bash
roslaunch service_robot_diff_navigation diff_navigation.launch gui:=false rviz:=false
```

另一个终端运行同一组五项顺序任务：

```bash
source devel/setup.bash
python3 src/service_robot_diff_navigation/scripts/run_task_tests.py
```

也可以用 `--config`、`--move-base`、`--pose-topic`、`--initial-pose-topic`、`--clear-costmaps-service` 和 `--server-timeout` 覆盖 runner 默认值。

## 对比边界

- 差速底盘车头与全向轮一样定义为 `+X`，左右轮中心位于 `y=±0.198 m`。
- 五项任务的 waypoint、顺序、容差、地图和出生位姿与全向轮完全一致。
- `/cmd_vel`、`/odom`、`/tf`、`/scan` 是导航通信接口，不以可见速度控制板或里程计模块表达。
- 差速轮不支持 `linear.y`；DWA 使用 `holonomic_robot: false`，关闭横向速度采样。
- 不要与全向轮仿真同时启动，因为两套模型使用相同的全局 ROS 话题和 TF 名称。

同一点位下的失败或不可达结果应保留为底盘对比证据，不通过修改任务点规避。
