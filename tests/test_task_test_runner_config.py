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
