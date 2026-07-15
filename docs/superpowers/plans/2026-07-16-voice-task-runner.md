# 语音任务执行器 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增一个 ROS Noetic Python 语音任务执行器，将 `ExtractKeyword.srv` 返回的 `task1`～`task5` 映射到现有导航任务，并通过 `SynthesizeSpeech.srv` 播报任务状态。

**Architecture:** 新脚本复用 `run_task_tests.py` 的配置加载和 `TaskTestRunner.execute_task`，只增加任务选择、语音服务调用和状态播报。纯任务编号/播报逻辑保持为无 ROS 依赖的函数；ROS 服务控制器通过可注入的 client/request factory 测试，生产入口再创建真实 ROS service proxy。

**Tech Stack:** Python 3、ROS Noetic、`rospy`、`voice_keyword_extractor/ExtractKeyword.srv`、`cloud_tts/SynthesizeSpeech.srv`、`unittest`、YAML。

---

## 文件结构

- Create: `src/service_robot_navigation/scripts/run_voice_tasks.py` — 任务编号规范化、播报文本、语音服务控制器、ROS CLI 入口。
- Create: `tests/test_voice_task_runner.py` — 纯逻辑、fake service 和 fake navigation runner 测试。
- Modify: `src/service_robot_navigation/CMakeLists.txt` — 安装新脚本。
- Modify: `src/service_robot_navigation/package.xml` — 声明两个语音包的运行依赖。
- Modify: `README.md` — 增加语音任务启动顺序和接口命令。

## Task 1: 先为任务路由和播报文本建立失败测试

**Files:**
- Create: `tests/test_voice_task_runner.py`
- Test target: `src/service_robot_navigation/scripts/run_voice_tasks.py`（此时文件尚不存在）

- [ ] **Step 1: 写出第一组失败测试**

在 `tests/test_voice_task_runner.py` 中加入以下可直接运行的测试入口和任务 ID 测试：

```python
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "src" / "service_robot_navigation" / "scripts" / "run_voice_tasks.py"


def load_module():
    spec = importlib.util.spec_from_file_location("run_voice_tasks", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class VoiceTaskRoutingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def test_normalize_task_id_accepts_supported_forms(self):
        for value in ("task1", "task_1", "task 1", "任务1", "1"):
            with self.subTest(value=value):
                self.assertEqual(self.module.normalize_task_id(value), "task1")

    def test_normalize_task_id_rejects_unknown_values(self):
        for value in ("", "medicine", "task6", "任务六", None):
            with self.subTest(value=value):
                self.assertIsNone(self.module.normalize_task_id(value))

    def test_build_task_index_uses_yaml_task_numbers(self):
        tasks = [
            {"name": "task_1_take_medicine_to_ward_a"},
            {"name": "task_2_take_medicine_to_ward_b"},
            {"name": "task_3_long_counter_service"},
            {"name": "task_4_staggered_channel"},
            {"name": "task_5_narrow_area_to_dock"},
        ]
        index = self.module.build_task_index(tasks)
        self.assertIs(index["task1"], tasks[0])
        self.assertIs(index["task5"], tasks[4])

    def test_build_task_index_rejects_duplicate_or_missing_task_numbers(self):
        with self.assertRaises(ValueError):
            self.module.build_task_index([{"name": "task_1_first"}, {"name": "task_1_again"}])

    def test_build_status_text_is_stable(self):
        task = {"description": "请去取药台取药并送至病房A"}
        self.assertEqual(
            self.module.build_status_text("task1", task, "start"),
            "准备执行任务1：请去取药台取药并送至病房A。",
        )
        self.assertEqual(
            self.module.build_status_text("task1", task, "success"),
            "任务1已完成。",
        )
        self.assertEqual(
            self.module.build_status_text("task1", task, "failure"),
            "任务1执行失败，请检查导航状态。",
        )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试确认按预期失败**

运行：

```powershell
python -m unittest tests.test_voice_task_runner -v
```

预期：测试模块加载失败，原因是 `src/service_robot_navigation/scripts/run_voice_tasks.py` 尚不存在；这证明测试确实针对新功能而不是已有行为。

- [ ] **Step 3: 实现最小纯函数**

在新脚本中实现 `normalize_task_id`、`build_task_index` 和 `build_status_text`。任务名用正则 `^task_(\d+)(?:_|$)` 提取编号；只允许 1～5，重复编号或缺少任一编号时抛出 `ValueError`。`normalize_task_id` 接受 `task1`、`task_1`、`task 1`、`任务1` 和纯数字，并对其它输入返回 `None`。

- [ ] **Step 4: 运行测试确认通过**

运行：

```powershell
python -m unittest tests.test_voice_task_runner.VoiceTaskRoutingTest -v
```

预期：路由和播报测试全部 PASS。

## Task 2: 用 fake 服务测试语音控制器

**Files:**
- Modify: `tests/test_voice_task_runner.py`
- Test target: `src/service_robot_navigation/scripts/run_voice_tasks.py`

- [ ] **Step 1: 写出控制器失败测试**

在测试文件中追加以下 fake 对象和测试：

```python
class FakeRequest:
    def __init__(self):
        self.start_recording = False
        self.record_seconds = 0.0
        self.text = ""
        self.play_audio = False


