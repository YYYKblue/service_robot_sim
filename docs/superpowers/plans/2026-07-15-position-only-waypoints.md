# 位置型中转 waypoint 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 Task 4 的全部 waypoint 和 Task 5 的三个狭窄区域中转点只约束 XY 位置，同时保留 Task 5 `dock` 及 Task 1、2、3 的完整位姿语义。

**Architecture:** YAML 使用互斥的 `pose: [x, y, yaw]` 与 `position: [x, y]` 表达两类目标；公共纯函数负责目标解析、误差计算、goal 构造及诊断格式。完整位姿继续阻塞等待 `move_base` 终态，位置型目标改为短周期轮询 action 与 AMCL，在 XY 达标时记录取消前状态、取消 goal 并成功结束。

**Tech Stack:** Python 3、ROS Noetic（rospy、actionlib、move_base）、PyYAML、unittest。

---

## 文件结构

- 修改：`src/service_robot_navigation/config/task_tests.yaml`
  - Task 4 三个点改为 `position`，删除 yaw 与 `yaw_tolerance`。
  - Task 5 的 `narrow_entry`、`narrow_mid`、`narrow_exit` 改为 `position`；`dock` 保持完整 `pose`。
- 修改：`src/service_robot_navigation/scripts/run_task_tests.py`
  - 增加目标类型解析、位置误差、位置容差、位置 goal 构造、位置诊断和位置型执行循环。
  - 保持完整位姿 waypoint 的既有 action 成功语义。
- 修改：`tests/test_task_test_runner_config.py`
  - 扩展离线测试 fake，覆盖配置、纯函数、目标四元数、取消顺序、异常和摘要。
- 不修改：README、DWA、GlobalPlanner、costmap、AMCL 参数、Gazebo world 与地图。

### Task 1: 扩展配置模型并转换 Task 4、5 中转点

**Files:**

- Modify: `tests/test_task_test_runner_config.py:25-80`
- Modify: `src/service_robot_navigation/scripts/run_task_tests.py:94-113`
- Modify: `src/service_robot_navigation/config/task_tests.yaml:46-74`

- [ ] **Step 1: 写配置语义与校验失败测试**

将现有 `test_task_config_defines_five_ordered_pose_tasks` 重命名为
`test_task_config_defines_five_ordered_tasks`。保留任务名称和 waypoint 顺序断言，
删除循环中“所有 waypoint 都必须有三元素 pose”的断言，并在该测试末尾加入：

```python
        task_4_waypoints = config["tasks"][3]["waypoints"]
        self.assertEqual(
            [[4.5, 8.0], [6.55, 7.15], [8.4, 6.4]],
            [waypoint["position"] for waypoint in task_4_waypoints],
        )
        for waypoint in task_4_waypoints:
            self.assertNotIn("pose", waypoint)
            self.assertNotIn("yaw_tolerance", waypoint)

        task_5_waypoints = config["tasks"][4]["waypoints"]
        self.assertEqual(
            [[7.2, 2.5], [9.0, 2.5], [11.4, 2.5]],
            [waypoint["position"] for waypoint in task_5_waypoints[:3]],
        )
        for waypoint in task_5_waypoints[:3]:
            self.assertNotIn("pose", waypoint)
        self.assertEqual([13.25, 2.6, 0.0], task_5_waypoints[3]["pose"])
        self.assertNotIn("position", task_5_waypoints[3])
```

在同一测试类中增加配置校验测试：

```python
    def test_validate_task_config_accepts_pose_or_position(self):
        runner = load_runner_module()
        config = {
            "tasks": [
                {
                    "name": "mixed_targets",
                    "waypoints": [
                        {"name": "position_only", "position": [1.0, 2.0]},
                        {"name": "full_pose", "pose": [3.0, 4.0, 1.57]},
                    ],
                }
            ]
        }

        runner.validate_task_config(config, "test.yaml")

    def test_validate_task_config_rejects_missing_or_ambiguous_target(self):
        runner = load_runner_module()
        invalid_waypoints = [
            ({"name": "missing"}, "exactly one of pose or position"),
            (
                {"name": "ambiguous", "pose": [1.0, 2.0, 0.0], "position": [1.0, 2.0]},
                "exactly one of pose or position",
            ),
            ({"name": "short_pose", "pose": [1.0, 2.0]}, r"pose \[x, y, yaw\]"),
            ({"name": "long_position", "position": [1.0, 2.0, 3.0]}, r"position \[x, y\]"),
            ({"name": "text_pose", "pose": [1.0, 2.0, "north"]}, "numeric pose"),
            ({"name": "text_position", "position": [1.0, "two"]}, "numeric position"),
        ]

        for waypoint, message in invalid_waypoints:
            with self.subTest(waypoint=waypoint["name"]):
                config = {"tasks": [{"name": "invalid", "waypoints": [waypoint]}]}
                with self.assertRaisesRegex(ValueError, message):
                    runner.validate_task_config(config, "test.yaml")
```

