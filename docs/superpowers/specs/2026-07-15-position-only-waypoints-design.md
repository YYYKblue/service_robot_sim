# 位置型中转 waypoint 设计

## 目标

让 Task 4 的三个通道测试点和 Task 5 的三个狭窄区域中转点只约束
XY 位置，不要求机器人到点时满足指定 yaw。Task 1、2、3 以及 Task 5
最终 `dock` 的完整位姿约束保持不变。

## 背景

ROS `move_base` 的目标消息必须包含完整姿态，不能直接发送一个只有
`x, y` 的 action goal。因此，位置型 waypoint 仍需构造一个合法四元数，
但任务执行器必须在机器人进入 XY 容差后主动结束该 waypoint，不能继续等待
DWA 对齐一个业务上没有意义的 yaw。

## 配置模型

每个 waypoint 必须且只能定义以下字段之一：

- `pose: [x, y, yaw]`：完整位姿型 waypoint。
- `position: [x, y]`：仅位置型 waypoint。

同时出现 `pose` 和 `position`，或二者都不存在，均视为配置错误。

Task 4 调整为：

```yaml
  - name: task_4_staggered_channel
    description: Traverse the horizontal staggered channel through required intermediate positions.
    waypoints:
      - name: staggered_entry
        position: [4.5, 8.0]
        xy_tolerance: 0.30
      - name: staggered_mid
        position: [6.55, 7.15]
        xy_tolerance: 0.30
      - name: staggered_exit
        position: [8.4, 6.4]
        xy_tolerance: 0.30
```

Task 5 调整为：

```yaml
  - name: task_5_narrow_area_to_dock
    description: Pass through the narrow area and finish at the docking pose.
    waypoints:
      - name: narrow_entry
        position: [7.2, 2.5]
      - name: narrow_mid
        position: [9.0, 2.5]
      - name: narrow_exit
        position: [11.4, 2.5]
      - name: dock
        pose: [13.25, 2.6, 0.0]
        hold_time: 2.0
```

Task 4 的现有 `yaw_tolerance` 删除，因为位置型 waypoint 不读取该设置。
Task 5 的 `dock` 继续使用默认 yaw 容差。

## 目标构造

完整位姿型 waypoint 按现有逻辑使用配置中的 yaw。

位置型 waypoint 发送 goal 前读取机器人当前 AMCL yaw，并以该 yaw 构造合法
四元数。这个 yaw 只用于满足 `move_base` 消息格式，不是 waypoint 的成功条件。

## 成功判定

### 完整位姿型 waypoint

保持现有行为：

- 发送前同时检查 XY 和 yaw。
- `move_base SUCCEEDED` 后判定成功。
- 最终摘要记录 XY/Yaw 误差。

### 位置型 waypoint

执行器按短周期轮询 action 和 AMCL：

1. 发送前只检查 XY；已经进入容差则直接跳过。
2. 发送 goal 后，每次短暂等待 action，再读取当前 AMCL 位姿。
3. 当前 XY 误差进入 `xy_tolerance` 时，保存取消前 action state，取消 goal，
   将 waypoint 判定为成功。
4. 若 action 先返回 `SUCCEEDED`，也将 waypoint 判定为成功。
5. 若 action 先返回其他终态且 XY 尚未满足，返回失败诊断。
6. 到达 timeout 时取消 goal，并返回 timeout 诊断。

位置型成功结果只保存 `error: {xy: ...}`，摘要不输出 yaw。

## 纯函数边界

新增或调整以下纯函数，使 ROS 逻辑保持集中：

- 获取 waypoint 的目标类型与目标数值。
- 计算位置型 waypoint 的 XY 误差。
- 判断位置型 waypoint 是否满足 XY 容差。
- 格式化只有 XY 的成功摘要。
- 失败诊断支持 `target_position: [x, y]`，完整位姿诊断继续使用
  `target_pose: [x, y, yaw]`。

现有完整位姿函数和字段保持向后兼容。

## 错误处理

配置校验必须拒绝：

- `pose` 不是三个数值。
- `position` 不是两个数值。
- 同一个 waypoint 同时包含 `pose` 和 `position`。
- waypoint 既无 `pose` 也无 `position`。

位置型执行期间若 AMCL 暂时读取失败，记录 warning 并继续等待，直到 action
结束或 timeout；一次读取失败不能立即终止任务。

timeout、非成功 action state、fail-fast 和 clear-costmaps 行为保持不变。

## 文件范围

修改：

- `src/service_robot_navigation/config/task_tests.yaml`
- `src/service_robot_navigation/scripts/run_task_tests.py`
- `tests/test_task_test_runner_config.py`

不修改：

- Task 1、2、3 waypoint。
- Task 5 的 `dock` 位姿。
- DWA、GlobalPlanner、costmap、AMCL 参数。
- Gazebo world 与地图。

## 测试

测试先行覆盖：

1. 配置校验接受合法 `pose` 和 `position`。
2. 配置校验拒绝缺失目标、双目标和错误长度。
3. Task 4 三点全部使用 `position`，没有 `pose` 或 `yaw_tolerance`。
4. Task 5 三个中转点使用 `position`，`dock` 保持完整 `pose`。
5. 位置型 pre-check 只看 XY，不看 yaw。
6. goal 使用发送时当前 yaw 构造合法姿态。
7. XY 满足时先保存 state、再取消 goal，并返回成功。
8. 位置型 action 非成功、timeout 和 AMCL 暂时不可用的行为。
9. 摘要对位置型成功只显示 XY。
10. 现有完整位姿、失败诊断和五任务顺序测试继续通过。

## 验收

离线：

```powershell
python -m unittest discover -s tests -v
python -m py_compile src/service_robot_navigation/scripts/run_task_tests.py
git diff --check
```

Ubuntu ROS/Gazebo：

- Task 4 的入口、中点、出口只要求进入对应位置容差。
- Task 5 的三个狭窄区域点只要求进入位置容差。
- Task 5 的 `dock` 仍要求 `move_base` 完成最终姿态。
- Task 1、2、3 行为不变。
