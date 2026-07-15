# 导航任务路线与成功判定设计

## 目标

让五项导航测试严格表达用户确认的任务语义，并消除
`move_base` 已返回 `SUCCEEDED`、测试脚本却因随后一次 AMCL
采样轻微漂移而将 waypoint 判为失败的问题。

## 已确认的根因

Task 3 的最新运行结果中，`action_state=3`，即
`move_base` 已经判定 `long_counter_left` 成功。测试脚本随后读取
AMCL 位姿，得到 `xy=0.197 m`、`yaw=0.251 rad`；默认脚本容差为
`0.25 m / 0.25 rad`，yaw 仅超出约 `0.001 rad`。第二次 AMCL
采样因此推翻了 action 的成功结果，形成两套互相冲突的成功标准。

Task 2 当前包含多个横向错位通道中转点。这些 waypoint 是早期排查路线
卡死时加入的临时强制路径，但用户现已确认 Task 2 只要求去取药台取药并
送到病房 B，不要求经过指定区域。

## 成功判定

`move_base` action 的终态是 waypoint 的最终判定依据：

- `SUCCEEDED`：waypoint 成功。
- timeout：waypoint 失败，并保留 timeout 诊断。
- 其他 action state：waypoint 失败，并保留 state、目标位姿、可用的
  AMCL 位姿与误差诊断。

action 返回 `SUCCEEDED` 后，脚本仍读取一次 AMCL 位姿并计算 XY/Yaw
误差，但该误差只用于结果摘要，不再推翻成功状态。

发送目标前的“已经满足 waypoint”检查保持不变。它用于避免机器人已在目标
容差范围内时重复发送 goal。

## 五项任务定义

### Task 1：取药并送至病房 A

严格保留两个语义 waypoint：

```text
take_medicine -> ward_a
```

### Task 2：取药并送至病房 B

只保留两个语义 waypoint：

```text
take_medicine -> ward_b
```

Task 1 结束时机器人位于病房 A。Task 2 启动后，全局规划器自行选择从病房 A
到取药台、再到病房 B 的路线，不强制经过横向错位通道。

### Task 3：依次服务长柜台三个人

必须按顺序到达三个服务点：

```text
long_counter_left -> long_counter_middle -> long_counter_right
```

三个服务点的现有坐标、朝向和停留时间保持不变。

### Task 4：横向错位通道测试

保留入口、中点和出口，强制穿过目标区域：

```text
staggered_entry -> staggered_mid -> staggered_exit
```

### Task 5：狭窄区域到停靠点

保留狭窄区域的入口、中点、出口和最终停靠点：

```text
narrow_entry -> narrow_mid -> narrow_exit -> dock
```

## 文件范围

修改：

- `src/service_robot_navigation/config/task_tests.yaml`
  - 将 Task 2 从六个 waypoint 精简为 `take_medicine -> ward_b`。
- `src/service_robot_navigation/scripts/run_task_tests.py`
  - action 返回 `SUCCEEDED` 后不再以二次 AMCL 容差检查推翻结果。
- `tests/test_task_test_runner_config.py`
  - 锁定五项任务的 waypoint 语义与新的成功判定。

不修改：

- Task 1、3、4、5 的 waypoint 坐标和顺序。
- DWA、GlobalPlanner、costmap、AMCL 参数。
- Gazebo world 与导航地图。
- timeout、fail-fast、AMCL 初始化和 clear-costmaps 行为。

## 错误处理

timeout 和非 `SUCCEEDED` action state 继续进入现有失败诊断路径。
`SUCCEEDED` 后若能够读取 AMCL，则记录最终误差；本次范围不改变
`current_pose()` 读取异常的现有处理方式。

## 测试

测试先行，覆盖以下行为：

1. Task 2 的 waypoint 必须严格等于
   `[take_medicine, ward_b]`。
2. Task 3 必须严格保留三个服务点及顺序。
3. Task 4 必须保留横向错位通道入口、中点、出口。
4. Task 5 必须保留狭窄区域入口、中点、出口和 dock。
5. `move_base` 返回 `SUCCEEDED` 后，即使随后 AMCL 误差超出脚本
   默认容差，waypoint 仍返回成功，并在结果中记录误差。
6. timeout 与非成功 action state 的既有测试继续通过。

## 验收

离线验收：

```powershell
python -m unittest discover -s tests -v
python -m py_compile src/service_robot_navigation/scripts/run_task_tests.py
git diff --check
```

Ubuntu ROS/Gazebo 验收：

- Task 1、2 仅按任务语义导航，不再强制 Task 2 经过错位通道。
- Task 3 依次执行三个柜台服务点。
- Task 4、5 仍强制通过各自指定区域。
- action 返回 `SUCCEEDED` 时，测试摘要显示 waypoint 为 PASS，
  同时保留 XY/Yaw 误差用于观察。