- [ ] **Step 2: 运行配置测试并确认 RED**

运行：

```powershell
python -m unittest tests.test_task_test_runner_config.TaskTestRunnerConfigTest.test_task_config_defines_five_ordered_tasks tests.test_task_test_runner_config.TaskTestRunnerConfigTest.test_validate_task_config_accepts_pose_or_position tests.test_task_test_runner_config.TaskTestRunnerConfigTest.test_validate_task_config_rejects_missing_or_ambiguous_target -v
```

预期：配置语义测试因 Task 4、5 仍使用 `pose` 而失败；合法 `position`
配置因旧校验只接受 `pose` 而失败；非法配置测试至少有一项错误信息不匹配。

- [ ] **Step 3: 实现互斥目标校验**

将 `validate_task_config` 内 waypoint 的旧 `pose` 校验替换为：

```python
            has_pose = "pose" in waypoint
            has_position = "position" in waypoint
            if has_pose == has_position:
                raise ValueError(
                    "Waypoint {} must define exactly one of pose or position".format(
                        waypoint["name"]
                    )
                )

            target_key = "pose" if has_pose else "position"
            target = waypoint[target_key]
            expected_length = 3 if has_pose else 2
            expected_shape = "pose [x, y, yaw]" if has_pose else "position [x, y]"
            if not isinstance(target, list) or len(target) != expected_length:
                raise ValueError(
                    "Waypoint {} must use {}".format(waypoint["name"], expected_shape)
                )
            if not all(
                isinstance(value, (int, float)) and not isinstance(value, bool)
                for value in target
            ):
                raise ValueError(
                    "Waypoint {} must use numeric {}".format(
                        waypoint["name"], target_key
                    )
                )
```

- [ ] **Step 4: 转换 YAML 中的位置型 waypoint**

将 Task 4、5 完整替换为：

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

- [ ] **Step 5: 运行配置测试并确认 GREEN**

运行：

```powershell
python -m unittest discover -s tests -p test_task_test_runner_config.py -v
```

预期：配置测试通过；此时尚未用 fake 执行新的位置型 waypoint，因此运行时行为在
Task 3 实现。

- [ ] **Step 6: 提交配置模型变更**

```powershell
git add src/service_robot_navigation/config/task_tests.yaml src/service_robot_navigation/scripts/run_task_tests.py tests/test_task_test_runner_config.py
git commit -m "feat: define position-only navigation waypoints"
```

### Task 2: 增加位置目标纯函数、goal 构造与诊断格式

**Files:**

- Modify: `tests/test_task_test_runner_config.py:82-153`
- Modify: `src/service_robot_navigation/scripts/run_task_tests.py:38-83`
- Modify: `src/service_robot_navigation/scripts/run_task_tests.py:141-155`
- Modify: `src/service_robot_navigation/scripts/run_task_tests.py:391-407`

- [ ] **Step 1: 写位置误差、目标构造、诊断和摘要失败测试**

在 `test_runner_loads_config_and_computes_pose_errors_without_ros` 后增加：

