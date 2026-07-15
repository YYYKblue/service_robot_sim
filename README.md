# Service Robot ROS/Gazebo Project Handoff

本项目是运行在 Ubuntu 20.04 + ROS Noetic + Gazebo 上的室内服务机器人仿真工程。当前机器人已经可以启动 Gazebo、建图、保存地图、导航，并具备一套按任务顺序执行的 Python 导航测试程序。2026-07-15 的最新完整脚本运行中，Task 1、Task 2 已通过，Task 3 在长柜台第一个服务点超时，Task 4、Task 5 因 fail-fast 尚未执行。后续重点是定位 Task 3 的局部规划瓶颈，然后完成剩余任务回归。

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

- `use_grid_path: false` 已在 Gazebo runtime 中生效。此前反复出现的
  `Failed to get a plan from potential when a legal potential was found` / `NO PATH!`
  在本轮脚本测试中未再出现。
- AMCL 初始化已验证：本轮初始位姿收敛误差为 `xy=0.004 m`、`yaw=0.002 rad`。
- Task 1 通过：取药点到病房 A。
- Task 2 通过：以下 6 个 waypoint 全部成功：

```text
ward_a_door -> staggered_exit -> staggered_mid -> staggered_entry -> take_medicine -> ward_b
```

- Task 3 在第一个 waypoint `long_counter_left [1.55, 2.15, 1.5708]` 等待
  `90.0 s` 后超时。
- Task 4、Task 5 未执行；脚本在 Task 3 失败后按 fail-fast 规则结束。
- 本轮结果是 `2/3` 个已执行任务通过，不能写成 `2/5` 全量任务通过。
- Task 1、Task 2 目前只有本轮成功证据，仍需至少再做两次连续回归来判断稳定性。

关键文件：

```text
src/service_robot_navigation/config/task_tests.yaml
src/service_robot_navigation/scripts/run_task_tests.py
```

## 4. 当前主要问题：Task 3 局部规划超时

本轮日志没有再次出现全局规划器的 `NO PATH!`。当前失败表现为：

```text
Sending waypoint: long_counter_left -> [1.55, 2.15, 1.5708]
Task task_3_long_counter_service failed at waypoint long_counter_left:
timeout after 90.0s
```

### 4.1 目标点本身不是最窄位置

根据 `indoor.world` 碰撞几何计算：

```text
long_counter_left 中心:       [1.55, 2.15]
long_tabble 下边缘:            y = 2.60
中心到柜台碰撞体距离:          0.45 m
扣除 robot_radius=0.25 后间隙: 0.20 m
超出 inflation_radius=0.26:   0.19 m
```

因此“目标中心已经落入障碍或致命膨胀层”与当前静态几何不符。截图中机器人也已经接近长柜台左服务点，不能仅凭超时把目标点判定为不可达。

### 4.2 从病房 B 离开时存在更危险的瓶颈

Task 2 结束于 `ward_b [5.15, 2.4]`。Task 3 前往长柜台时必须绕过病房 B 左墙底端：

```text
B_left 底端:       y = 1.75
B_bottom 上沿:     y = 1.10
两者垂直净口:      0.65 m
机器人直径:        0.50 m
理论居中外壳余量:  每侧约 0.075 m
```

对当前 PGM 做 `0.25 m` 车体半径膨胀后的静态 A* 检查，路径仍连通，但最窄采样点约为：

```text
[4.225, 1.525]
机器人中心到 B_left: 约 0.257 m
扣除车体半径后余量:   约 0.007 m
```

PGM 栅格距离变换得到的最小中心净空约 `0.269 m`，也只有约 `0.019 m` 车体余量。连续几何与 5 cm 栅格存在量化差异，但两者都说明这段路线是临界通道。定位误差、激光标记或 DWA 连续轨迹检查都可能让静态全局路径可达、局部轨迹却暂时无解。

### 4.3 两条警告的含义

```text
Clearing both costmaps outside a square (2.00m) large centered on the robot.
```

这是 `move_base` 在规划器或控制器持续失败后进入 costmap recovery 的结果，不是根因。该警告出现在仿真时间 `220.403 s`，位于 Task 3 执行期间，证明 Task 3 中至少触发过一次恢复行为。

```text
DWA planner failed to produce path.
```

