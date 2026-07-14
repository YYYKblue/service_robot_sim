#!/usr/bin/env python3
import argparse
import math
from pathlib import Path
import sys
import time

import yaml


DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / "config" / "task_tests.yaml"


def normalize_angle(angle):
    return math.atan2(math.sin(angle), math.cos(angle))


def yaw_to_quaternion(yaw):
    half_yaw = yaw * 0.5
    return {
        "x": 0.0,
        "y": 0.0,
        "z": math.sin(half_yaw),
        "w": math.cos(half_yaw),
    }


def quaternion_to_yaw(quaternion):
    x = quaternion.x
    y = quaternion.y
    z = quaternion.z
    w = quaternion.w
    siny_cosp = 2.0 * (w * z + x * y)
    cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
    return math.atan2(siny_cosp, cosy_cosp)


def compute_pose_error(current_pose, target_pose):
    dx = current_pose[0] - target_pose[0]
    dy = current_pose[1] - target_pose[1]
    return {
        "xy": math.hypot(dx, dy),
        "yaw": abs(normalize_angle(current_pose[2] - target_pose[2])),
    }


def load_task_config(path):
    config_path = Path(path)
    with config_path.open(encoding="utf-8") as fh:
        config = yaml.safe_load(fh)
    validate_task_config(config, config_path)
    return config


def validate_task_config(config, config_path):
    if not isinstance(config, dict):
        raise ValueError("{} must contain a YAML mapping".format(config_path))
    if "tasks" not in config or not isinstance(config["tasks"], list):
        raise ValueError("{} must define a tasks list".format(config_path))
    if not config["tasks"]:
        raise ValueError("{} must define at least one task".format(config_path))

    for task in config["tasks"]:
        if "name" not in task:
            raise ValueError("Every task must have a name")
        waypoints = task.get("waypoints")
        if not isinstance(waypoints, list) or not waypoints:
            raise ValueError("Task {} must define at least one waypoint".format(task["name"]))
        for waypoint in waypoints:
            if "name" not in waypoint:
                raise ValueError("Task {} has a waypoint without a name".format(task["name"]))
            pose = waypoint.get("pose")
            if not isinstance(pose, list) or len(pose) != 3:
                raise ValueError("Waypoint {} must use pose [x, y, yaw]".format(waypoint["name"]))


def get_setting(config, waypoint, key):
    if key in waypoint:
        return waypoint[key]
    return config.get("defaults", {}).get(key)


def make_goal(move_base_goal_cls, waypoint, frame_id):
    goal = move_base_goal_cls()
    goal.target_pose.header.frame_id = frame_id

    x, y, yaw = waypoint["pose"]
    goal.target_pose.pose.position.x = float(x)
    goal.target_pose.pose.position.y = float(y)
    goal.target_pose.pose.position.z = 0.0

    quat = yaw_to_quaternion(float(yaw))
    goal.target_pose.pose.orientation.x = quat["x"]
    goal.target_pose.pose.orientation.y = quat["y"]
    goal.target_pose.pose.orientation.z = quat["z"]
    goal.target_pose.pose.orientation.w = quat["w"]
    return goal


def pose_tuple_from_amcl(msg):
    position = msg.pose.pose.position
    orientation = msg.pose.pose.orientation
    return (position.x, position.y, quaternion_to_yaw(orientation))


