# Service Robot ROS/Gazebo Project Handoff

本项目是运行在 Ubuntu 20.04 + ROS Noetic + Gazebo 上的室内服务机器人仿真工程。当前机器人已经可以启动 Gazebo、建图、保存地图、导航，并具备一套按任务顺序执行的 Python 导航测试程序。后续主要工作不再是基础跑通，而是提升门框、狭窄通道、横向错位通道等临界区域的导航稳定性。

## 1. 工作区结构

```text
service_robot/
  scripts/
    world_to_map.py                         # 从 Gazebo world 直接生成 PGM/YAML 地图
  src/
    my_world/
      worlds/indoor.world                   # Gazebo 静态室内环境
      平面图.png                              # 场景设计图
    service_robot_sim/
      launch/omni4_indoor.launch            # 同时启动 Gazebo world 和机器人
    service_robot_navigation/
      launch/sim_mapping.launch             # 仿真建图
      launch/sim_navigation.launch          # 仿真定位导航
      config/*.yaml                         # AMCL、move_base、DWA、costmap、任务测试配置
      config/task_tests.yaml                # 五个任务的位姿 waypoint 配置
      maps/indoor.pgm
      maps/indoor.yaml                      # 当前导航地图，已改为 world_to_map 生成风格
      scripts/run_task_tests.py             # 顺序执行五个导航任务
      scripts/save_map.sh
    sweeper_robot_omni4_base_ros/
      urdf/sweeper_robot_omni4_base.urdf    # 四全向轮底盘、雷达、Gazebo 插件
      meshes/                               # 已替换为轻量化模型，当前运行不卡顿
  tests/
    test_robot_optimization_config.py
    test_task_test_runner_config.py         # 本地静态测试，不依赖 ROS runtime
```

## 2. 基础启动

在 Ubuntu 20.04 ROS Noetic 环境中：

```bash
cd ~/service_robot
rosdep install --from-paths src --ignore-src -r -y
catkin_make
source devel/setup.bash
```

启动导航仿真：

```bash
roslaunch service_robot_navigation sim_navigation.launch
```

启动顺序任务测试：

```bash
source ~/service_robot/devel/setup.bash
rosrun service_robot_navigation run_task_tests.py
```

如果直接在脚本目录运行也可以：

```bash
cd ~/service_robot/src/service_robot_navigation/scripts
python3 run_task_tests.py
```

但推荐使用 `rosrun`，这样能验证 catkin 安装路径和包依赖。

## 3. 当前已经完成的优化

### 3.1 机器人模型

- 已将原先非常大的轮子 mesh 交由建模侧优化并替换。
- 当前运行 Gazebo/RViz 已无明显模型加载卡顿。
- URDF 中 `/cmd_vel` 和 `/odom` 不再表现为底盘上的可见硬件接口；它们只作为 ROS/Gazebo 插件 topic 存在。
- 雷达已放回机器人中心。
- `+X` 方向已作为车头，并用橙色箭头 visual 标识。

关键文件：

```text
src/sweeper_robot_omni4_base_ros/urdf/sweeper_robot_omni4_base.urdf
```

### 3.2 导航参数

当前 costmap 参数偏向“允许通过窄门/窄通道”，不是保守安全配置：

```yaml
robot_radius: 0.25
footprint_padding: 0.0
inflation_radius: 0.26
cost_scaling_factor: 12.0
```

注意：`inflation_radius` 是从障碍物向外算的距离，也可以理解为机器人中心到障碍物的代价影响范围。对于直径 0.5 m 的圆形机器人：

```text
robot_radius = 0.25
inflation_radius = 0.26
```

意味着机器人外壳只保留约 1 cm 的额外代价缓冲。这个配置是为当前窄门测试做出的折中，不能简单视为真实安全导航参数。

全局规划器当前使用：

```yaml
use_grid_path: false
default_tolerance: 0.20
```

`use_grid_path: false` 使用 GlobalPlanner 默认的梯度回溯。栅格回溯在窄通道的等势区域可能循环并报出
`NO PATH!`，即使势场计算已经确认目标可达。

DWA 当前使用：

```yaml
xy_goal_tolerance: 0.15
yaw_goal_tolerance: 0.20
min_vel_theta: 0.05
```

关键文件：

