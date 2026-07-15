import contextlib
import io
from pathlib import Path
import importlib.util
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
NAV_PKG = ROOT / "src" / "service_robot_navigation"
TASK_CONFIG = NAV_PKG / "config" / "task_tests.yaml"
RUNNER = NAV_PKG / "scripts" / "run_task_tests.py"
CMAKE = NAV_PKG / "CMakeLists.txt"
PACKAGE = NAV_PKG / "package.xml"


def load_runner_module():
    spec = importlib.util.spec_from_file_location("run_task_tests", RUNNER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TaskTestRunnerConfigTest(unittest.TestCase):
    def test_task_config_defines_five_ordered_pose_tasks(self):
        with TASK_CONFIG.open(encoding="utf-8") as fh:
            config = yaml.safe_load(fh)

        self.assertTrue(config["defaults"]["initialize_amcl"])
        self.assertEqual([2.0, 8.05, 1.5708], config["defaults"]["initial_pose"])

        task_names = [task["name"] for task in config["tasks"]]
        self.assertEqual(
            [
                "task_1_take_medicine_to_ward_a",
                "task_2_take_medicine_to_ward_b",
                "task_3_long_counter_service",
                "task_4_staggered_channel",
                "task_5_narrow_area_to_dock",
            ],
            task_names,
        )

        for task in config["tasks"]:
            self.assertGreaterEqual(len(task["waypoints"]), 1, task["name"])
            for waypoint in task["waypoints"]:
                self.assertEqual(3, len(waypoint["pose"]), waypoint["name"])
                self.assertIsInstance(waypoint["pose"][2], (int, float))

        self.assertEqual(2, len(config["tasks"][0]["waypoints"]))
        self.assertGreaterEqual(len(config["tasks"][1]["waypoints"]), 6)
        self.assertEqual(
            [
                "ward_a_door",
                "staggered_exit",
                "staggered_mid",
                "staggered_entry",
                "take_medicine",
                "ward_b",
            ],
            [waypoint["name"] for waypoint in config["tasks"][1]["waypoints"]],
        )
        self.assertEqual(3, len(config["tasks"][2]["waypoints"]))
        self.assertEqual([3.05, 2.15, 1.5708], config["tasks"][2]["waypoints"][2]["pose"])
        self.assertGreaterEqual(len(config["tasks"][3]["waypoints"]), 3)
        self.assertGreaterEqual(len(config["tasks"][4]["waypoints"]), 4)

    def test_runner_loads_config_and_computes_pose_errors_without_ros(self):
        runner = load_runner_module()
        config = runner.load_task_config(TASK_CONFIG)

        self.assertEqual(5, len(config["tasks"]))
        self.assertAlmostEqual(0.0, runner.normalize_angle(6.283185307179586), places=6)
        self.assertAlmostEqual(0.1, runner.normalize_angle(0.1), places=6)
        self.assertAlmostEqual(-0.1, runner.normalize_angle(-0.1), places=6)

        error = runner.compute_pose_error((1.0, 2.0, 3.10), (1.3, 1.6, -3.10))
        self.assertAlmostEqual(0.5, error["xy"], places=6)
        self.assertAlmostEqual(0.08318530717958605, error["yaw"], places=6)

        self.assertTrue(runner.pose_within_tolerance((2.0, 8.05, 1.5708), [2.0, 8.05, 1.5708], 0.05, 0.05))
        self.assertFalse(runner.pose_within_tolerance((2.0, 8.05, 0.0), [2.0, 8.05, 1.5708], 0.05, 0.05))

    def test_build_failure_diagnostics_includes_current_pose_and_error(self):
        runner = load_runner_module()

        diagnostics = runner.build_failure_diagnostics(
            [1.55, 2.15, 1.5708],
            1,
            current_pose=(1.25, 2.55, 1.3708),
        )

        self.assertEqual([1.55, 2.15, 1.5708], diagnostics["target_pose"])
        self.assertEqual(1, diagnostics["action_state"])
        self.assertEqual([1.25, 2.55, 1.3708], diagnostics["current_pose"])
        self.assertAlmostEqual(0.5, diagnostics["error"]["xy"], places=6)
        self.assertAlmostEqual(0.2, diagnostics["error"]["yaw"], places=6)

    def test_build_failure_diagnostics_includes_pose_error_message_without_pose(self):
        runner = load_runner_module()

        diagnostics = runner.build_failure_diagnostics(
            [1.55, 2.15, 1.5708],
            1,
            pose_error_message="timed out waiting for /amcl_pose",
        )

        self.assertEqual([1.55, 2.15, 1.5708], diagnostics["target_pose"])
        self.assertEqual(1, diagnostics["action_state"])
        self.assertEqual("timed out waiting for /amcl_pose", diagnostics["pose_error_message"])
        self.assertNotIn("current_pose", diagnostics)
        self.assertNotIn("error", diagnostics)

    def test_format_failure_diagnostics_includes_all_available_fields(self):
        runner = load_runner_module()

        result = runner.format_failure_diagnostics(
            {
                "action_state": 1,
                "current_pose": [1.25, 2.55, 1.3708],
                "target_pose": [1.55, 2.15, 1.5708],
                "error": {"xy": 0.5, "yaw": 0.2},
                "pose_error_message": "amcl read failed",
            }
        )

        self.assertIn("action_state=1", result)
        self.assertIn("current_pose=(1.250,2.550,1.371)", result)
        self.assertIn("target_pose=(1.550,2.150,1.571)", result)
        self.assertIn("final_xy=0.500", result)
        self.assertIn("final_yaw=0.200", result)
        self.assertIn("pose_read_error=amcl read failed", result)

        newline_result = runner.format_failure_diagnostics(
            {"pose_error_message": "amcl\nread failed"}
        )

        self.assertNotIn("\n", newline_result)
        self.assertIn("pose_read_error=amcl read failed", newline_result)

    def make_fake_waypoint_runner(self, runner_module, finished, state, poses):
        class FakeGoal:
            def __init__(self):
                self.target_pose = type(
                    "TargetPose",
                    (),
                    {
                        "header": type("Header", (), {"frame_id": "", "stamp": None})(),
                        "pose": type(
                            "Pose",
                            (),
                            {
                                "position": type("Position", (), {"x": 0.0, "y": 0.0, "z": 0.0})(),
                                "orientation": type("Orientation", (), {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0})(),
                            },
                        )(),
                    },
                )()

        class FakeClient:
            def __init__(self):
                self.cancelled = False
                self.events = []
                self.state = state

            def send_goal(self, goal):
                pass

            def wait_for_result(self, timeout):
                return finished

            def get_state(self):
                self.events.append("get_state")
                return self.state

            def cancel_goal(self):
                self.cancelled = True
                self.events.append("cancel_goal")
                self.state = 2

        class FakeRospy:
            Time = type("Time", (), {"now": staticmethod(lambda: 0.0)})

            def Duration(self, timeout):
                return timeout

            def loginfo(self, *args):
                pass

            def logwarn(self, *args):
                pass

        fake_runner = object.__new__(runner_module.TaskTestRunner)
        fake_runner.config = {"defaults": {"timeout": 1.0}}
        fake_runner.goal_cls = FakeGoal
        fake_runner.goal_status_cls = type("GoalStatus", (), {"SUCCEEDED": 3})
        fake_runner.client = FakeClient()
        fake_runner.rospy = FakeRospy()
        fake_runner.clear_costmaps = lambda: None
        pose_values = iter(poses)
        fake_runner.current_pose = lambda: next(pose_values)
        return fake_runner

    def test_execute_waypoint_timeout_includes_cancelled_action_and_pose_diagnostics(self):
        runner_module = load_runner_module()
        fake_runner = self.make_fake_waypoint_runner(
            runner_module,
            finished=False,
            state=1,
            poses=[(1.25, 2.55, 1.3708), (1.25, 2.55, 1.3708)],
        )

        result = fake_runner.execute_waypoint(
            {"name": "counter", "pose": [1.55, 2.15, 1.5708]}
        )

        self.assertFalse(result["success"])
        self.assertIn("timeout", result["reason"])
        self.assertTrue(fake_runner.client.cancelled)
        self.assertEqual(1, result["diagnostics"]["action_state"])
        self.assertEqual([1.25, 2.55, 1.3708], result["diagnostics"]["current_pose"])
        self.assertEqual(["get_state", "cancel_goal"], fake_runner.client.events)

    def test_execute_waypoint_records_diagnostics_for_non_success_action_state(self):
        runner_module = load_runner_module()
        fake_runner = self.make_fake_waypoint_runner(
            runner_module,
            finished=True,
            state=4,
            poses=[(1.25, 2.55, 1.3708), (1.25, 2.55, 1.3708)],
        )

        result = fake_runner.execute_waypoint(
            {"name": "counter", "pose": [1.55, 2.15, 1.5708]}
        )

        self.assertFalse(result["success"])
        self.assertEqual("move_base returned state 4", result["reason"])
        self.assertEqual(4, result["diagnostics"]["action_state"])
        self.assertEqual([1.25, 2.55, 1.3708], result["diagnostics"]["current_pose"])
        self.assertAlmostEqual(0.5, result["diagnostics"]["error"]["xy"], places=6)

    def test_print_summary_keeps_diagnostics_on_failed_waypoint_lines_only(self):
        runner = load_runner_module()
        results = [
            {
                "name": "successful_task",
                "success": True,
                "duration": 0.1,
                "waypoints": [
                    {
                        "name": "successful_waypoint",
                        "success": True,
                        "diagnostics": {"pose_error_message": "should not print"},
                    }
                ],
            },
            {
                "name": "timeout_task",
                "success": False,
                "duration": 0.2,
                "waypoints": [
                    {
                        "name": "timeout_waypoint",
                        "success": False,
                        "reason": "timeout after 1.0s",
                    }
                ],
            },
            {
                "name": "diagnostic_task",
                "success": False,
                "duration": 0.3,
                "waypoints": [
                    {
                        "name": "diagnostic_waypoint",
                        "success": False,
                        "reason": "move_base returned state 4",
                        "diagnostics": {"pose_error_message": "amcl\nread failed"},
                    }
                ],
            },
        ]
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            runner.print_summary(results)

        lines = output.getvalue().splitlines()
        successful_line = next(line for line in lines if "successful_waypoint" in line)
        timeout_line = next(line for line in lines if "timeout_waypoint" in line)
        diagnostic_lines = [line for line in lines if "diagnostic_waypoint" in line]

        self.assertNotIn("diagnostics=", successful_line)
        self.assertIn("reason=timeout after 1.0s", timeout_line)
        self.assertNotIn("diagnostics=", timeout_line)
        self.assertEqual(1, len(diagnostic_lines))
        self.assertIn("diagnostics=", diagnostic_lines[0])
        self.assertIn("pose_read_error=amcl read failed", diagnostic_lines[0])
        self.assertNotIn("amcl\nread failed", output.getvalue())

    def test_execute_waypoint_records_diagnostics_for_success_state_with_pose_error(self):
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

        self.assertFalse(result["success"])
        self.assertIn("pose error", result["reason"])
        self.assertEqual(3, result["diagnostics"]["action_state"])
        self.assertEqual([1.55, 2.15, 1.5708], result["diagnostics"]["target_pose"])
        self.assertEqual([1.25, 2.55, 1.3708], result["diagnostics"]["current_pose"])
        self.assertAlmostEqual(0.5, result["diagnostics"]["error"]["xy"], places=6)

    def test_collect_failure_diagnostics_records_amcl_read_error(self):
        runner_module = load_runner_module()
        fake_runner = object.__new__(runner_module.TaskTestRunner)

        def raise_pose_error():
            raise RuntimeError("timed out waiting for /amcl_pose")

        fake_runner.current_pose = raise_pose_error
        diagnostics = fake_runner.collect_failure_diagnostics([1.55, 2.15, 1.5708], 1)

        self.assertEqual(1, diagnostics["action_state"])
        self.assertEqual("timed out waiting for /amcl_pose", diagnostics["pose_error_message"])

    def test_runner_waits_for_amcl_pose_after_publishing_initial_pose(self):
        runner_module = load_runner_module()

        class FakePose:
            def __init__(self):
                self.header = type("Header", (), {"frame_id": "", "stamp": None})()
                position = type("Position", (), {"x": 0.0, "y": 0.0, "z": 0.0})()
                orientation = type("Orientation", (), {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0})()
                pose = type("Pose", (), {"position": position, "orientation": orientation})()
                self.pose = type("PoseWithCovariance", (), {"pose": pose, "covariance": [0.0] * 36})()

        class FakePublisher:
            def publish(self, msg):
                pass

        class FakeRospy:
            def __init__(self):
                self.sleep_calls = []
                self.Time = type("Time", (), {"now": staticmethod(lambda: 0.0)})

            def Publisher(self, *args, **kwargs):
                return FakePublisher()

            def sleep(self, duration):
                self.sleep_calls.append(duration)

            def loginfo(self, *args):
                pass

        fake_runner = object.__new__(runner_module.TaskTestRunner)
        fake_runner.config = {
            "defaults": {
                "initialize_amcl": True,
                "initial_pose": [2.0, 8.05, 1.5708],
                "frame_id": "map",
                "xy_tolerance": 0.25,
                "yaw_tolerance": 0.25,
                "amcl_settle_timeout": 1.0,
            }
        }
        fake_runner.initial_pose_topic = "/initialpose"
        fake_runner.pose_msg_cls = FakePose
        fake_runner.rospy = FakeRospy()
        pose_checks = []

        def current_pose():
            pose_checks.append(True)
            return (2.0, 8.05, 1.5708)

        fake_runner.current_pose = current_pose
        fake_runner.initialize_amcl_if_requested()

        self.assertGreaterEqual(len(pose_checks), 1)

    def test_runner_is_installed_and_declares_runtime_dependencies(self):
        cmake = CMAKE.read_text(encoding="utf-8")
        package_xml = PACKAGE.read_text(encoding="utf-8")

        self.assertIn("scripts/run_task_tests.py", cmake)
        for dependency in [
            "rospy",
            "actionlib",
            "actionlib_msgs",
            "move_base_msgs",
            "geometry_msgs",
            "std_srvs",
            "python3-yaml",
        ]:
            self.assertIn(f"<exec_depend>{dependency}</exec_depend>", package_xml)


if __name__ == "__main__":
    unittest.main()