表示当时 DWA 采样不到合法局部轨迹。不过给出的时间 `133.099 s` 位于本轮 Task 2，而不是 Task 3，不能直接作为 `long_counter_left` 失败的证据。

### 4.4 仍未确认的分支

当前脚本超时时只记录 `timeout`，没有记录超时瞬间的 AMCL 位姿、目标误差、action state 和 `/cmd_vel`。因此尚不能区分：

1. 机器人主要耗时或卡在 `B_left` / `B_bottom` 临界净口。
2. 机器人已到达 `long_counter_left` 附近，但没有进入 DWA 的 `0.15 m` XY 或 `0.20 rad` yaw 成功容差。
3. 局部 costmap 中存在由激光层写入、静态 PGM 中没有的障碍。

在取得这些运行时证据前，不应先移动 Task 3 目标点或继续大幅修改 DWA 参数。

## 5. 推荐的后续路线

### 5.1 先复现并定位 Task 3

下一次运行时，在 Task 3 卡住期间保存以下信息：

```bash
rostopic echo -n 1 /amcl_pose
rostopic echo -n 1 /move_base/status
rostopic echo -n 1 /cmd_vel
rostopic echo -n 1 /move_base/DWAPlannerROS/local_plan
```

RViz 必须同时显示：

```text
/move_base/global_costmap/costmap
/move_base/local_costmap/costmap
/move_base/GlobalPlanner/plan
/move_base/DWAPlannerROS/local_plan
```

重点截取两个位置：`B_left` 底端附近，以及 `long_counter_left` 最终停车位置。还需要保留触发 costmap recovery 前 10 秒的 `move_base` 终端日志。

### 5.2 根据证据修改 Gazebo world 几何

如果确认局部规划在病房 B 出口瓶颈失败，优先修改：

```text
src/my_world/worlds/indoor.world
```

第一目标是把 `B_left` 底端和 `B_bottom` 上沿之间当前约 `0.65 m` 的净口扩大到至少 `0.85 m`。之后再处理以下尚未完成全量回归的区域：

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

### 5.3 修改 world 后重新生成导航地图

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

### 5.4 修改任务点

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
- 横向错位通道墙体拐角连接关系。

当前静态测试共 `10` 项。它们只检查仓库内容，不能替代 ROS/Gazebo 运行验证。

## 8. 接手时的优先级

建议后续 agent 按以下顺序工作：

1. 保持当前 `use_grid_path: false`，不要重新开启 GridPath。
2. 复现 Task 3，记录超时瞬间位姿、目标误差、action state、`cmd_vel` 和局部路径。
3. 判断失败发生在 `B_left` 底端瓶颈，还是发生在 `long_counter_left` 最终收敛阶段。
4. 若是瓶颈，先扩大 `B_left` / `B_bottom` 净口，再同步生成 `indoor.pgm/yaml` 和 `src/my_world/平面图.png`。
5. 若机器人已在目标附近，再检查 DWA 成功容差和目标 yaw；不要先用增加 90 秒 timeout 掩盖问题。
6. Task 3 连续通过至少 3 次后，继续执行尚未验证的 Task 4、Task 5。
7. 最终目标是五个任务连续完整通过至少 2 轮，并记录每轮 waypoint 误差与耗时。

## 9. 当前重要结论

- 机器人直径 0.5 m，理论能通过 0.75 m 门，但每侧余量只有 12.5 cm；在栅格地图、costmap inflation、定位误差、局部规划误差叠加后，这是临界场景。
- 全向轮提高的是局部运动能力，不会绕过全局 costmap 的可通行性判断。
- `use_grid_path: false` 已解决此前势场合法但 GridPath 回溯失败的 runtime 问题；不要把当前 Task 3 超时与旧 `NO PATH!` 混为同一故障。
- `long_counter_left` 本身有约 `0.20 m` 外壳间隙，当前更值得怀疑的是从病房 B 离开时仅约 `0.65 m` 的几何净口，以及最终姿态是否满足 DWA 成功条件。
- Task 1、Task 2 已在一轮脚本测试中通过；Task 3 未通过；Task 4、Task 5 仍无本轮运行结果。
- 当前项目已经具备测试框架；下一阶段应先补齐 Task 3 的运行时证据，再做单变量修改和完整回归。