```text
src/service_robot_navigation/config/costmap_common_params.yaml
src/service_robot_navigation/config/global_planner_params.yaml
src/service_robot_navigation/config/dwa_local_planner_params.yaml
```

### 3.3 任务测试脚本

`run_task_tests.py` 会：

- 发布 AMCL 初始位姿。
- 按 `task_tests.yaml` 顺序执行任务。
- 每个 waypoint 都是 `[x, y, yaw]` 位姿，而不是单纯位置。
- 每个未满足的 waypoint 前调用 `/move_base/clear_costmaps`。
- 如果当前位姿已经满足 waypoint 容差，则跳过发送 `move_base` goal，避免出生点原地打转。
- fail-fast：某个 waypoint 失败后停止后续任务。

当前任务：

```text
task_1_take_medicine_to_ward_a
task_2_take_medicine_to_ward_b
task_3_long_counter_service
task_4_staggered_channel
task_5_narrow_area_to_dock
```

最新测试观察：

- Task 1 已经能够通过。
- Task 2 从病房 A 返回取药台时，曾在横向错位通道拐角处卡死；之后已将 task2 拆成多个中途点：

```text
ward_a_door -> staggered_exit -> staggered_mid -> staggered_entry -> take_medicine -> ward_b
```

是否完全稳定仍需要后续继续实机仿真验证。

关键文件：

```text
src/service_robot_navigation/config/task_tests.yaml
src/service_robot_navigation/scripts/run_task_tests.py
```

## 4. 当前主要问题

多轮测试显示，机器人在经过门框、横向错位通道、狭窄区域时仍容易出现：

```text
NO PATH!
Failed to get a plan from potential when a legal potential was found.
move_base returned state 4
```

已经确认：

- 单纯轻量化模型解决了卡顿，但不解决窄通道规划失败。
- 单纯把 gmapping 毛刺地图换成更干净的 PGM/YAML，效果仍然一般。
- 失败点通常位于门框、拐角、高代价包围区域。
- 任务点或中途点如果太靠近障碍，也会导致规划失败。

目前判断：根因不只是地图毛刺，而是 Gazebo world 中部分门框、通道、拐角本身对 0.5 m 直径机器人来说余量偏小。全向轮能改善局部运动自由度，但 `move_base` 的全局规划仍然基于 2D costmap。如果 costmap 认为中心线不连续，全向轮也无法强行通过。

## 5. 推荐的后续路线

### 5.1 优先修改 Gazebo world 几何

下一步建议直接修改：

```text
src/my_world/worlds/indoor.world
```

目标是适当加大以下区域净宽：

- 病房 A/B 门框。
- 横向错位通道拐角。
- 狭窄区域障碍间距。
- 充电/停靠区入口。
- 长柜台右侧服务点附近。

重点不是无限扩大场景，而是让 0.5 m 机器人至少有稳定的中心线余量。建议目标：

```text
普通门/窄通道净宽: 尽量 >= 0.85 m
高难度测试通道净宽: 不低于 0.75 m
拐角处有效可通行圆角/空间: 尽量留出 0.8 m 以上局部转圜空间
服务点中心到最近障碍距离: 尽量 >= 0.35 m
```

当前世界文件中和任务强相关的模型名：

```text
护士站/取药台:
  hushizhan_*
  hushizhan_tabble
  service_1

横向错位通道:
  heng_top_a
  heng_top_b
  heng_left
  heng_right
  heng_bottom_a
  heng_bottom_b

病房 A:
  A_left_a
  A_left_b
  A_bottom_a
  A_bottom_b
  A_bed
  A_tabble
  service_2

长柜台服务区:
  long_top_a
  long_top_b
  long_tabble
  service_3
  service_4
  service_5

病房 B:
  B_left
  B_bottom
  B_right_a
  B_right_b
  B_bed
  B_tabble
  service_6

狭窄区域:
  L_top
  L_bottom
  L_shu
  L_yuanzhu
  narrow_obs_L1
  narrow_obs_L2
  narrow_obs_L3

停靠/充电区:
  charge_top
  charge_left
  charge
  charge_sign
  service_7
```

### 5.2 修改 world 后重新生成导航地图

不要再优先用 gmapping 反推地图。当前项目已有 world 转地图脚本：