class FakeKeywordResponse:
    def __init__(self, success=True, keyword="task1", error_message=""):
        self.success = success
        self.keyword = keyword
        self.transcript = ""
        self.error_message = error_message


class FakeTtsResponse:
    def __init__(self, success=True):
        self.success = success
        self.error_message = ""


class FakeRospy:
    def __init__(self):
        self.infos = []
        self.warnings = []

    def loginfo(self, *args):
        self.infos.append(args)

    def logwarn(self, *args):
        self.warnings.append(args)


class FakeNavigationRunner:
    def __init__(self, result):
        self.result = result
        self.executed = []

    def execute_task(self, task):
        self.executed.append(task)
        return self.result


class VoiceTaskControllerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def setUp(self):
        self.tasks = {
            "task1": {"name": "task_1_demo", "description": "请去取药台取药并送至病房A"},
        }
        self.keyword_requests = []
        self.tts_requests = []

        def keyword_client(request):
            self.keyword_requests.append(request)
            return FakeKeywordResponse()

        def tts_client(request):
            self.tts_requests.append(request)
            return FakeTtsResponse()

        self.keyword_client = keyword_client
        self.tts_client = tts_client

    def make_controller(self, navigation_result):
        return self.module.VoiceTaskController(
            tasks=self.tasks,
            task_runner=FakeNavigationRunner(navigation_result),
            keyword_client=self.keyword_client,
            tts_client=self.tts_client,
            keyword_request_factory=FakeRequest,
            tts_request_factory=FakeRequest,
            rospy_module=FakeRospy(),
            record_seconds=4.0,
        )

    def test_execute_once_records_command_executes_selected_task_and_speaks(self):
        controller = self.make_controller([{"success": True}])
        result = controller.execute_once()
        self.assertTrue(result["success"])
        self.assertEqual(len(controller.task_runner.executed), 1)
        self.assertEqual(controller.task_runner.executed[0]["name"], "task_1_demo")
        self.assertEqual(self.keyword_requests[0].start_recording, True)
        self.assertEqual(self.keyword_requests[0].record_seconds, 4.0)
        self.assertEqual(self.tts_requests[0].play_audio, True)
        self.assertIn("准备执行任务1", self.tts_requests[0].text)
        self.assertIn("任务1已完成", self.tts_requests[1].text)

    def test_unknown_command_does_not_execute_navigation(self):
        def keyword_client(request):
            return FakeKeywordResponse(keyword="medicine")

        controller = self.make_controller([{"success": True}])
        controller.keyword_client = keyword_client
        self.assertIsNone(controller.execute_once())
        self.assertEqual(controller.task_runner.executed, [])

    def test_keyword_failure_does_not_execute_navigation(self):
        def keyword_client(request):
            return FakeKeywordResponse(success=False, error_message="recognizer failed")

        controller = self.make_controller([{"success": True}])
        controller.keyword_client = keyword_client
        self.assertIsNone(controller.execute_once())
        self.assertEqual(controller.task_runner.executed, [])

    def test_tts_failure_does_not_change_navigation_result(self):
        def tts_client(request):
            return FakeTtsResponse(success=False)

        controller = self.make_controller([{"success": True}])
        controller.tts_client = tts_client
        result = controller.execute_once()
        self.assertTrue(result["success"])
        self.assertEqual(len(controller.task_runner.executed), 1)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行控制器测试确认失败**

运行：

```powershell
python -m unittest tests.test_voice_task_runner.VoiceTaskControllerTest -v
```