```python
    def test_position_helpers_ignore_yaw(self):
        runner = load_runner_module()

        error = runner.compute_position_error((1.0, 2.0, -2.5), [1.3, 1.6])
        self.assertEqual({"xy": 0.5}, error)
        self.assertTrue(
            runner.position_within_tolerance((1.0, 2.0, -3.0), [1.0, 2.0], 0.01)
        )
        self.assertFalse(
            runner.position_within_tolerance((1.2, 2.0, 0.0), [1.0, 2.0], 0.10)
        )

    def test_make_goal_uses_current_yaw_for_position_target(self):
        runner = load_runner_module()
        fake_runner = self.make_fake_waypoint_runner(
            runner,
            finished=True,
            state=3,
            poses=[(0.0, 0.0, 1.2), (1.0, 2.0, -2.0)],
        )

        goal = runner.make_goal(
            fake_runner.goal_cls,
            {"name": "position_only", "position": [1.0, 2.0]},
            "map",
            position_yaw=1.2,
        )

        self.assertEqual(1.0, goal.target_pose.pose.position.x)
        self.assertEqual(2.0, goal.target_pose.pose.position.y)
        self.assertAlmostEqual(
            1.2,
            runner.quaternion_to_yaw(goal.target_pose.pose.orientation),
            places=6,
        )

    def test_make_goal_requires_yaw_for_position_target(self):
        runner = load_runner_module()
        fake_runner = self.make_fake_waypoint_runner(
            runner,
            finished=True,
            state=3,
            poses=[(0.0, 0.0, 0.0)],
        )

        with self.assertRaisesRegex(ValueError, "position_yaw"):
            runner.make_goal(
                fake_runner.goal_cls,
                {"name": "position_only", "position": [1.0, 2.0]},
                "map",
            )

    def test_position_failure_diagnostics_use_target_position_and_xy_only(self):
        runner = load_runner_module()

        diagnostics = runner.build_failure_diagnostics(
            [1.0, 2.0],
            4,
            current_pose=(1.3, 1.6, -2.0),
            target_kind="position",
        )
        text = runner.format_failure_diagnostics(diagnostics)

        self.assertEqual([1.0, 2.0], diagnostics["target_position"])
        self.assertNotIn("target_pose", diagnostics)
        self.assertEqual({"xy": 0.5}, diagnostics["error"])
        self.assertIn("target_position=(1.000,2.000)", text)
        self.assertIn("final_xy=0.500", text)
        self.assertNotIn("final_yaw", text)

    def test_print_summary_supports_position_only_success_error(self):
        runner = load_runner_module()
        results = [
            {
                "name": "position_task",
                "success": True,
                "duration": 0.1,
                "waypoints": [
                    {
                        "name": "position_only",
                        "success": True,
                        "error": {"xy": 0.125},
                    }
                ],
            }
        ]
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            runner.print_summary(results)

        self.assertIn("PASS position_only xy=0.125", output.getvalue())
        self.assertNotIn("yaw=", output.getvalue())
```

- [ ] **Step 2: 运行新增纯函数测试并确认 RED**

运行：

```powershell
python -m unittest tests.test_task_test_runner_config.TaskTestRunnerConfigTest.test_position_helpers_ignore_yaw tests.test_task_test_runner_config.TaskTestRunnerConfigTest.test_make_goal_uses_current_yaw_for_position_target tests.test_task_test_runner_config.TaskTestRunnerConfigTest.test_make_goal_requires_yaw_for_position_target tests.test_task_test_runner_config.TaskTestRunnerConfigTest.test_position_failure_diagnostics_use_target_position_and_xy_only tests.test_task_test_runner_config.TaskTestRunnerConfigTest.test_print_summary_supports_position_only_success_error -v
```

预期：因位置辅助函数和 `position_yaw` 尚不存在、诊断仍固定为
`target_pose`、摘要强制读取 `yaw` 而失败。

- [ ] **Step 3: 增加目标解析与位置误差纯函数**

在 `compute_pose_error` 后加入：

```python
def compute_position_error(current_pose, target_position):
    dx = current_pose[0] - target_position[0]
    dy = current_pose[1] - target_position[1]
    return {"xy": math.hypot(dx, dy)}


def position_within_tolerance(current_pose, target_position, xy_tolerance):
    return compute_position_error(current_pose, target_position)["xy"] <= xy_tolerance


def waypoint_target(waypoint):
    if "pose" in waypoint:
        return "pose", waypoint["pose"]
    return "position", waypoint["position"]
```

- [ ] **Step 4: 让失败诊断区分 pose 与 position**

将 `build_failure_diagnostics` 完整替换为：

