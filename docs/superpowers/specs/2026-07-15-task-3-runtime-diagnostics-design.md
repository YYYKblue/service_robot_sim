# Task 3 运行时诊断设计

## 目标

让任务执行器在 Task 3 超时时能够从终端输出中定位故障，并通过一次
ROS Noetic/Gazebo 复现选择唯一的后续修复分支。本次变更不调整导航参数、
不移动 waypoint，也不修改 world 几何。

## 现有证据

- 顺序任务执行器已完成过一次 Task 1 和 Task 2。
- Task 3 在 `long_counter_left` 等待 90 秒后超时。
- 使用 `use_grid_path: false` 后，之前的 GlobalPlanner `NO PATH!` 问题未再出现。
- 目前超时时执行器只报告耗时，无法区分机器人是卡在病房 B 出口、已到服务点附近但
  未收敛，还是被局部 costmap 的动态观测阻断。

## 范围

只修改 `src/service_robot_navigation/scripts/run_task_tests.py`：当 waypoint
超时或 action 返回非成功状态时，输出失败诊断证据。现有任务顺序、超时配置、
清理 costmap 的行为和 fail-fast 行为均保持不变。

为新增的纯 Python 格式化/计算辅助函数补充离线单元测试。ROS/Gazebo 复现及其
采集结果属于运行时验证，不是本次源码变更内容。

## 执行器行为

每个失败 waypoint 的结果中，在能够获取时加入 `diagnostics` 对象：

| 字段 | 来源 | 作用 |
| --- | --- | --- |
| `current_pose` | 最新 `/amcl_pose` | 定位失败时机器人所在位置。 |
| `target_pose` | waypoint 配置 | 保留原始目标位姿。 |
| `error` | 现有位姿误差计算 | 分离位置收敛与朝向收敛问题。 |
| `action_state` | `SimpleActionClient.get_state()` | 区分超时与终止 action 失败。 |
| `pose_error_message` | 读取 AMCL 失败时的异常 | 保留位姿不可读证据，且不掩盖原始失败原因。 |

发生超时时，执行器会先取消 goal，再读取一次最新位姿。如果读取失败，仍返回原有的
超时结果，并把异常文本放入诊断信息；不得把导航超时升级为未捕获的执行器异常。

控制台汇总对失败 waypoint 以单行、可读的形式打印诊断字段；成功和已满足的
waypoint 保持现有的简洁输出。

## 运行时复现步骤

在 Ubuntu 20.04 + ROS Noetic 环境中，以现有方式运行顺序任务执行器。Task 3
执行期间采集 `/amcl_pose`、`/move_base/status`、`/cmd_vel` 和
`/move_base/DWAPlannerROS/local_plan`；RViz 同时显示 global/local costmap、
global plan 和 DWA local plan。若触发 costmap recovery，保留前 10 秒的终端日志。

## 决策规则

1. 若最终位姿停在 `B_left`/`B_bottom` 开口附近，且局部路径缺失或持续被拒绝，
   则扩大 `indoor.world` 的该开口，重新生成 `indoor.pgm` 和 `indoor.yaml` 后复测。
2. 若最终位姿已接近 `long_counter_left`，但报告的 XY 或 yaw 误差仍超出容差，
   则先检查该 waypoint 的朝向和相关 DWA 目标容差，再决定是否改变几何。
3. 若静态全局路线连通，但局部 costmap 存在地图中没有的观测障碍，
   则检查激光 marking/clearing 行为，不改几何也不改规划容差。

任何分支都不得仅通过增加 timeout 掩盖无法收敛的目标。

## 验证

运行时复现前：

1. 在仓库根目录执行 `python -m unittest discover -s tests -v`。
2. 执行 `git diff --check`。

运行时复现后，结果必须包含失败 waypoint 的最终位姿（或明确的位姿读取失败）、
可用的目标误差、action state，以及四项要求采集的 ROS/RViz 观测。只有获得这些
证据后，后续改动才可以针对 world 几何、目标配置或 costmap 行为。

## 非目标

- 不重新启用 `use_grid_path`。
- 不在缺少新证据时调整 DWA 或 costmap 参数。
- 不修改 `task_tests.yaml` 的 waypoint 位置或容差。
- 不修改 `indoor.world`，也不重新生成地图。
