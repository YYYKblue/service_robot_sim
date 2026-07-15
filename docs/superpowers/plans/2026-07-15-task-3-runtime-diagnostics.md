# Task 3 运行时诊断实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 当 Task 3 的 waypoint 超时或失败时，输出可复现的运行时诊断信息，并以 ROS/Gazebo 证据选择唯一的后续修复方向。

**Architecture:** 在执行器模块中增加两个纯 Python 函数：一个构造失败诊断字典，另一个将字典格式化到控制台摘要。执行器在 timeout、非成功 action state、最终位姿误差三条失败路径中采集最新 AMCL 位姿；位姿不可读时保留原始失败原因并记录异常文本。

**Tech Stack:** Python 3、ROS Noetic（rospy、actionlib、move_base）、PyYAML、unittest。

---

## 文件结构

- 修改：`src/service_robot_navigation/scripts/run_task_tests.py`
  - 保留任务顺序、timeout、清理 costmap 和 fail-fast 行为；新增失败诊断构造、采集和摘要输出。
- 修改：`tests/test_task_test_runner_config.py`
  - 对新增纯函数和 timeout 结果进行离线回归测试。
- 不修改：`src/service_robot_navigation/config/task_tests.yaml`
  - Task 3 目标、容差、90 秒 timeout 不变。
- 不修改：`src/my_world/worlds/indoor.world` 与 `src/service_robot_navigation/maps/indoor.*`
  - 在得到运行时证据前不改变几何或地图。

### Task 1: 锁定失败诊断数据结构

**Files:**

- Modify: `tests/test_task_test_runner_config.py:83-151`
- Modify: `src/service_robot_navigation/scripts/run_task_tests.py:22-43`

- [ ] **Step 1: 写出失败的纯 Python 测试**

在 `TaskTestRunnerConfigTest` 添加以下两个方法，规定诊断字段名、位姿格式和 AMCL 读取失败时的行为：

```python
    def test_failure_diagnostics_keeps_target_pose_state_and_pose_error(self):
        runner = load_runner_module()

        diagnostics = runner.build_failure_diagnostics(
            target_pose=[1.55, 2.15, 1.5708],
            action_state=1,
            current_pose=(1.25, 2.55, 1.3708),
        )

        self.assertEqual([1.55, 2.15, 1.5708], diagnostics["target_pose"])
        self.assertEqual(1, diagnostics["action_state"])
        self.assertEqual([1.25, 2.55, 1.3708], diagnostics["current_pose"])
        self.assertAlmostEqual(0.5, diagnostics["error"]["xy"], places=6)
        self.assertAlmostEqual(0.2, diagnostics["error"]["yaw"], places=6)

    def test_failure_diagnostics_preserves_pose_read_error(self):
        runner = load_runner_module()

        diagnostics = runner.build_failure_diagnostics(
            target_pose=[1.55, 2.15, 1.5708],
            action_state=1,
            pose_error_message="timed out waiting for /amcl_pose",
        )

        self.assertEqual([1.55, 2.15, 1.5708], diagnostics["target_pose"])
        self.assertEqual(1, diagnostics["action_state"])
        self.assertEqual(
            "timed out waiting for /amcl_pose",
            diagnostics["pose_error_message"],
        )
        self.assertNotIn("current_pose", diagnostics)
        self.assertNotIn("error", diagnostics)
```

- [ ] **Step 2: 运行测试并确认先失败**

运行：

```powershell
python -m unittest discover -s tests -p test_task_test_runner_config.py -v
```

预期：两个新增测试以 `AttributeError` 失败，提示模块没有
`build_failure_diagnostics`；其他既有测试通过。

- [ ] **Step 3: 实现最小的纯函数**

在 `compute_pose_error` 后、`pose_within_tolerance` 前加入：