```python
def build_failure_diagnostics(
    target,
    action_state,
    current_pose=None,
    pose_error_message=None,
    target_kind="pose",
):
    target_key = "target_pose" if target_kind == "pose" else "target_position"
    diagnostics = {
        target_key: [float(value) for value in target],
    }
    if action_state is not None:
        diagnostics["action_state"] = action_state
    if current_pose is not None:
        current_pose = [float(value) for value in current_pose]
        diagnostics["current_pose"] = current_pose
        if target_kind == "pose":
            diagnostics["error"] = compute_pose_error(
                current_pose, diagnostics["target_pose"]
            )
        else:
            diagnostics["error"] = compute_position_error(
                current_pose, diagnostics["target_position"]
            )
    if pose_error_message is not None:
        diagnostics["pose_error_message"] = str(pose_error_message)
    return diagnostics
```

在 `format_failure_diagnostics` 的 `target_pose` 分支后加入：

```python
    if "target_position" in diagnostics:
        fields.append(
            "target_position=({:.3f},{:.3f})".format(
                *diagnostics["target_position"]
            )
        )
```

- [ ] **Step 5: 扩展 goal 构造但保持 pose 调用兼容**

将 `make_goal` 完整替换为：

```python
def make_goal(move_base_goal_cls, waypoint, frame_id, position_yaw=None):
    goal = move_base_goal_cls()
    goal.target_pose.header.frame_id = frame_id

    target_kind, target = waypoint_target(waypoint)
    if target_kind == "pose":
        x, y, yaw = target
    else:
        if position_yaw is None:
            raise ValueError("position_yaw is required for a position waypoint")
        x, y = target
        yaw = position_yaw

    goal.target_pose.pose.position.x = float(x)
    goal.target_pose.pose.position.y = float(y)
    goal.target_pose.pose.position.z = 0.0

    quat = yaw_to_quaternion(float(yaw))
    goal.target_pose.pose.orientation.x = quat["x"]
    goal.target_pose.pose.orientation.y = quat["y"]
    goal.target_pose.pose.orientation.z = quat["z"]
    goal.target_pose.pose.orientation.w = quat["w"]
    return goal
```

- [ ] **Step 6: 让成功摘要按实际误差字段输出**

将 `print_summary` 中成功误差格式化替换为：

```python
            if "error" in waypoint:
                detail = " xy={:.3f}".format(waypoint["error"]["xy"])
                if "yaw" in waypoint["error"]:
                    detail += " yaw={:.3f}".format(waypoint["error"]["yaw"])
```

- [ ] **Step 7: 运行相关测试和全量离线测试**

运行：

```powershell
python -m unittest discover -s tests -p test_task_test_runner_config.py -v
python -m unittest discover -s tests -v
python -m py_compile src/service_robot_navigation/scripts/run_task_tests.py
```

预期：全部测试通过；`py_compile` 退出码为 0。完整位姿诊断仍输出
`target_pose` 和 yaw，位置诊断只输出 `target_position` 和 XY。

- [ ] **Step 8: 提交位置目标基础能力**

```powershell
git add src/service_robot_navigation/scripts/run_task_tests.py tests/test_task_test_runner_config.py
git commit -m "feat: support position-only waypoint targets"
```

### Task 3: 实现位置型 action 轮询与 XY 达标主动取消

**Files:**

- Modify: `tests/test_task_test_runner_config.py:155-346`
- Modify: `src/service_robot_navigation/scripts/run_task_tests.py:319-388`

- [ ] **Step 1: 扩展 fake client 支持轮询、goal 记录和 AMCL 异常**

在测试文件顶部加入：

```python
from unittest import mock
```

将 `make_fake_waypoint_runner` 内的 `FakeClient` 和 pose iterator 替换为：

```python
        class FakeClient:
            def __init__(self):
                self.cancelled = False
                self.events = []
                self.state = state
                values = finished if isinstance(finished, list) else [finished]
                self.finished_values = iter(values)
                self.last_finished = values[-1]
                self.sent_goal = None

            def send_goal(self, goal):
                self.sent_goal = goal

            def wait_for_result(self, timeout):
                try:
                    self.last_finished = next(self.finished_values)
                except StopIteration:
                    pass
                return self.last_finished

            def get_state(self):
                self.events.append("get_state")
                return self.state

            def cancel_goal(self):
                self.cancelled = True
                self.events.append("cancel_goal")
                self.state = 2
```

