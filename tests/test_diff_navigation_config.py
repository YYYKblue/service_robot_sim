import hashlib
from pathlib import Path
import xml.etree.ElementTree as ET
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
DIFF_MODEL = ROOT / "src" / "sweeper_robot_diff2_submit_ros"
DIFF_URDF = DIFF_MODEL / "urdf" / "sweeper_robot_diff2_submit.urdf"
OMNI_URDF = ROOT / "src" / "sweeper_robot_omni4_base_ros" / "urdf" / "sweeper_robot_omni4_base.urdf"
DIFF_NAV = ROOT / "src" / "service_robot_diff_navigation"
OMNI_NAV = ROOT / "src" / "service_robot_navigation"


def load_yaml(path):
    with path.open(encoding="utf-8") as stream:
        return yaml.safe_load(stream)


def load_robot(path):
    return ET.parse(path).getroot()


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_element(element):
    return (
        element.tag,
        tuple(sorted(element.attrib.items())),
        (element.text or "").strip(),
        tuple(canonical_element(child) for child in element),
    )


class DifferentialNavigationContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.diff_robot = load_robot(DIFF_URDF)
        cls.omni_robot = load_robot(OMNI_URDF)

    def test_diff_model_hides_visible_interface_hardware(self):
        link_names = {link.attrib["name"] for link in self.diff_robot.findall("link")}
        self.assertNotIn("odometry_link", link_names)
        self.assertNotIn("cmd_vel_interface_link", link_names)

        visual_names = {
            visual.attrib.get("name")
            for link in self.diff_robot.findall("link")
            for visual in link.findall("visual")
        }
        self.assertFalse(any("odometry" in name for name in visual_names if name))
        self.assertFalse(any("cmd_vel" in name for name in visual_names if name))

    def test_diff_model_matches_omni_body_and_front_marker_contract(self):
        diff_base = self.diff_robot.find("./link[@name='base_link']")
        omni_base = self.omni_robot.find("./link[@name='base_link']")
        self.assertIsNotNone(diff_base)
        self.assertIsNotNone(omni_base)

        for visual_name in (
            "single_round_0p5m_chassis",
            "slightly_raised_top_plate",
            "front_x_arrow_marker",
            "front_x_arrow_tip_marker",
        ):
            diff_visual = diff_base.find("./visual[@name='{}']".format(visual_name))
            omni_visual = omni_base.find("./visual[@name='{}']".format(visual_name))
            self.assertIsNotNone(diff_visual, visual_name)
            self.assertIsNotNone(omni_visual, visual_name)
            self.assertEqual(
                canonical_element(omni_visual),
                canonical_element(diff_visual),
            )

        diff_collision = diff_base.find("./collision[@name='chassis_collision']")
        omni_collision = omni_base.find("./collision[@name='chassis_collision']")
        self.assertIsNotNone(diff_collision)
        self.assertIsNotNone(omni_collision)
        self.assertEqual(
            canonical_element(omni_collision),
            canonical_element(diff_collision),
        )

        diff_mass = diff_base.find("./inertial/mass")
        omni_mass = omni_base.find("./inertial/mass")
        self.assertEqual(omni_mass.attrib, diff_mass.attrib)

    def test_diff_model_uses_centered_omni_lidar_contract(self):
        lidar_joint = self.diff_robot.find("./joint[@name='lidar_joint']/origin")
        self.assertIsNotNone(lidar_joint)
        self.assertEqual("0 0 0.1610", lidar_joint.attrib["xyz"])

        visualize = self.diff_robot.find("./gazebo[@reference='lidar_link']/sensor/visualize")
        self.assertIsNotNone(visualize)
        self.assertEqual("false", visualize.text.strip())

        samples = self.diff_robot.find(
            "./gazebo[@reference='lidar_link']/sensor/ray/scan/horizontal/samples"
        )
        self.assertIsNotNone(samples)
        self.assertEqual("720", samples.text.strip())

        plugin = self.diff_robot.find("./gazebo[@reference='lidar_link']/sensor/plugin")
        self.assertIsNotNone(plugin)
        self.assertEqual("/scan", plugin.findtext("topicName"))
        self.assertEqual("lidar_link", plugin.findtext("frameName"))

    def test_diff_wheels_use_x_forward_left_right_geometry(self):
        left_joint = self.diff_robot.find("./joint[@name='left_drive_wheel_joint']")
        right_joint = self.diff_robot.find("./joint[@name='right_drive_wheel_joint']")
        self.assertEqual("0 0.1980 0.0680", left_joint.find("origin").attrib["xyz"])
        self.assertEqual("0 -0.1980 0.0680", right_joint.find("origin").attrib["xyz"])
        self.assertEqual("0 1 0", left_joint.find("axis").attrib["xyz"])
        self.assertEqual("0 1 0", right_joint.find("axis").attrib["xyz"])

        drive = self.diff_robot.find("./gazebo/plugin[@filename='libgazebo_ros_diff_drive.so']")
        self.assertIsNotNone(drive)
        self.assertEqual("cmd_vel", drive.findtext("commandTopic"))
        self.assertEqual("odom", drive.findtext("odometryTopic"))
        self.assertEqual("0.3960", drive.findtext("wheelSeparation"))
        self.assertEqual("0.1360", drive.findtext("wheelDiameter"))

    def test_diff_model_has_hidden_symmetric_low_friction_pitch_supports(self):
        supports = {
            "front_passive_support": "0.1800 0 0.0250",
            "rear_passive_support": "-0.1800 0 0.0250",
        }
        for support_name, expected_origin in supports.items():
            link_name = "{}_link".format(support_name)
            link = self.diff_robot.find("./link[@name='{}']".format(link_name))
            self.assertIsNotNone(link, link_name)
            self.assertIsNone(link.find("visual"), link_name)

            sphere = link.find("./collision[@name='support_collision']/geometry/sphere")
            self.assertIsNotNone(sphere, link_name)
            self.assertEqual("0.0250", sphere.attrib["radius"])

            joint = self.diff_robot.find("./joint[@name='{}_joint']".format(support_name))
            self.assertIsNotNone(joint, support_name)
            self.assertEqual("fixed", joint.attrib["type"])
            self.assertEqual("base_link", joint.find("parent").attrib["link"])
            self.assertEqual(link_name, joint.find("child").attrib["link"])
            self.assertEqual(expected_origin, joint.find("origin").attrib["xyz"])

            gazebo = self.diff_robot.find("./gazebo[@reference='{}']".format(link_name))
            self.assertIsNotNone(gazebo, link_name)
            self.assertEqual("0.02", gazebo.findtext("mu1"))
            self.assertEqual("0.02", gazebo.findtext("mu2"))

    def test_diff_navigation_package_files_and_dependencies_exist(self):
        required_files = (
            "package.xml",
            "CMakeLists.txt",
            "launch/diff_sim.launch",
            "launch/navigation.launch",
            "launch/diff_navigation.launch",
            "config/task_tests.yaml",
            "config/amcl_params.yaml",
            "config/dwa_local_planner_params.yaml",
            "maps/indoor.yaml",
            "maps/indoor.pgm",
            "rviz/navigation.rviz",
            "scripts/run_task_tests.py",
            "README.md",
        )
        for relative_path in required_files:
            self.assertTrue((DIFF_NAV / relative_path).is_file(), relative_path)

        package = ET.parse(DIFF_NAV / "package.xml").getroot()
        self.assertEqual("service_robot_diff_navigation", package.findtext("name"))
        dependencies = {
            dependency.text
            for tag in ("depend", "build_depend", "exec_depend")
            for dependency in package.findall(tag)
        }
        self.assertTrue(
            {
                "sweeper_robot_diff2_submit_ros",
                "my_world",
                "gazebo_ros",
                "robot_state_publisher",
                "map_server",
                "amcl",
                "move_base",
                "dwa_local_planner",
                "global_planner",
                "rospy",
                "python3-yaml",
            }.issubset(dependencies)
        )

    def test_diff_navigation_reuses_task_config_and_map_exactly(self):
        self.assertEqual(
            load_yaml(OMNI_NAV / "config" / "task_tests.yaml"),
            load_yaml(DIFF_NAV / "config" / "task_tests.yaml"),
        )
        self.assertEqual(
            sha256(OMNI_NAV / "maps" / "indoor.pgm"),
            sha256(DIFF_NAV / "maps" / "indoor.pgm"),
        )
        self.assertEqual(
            (OMNI_NAV / "maps" / "indoor.yaml").read_text(encoding="utf-8"),
            (DIFF_NAV / "maps" / "indoor.yaml").read_text(encoding="utf-8"),
        )

    def test_diff_navigation_changes_only_required_motion_parameters(self):
        shared_configs = (
            "move_base_params.yaml",
            "global_planner_params.yaml",
            "costmap_common_params.yaml",
            "global_costmap_params.yaml",
            "local_costmap_params.yaml",
        )
        for filename in shared_configs:
            self.assertEqual(
                load_yaml(OMNI_NAV / "config" / filename),
                load_yaml(DIFF_NAV / "config" / filename),
                filename,
            )

        omni_amcl = load_yaml(OMNI_NAV / "config" / "amcl_params.yaml")
        diff_amcl = load_yaml(DIFF_NAV / "config" / "amcl_params.yaml")
        self.assertEqual("omni", omni_amcl["odom_model_type"])
        self.assertEqual("diff", diff_amcl["odom_model_type"])
        omni_amcl.pop("odom_model_type")
        diff_amcl.pop("odom_model_type")
        self.assertEqual(omni_amcl, diff_amcl)

        omni_dwa = load_yaml(OMNI_NAV / "config" / "dwa_local_planner_params.yaml")["DWAPlannerROS"]
        diff_dwa = load_yaml(DIFF_NAV / "config" / "dwa_local_planner_params.yaml")["DWAPlannerROS"]
        for key in ("holonomic_robot", "min_vel_y", "max_vel_y", "acc_lim_y", "vy_samples"):
            omni_dwa.pop(key, None)
            diff_dwa.pop(key, None)
        self.assertEqual(omni_dwa, diff_dwa)

        diff_dwa = load_yaml(DIFF_NAV / "config" / "dwa_local_planner_params.yaml")["DWAPlannerROS"]
        self.assertFalse(diff_dwa["holonomic_robot"])
        self.assertEqual(0.0, diff_dwa["min_vel_y"])
        self.assertEqual(0.0, diff_dwa["max_vel_y"])
        self.assertEqual(0.0, diff_dwa["acc_lim_y"])
        self.assertEqual(1, diff_dwa["vy_samples"])

    def test_diff_runner_preserves_task_runner_cli_contract(self):
        runner = DIFF_NAV / "scripts" / "run_task_tests.py"
        text = runner.read_text(encoding="utf-8")
        self.assertIn('DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / "config" / "task_tests.yaml"', text)
        for option in (
            "--config",
            "--move-base",
            "--pose-topic",
            "--initial-pose-topic",
            "--clear-costmaps-service",
            "--server-timeout",
        ):
            self.assertIn(option, text)


if __name__ == "__main__":
    unittest.main()