```python
def build_failure_diagnostics(
    target_pose,
    action_state,
    current_pose=None,
    pose_error_message=None,
):
    diagnostics = {
        "target_pose": [float(value) for value in target_pose],
        "action_state": action_state,
    }
    if current_pose is not None:
        diagnostics["current_pose"] = [float(value) for value in current_pose]
        diagnostics["error"] = compute_pose_error(current_pose, target_pose)
    if pose_error_message is not None:
        diagnostics["pose_error_message"] = str(pose_error_message)
    return diagnostics
```

- [ ] **Step 4: 确认纯函数测试通过**

运行：

```powershell
python -m unittest discover -s tests -p test_task_test_runner_config.py -v
```

预期：全部 6 个 `TaskTestRunnerConfigTest` 测试通过。

- [ ] **Step 5: 提交数据结构和测试**

```powershell
git add tests/test_task_test_runner_config.py src/service_robot_navigation/scripts/run_task_tests.py
git commit -m "feat: add waypoint failure diagnostics"
```

### Task 2: 在失败路径采集 AMCL 位姿与 action state

**Files:**

- Modify: `tests/test_task_test_runner_config.py:83-151`
- Modify: `src/service_robot_navigation/scripts/run_task_tests.py:285-356`

- [ ] **Step 1: 写出 timeout 的失败行为测试**

在测试类中加入以下 fake client 测试；它约束 timeout 时先读取 action state、取消 goal，再返回最新位姿的诊断结果：

```python
    def test_timeout_result_contains_latest_pose_and_action_state(self):
        runner_module = load_runner_module()

        class FakeGoal:
            def __init__(self):
                self.target_pose = type("TargetPose", (), {
                    "header": type("Header", (), {"frame_id": "", "stamp": None})(),
                    "pose": type("Pose", (), {
                        "position": type("Position", (), {"x": 0.0, "y": 0.0, "z": 0.0})(),
                        "orientation": type("Orientation", (), {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0})(),
                    })(),
                })()

        class FakeClient:
            def __init__(self):
                self.cancelled = False

            def send_goal(self, goal):
                self.goal = goal

            def wait_for_result(self, duration):
                return False

            def get_state(self):
                return 1

            def cancel_goal(self):
                self.cancelled = True

        fake_runner = object.__new__(runner_module.TaskTestRunner)
        fake_runner.config = {
            "defaults": {
                "frame_id": "map", "timeout": 1.0,
                "xy_tolerance": 0.25, "yaw_tolerance": 0.25,
            }
        }
        fake_runner.goal_cls = FakeGoal
        fake_runner.client = FakeClient()
        fake_runner.rospy = type("Rospy", (), {
            "Duration": staticmethod(lambda seconds: seconds),
            "Time": type("Time", (), {"now": staticmethod(lambda: 0.0)}),
            "loginfo": staticmethod(lambda *args: None),
            "logwarn": staticmethod(lambda *args: None),
        })()
        fake_runner.clear_costmaps = lambda: None
        fake_runner.current_pose = lambda: (1.25, 2.55, 1.3708)

        result = fake_runner.execute_waypoint({
            "name": "long_counter_left",
            "pose": [1.55, 2.15, 1.5708],
        })

        self.assertFalse(result["success"])
        self.assertIn("timeout", result["reason"])
        self.assertTrue(fake_runner.client.cancelled)
        self.assertEqual(1, result["diagnostics"]["action_state"])
        self.assertEqual(
            [1.25, 2.55, 1.3708],
            result["diagnostics"]["current_pose"],
        )

    def test_failed_pose_read_becomes_diagnostic_evidence(self):
        runner_module = load_runner_module()
        fake_runner = object.__new__(runner_module.TaskTestRunner)

        def unavailable_pose():
            raise RuntimeError("timed out waiting for /amcl_pose")

        fake_runner.current_pose = unavailable_pose
        diagnostics = fake_runner.collect_failure_diagnostics(
            [1.55, 2.15, 1.5708],
            1,
        )

        self.assertEqual(1, diagnostics["action_state"])
        self.assertEqual(
            "timed out waiting for /amcl_pose",
            diagnostics["pose_error_message"],
        )
```

- [ ] **Step 2: 运行测试并确认先失败**

