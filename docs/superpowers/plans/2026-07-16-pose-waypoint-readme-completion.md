# 位姿型五任务完成状态 README 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将根 README 更新为位姿型 waypoint 五项任务已在 Ubuntu ROS/Gazebo 中完整通过、本阶段工作完成的当前交接文档。

**Architecture:** 只重写根目录 `README.md`，以 `main` 当前配置、脚本和用户提供的 Ubuntu 验证结果为事实来源。删除围绕旧 Task 3 失败形成的状态、推测和待办，保留启动、参数、地图生成、通用 Debug 与本地静态验证说明。

**Tech Stack:** Markdown、ROS Noetic、Gazebo、move_base、Python unittest。

---

## 文件结构

- Modify: `README.md`
  - 当前项目状态、启动方式、完成的优化、五项位姿任务、地图维护、Debug 和静态测试。
- Verify only: `src/service_robot_navigation/config/task_tests.yaml`
  - 五项任务及 `[x, y, yaw]` waypoint 的事实来源。
- Verify only: `src/service_robot_navigation/config/dwa_local_planner_params.yaml`
  - README 中 `xy_goal_tolerance: 0.18` 的事实来源。
- Verify only: `src/service_robot_navigation/scripts/run_task_tests.py`
  - `move_base SUCCEEDED`、AMCL 初始化、clear-costmaps 和 fail-fast 语义来源。
- 不修改 Python、YAML、launch、URDF、world、地图或位置型 waypoint 分支。

### Task 1: 用当前完成状态重写根 README

**Files:**

- Modify: `README.md:1-496`

- [ ] **Step 1: 运行过期状态扫描并确认文档 RED**

运行：

```powershell
rg -n 'Task 3 未通过|Task 4、Task 5 未执行|2/3|当前静态测试共 `10`|下一阶段应先补齐 Task 3' README.md
```

预期：命令返回多个匹配，证明 README 仍描述旧失败状态。

- [ ] **Step 2: 将 README 完整替换为以下内容**

````markdown
# Service Robot ROS/Gazebo Project Handoff

本项目是运行在 Ubuntu 20.04、ROS Noetic 和 Gazebo 上的室内服务机器人仿真工程，
包含四全向轮机器人、室内 world、地图生成、定位导航以及顺序任务测试程序。

截至 2026-07-16，`main` 分支当前的位姿型 waypoint 方案已经在 Ubuntu
ROS/Gazebo 环境完成五项任务的连续顺序测试，最终结果为：

```text
Task test summary: 5/5 tasks passed
```

五项任务的所有 waypoint 均为完整 `[x, y, yaw]` 位姿。本阶段的导航任务配置、
脚本成功判定和五任务运行验证已经完成。

## 1. 工作区结构

```text
service_robot/
  scripts/
    world_to_map.py                         # 从 Gazebo world 生成 PGM/YAML 地图
  src/
    my_world/
      worlds/indoor.world                   # Gazebo 静态室内环境
      平面图.png                              # 场景设计图
    service_robot_sim/
      launch/omni4_indoor.launch            # 启动 Gazebo world 和机器人
    service_robot_navigation/
      launch/sim_mapping.launch             # 仿真建图
      launch/sim_navigation.launch          # 仿真定位导航
      config/*.yaml                         # AMCL、move_base、DWA、costmap、任务配置
      config/task_tests.yaml                # 五项位姿型任务
      maps/indoor.pgm
      maps/indoor.yaml
      scripts/run_task_tests.py             # 顺序执行五项任务
      scripts/save_map.sh
    sweeper_robot_omni4_base_ros/
      urdf/sweeper_robot_omni4_base.urdf    # 四全向轮底盘、雷达和 Gazebo 插件
      meshes/                               # 轻量化模型
  tests/
    test_robot_optimization_config.py
    test_task_test_runner_config.py
    test_world_geometry.py
```

## 2. Ubuntu 构建与运行

安装依赖并构建：

```bash
cd ~/service_robot
rosdep install --from-paths src --ignore-src -r -y
catkin_make
source devel/setup.bash
```

终端一启动导航仿真：

```bash
cd ~/service_robot
source devel/setup.bash
roslaunch service_robot_navigation sim_navigation.launch
```

等待 Gazebo、AMCL 和 `move_base` 就绪后，在终端二运行五项任务：

```bash
cd ~/service_robot
source devel/setup.bash
rosrun service_robot_navigation run_task_tests.py
```

也可以直接运行脚本：

```bash
cd ~/service_robot/src/service_robot_navigation/scripts
python3 run_task_tests.py
```

推荐优先使用 `rosrun`，以同时验证 catkin 安装路径和运行依赖。

## 3. 已完成的优化

### 3.1 机器人模型