class TaskTestRunner:
    def __init__(self, config, move_base_name="/move_base", pose_topic="/amcl_pose"):
        import actionlib
        import rospy
        from actionlib_msgs.msg import GoalStatus
        from geometry_msgs.msg import PoseWithCovarianceStamped
        from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal

        self.actionlib = actionlib
        self.goal_status_cls = GoalStatus
        self.rospy = rospy
        self.pose_msg_cls = PoseWithCovarianceStamped
        self.goal_cls = MoveBaseGoal
        self.client = actionlib.SimpleActionClient(move_base_name, MoveBaseAction)
        self.config = config
        self.pose_topic = pose_topic

    def wait_for_server(self, timeout):
        self.rospy.loginfo("Waiting for move_base action server...")
        if not self.client.wait_for_server(self.rospy.Duration(timeout)):
            raise RuntimeError("move_base action server is not available")

    def current_pose(self):
        msg = self.rospy.wait_for_message(
            self.pose_topic,
            self.pose_msg_cls,
            timeout=5.0,
        )
        return pose_tuple_from_amcl(msg)

    def execute(self):
        results = []
        for task in self.config["tasks"]:
            task_result = self.execute_task(task)
            results.append(task_result)
            if not task_result["success"]:
                break
        return results

    def execute_task(self, task):
        self.rospy.loginfo("Starting task: %s", task["name"])
        task_start = time.time()
        waypoint_results = []

        for waypoint in task["waypoints"]:
            result = self.execute_waypoint(waypoint)
            waypoint_results.append(result)
            if not result["success"]:
                self.rospy.logerr(
                    "Task %s failed at waypoint %s: %s",
                    task["name"],
                    waypoint["name"],
                    result["reason"],
                )
                return {
                    "name": task["name"],
                    "success": False,
                    "duration": time.time() - task_start,
                    "waypoints": waypoint_results,
                }

        return {
            "name": task["name"],
            "success": True,
            "duration": time.time() - task_start,
            "waypoints": waypoint_results,
        }

    def execute_waypoint(self, waypoint):
        frame_id = get_setting(self.config, waypoint, "frame_id") or "map"
        timeout = float(get_setting(self.config, waypoint, "timeout") or 90.0)
        hold_time = float(get_setting(self.config, waypoint, "hold_time") or 0.0)
        xy_tolerance = float(get_setting(self.config, waypoint, "xy_tolerance") or 0.25)
        yaw_tolerance = float(get_setting(self.config, waypoint, "yaw_tolerance") or 0.25)

        self.rospy.loginfo("Sending waypoint: %s -> %s", waypoint["name"], waypoint["pose"])
        goal = make_goal(self.goal_cls, waypoint, frame_id)
        goal.target_pose.header.stamp = self.rospy.Time.now()

        start = time.time()
        self.client.send_goal(goal)
        finished = self.client.wait_for_result(self.rospy.Duration(timeout))
        if not finished:
            self.client.cancel_goal()
            return {
                "name": waypoint["name"],
                "success": False,
                "duration": time.time() - start,
                "reason": "timeout after {:.1f}s".format(timeout),
            }

        state = self.client.get_state()
        if state != self.goal_status_cls.SUCCEEDED:
            return {
                "name": waypoint["name"],
                "success": False,
                "duration": time.time() - start,
                "reason": "move_base returned state {}".format(state),
            }

        current_pose = self.current_pose()
        error = compute_pose_error(current_pose, waypoint["pose"])
        if error["xy"] > xy_tolerance or error["yaw"] > yaw_tolerance:
            return {
                "name": waypoint["name"],
                "success": False,
                "duration": time.time() - start,
                "reason": "pose error xy={:.3f}, yaw={:.3f}".format(error["xy"], error["yaw"]),
                "error": error,
            }

        if hold_time > 0:
            self.rospy.sleep(hold_time)

        return {
            "name": waypoint["name"],
            "success": True,
            "duration": time.time() - start,
            "error": error,
        }


def print_summary(results):
    passed = sum(1 for result in results if result["success"])
    print("")
    print("Task test summary: {}/{} tasks passed".format(passed, len(results)))
    for result in results:
        status = "PASS" if result["success"] else "FAIL"
        print("- {} {} ({:.1f}s)".format(status, result["name"], result["duration"]))
        for waypoint in result["waypoints"]:
            waypoint_status = "PASS" if waypoint["success"] else "FAIL"
            detail = ""
            if "error" in waypoint:
                detail = " xy={xy:.3f} yaw={yaw:.3f}".format(**waypoint["error"])
            if not waypoint["success"]:
                detail += " reason={}".format(waypoint["reason"])
            print("  - {} {}{}".format(waypoint_status, waypoint["name"], detail))


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Run ordered service robot navigation task tests.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="Path to task_tests.yaml")
    parser.add_argument("--move-base", default="/move_base", help="move_base action name")
    parser.add_argument("--pose-topic", default="/amcl_pose", help="Pose topic used for final error checks")
    parser.add_argument("--server-timeout", type=float, default=30.0, help="Seconds to wait for move_base")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    config = load_task_config(args.config)

    import rospy

    rospy.init_node("service_robot_task_test_runner")
    runner = TaskTestRunner(config, args.move_base, args.pose_topic)
    runner.wait_for_server(args.server_timeout)
    results = runner.execute()
    print_summary(results)

    if len(results) != len(config["tasks"]) or not all(result["success"] for result in results):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
