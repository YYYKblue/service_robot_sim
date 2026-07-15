# 导航任务路线与成功判定实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让五项任务的 waypoint 与用户确认的语义一致，并以 `move_base SUCCEEDED` 作为 waypoint 最终成功标准。

**Architecture:** `task_tests.yaml` 只负责声明任务必须到达的语义点或强制测试区域；全局规划器负责 Task 1、2 的具体路线。`run_task_tests.py` 保留 action 失败诊断，但 action 成功后的 AMCL 误差仅进入结果摘要，不再形成第二套失败判定。

**Tech Stack:** Python 3、ROS Noetic（rospy、actionlib、move_base）、PyYAML、unittest。

---

## 文件结构

- 修改：`src/service_robot_navigation/config/task_tests.yaml`
  - Task 2 精简为 `take_medicine -> ward_b`，其他任务的 waypoint 保持已确认顺序。
- 修改：`src/service_robot_navigation/scripts/run_task_tests.py`
  - 删除 `SUCCEEDED` 后以 AMCL 容差推翻成功的分支。
- 修改：`tests/test_task_test_runner_config.py`
  - 锁定五项任务路线语义和 action 成功判定。
- 不修改：DWA、GlobalPlanner、costmap、AMCL、world、地图及任务点坐标。

### Task 1: 将任务 waypoint 与任务语义对齐

**Files:**

- Modify: `tests/test_task_test_runner_config.py:26-70`
- Modify: `src/service_robot_navigation/config/task_tests.yaml:11-89`

- [ ] **Step 1: 先修改任务配置测试，使旧配置失败**

将 `test_task_config_defines_five_ordered_pose_tasks` 中任务 waypoint 的断言替换为以下精确结构：

```python
        expected_waypoints = {
            "task_1_take_medicine_to_ward_a": [
                "take_medicine",
                "ward_a",
            ],
            "task_2_take_medicine_to_ward_b": [
                "take_medicine",
                "ward_b",
            ],
            "task_3_long_counter_service": [
                "long_counter_left",
                "long_counter_middle",
                "long_counter_right",
            ],
            "task_4_staggered_channel": [
                "staggered_entry",
                "staggered_mid",
                "staggered_exit",
            ],
            "task_5_narrow_area_to_dock": [
                "narrow_entry",
                "narrow_mid",
                "narrow_exit",
                "dock",
            ],
        }

        for task in config["tasks"]:
            self.assertEqual(
                expected_waypoints[task["name"]],
                [waypoint["name"] for waypoint in task["waypoints"]],
                task["name"],
            )

        self.assertEqual(
            [3.05, 2.15, 1.5708],
            config["tasks"][2]["waypoints"][2]["pose"],
        )
```

保留对任务总数、任务名称顺序、每个 pose 长度与 yaw 类型的既有断言；删除 Task 2
必须至少六个 waypoint 以及旧六点名称列表的断言。

- [ ] **Step 2: 运行测试并确认 RED**

运行：

```powershell
python -m unittest discover -s tests -p test_task_test_runner_config.py -v
```

预期：`test_task_config_defines_five_ordered_pose_tasks` 失败，差异显示
Task 2 当前仍是
`ward_a_door -> staggered_exit -> staggered_mid -> staggered_entry -> take_medicine -> ward_b`，
而期望为 `take_medicine -> ward_b`；其他测试通过。

- [ ] **Step 3: 最小修改 Task 2 配置**

将 `task_2_take_medicine_to_ward_b` 的 `waypoints` 完整替换为：

```yaml
    waypoints:
      - name: take_medicine
        pose: [2.0, 8.05, 1.5708]
        hold_time: 2.0
      - name: ward_b
        pose: [5.15, 2.4, 3.1416]
        hold_time: 2.0
```

不修改 Task 1、3、4、5 的 waypoint、坐标、yaw、容差或停留时间。

- [ ] **Step 4: 运行测试并确认 GREEN**

运行：

```powershell
python -m unittest discover -s tests -p test_task_test_runner_config.py -v
```

预期：全部 12 个 `TaskTestRunnerConfigTest` 测试通过。

- [ ] **Step 5: 提交任务路线调整**

```powershell
git add src/service_robot_navigation/config/task_tests.yaml tests/test_task_test_runner_config.py
git commit -m "fix: align navigation tasks with requirements"
```

### Task 2: 以 move_base action 结果作为最终成功标准

**Files:**

- Modify: `tests/test_task_test_runner_config.py:303-324`
- Modify: `src/service_robot_navigation/scripts/run_task_tests.py:375-399`

- [ ] **Step 1: 先修改成功状态测试，使旧逻辑失败**

将
`test_execute_waypoint_records_diagnostics_for_success_state_with_pose_error`
替换为：