- 已替换体积过大的轮子 mesh，Gazebo/RViz 不再出现明显模型加载卡顿。
- `/cmd_vel` 和 `/odom` 只作为 ROS/Gazebo 插件 topic，不再显示为底盘硬件模型。
- 雷达位于机器人中心。
- `+X` 为车头方向，并使用橙色箭头 visual 标识。
- Gazebo 激光可视化已关闭，以降低仿真渲染负载。

关键文件：

```text
src/sweeper_robot_omni4_base_ros/urdf/sweeper_robot_omni4_base.urdf
```

### 3.2 导航参数

当前 costmap 参数偏向通过窄门和窄通道：

```yaml
robot_radius: 0.25
footprint_padding: 0.0
inflation_radius: 0.26
cost_scaling_factor: 12.0
```

机器人半径为 `0.25 m`，膨胀半径为 `0.26 m`，意味着机器人外壳之外只保留
约 `0.01 m` 的额外代价缓冲。这是仿真测试中的通行性折中，不应直接作为真实
服务机器人的安全参数。

GlobalPlanner 当前关键参数：

```yaml
default_tolerance: 0.20
use_grid_path: false
```

`use_grid_path: false` 使用梯度回溯，避免窄通道等势区域中 GridPath 回溯循环。

DWA 当前关键参数：

```yaml
xy_goal_tolerance: 0.18
yaw_goal_tolerance: 0.20
min_vel_theta: 0.05
latch_xy_goal_tolerance: true
```

关键文件：

```text
src/service_robot_navigation/config/costmap_common_params.yaml
src/service_robot_navigation/config/global_planner_params.yaml
src/service_robot_navigation/config/dwa_local_planner_params.yaml
```

### 3.3 顺序任务测试脚本

`run_task_tests.py` 会：

- 等待 `move_base` action server。
- 按配置发布并等待 AMCL 初始位姿收敛。
- 按 `task_tests.yaml` 顺序执行任务和 waypoint。
- 对尚未满足的 waypoint 调用 `/move_base/clear_costmaps`。
- 当前位姿已经满足 XY/yaw 容差时跳过重复 goal。
- 在 timeout 时先保存 action state，再取消 goal并输出诊断。
- 对非 `SUCCEEDED` action state 输出当前位姿、目标位姿和最终误差。
- 以 `move_base SUCCEEDED` 作为 waypoint 最终成功标准；成功后的 AMCL 误差只进入摘要。
- 任一 waypoint 失败后 fail-fast，不继续执行后续任务。

关键文件：

```text
src/service_robot_navigation/config/task_tests.yaml
src/service_robot_navigation/scripts/run_task_tests.py
```

## 4. 五项位姿任务与验收结果

所有任务均已在 Ubuntu ROS/Gazebo 中按以下顺序通过：

| 任务 | Waypoint 顺序 | 目的 | 结果 |
| --- | --- | --- | --- |
| Task 1 | `take_medicine -> ward_a` | 取药并送至病房 A | PASS |
| Task 2 | `take_medicine -> ward_b` | 取药并送至病房 B | PASS |
| Task 3 | `long_counter_left -> long_counter_middle -> long_counter_right` | 依次服务长柜台三人 | PASS |
| Task 4 | `staggered_entry -> staggered_mid -> staggered_exit` | 强制通过横向错位通道 | PASS |
| Task 5 | `narrow_entry -> narrow_mid -> narrow_exit -> dock` | 强制通过狭窄区域并到达停靠点 | PASS |

Task 4、Task 5 的中转点用于约束机器人必须经过指定测试区域。当前验收版本中，
这些中转点与其他任务点一样，均包含目标 yaw。

本次完成状态只记录用户已经确认的五任务成功结果，不推断连续运行轮数、总耗时
或未提供的最终误差值。

## 5. World 与地图维护

Gazebo 场景源文件：

```text
src/my_world/worlds/indoor.world
```

如果修改了墙体、门、柜台或障碍物几何，应重新生成导航地图。项目提供：

```text
scripts/world_to_map.py
```

当前 world 的推荐命令：

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

输出文件：

```text
src/service_robot_navigation/maps/indoor.pgm
src/service_robot_navigation/maps/indoor.yaml
```

修改 world 后必须同步检查 `task_tests.yaml` 中的 waypoint 是否仍位于可通行区域。

## 6. Debug 与回归建议

如果后续修改引入导航失败，在 RViz 中同时检查：

```text
/map
/move_base/global_costmap/costmap
/move_base/local_costmap/costmap
/move_base/GlobalPlanner/plan
/move_base/DWAPlannerROS/local_plan
```

常用命令：

```bash
rostopic echo -n 1 /amcl_pose
rostopic echo -n 1 /move_base/status
rostopic echo -n 1 /move_base/result
rostopic echo -n 1 /cmd_vel
rosservice call /move_base/clear_costmaps "{}"
```

判断顺序：