```python
        pose_values = iter(poses)

        def current_pose():
            value = next(pose_values)
            if isinstance(value, Exception):
                raise value
            return value

        fake_runner.current_pose = current_pose
```

- [ ] **Step 2: 写位置型执行循环失败测试**

在既有 waypoint 执行测试后增加：

```python
    def test_execute_position_waypoint_cancels_after_xy_is_satisfied(self):
        runner_module = load_runner_module()
        fake_runner = self.make_fake_waypoint_runner(
            runner_module,
            finished=[False],
            state=1,
            poses=[(0.0, 0.0, 1.2), (1.1, 2.1, -2.5)],
        )

        result = fake_runner.execute_waypoint(
            {
                "name": "position_only",
                "position": [1.0, 2.0],
                "xy_tolerance": 0.15,
            }
        )

        self.assertTrue(result["success"])
        self.assertAlmostEqual(0.141421, result["error"]["xy"], places=6)
        self.assertNotIn("yaw", result["error"])
        self.assertEqual(["get_state", "cancel_goal"], fake_runner.client.events)
        self.assertTrue(fake_runner.client.cancelled)
        self.assertAlmostEqual(
            1.2,
            runner_module.quaternion_to_yaw(
                fake_runner.client.sent_goal.target_pose.pose.orientation
            ),
            places=6,
        )

    def test_execute_position_waypoint_trusts_move_base_success(self):
        runner_module = load_runner_module()
        fake_runner = self.make_fake_waypoint_runner(
            runner_module,
            finished=[True],
            state=3,
            poses=[(0.0, 0.0, 0.5), (0.6, 0.0, -2.0)],
        )

        result = fake_runner.execute_waypoint(
            {"name": "position_only", "position": [1.0, 0.0], "xy_tolerance": 0.10}
        )

        self.assertTrue(result["success"])
        self.assertFalse(fake_runner.client.cancelled)
        self.assertEqual({"xy": 0.4}, result["error"])

    def test_execute_position_waypoint_accepts_xy_after_non_success_terminal_state(self):
        runner_module = load_runner_module()
        fake_runner = self.make_fake_waypoint_runner(
            runner_module,
            finished=[True],
            state=4,
            poses=[(0.0, 0.0, 0.5), (0.95, 0.0, -2.0)],
        )

        result = fake_runner.execute_waypoint(
            {"name": "position_only", "position": [1.0, 0.0], "xy_tolerance": 0.10}
        )

        self.assertTrue(result["success"])
        self.assertEqual(["get_state", "cancel_goal"], fake_runner.client.events)

    def test_execute_position_waypoint_fails_on_terminal_state_outside_xy(self):
        runner_module = load_runner_module()
        fake_runner = self.make_fake_waypoint_runner(
            runner_module,
            finished=[True],
            state=4,
            poses=[(0.0, 0.0, 0.5), (0.5, 0.0, -2.0)],
        )

        result = fake_runner.execute_waypoint(
            {"name": "position_only", "position": [1.0, 0.0], "xy_tolerance": 0.10}
        )

        self.assertFalse(result["success"])
        self.assertEqual("move_base returned state 4", result["reason"])
        self.assertEqual([1.0, 0.0], result["diagnostics"]["target_position"])
        self.assertEqual({"xy": 0.5}, result["diagnostics"]["error"])

    def test_execute_position_waypoint_retries_after_amcl_read_error(self):
        runner_module = load_runner_module()
        fake_runner = self.make_fake_waypoint_runner(
            runner_module,
            finished=[False, False],
            state=1,
            poses=[
                (0.0, 0.0, 0.5),
                RuntimeError("temporary AMCL failure"),
                (0.95, 0.0, -2.0),
            ],
        )

        result = fake_runner.execute_waypoint(
            {"name": "position_only", "position": [1.0, 0.0], "xy_tolerance": 0.10}
        )

        self.assertTrue(result["success"])
        self.assertTrue(fake_runner.client.cancelled)

    def test_execute_position_waypoint_timeout_saves_state_before_cancel(self):
        runner_module = load_runner_module()
        fake_runner = self.make_fake_waypoint_runner(
            runner_module,
            finished=[False],
            state=1,
            poses=[(0.0, 0.0, 0.5), (0.2, 0.0, 0.5)],
        )

        with mock.patch.object(
            runner_module.time,
            "time",
            side_effect=[0.0, 2.0, 2.0],
        ):
            result = fake_runner.execute_waypoint(
                {
                    "name": "position_only",
                    "position": [1.0, 0.0],
                    "xy_tolerance": 0.10,
                    "timeout": 1.0,
                }
            )

        self.assertFalse(result["success"])
        self.assertIn("timeout", result["reason"])
        self.assertEqual(["get_state", "cancel_goal"], fake_runner.client.events)
        self.assertEqual([1.0, 0.0], result["diagnostics"]["target_position"])

    def test_execute_position_waypoint_fails_when_initial_yaw_is_unavailable(self):
        runner_module = load_runner_module()
        fake_runner = self.make_fake_waypoint_runner(
            runner_module,
            finished=[False],
            state=1,
            poses=[RuntimeError("AMCL unavailable")],
        )

        result = fake_runner.execute_waypoint(
            {"name": "position_only", "position": [1.0, 0.0]}
        )

        self.assertFalse(result["success"])
        self.assertIn("could not read current pose", result["reason"])
        self.assertIsNone(fake_runner.client.sent_goal)
        self.assertEqual(
            "AMCL unavailable", result["diagnostics"]["pose_error_message"]
        )
```