运行：

```powershell
python -m unittest discover -s tests -p test_task_test_runner_config.py -v
```

预期：timeout 测试以 `KeyError: 'diagnostics'` 失败；位姿读取失败测试以
`AttributeError` 失败，提示没有 `collect_failure_diagnostics`；所有旧测试通过。

- [ ] **Step 3: 实现诊断采集并覆盖三条失败路径**

在 `TaskTestRunner.clear_costmaps` 后增加：

```python
    def collect_failure_diagnostics(self, target_pose, action_state):
        try:
            current_pose = self.current_pose()
        except Exception as exc:
            return build_failure_diagnostics(
                target_pose,
                action_state,
                pose_error_message=exc,
            )
        return build_failure_diagnostics(
            target_pose,
            action_state,
            current_pose=current_pose,
        )
```

将 `execute_waypoint` 的 timeout 分支替换为：

```python
        if not finished:
            state = self.client.get_state()
            self.client.cancel_goal()
            return {
                "name": waypoint["name"],
                "success": False,
                "duration": time.time() - start,
                "reason": "timeout after {:.1f}s".format(timeout),
                "diagnostics": self.collect_failure_diagnostics(
                    waypoint["pose"], state
                ),
            }
```

在 `state != self.goal_status_cls.SUCCEEDED` 的返回字典加入：

```python
                "diagnostics": self.collect_failure_diagnostics(
                    waypoint["pose"], state
                ),
```

在最终 `error` 容差失败的返回字典加入：

```python
                "diagnostics": build_failure_diagnostics(
                    waypoint["pose"],
                    state,
                    current_pose=current_pose,
                ),
```

- [ ] **Step 4: 确认失败路径测试通过**

运行：

```powershell
python -m unittest discover -s tests -p test_task_test_runner_config.py -v
```

预期：全部 8 个 `TaskTestRunnerConfigTest` 测试通过；timeout 测试确认
goal 已取消、state 为 `1`、诊断中含最终位姿；AMCL 读取失败测试确认原始异常
出现在 `pose_error_message` 中。

- [ ] **Step 5: 提交执行器诊断采集**

```powershell
git add tests/test_task_test_runner_config.py src/service_robot_navigation/scripts/run_task_tests.py
git commit -m "feat: capture diagnostics for failed waypoints"
```

### Task 3: 在控制台摘要中打印诊断

**Files:**

- Modify: `tests/test_task_test_runner_config.py:83-151`
- Modify: `src/service_robot_navigation/scripts/run_task_tests.py:358-379`

- [ ] **Step 1: 写出失败的格式化测试**

在测试类中加入：

```python
    def test_format_failure_diagnostics_includes_all_available_fields(self):
        runner = load_runner_module()
        detail = runner.format_failure_diagnostics({
            "action_state": 1,
            "current_pose": [1.25, 2.55, 1.3708],
            "target_pose": [1.55, 2.15, 1.5708],
            "error": {"xy": 0.5, "yaw": 0.2},
            "pose_error_message": "amcl read failed",
        })

        self.assertIn("action_state=1", detail)
        self.assertIn("current_pose=(1.250,2.550,1.371)", detail)
        self.assertIn("target_pose=(1.550,2.150,1.571)", detail)
        self.assertIn("final_xy=0.500", detail)
        self.assertIn("final_yaw=0.200", detail)
        self.assertIn("pose_read_error=amcl read failed", detail)
```

- [ ] **Step 2: 运行测试并确认先失败**

运行：

```powershell
python -m unittest discover -s tests -p test_task_test_runner_config.py -v
```

预期：新增测试以 `AttributeError` 失败，提示模块没有
`format_failure_diagnostics`。

- [ ] **Step 3: 实现格式化并接入 `print_summary`**

在 `TaskTestRunner` 类前加入：