1. 全局 costmap 已堵死：先检查 world、地图和 inflation，不要只调 DWA。
2. 全局路径存在但机器人不走：检查局部 costmap、激光障碍层和 DWA 轨迹。
3. 机器人已接近目标但 action 未成功：比较 XY/yaw 误差与 DWA 成功容差。
4. 修改 world、地图、导航参数或 waypoint 后：重新运行完整五任务回归。

## 7. Windows 本地静态测试

以下测试不依赖 ROS runtime：

```powershell
cd D:\service_robot
python -m unittest discover -s tests -v
```

当前 `main` 分支共 `18` 项静态测试，覆盖：

- URDF 接口语义、雷达位置和车头标识。
- costmap、DWA、GlobalPlanner 关键参数。
- 五项任务的顺序和完整位姿 waypoint。
- runner 的角度、位姿误差、action 成功/失败、timeout 和诊断摘要。
- ROS 运行依赖声明。
- 横向错位通道墙体拐角连接关系。

本地静态测试只能验证仓库配置和纯 Python 逻辑，不能替代 Ubuntu
ROS Noetic/Gazebo 中的 `catkin_make`、节点通信和真实导航回归。

## 8. 当前结论

- 位姿型 waypoint 五项任务已全部通过，本阶段工作完成。
- Task 1、2 只保留业务起点和终点，由全局规划器选择具体路线。
- Task 3 通过三个长柜台位姿点依次完成服务。
- Task 4、5 使用完整位姿中转点，强制机器人通过指定测试区域。
- `move_base SUCCEEDED` 是 waypoint 的最终成功标准，AMCL 误差用于结果记录和失败诊断。
- 当前窄通道参数优先保证仿真通行性；如果迁移到真实机器人，必须重新评估安全余量。
- 后续只有在 world、地图、导航参数、机器人尺寸或 waypoint 发生变化时，才需要重新开启调参与完整回归。
````

- [ ] **Step 3: 扫描必须存在的完成状态**

运行：

```powershell
rg -n '5/5 tasks passed|位姿型 waypoint 五项任务已全部通过|xy_goal_tolerance: 0.18|move_base SUCCEEDED|当前 `main` 分支共 `18` 项' README.md
```

预期：五类当前事实均至少匹配一次。

- [ ] **Step 4: 扫描并拒绝过期结论**

运行：

```powershell
$stale = rg -n 'Task 3 未通过|Task 4、Task 5 未执行|2/3|下一阶段应先补齐 Task 3|当前静态测试共 `10`' README.md
if ($LASTEXITCODE -eq 0) { $stale; exit 1 }
exit 0
```

预期：退出码为 0，无过期结论输出。

- [ ] **Step 5: 运行静态回归和格式检查**

运行：

```powershell
python -m unittest discover -s tests -v
git diff --check
git status --short
```

预期：18 项测试全部通过；`git diff --check` 无输出；`git status --short`
只显示 `README.md`。

- [ ] **Step 6: 检查修改范围并提交**

运行：

```powershell
git diff --name-only
git diff -- README.md
```

预期：实现差异只有 `README.md`，内容不包含位置型 waypoint 分支说明或伪造的
运行轮数、耗时和误差。

提交：

```powershell
git add README.md
git commit -m "docs: mark pose waypoint tasks complete"
```

### Task 2: 最终文档验收

**Files:**

- Verify: `README.md`
- Verify: `src/service_robot_navigation/config/task_tests.yaml`

- [ ] **Step 1: 对照配置核对 README 中的任务顺序**

确认 README 与 YAML 一致：

```text
Task 1: take_medicine -> ward_a
Task 2: take_medicine -> ward_b
Task 3: long_counter_left -> long_counter_middle -> long_counter_right
Task 4: staggered_entry -> staggered_mid -> staggered_exit
Task 5: narrow_entry -> narrow_mid -> narrow_exit -> dock
```

预期：没有旧 Task 2 六点返回路线，没有遗漏 Task 3/4/5 中转点。

- [ ] **Step 2: 重新运行最终验证**

```powershell
python -m unittest discover -s tests -v
git diff --check HEAD~1..HEAD
git status --short
```

预期：18 项测试全部通过；提交格式检查通过；工作树干净。

- [ ] **Step 3: 记录 Ubuntu 验证边界**

最终交接必须明确：

```text
用户已在 Ubuntu ROS/Gazebo 中确认位姿型五项任务全部成功。
本次 README 更新没有重新运行 Gazebo，也没有修改导航代码或配置。
```

## 计划自检

- 完整覆盖已确认设计中的当前状态、五项任务、成功标准、地图维护、Debug 和静态测试。
- 删除旧 Task 3 失败分析及其派生待办，不保留相互冲突的历史状态。
- 使用当前仓库实际参数 `xy_goal_tolerance: 0.18` 和当前实际测试数 `18`。
- 不提位置型 waypoint 分支，不修改任何代码或配置。
- 不写入用户未提供的运行轮数、耗时或 waypoint 最终误差。