- [ ] **Step 3: 运行位置型执行测试并确认 RED**

运行：

```powershell
python -m unittest tests.test_task_test_runner_config.TaskTestRunnerConfigTest.test_execute_position_waypoint_cancels_after_xy_is_satisfied tests.test_task_test_runner_config.TaskTestRunnerConfigTest.test_execute_position_waypoint_trusts_move_base_success tests.test_task_test_runner_config.TaskTestRunnerConfigTest.test_execute_position_waypoint_accepts_xy_after_non_success_terminal_state tests.test_task_test_runner_config.TaskTestRunnerConfigTest.test_execute_position_waypoint_fails_on_terminal_state_outside_xy tests.test_task_test_runner_config.TaskTestRunnerConfigTest.test_execute_position_waypoint_retries_after_amcl_read_error tests.test_task_test_runner_config.TaskTestRunnerConfigTest.test_execute_position_waypoint_timeout_saves_state_before_cancel tests.test_task_test_runner_config.TaskTestRunnerConfigTest.test_execute_position_waypoint_fails_when_initial_yaw_is_unavailable -v
```

预期：旧 `execute_waypoint` 读取 `waypoint["pose"]`，新增测试失败。

- [ ] **Step 4: 让失败诊断方法接受 waypoint 类型**

将 `collect_failure_diagnostics` 完整替换为：

```python
    def collect_failure_diagnostics(
        self,
        waypoint,
        action_state,
        current_pose=None,
        pose_error_message=None,
    ):
        target_kind, target = waypoint_target(waypoint)
        if current_pose is None and pose_error_message is None:
            try:
                current_pose = self.current_pose()
            except Exception as exc:
                pose_error_message = exc
        return build_failure_diagnostics(
            target,
            action_state,
            current_pose=current_pose,
            pose_error_message=pose_error_message,
            target_kind=target_kind,
        )
```

同步修改两个既有调用，将
`self.collect_failure_diagnostics(waypoint["pose"], state)` 改为
`self.collect_failure_diagnostics(waypoint, state)`；将既有单元测试中的直接调用目标
从 `[1.55, 2.15, 1.5708]` 改为
`{"name": "counter", "pose": [1.55, 2.15, 1.5708]}`。

- [ ] **Step 5: 增加位置型等待方法**

在 `collect_failure_diagnostics` 后加入：

