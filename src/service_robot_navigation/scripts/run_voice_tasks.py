#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import re
import sys
from pathlib import Path


def find_default_config():
    """Find task config from a source checkout or an installed ROS package."""
    source_config = Path(__file__).resolve().parents[1] / "config" / "task_tests.yaml"
    if source_config.is_file():
        return source_config

    try:
        import rospkg

        package_path = Path(rospkg.RosPack().get_path("service_robot_navigation"))
        return package_path / "config" / "task_tests.yaml"
    except Exception:
        return source_config


DEFAULT_CONFIG = find_default_config()
TASK_NUMBER_PATTERN = re.compile(r"^task_(\d+)(?:_|$)")
TASK_ID_PATTERN = re.compile(r"^(?:task[_ -]?|任务\s*)?([1-5])$")

DEFAULT_SPEECH_DESCRIPTIONS = {
    "task1": "请去取药台取药并送至病房A",
    "task2": "请去取药台取药并送至病房B",
    "task3": "请在长柜台服务区依次服务三个人",
    "task4": "请去横向错位通道进行测试",
    "task5": "请通过狭窄区域到停靠点",
}


def normalize_task_id(value):
    """Normalize supported speech-service task identifiers to task1-task5."""
    if value is None:
        return None

    text = str(value).strip().lower()
    match = TASK_ID_PATTERN.fullmatch(text)
    if match is None:
        return None
    return "task{}".format(match.group(1))


def build_task_index(tasks):
    """Build a validated task1-task5 index from task_tests.yaml entries."""
    index = {}
    for task in tasks:
        name = str(task.get("name", ""))
        match = TASK_NUMBER_PATTERN.match(name)
        if match is None:
            raise ValueError("Task name must start with task_<number>: {}".format(name))

        task_id = "task{}".format(match.group(1))
        if task_id not in DEFAULT_SPEECH_DESCRIPTIONS:
            raise ValueError("Unsupported task number in {}".format(name))
        if task_id in index:
            raise ValueError("Duplicate task number: {}".format(task_id))
        index[task_id] = task

    expected = set(DEFAULT_SPEECH_DESCRIPTIONS)
    if set(index) != expected:
        missing = sorted(expected - set(index))
        extra = sorted(set(index) - expected)
        raise ValueError("Task index must contain task1-task5; missing={}, extra={}".format(missing, extra))
    return index


def build_status_text(task_id, task, status):
    """Build the Chinese TTS text for a task lifecycle status."""
    number = task_id.replace("task", "", 1)
    if status == "start":
        description = task.get("speech_description") or DEFAULT_SPEECH_DESCRIPTIONS[task_id]
        return "准备执行任务{}：{}。".format(number, description.rstrip("。"))
    if status == "success":
        return "任务{}已完成。".format(number)
    if status == "failure":
        return "任务{}执行失败，请检查导航状态。".format(number)
    raise ValueError("Unsupported task status: {}".format(status))


class VoiceTaskController:
    """Connect one keyword command to one existing navigation task."""

    def __init__(
        self,
        tasks,
        task_runner,
        keyword_client,
        tts_client,
        keyword_request_factory,
        tts_request_factory,
        rospy_module,
        record_seconds=5.0,
    ):
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
            self.speak("语音服务暂不可用，请稍后重试。")
            return None

        task_id = normalize_task_id(response.keyword) if response.success else None
        if task_id is None or task_id not in self.tasks:
            self.rospy.logwarn(
                "No valid task from keyword response: keyword=%s error=%s",
                getattr(response, "keyword", ""),
                getattr(response, "error_message", ""),
            )
            self.speak("未识别到有效任务，请重新说出任务。")
            return None

        task = self.tasks[task_id]
        self.speak(build_status_text(task_id, task, "start"))
        result = self.task_runner.execute_task(task)
        result_status = "success" if result["success"] else "failure"
        self.speak(build_status_text(task_id, task, result_status))
        return result


def parse_args(argv):
    """Parse CLI arguments; ROS setup is intentionally deferred to main."""
    parser = argparse.ArgumentParser(description="Run voice-selected service robot tasks.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="Path to task_tests.yaml")
    parser.add_argument("--move-base", default="/move_base", help="move_base action name")
    parser.add_argument("--pose-topic", default="/amcl_pose", help="AMCL pose topic")
    parser.add_argument("--initial-pose-topic", default="/initialpose", help="AMCL initial pose topic")
    parser.add_argument(
        "--clear-costmaps-service",
        default="/move_base/clear_costmaps",
        help="Service used before unsatisfied waypoints; use '' to disable",
    )
    parser.add_argument("--server-timeout", type=float, default=30.0, help="Seconds to wait for move_base")
    parser.add_argument("--keyword-service", default="/extract_keyword", help="Keyword extraction service")
    parser.add_argument("--tts-service", default="/synthesize_speech", help="TTS service")
    parser.add_argument("--record-seconds", type=float, default=5.0, help="Seconds recorded per command")
    parser.add_argument(
        "--keyword-service-timeout",
        type=float,
        default=10.0,
        help="Seconds to wait for the keyword service",
    )
    parser.add_argument(
        "--tts-service-timeout",
        type=float,
        default=10.0,
        help="Seconds to wait for the TTS service",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Exit after the first valid task finishes",
    )
    return parser.parse_args(argv)


def main(argv=None):
    """Start navigation once, then process voice-selected tasks until shutdown."""
    args = parse_args(argv or sys.argv[1:])

    import rospy
    from cloud_tts.srv import SynthesizeSpeech, SynthesizeSpeechRequest
    from voice_keyword_extractor.srv import ExtractKeyword, ExtractKeywordRequest

    script_directory = str(Path(__file__).resolve().parent)
    if script_directory not in sys.path:
        sys.path.insert(0, script_directory)
    from run_task_tests import TaskTestRunner, load_task_config

    rospy.init_node("service_robot_voice_task_runner")

    try:
        config = load_task_config(args.config)
        task_index = build_task_index(config["tasks"])
        navigation_runner = TaskTestRunner(
            config,
            args.move_base,
            args.pose_topic,
            args.initial_pose_topic,
            args.clear_costmaps_service,
        )
        navigation_runner.wait_for_server(args.server_timeout)
        navigation_runner.initialize_amcl_if_requested()

        rospy.loginfo("Waiting for keyword service: %s", args.keyword_service)
        rospy.wait_for_service(args.keyword_service, timeout=args.keyword_service_timeout)

        try:
            rospy.wait_for_service(args.tts_service, timeout=args.tts_service_timeout)
        except rospy.ROSException as error:
            rospy.logwarn("TTS service is not ready; navigation will continue: %s", error)

        keyword_client = rospy.ServiceProxy(args.keyword_service, ExtractKeyword)
        tts_client = rospy.ServiceProxy(args.tts_service, SynthesizeSpeech)
        controller = VoiceTaskController(
            tasks=task_index,
            task_runner=navigation_runner,
            keyword_client=keyword_client,
            tts_client=tts_client,
            keyword_request_factory=ExtractKeywordRequest,
            tts_request_factory=SynthesizeSpeechRequest,
            rospy_module=rospy,
            record_seconds=args.record_seconds,
        )

        rospy.loginfo("Voice task runner is ready; waiting for task commands.")
        while not rospy.is_shutdown():
            result = controller.execute_once()
            if args.once and result is not None:
                return 0
        return 0
    except (RuntimeError, rospy.ROSException) as error:
        rospy.logfatal("Voice task runner stopped: %s", error)
        return 1
    except Exception as error:
        rospy.logexception("Voice task runner stopped unexpectedly: %s", error)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