预期：失败，原因是 `VoiceTaskController` 尚未定义，而不是 fake 测试本身导入错误。

- [ ] **Step 3: 实现最小 `VoiceTaskController`**

实现以下行为：

```python
class VoiceTaskController:
    def __init__(self, tasks, task_runner, keyword_client, tts_client,
                 keyword_request_factory, tts_request_factory,
                 rospy_module, record_seconds=5.0):
        self.tasks = tasks
        self.task_runner = task_runner
        self.keyword_client = keyword_client
        self.tts_client = tts_client
        self.keyword_request_factory = keyword_request_factory
        self.tts_request_factory = tts_request_factory
        self.rospy = rospy_module
        self.record_seconds = float(record_seconds)

    def speak(self, text):
        request = self.tts_request_factory()
        request.text = text
        request.play_audio = True
        try:
            response = self.tts_client(request)
            if not response.success:
                self.rospy.logwarn("TTS failed: %s", response.error_message)
        except Exception as error:
            self.rospy.logwarn("TTS service call failed: %s", error)

    def execute_once(self):
        request = self.keyword_request_factory()
        request.start_recording = True
        request.record_seconds = self.record_seconds
        try:
            response = self.keyword_client(request)
        except Exception as error:
            self.rospy.logwarn("Keyword service call failed: %s", error)
            return None

        task_id = normalize_task_id(response.keyword) if response.success else None
        if task_id is None or task_id not in self.tasks:
            self.speak("未识别到有效任务，请重新说出任务。")
            return None

        task = self.tasks[task_id]
        self.speak(build_status_text(task_id, task, "start"))
        result = self.task_runner.execute_task(task)
        self.speak(build_status_text(task_id, task, "success" if result["success"] else "failure"))
        return result
```

`execute_once` 对识别失败/未知任务返回 `None`，对导航任务返回原始 `execute_task` 结果；TTS 异常只记录 warning。

- [ ] **Step 4: 运行控制器测试确认通过**

运行：

```powershell
python -m unittest tests.test_voice_task_runner.VoiceTaskControllerTest -v
```

预期：控制器测试全部 PASS。

## Task 3: 接入 ROS 入口、安装脚本和运行依赖

**Files:**
- Modify: `src/service_robot_navigation/scripts/run_voice_tasks.py`
- Modify: `src/service_robot_navigation/CMakeLists.txt`
- Modify: `src/service_robot_navigation/package.xml`

- [ ] **Step 1: 为 CLI 和 ROS 初始化补充测试约束**

在 `tests/test_voice_task_runner.py` 中增加安装契约检查：

```python
class VoiceTaskPackagingTest(unittest.TestCase):
    def test_navigation_package_installs_voice_runner_and_declares_voice_dependencies(self):
        cmake = (ROOT / "src" / "service_robot_navigation" / "CMakeLists.txt").read_text(encoding="utf-8")
        package_xml = (ROOT / "src" / "service_robot_navigation" / "package.xml").read_text(encoding="utf-8")
        self.assertIn("scripts/run_voice_tasks.py", cmake)
        self.assertIn("<exec_depend>voice_keyword_extractor</exec_depend>", package_xml)
        self.assertIn("<exec_depend>cloud_tts</exec_depend>", package_xml)

    def test_voice_runner_exposes_required_cli_options(self):
        module = load_module()
        args = module.parse_args([
            "--keyword-service", "/custom/keyword",
            "--tts-service", "/custom/tts",
            "--record-seconds", "3",
            "--once",
        ])
        self.assertEqual(args.keyword_service, "/custom/keyword")
        self.assertEqual(args.tts_service, "/custom/tts")
        self.assertEqual(args.record_seconds, 3.0)
        self.assertTrue(args.once)
```

- [ ] **Step 2: 运行测试确认入口/安装约束失败**

运行：

```powershell
python -m unittest tests.test_voice_task_runner.VoiceTaskPackagingTest -v
```

预期：失败，因为新脚本 CLI、CMake 安装项和 package 依赖尚未加入。

- [ ] **Step 3: 实现生产入口**

在脚本中增加：