```python
    def wait_for_position_waypoint(
        self,
        waypoint,
        timeout,
        hold_time,
        xy_tolerance,
        start,
        initial_error,
    ):
        deadline = start + timeout
        last_error = initial_error

        while True:
            remaining = deadline - time.time()
            if remaining <= 0:
                state = self.client.get_state()
                self.client.cancel_goal()
                return {
                    "name": waypoint["name"],
                    "success": False,
                    "duration": time.time() - start,
                    "reason": "timeout after {:.1f}s".format(timeout),
                    "diagnostics": self.collect_failure_diagnostics(
                        waypoint, state
                    ),
                }

            finished = self.client.wait_for_result(
                self.rospy.Duration(min(0.2, remaining))
            )
            state = self.client.get_state() if finished else None

            if finished and state == self.goal_status_cls.SUCCEEDED:
                try:
                    current_pose = self.current_pose()
                    last_error = compute_position_error(
                        current_pose, waypoint["position"]
                    )
                except Exception as exc:
                    self.rospy.logwarn(
                        "Could not read final pose for waypoint %s: %s",
                        waypoint["name"],
                        exc,
                    )
                if hold_time > 0:
                    self.rospy.sleep(hold_time)
                return {
                    "name": waypoint["name"],
                    "success": True,
                    "duration": time.time() - start,
                    "error": last_error,
                }

            current_pose = None
            pose_error_message = None
            try:
                current_pose = self.current_pose()
                last_error = compute_position_error(
                    current_pose, waypoint["position"]
                )
                if last_error["xy"] <= xy_tolerance:
                    if state is None:
                        state = self.client.get_state()
                    self.client.cancel_goal()
                    if hold_time > 0:
                        self.rospy.sleep(hold_time)
                    return {
                        "name": waypoint["name"],
                        "success": True,
                        "duration": time.time() - start,
                        "error": last_error,
                    }
            except Exception as exc:
                pose_error_message = exc
                self.rospy.logwarn(
                    "Could not check position for waypoint %s: %s",
                    waypoint["name"],
                    exc,
                )

            if finished:
                return {
                    "name": waypoint["name"],
                    "success": False,
                    "duration": time.time() - start,
                    "reason": "move_base returned state {}".format(state),
                    "diagnostics": self.collect_failure_diagnostics(
                        waypoint,
                        state,
                        current_pose=current_pose,
                        pose_error_message=pose_error_message,
                    ),
                }
```

该顺序保证：`SUCCEEDED` 仍是最终成功；其他终态到达时先检查最新 XY，已进入
容差则成功，否则失败；XY 主动完成和 timeout 都先读取 action state 再取消。

- [ ] **Step 6: 在 execute_waypoint 中分派两类目标**

将 `execute_waypoint` 完整替换为：

```python
    def execute_waypoint(self, waypoint):
        frame_id = get_setting(self.config, waypoint, "frame_id") or "map"
        timeout = float(get_setting(self.config, waypoint, "timeout") or 90.0)
        hold_time = float(get_setting(self.config, waypoint, "hold_time") or 0.0)
        xy_tolerance = float(
            get_setting(self.config, waypoint, "xy_tolerance") or 0.25
        )
        yaw_tolerance = float(
            get_setting(self.config, waypoint, "yaw_tolerance") or 0.25
        )
        target_kind, target = waypoint_target(waypoint)

        current_pose = None
        try:
            current_pose = self.current_pose()
            if target_kind == "pose":
                satisfied = pose_within_tolerance(
                    current_pose, target, xy_tolerance, yaw_tolerance
                )
                error = compute_pose_error(current_pose, target)
            else:
                satisfied = position_within_tolerance(
                    current_pose, target, xy_tolerance
                )
                error = compute_position_error(current_pose, target)
            if satisfied:
                self.rospy.loginfo("Waypoint already satisfied: %s", waypoint["name"])
                if hold_time > 0:
                    self.rospy.sleep(hold_time)
                return {
                    "name": waypoint["name"],
                    "success": True,
                    "duration": 0.0,
                    "error": error,
                }
        except Exception as exc:
            self.rospy.logwarn(
                "Could not pre-check current pose before waypoint %s: %s",
                waypoint["name"],
                exc,
            )
            if target_kind == "position":
                return {
                    "name": waypoint["name"],
                    "success": False,
                    "duration": 0.0,
                    "reason": "could not read current pose before position waypoint: {}".format(
                        exc
                    ),
                    "diagnostics": self.collect_failure_diagnostics(
                        waypoint,
                        None,
                        pose_error_message=exc,
                    ),
                }

        self.clear_costmaps()
        self.rospy.loginfo("Sending waypoint: %s -> %s", waypoint["name"], target)
        position_yaw = current_pose[2] if target_kind == "position" else None
        goal = make_goal(
            self.goal_cls,
            waypoint,
            frame_id,
            position_yaw=position_yaw,
        )
        goal.target_pose.header.stamp = self.rospy.Time.now()

        start = time.time()
        self.client.send_goal(goal)

        if target_kind == "position":
            return self.wait_for_position_waypoint(
                waypoint,
                timeout,
                hold_time,
                xy_tolerance,
                start,
                compute_position_error(current_pose, target),
            )

        finished = self.client.wait_for_result(self.rospy.Duration(timeout))
        if not finished:
            state = self.client.get_state()
            self.client.cancel_goal()
            return {
                "name": waypoint["name"],
                "success": False,
                "duration": time.time() - start,
                "reason": "timeout after {:.1f}s".format(timeout),
                "diagnostics": self.collect_failure_diagnostics(waypoint, state),
            }

        state = self.client.get_state()
        if state != self.goal_status_cls.SUCCEEDED:
            return {
                "name": waypoint["name"],
                "success": False,
                "duration": time.time() - start,
                "reason": "move_base returned state {}".format(state),
                "diagnostics": self.collect_failure_diagnostics(waypoint, state),
            }

        current_pose = self.current_pose()
        error = compute_pose_error(current_pose, target)
        if hold_time > 0:
            self.rospy.sleep(hold_time)
        return {
            "name": waypoint["name"],
            "success": True,
            "duration": time.time() - start,
            "error": error,
        }
```

