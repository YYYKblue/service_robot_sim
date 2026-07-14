from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

import yaml


ROOT = Path(__file__).resolve().parents[1]
URDF = ROOT / "src" / "sweeper_robot_omni4_base_ros" / "urdf" / "sweeper_robot_omni4_base.urdf"
NAV_CONFIG = ROOT / "src" / "service_robot_navigation" / "config"


class RobotOptimizationConfigTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.robot = ET.parse(URDF).getroot()

    def test_topic_interfaces_are_not_visible_robot_hardware(self):
        link_names = {link.attrib["name"] for link in self.robot.findall("link")}

        self.assertNotIn("odometry_link", link_names)
        self.assertNotIn("cmd_vel_interface_link", link_names)

        gazebo_references = {
            gazebo.attrib.get("reference")
            for gazebo in self.robot.findall("gazebo")
            if gazebo.attrib.get("reference")
        }
        self.assertNotIn("odometry_link", gazebo_references)
        self.assertNotIn("cmd_vel_interface_link", gazebo_references)

        planar_move = self.robot.find("./gazebo/plugin[@filename='libgazebo_ros_planar_move.so']")
        self.assertIsNotNone(planar_move)
        self.assertEqual("cmd_vel", planar_move.findtext("commandTopic"))
        self.assertEqual("odom", planar_move.findtext("odometryTopic"))

    def test_lidar_is_centered_on_base_link(self):
        lidar_joint = self.robot.find("./joint[@name='lidar_joint']/origin")

        self.assertIsNotNone(lidar_joint)
        self.assertEqual("0 0 0.1610", lidar_joint.attrib["xyz"])

    def test_front_x_marker_is_obvious_visual_only_geometry(self):
        base_link = self.robot.find("./link[@name='base_link']")
        visual_names = {visual.attrib.get("name") for visual in base_link.findall("visual")}
        collision_names = {collision.attrib.get("name") for collision in base_link.findall("collision")}

        material = self.robot.find("./material[@name='orange_marker']/color")
        self.assertIsNotNone(material)
        self.assertEqual("1.0 0.5 0.0 1.0", material.attrib["rgba"])

        self.assertIn("front_x_arrow_marker", visual_names)
        self.assertIn("front_x_arrow_tip_marker", visual_names)
        self.assertNotIn("front_x_arrow_marker_collision", collision_names)
        self.assertNotIn("front_x_arrow_tip_marker_collision", collision_names)

        marker_origin = base_link.find("./visual[@name='front_x_arrow_marker']/origin")
        marker_geometry = base_link.find("./visual[@name='front_x_arrow_marker']/geometry/box")
        tip_material = base_link.find("./visual[@name='front_x_arrow_tip_marker']/material")

        self.assertEqual("0.225 0 0.176", marker_origin.attrib["xyz"])
        self.assertEqual("0.120 0.045 0.018", marker_geometry.attrib["size"])
        self.assertEqual("orange_marker", tip_material.attrib["name"])

    def test_gazebo_laser_visualization_is_disabled(self):
        visualize = self.robot.find("./gazebo[@reference='lidar_link']/sensor/visualize")

        self.assertIsNotNone(visualize)
        self.assertEqual("false", visualize.text.strip())

    def test_navigation_visualization_and_publish_load_is_reduced(self):
        with (NAV_CONFIG / "dwa_local_planner_params.yaml").open(encoding="utf-8") as fh:
            dwa = yaml.safe_load(fh)
        with (NAV_CONFIG / "local_costmap_params.yaml").open(encoding="utf-8") as fh:
            local_costmap = yaml.safe_load(fh)
        with (NAV_CONFIG / "global_costmap_params.yaml").open(encoding="utf-8") as fh:
            global_costmap = yaml.safe_load(fh)
        with (NAV_CONFIG / "amcl_params.yaml").open(encoding="utf-8") as fh:
            amcl = yaml.safe_load(fh)
        with (NAV_CONFIG / "gmapping_params.yaml").open(encoding="utf-8") as fh:
            gmapping = yaml.safe_load(fh)
        with (NAV_CONFIG / "costmap_common_params.yaml").open(encoding="utf-8") as fh:
            costmap_common = yaml.safe_load(fh)
        with (NAV_CONFIG / "global_planner_params.yaml").open(encoding="utf-8") as fh:
            global_planner = yaml.safe_load(fh)

        self.assertFalse(dwa["DWAPlannerROS"]["publish_traj_pc"])
        self.assertFalse(dwa["DWAPlannerROS"]["publish_cost_grid_pc"])
        self.assertEqual(0.15, dwa["DWAPlannerROS"]["xy_goal_tolerance"])
        self.assertEqual(0.20, dwa["DWAPlannerROS"]["yaw_goal_tolerance"])
        self.assertEqual(0.05, dwa["DWAPlannerROS"]["min_vel_theta"])

        self.assertFalse(local_costmap["always_send_full_costmap"])
        self.assertEqual(5.0, local_costmap["update_frequency"])
        self.assertEqual(2.0, local_costmap["publish_frequency"])

        self.assertFalse(global_costmap["always_send_full_costmap"])
        self.assertEqual(2.0, global_costmap["update_frequency"])
        self.assertEqual(1.0, global_costmap["publish_frequency"])

        self.assertLessEqual(amcl["max_particles"], 1000)
        self.assertLessEqual(gmapping["particles"], 30)
        self.assertEqual(0.25, costmap_common["robot_radius"])
        self.assertEqual(0.0, costmap_common["footprint_padding"])
        self.assertEqual(0.26, costmap_common["inflation_layer"]["inflation_radius"])
        self.assertEqual(12.0, costmap_common["inflation_layer"]["cost_scaling_factor"])

        self.assertEqual(0.20, global_planner["GlobalPlanner"]["default_tolerance"])
        self.assertTrue(global_planner["GlobalPlanner"]["use_grid_path"])


if __name__ == "__main__":
    unittest.main()