```text
scripts/world_to_map.py
```

推荐使用方式示例：

```bash
cd ~/service_robot
python3 scripts/world_to_map.py \
  src/my_world/worlds/indoor.world \
  src/service_robot_navigation/maps/indoor \
  --xmin -0.25 \
  --xmax 14.25 \
  --ymin -0.25 \
  --ymax 10.25 \
  --resolution 0.05 \
  --min-obstacle-z 0.05 \
  --max-obstacle-z 1.5
```

生成后会得到：

```text
src/service_robot_navigation/maps/indoor.pgm
src/service_robot_navigation/maps/indoor.yaml
```

当前 `indoor.yaml` 已是相对路径形式：

```yaml
image: indoor.pgm
resolution: 0.05
origin: [-0.25, -0.25, 0.0]
```

这比绝对路径更适合交接和换机器。

### 5.3 修改任务点

修改 world 几何后，必须重新核对：

```text
src/service_robot_navigation/config/task_tests.yaml
```

尤其是：

- `ward_a_door`
- `staggered_exit`
- `staggered_mid`
- `staggered_entry`
- `long_counter_right`
- `narrow_*`
- `dock`

原则：

- waypoint 不能放在高代价区或障碍边缘。
- 需要通过指定区域的任务必须给入口、中点、出口，不要只给最终点。
- 每个任务点都应保留 yaw，用于体现全向轮在保持朝向时横移/斜移的优势。

## 6. Debug 建议

在 RViz 中同时打开：

```text
/map
/move_base/global_costmap/costmap
/move_base/local_costmap/costmap
/move_base/GlobalPlanner/plan
/move_base/DWAPlannerROS/local_plan
```

判断失败类型：

```text
global_costmap 中通道已经被堵死:
  优先改 world 几何或地图生成脚本，不要继续盲目调 DWA。

global plan 有路，但 local plan 不走:
  看 DWA 参数、局部障碍层、激光残留、机器人当前 yaw。

目标点在高代价区:
  移动 waypoint 或放宽 default_tolerance/xy_tolerance。

机器人在原地旋转:
  检查 yaw_goal_tolerance、min_vel_theta、AMCL 初始位姿和目标 yaw。
```

常用排查命令：

```bash
rostopic echo /amcl_pose
rostopic echo /move_base/status
rostopic echo /move_base/result
rosservice call /move_base/clear_costmaps "{}"
```

## 7. 本地静态测试

这些测试可在 Windows 或无 ROS 的 Python 环境中运行，用于检查配置结构，不验证 Gazebo runtime：

```bash
cd D:/service_robot
python -m unittest discover -s tests -v
```

当前测试覆盖：

- URDF 语义清理。
- 雷达居中和车头标识。
- costmap / DWA / GlobalPlanner 关键参数。
- `task_tests.yaml` 的任务顺序和 waypoint 结构。
- `run_task_tests.py` 的纯 Python 工具函数。
- ROS 运行依赖声明。

## 8. 接手时的优先级

建议后续 agent 按以下顺序工作：

1. 先不要继续大幅调整 navigation 参数。
2. 修改 `indoor.world`，扩大门框、横向错位通道和狭窄区域的实际净宽。
3. 用 `scripts/world_to_map.py` 重新生成 `indoor.pgm/yaml`。
4. 在 RViz 检查 `/map` 与 `global_costmap`，确认关键通道没有被高代价区域封死。
5. 微调 `task_tests.yaml` 中的 waypoint。
6. 运行 `run_task_tests.py`，记录通过到第几个任务、失败 waypoint、`move_base` 状态码。
7. 只有在 world 几何和地图确认合理后，再微调 `inflation_radius`、DWA、GlobalPlanner。

## 9. 当前重要结论

- 机器人直径 0.5 m，理论能通过 0.75 m 门，但每侧余量只有 12.5 cm；在栅格地图、costmap inflation、定位误差、局部规划误差叠加后，这是临界场景。
- 全向轮提高的是局部运动能力，不会绕过全局 costmap 的可通行性判断。
- 如果门框或拐角本身接近临界，最稳的方案是改 Gazebo world 几何，然后用 world 直接生成干净地图。
- 当前项目已经具备测试框架；下一阶段应把主要精力放在地图几何与任务 waypoint 的协同优化上。