```python
    def test_execute_waypoint_accepts_success_state_with_latest_pose_drift(self):
        runner_module = load_runner_module()
        fake_runner = self.make_fake_waypoint_runner(
            runner_module,
            finished=True,
            state=3,
            poses=[(0.0, 0.0, 0.0), (1.25, 2.55, 1.3708)],
        )

        result = fake_runner.execute_waypoint(
            {"name": "counter", "pose": [1.55, 2.15, 1.5708]}
        )

        self.assertTrue(result["success"])
        self.assertNotIn("reason", result)
        self.assertNotIn("diagnostics", result)
        self.assertAlmostEqual(0.5, result["error"]["xy"], places=6)
        self.assertAlmostEqual(0.2, result["error"]["yaw"], places=6)
```

该 fake 的 action state 为 `SUCCEEDED=3`，但 action 完成后读取的 AMCL
位置误差为 `0.5 m`，明确超过脚本默认 `0.25 m` 容差，用于证明 action
成功不能被第二次采样推翻。

- [ ] **Step 2: 运行测试并确认 RED**

运行：

```powershell
python -m unittest discover -s tests -p test_task_test_runner_config.py -v
```

预期：
`test_execute_waypoint_accepts_success_state_with_latest_pose_drift`
在 `self.assertTrue(result["success"])` 失败，因为旧实现仍返回
`pose error xy=0.500, yaw=0.200`。

- [ ] **Step 3: 删除 action 成功后的二次失败分支**

在 `execute_waypoint` 中保留：

```python
        current_pose = self.current_pose()
        error = compute_pose_error(current_pose, waypoint["pose"])
```

删除以下整个条件分支：

```python
        if error["xy"] > xy_tolerance or error["yaw"] > yaw_tolerance:
            return {
                "name": waypoint["name"],
                "success": False,
                "duration": time.time() - start,
                "reason": "pose error xy={:.3f}, yaw={:.3f}".format(
                    error["xy"], error["yaw"]
                ),
                "error": error,
                "diagnostics": build_failure_diagnostics(
                    waypoint["pose"], state, current_pose=current_pose
                ),
            }
```

保留 `hold_time` 和原有成功返回：

```python
        if hold_time > 0:
            self.rospy.sleep(hold_time)

        return {
            "name": waypoint["name"],
            "success": True,
            "duration": time.time() - start,
            "error": error,
        }
```

timeout 与 `state != SUCCEEDED` 分支不变。

- [ ] **Step 4: 运行相关与全量测试**

运行：

```powershell
python -m unittest discover -s tests -p test_task_test_runner_config.py -v
python -m unittest discover -s tests -v
python -m py_compile src/service_robot_navigation/scripts/run_task_tests.py
git diff --check
```

预期：12 个 runner/config 测试和 18 个全量离线测试全部通过；`py_compile`
退出码为 0；`git diff --check` 无输出。

- [ ] **Step 5: 提交成功判定调整**

```powershell
git add src/service_robot_navigation/scripts/run_task_tests.py tests/test_task_test_runner_config.py
git commit -m "fix: trust move_base success for waypoints"
```

### Task 3: 最终检查与 Ubuntu 交接

**Files:**

- Verify: `src/service_robot_navigation/config/task_tests.yaml`
- Verify: `src/service_robot_navigation/scripts/run_task_tests.py`
- Verify: `tests/test_task_test_runner_config.py`

- [ ] **Step 1: 重新运行最终离线验证**

```powershell
python -m unittest discover -s tests -v
python -m py_compile src/service_robot_navigation/scripts/run_task_tests.py
git diff --check
git status --short
```

预期：18 项测试全部通过，`py_compile` 和 `git diff --check` 成功，
`git status --short` 无输出。

- [ ] **Step 2: Ubuntu 中重启并运行完整任务**

```bash
cd ~/service_robot
catkin_make
source devel/setup.bash
roslaunch service_robot_navigation sim_navigation.launch
```

另开终端：

```bash
source ~/service_robot/devel/setup.bash
rosrun service_robot_navigation run_task_tests.py
```

预期：

```text
Task 1: take_medicine -> ward_a
Task 2: take_medicine -> ward_b
Task 3: long_counter_left -> long_counter_middle -> long_counter_right
Task 4: staggered_entry -> staggered_mid -> staggered_exit
Task 5: narrow_entry -> narrow_mid -> narrow_exit -> dock
```

当 action state 为 `SUCCEEDED` 时，对应 waypoint 显示 PASS；摘要仍显示
最新 AMCL XY/Yaw 误差。timeout 或其他 action state 仍应失败并 fail-fast。

## 计划自检

- Task 1 覆盖五项任务的全部 waypoint 语义，没有修改任务点坐标。
- Task 2 只改变 action 成功后的二次判定，没有弱化 timeout 或非成功 state。
- Task 3 明确区分离线验证与 Ubuntu ROS/Gazebo 运行验证。
- 计划未触及 DWA、costmap、AMCL、world 或地图。