```python
def parse_args(argv):
    parser = argparse.ArgumentParser(description="Run voice-selected service robot tasks.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--move-base", default="/move_base")
    parser.add_argument("--pose-topic", default="/amcl_pose")
    parser.add_argument("--initial-pose-topic", default="/initialpose")
    parser.add_argument("--clear-costmaps-service", default="/move_base/clear_costmaps")
    parser.add_argument("--server-timeout", type=float, default=30.0)
    parser.add_argument("--keyword-service", default="/extract_keyword")
    parser.add_argument("--tts-service", default="/synthesize_speech")
    parser.add_argument("--record-seconds", type=float, default=5.0)
    parser.add_argument("--keyword-service-timeout", type=float, default=10.0)
    parser.add_argument("--tts-service-timeout", type=float, default=10.0)
    parser.add_argument("--once", action="store_true")
    return parser.parse_args(argv)
```

`main` 中按以下顺序创建真实对象：加载 YAML、`rospy.init_node("service_robot_voice_task_runner")`、创建 `TaskTestRunner`、等待 move_base、初始化 AMCL、校验五项任务索引、等待两个语音服务、构造 `VoiceTaskController`。默认循环使用 `while not rospy.is_shutdown()` 调用 `execute_once()`；`--once` 在首个有效任务返回后退出。通过 `voice_keyword_extractor.srv` 和 `cloud_tts.srv` 的 generated request/service 类型创建 service proxy，不修改两个服务定义。

在 `CMakeLists.txt` 的 `install(PROGRAMS ...)` 中加入 `scripts/run_voice_tasks.py`；在 `package.xml` 中加入：

```xml
<exec_depend>voice_keyword_extractor</exec_depend>
<exec_depend>cloud_tts</exec_depend>
```

- [ ] **Step 4: 运行入口测试和全量静态测试**

运行：

```powershell
python -m unittest tests.test_voice_task_runner -v
python -m unittest discover -s tests -v
```

预期：新增测试和现有测试全部 PASS。

- [ ] **Step 5: 更新项目 README**

在根目录 `README.md` 的运行章节增加以下真实启动顺序，并明确识别节点必须实际提供 `/extract_keyword`：

```text
终端 1：roslaunch service_robot_navigation sim_navigation.launch
终端 2：roslaunch cloud_tts cloud_tts.launch
终端 3：启动提供 /extract_keyword 的 voice_keyword_extractor 节点
终端 4：python3 src/service_robot_navigation/scripts/run_voice_tasks.py
```

同时注明：`--once` 只执行一条有效语音任务；当前仓库虽有 `voice_keyword_extractor` 服务定义和 launch 文件，但没有提交 `keyword_service_node.py`，因此 ASR 节点仍需由现有语音实现提供。

## Task 4: ROS Noetic 构建、脚本入口和语音闭环验证

**Files:**
- Verify: `src/service_robot_navigation/scripts/run_voice_tasks.py`
- Verify: `src/voice_keyword_extractor/srv/ExtractKeyword.srv`
- Verify: `src/cloud_tts/srv/SynthesizeSpeech.srv`

- [ ] **Step 1: 执行最终 Windows 静态验证**

运行：

```powershell
python -m unittest discover -s tests -v
python -m py_compile src/service_robot_navigation/scripts/run_task_tests.py src/service_robot_navigation/scripts/run_voice_tasks.py
git diff --check HEAD~1
```

预期：测试、编译检查和 diff 检查均返回退出码 0。

- [ ] **Step 2: 在 Ubuntu ROS Noetic 侧构建**

运行：

```bash
source /opt/ros/noetic/setup.bash
cd ~/service_robot
rosdep install --from-paths src --ignore-src -r -y
catkin_make
source devel/setup.bash
rosrun service_robot_navigation run_voice_tasks.py --help
```

预期：catkin 构建成功，`--help` 输出 keyword/TTS 服务和录音时长参数。

- [ ] **Step 3: 执行一次真实语音选择任务**

在仿真、识别和 TTS 节点均启动后运行：

```bash
python3 src/service_robot_navigation/scripts/run_voice_tasks.py --once
```

口述“请去取药台取药并送至病房A”，检查日志中的识别结果为 `task1`，随后听到任务开始播报，导航完成后听到任务完成播报。再分别用 `task2`～`task5` 的语义命令验证任务选择；不要在未确认任务结果时自动重复执行，以免触发重复导航。

- [ ] **Step 4: 检查失败路径**

分别测试未知语句、识别服务失败和 TTS 服务关闭三种情况：未知/识别失败不得发送 move_base 任务；TTS 关闭时导航仍应按原 runner 结果执行并记录 warning。