```python
def format_failure_diagnostics(diagnostics):
    parts = ["action_state={}".format(diagnostics["action_state"])]
    for key in ("current_pose", "target_pose"):
        if key in diagnostics:
            parts.append(
                "{}=({:.3f},{:.3f},{:.3f})".format(key, *diagnostics[key])
            )
    if "error" in diagnostics:
        parts.append("final_xy={xy:.3f}".format(**diagnostics["error"]))
        parts.append("final_yaw={yaw:.3f}".format(**diagnostics["error"]))
    if "pose_error_message" in diagnostics:
        parts.append(
            "pose_read_error={}".format(diagnostics["pose_error_message"])
        )
    return " diagnostics=" + " ".join(parts)
```

在 `print_summary` 中、追加 `reason` 后加入：

```python
            if not waypoint["success"] and "diagnostics" in waypoint:
                detail += format_failure_diagnostics(waypoint["diagnostics"])
```

- [ ] **Step 4: 确认全部离线验证通过**

运行：

```powershell
python -m unittest discover -s tests -v
git diff --check
```

预期：15 个离线测试全部通过；`git diff --check` 无输出且退出码为 0。

- [ ] **Step 5: 提交控制台诊断输出**

```powershell
git add tests/test_task_test_runner_config.py src/service_robot_navigation/scripts/run_task_tests.py
git commit -m "feat: print waypoint failure diagnostics"
```

### Task 4: 在 ROS Noetic/Gazebo 中复现并选择修复分支

**Files:**

- Verify: `src/service_robot_navigation/scripts/run_task_tests.py`
- Verify: `src/service_robot_navigation/config/task_tests.yaml`
- Inspect only: `src/my_world/worlds/indoor.world`

- [ ] **Step 1: 构建并启动导航仿真**

在 Ubuntu 20.04 + ROS Noetic 中运行：

```bash
cd ~/service_robot
catkin_make
source devel/setup.bash
roslaunch service_robot_navigation sim_navigation.launch
```

预期：Gazebo、AMCL、`/move_base` 已启动，RViz 能显示 `/map`。

- [ ] **Step 2: 启动只读采集并配置 RViz**

在四个独立终端分别运行：

```bash
source ~/service_robot/devel/setup.bash
rostopic echo /amcl_pose
```

```bash
source ~/service_robot/devel/setup.bash
rostopic echo /move_base/status
```

```bash
source ~/service_robot/devel/setup.bash
rostopic echo /cmd_vel
```

```bash
source ~/service_robot/devel/setup.bash
rostopic echo /move_base/DWAPlannerROS/local_plan
```

预期：RViz 同时显示 `/move_base/global_costmap/costmap`、
`/move_base/local_costmap/costmap`、`/move_base/GlobalPlanner/plan` 和
`/move_base/DWAPlannerROS/local_plan`。

- [ ] **Step 3: 运行任务并保留 Task 3 证据**

```bash
source ~/service_robot/devel/setup.bash
rosrun service_robot_navigation run_task_tests.py
```

预期：Task 3 若仍失败，摘要含 `action_state`、`current_pose`、
`target_pose`、`final_xy`、`final_yaw` 或 `pose_read_error`；保存
costmap recovery 前 10 秒的 move_base 日志和四个 topic 的对应片段。

- [ ] **Step 4: 仅记录唯一的下一修复分支，不在本任务修改它**

```text
B_left/B_bottom 附近缺少或拒绝 local plan
  -> 下一计划修改 indoor.world、扩大净口、重建 indoor.pgm/yaml。

接近 long_counter_left 但 final_xy 或 final_yaw 超出容差
  -> 下一计划核对目标 yaw 与 DWA 成功容差。

static map 有路但 local costmap 出现额外障碍
  -> 下一计划检查 /scan 的 marking 与 clearing。
```

## 计划自检

- 设计要求的诊断字段在 Task 1、Task 2、Task 3 中依次定义、采集和输出。
- timeout、非成功 action state、最终位姿误差三条失败路径均由 Task 2 覆盖。
- ROS 运行时证据和三条决策规则均由 Task 4 覆盖。
- 本计划未调整 waypoint、DWA、costmap、world 或地图；这些改动必须由运行时证据触发。
