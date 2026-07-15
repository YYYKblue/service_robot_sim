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
            self.module.build_task_index(
                [{"name": "task_1_first"}, {"name": "task_1_again"}]
            )

        with self.assertRaises(ValueError):
            self.module.build_task_index([{"name": "task_1_only"}])

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

    def test_default_config_points_to_existing_task_config_in_source_checkout(self):
        self.assertTrue(self.module.DEFAULT_CONFIG.is_file())


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
            "task1": {
                "name": "task_1_demo",
                "description": "请去取药台取药并送至病房A",
            },
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
        controller = self.make_controller({"success": True})
        result = controller.execute_once()
        self.assertTrue(result["success"])
        self.assertEqual(len(controller.task_runner.executed), 1)
        self.assertEqual(controller.task_runner.executed[0]["name"], "task_1_demo")
        self.assertTrue(self.keyword_requests[0].start_recording)
        self.assertEqual(self.keyword_requests[0].record_seconds, 4.0)
        self.assertTrue(self.tts_requests[0].play_audio)
        self.assertIn("准备执行任务1", self.tts_requests[0].text)
        self.assertIn("任务1已完成", self.tts_requests[1].text)

    def test_unknown_command_does_not_execute_navigation(self):
        def keyword_client(request):
            return FakeKeywordResponse(keyword="medicine")

        controller = self.make_controller({"success": True})
        controller.keyword_client = keyword_client
        self.assertIsNone(controller.execute_once())
        self.assertEqual(controller.task_runner.executed, [])

    def test_keyword_failure_does_not_execute_navigation(self):
        def keyword_client(request):
            return FakeKeywordResponse(success=False, error_message="recognizer failed")

        controller = self.make_controller({"success": True})
        controller.keyword_client = keyword_client
        self.assertIsNone(controller.execute_once())
        self.assertEqual(controller.task_runner.executed, [])

    def test_tts_failure_does_not_change_navigation_result(self):
        def tts_client(request):
            return FakeTtsResponse(success=False)

        controller = self.make_controller({"success": True})
        controller.tts_client = tts_client
        result = controller.execute_once()
        self.assertTrue(result["success"])
        self.assertEqual(len(controller.task_runner.executed), 1)


class VoiceTaskPackagingTest(unittest.TestCase):
    def test_navigation_package_installs_voice_runner_and_declares_voice_dependencies(self):
        cmake = (
            ROOT / "src" / "service_robot_navigation" / "CMakeLists.txt"
        ).read_text(encoding="utf-8")
        package_xml = (
            ROOT / "src" / "service_robot_navigation" / "package.xml"
        ).read_text(encoding="utf-8")
        self.assertIn("scripts/run_voice_tasks.py", cmake)
        self.assertIn("<exec_depend>voice_keyword_extractor</exec_depend>", package_xml)
        self.assertIn("<exec_depend>cloud_tts</exec_depend>", package_xml)

    def test_voice_runner_exposes_required_cli_options(self):
        module = load_module()
        args = module.parse_args(
            [
                "--keyword-service",
                "/custom/keyword",
                "--tts-service",
                "/custom/tts",
                "--record-seconds",
                "3",
                "--once",
            ]
        )
        self.assertEqual(args.keyword_service, "/custom/keyword")
        self.assertEqual(args.tts_service, "/custom/tts")
        self.assertEqual(args.record_seconds, 3.0)
        self.assertTrue(args.once)


class VoiceProviderContractTest(unittest.TestCase):
    def test_keyword_provider_matches_task_service_contract(self):
        node = (
            ROOT
            / "src"
            / "voice_keyword_extractor"
            / "scripts"
            / "keyword_service_node.py"
        ).read_text(encoding="utf-8")
        vocabulary = (
            ROOT
            / "src"
            / "voice_keyword_extractor"
            / "config"
            / "vocabulary.yaml"
        ).read_text(encoding="utf-8")
        cmake = (
            ROOT / "src" / "voice_keyword_extractor" / "CMakeLists.txt"
        ).read_text(encoding="utf-8")

        self.assertIn('rospy.Service(\n        "/extract_keyword"', node)
        for task_id in ("task1", "task2", "task3", "task4", "task5"):
            self.assertIn(task_id, node)
            self.assertIn("- {}".format(task_id), vocabulary)
        self.assertIn("scripts/keyword_service_node.py", cmake)

    def test_tts_provider_installs_launch_target(self):
        cmake = (ROOT / "src" / "cloud_tts" / "CMakeLists.txt").read_text(
            encoding="utf-8"
        )
        self.assertIn("scripts/tts_service_node.py", cmake)
        self.assertIn("install(DIRECTORY config launch", cmake)

        voice_cmake = (
            ROOT / "src" / "voice_keyword_extractor" / "CMakeLists.txt"
        ).read_text(encoding="utf-8")
        self.assertIn("install(DIRECTORY config launch", voice_cmake)

    def test_tts_provider_resolves_installed_config_and_declares_runtime_files(self):
        node = (ROOT / "src" / "cloud_tts" / "scripts" / "tts_service_node.py").read_text(
            encoding="utf-8"
        )
        package_xml = (ROOT / "src" / "cloud_tts" / "package.xml").read_text(
            encoding="utf-8"
        )
        self.assertIn("rospkg.RosPack", node)
        self.assertIn("<exec_depend>rospkg</exec_depend>", package_xml)
        self.assertIn("<exec_depend>python3-requests</exec_depend>", package_xml)
        self.assertIn("<exec_depend>python3-yaml</exec_depend>", package_xml)
        self.assertIn("dashscope", (ROOT / "src" / "cloud_tts" / "requirements.txt").read_text(encoding="utf-8"))
        self.assertIn("openai", (ROOT / "src" / "voice_keyword_extractor" / "requirements.txt").read_text(encoding="utf-8"))

    def test_navigation_declares_rospkg_for_installed_config_lookup(self):
        package_xml = (
            ROOT / "src" / "service_robot_navigation" / "package.xml"
        ).read_text(encoding="utf-8")
        self.assertIn("<exec_depend>rospkg</exec_depend>", package_xml)


if __name__ == "__main__":
    unittest.main()