- [ ] **Step 7: 运行位置型测试、既有回归和语法检查**

运行：

```powershell
python -m unittest discover -s tests -p test_task_test_runner_config.py -v
python -m unittest discover -s tests -v
python -m py_compile src/service_robot_navigation/scripts/run_task_tests.py
git diff --check
```

预期：全部离线测试通过；完整位姿的 timeout、非成功 state、成功后 AMCL
误差记录测试继续通过；`py_compile` 与 `git diff --check` 无错误。

- [ ] **Step 8: 提交位置型执行循环**

```powershell
git add src/service_robot_navigation/scripts/run_task_tests.py tests/test_task_test_runner_config.py
git commit -m "feat: finish position waypoints by xy tolerance"
```

### Task 4: 最终离线验证与 Ubuntu 交接

**Files:**

- Verify: `src/service_robot_navigation/config/task_tests.yaml`
- Verify: `src/service_robot_navigation/scripts/run_task_tests.py`
- Verify: `tests/test_task_test_runner_config.py`

- [ ] **Step 1: 运行最终离线验证**

```powershell
python -m unittest discover -s tests -v
python -m py_compile src/service_robot_navigation/scripts/run_task_tests.py
git diff --check
git status --short
```

预期：全量测试全部通过，`py_compile` 和 `git diff --check` 成功；完成各任务提交后
`git status --short` 无输出。

- [ ] **Step 2: Ubuntu 中构建并运行五项任务**

终端一：

```bash
cd ~/service_robot
catkin_make
source devel/setup.bash
roslaunch service_robot_navigation sim_navigation.launch
```

终端二：

```bash
cd ~/service_robot
source devel/setup.bash
rosrun service_robot_navigation run_task_tests.py
```

预期：

- Task 1、2、3 的成功摘要仍包含 `xy=... yaw=...`。
- Task 4 的三个点只要进入各自 XY 容差即可完成，摘要仅包含 `xy=...`。
- Task 5 的前三点只要进入 XY 容差即可完成，`dock` 仍由
  `move_base SUCCEEDED` 完成且摘要包含 yaw。
- Task 4、5 的位置型点不再为对齐配置 yaw 而原地旋转或因 yaw 未满足而停滞。
- timeout 或 XY 未满足时的非成功 action state 仍使任务失败并输出诊断。

## 计划自检

- 配置模型覆盖 `pose`、`position`、互斥约束、长度和数值类型。
- Task 4 三点与 Task 5 三个中转点均转换为位置型；Task 5 `dock` 保持完整位姿。
- 位置 goal 使用发送前 AMCL yaw；初始 AMCL 不可用时不会伪造 yaw 或发送 goal。
- 位置执行覆盖 pre-check、轮询、XY 主动完成、`SUCCEEDED`、其他终态、timeout、AMCL 临时失败和取消顺序。
- 诊断与摘要按目标类型输出，既有完整位姿接口与测试保持兼容。
- 计划未触及导航参数、world、地图或用户未授权的模块。
