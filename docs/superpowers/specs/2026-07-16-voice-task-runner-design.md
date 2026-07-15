# 语音任务执行器设计

## 目标

在现有 `run_task_tests.py` 五项位姿任务已经可用的基础上，新增一个由语音命令触发的 ROS Noetic Python 脚本。脚本通过 `voice_keyword_extractor/ExtractKeyword.srv` 获取 `task1`～`task5`，执行对应 YAML 任务，并通过 `cloud_tts/SynthesizeSpeech.srv` 在任务关键阶段播报状态。

## 当前项目边界

- `run_task_tests.py` 继续负责 move_base action、AMCL 初始化、waypoint 顺序执行、clear-costmaps、超时处理和失败诊断。
- 新脚本只负责语音交互、任务选择和状态播报，不复制导航控制逻辑。
- 语音识别节点需要在 `/extract_keyword` 提供 `ExtractKeyword` 服务；本次实现不猜测具体 ASR 厂商或录音算法。
- `cloud_tts` 需要在 `/synthesize_speech` 提供 `SynthesizeSpeech` 服务；TTS 具体云端合成由现有包负责。
- 不修改五项任务的 waypoint、导航参数或 world 几何。

## 方案

新增 `src/service_robot_navigation/scripts/run_voice_tasks.py`，在同一 ROS 包内导入并复用 `run_task_tests.py` 的 `load_task_config`、`TaskTestRunner` 和任务执行结果结构。

脚本启动后只初始化一次 ROS、move_base 和 AMCL，然后进入命令循环：

```text
等待 move_base -> 初始化 AMCL -> 等待语音识别服务
       -> 录音并识别 -> 规范化 task id -> 播报准备信息
       -> 执行一个 YAML task -> 播报成功/失败 -> 等待下一条命令
```

任务选择使用 YAML 的任务列表建立索引，并将列表顺序映射为 `task1`～`task5`。同时接受常见的等价结果 `task_1`、`任务1` 和 `1`，统一转换为规范 task id。未知结果、空结果和识别服务失败只播报提示，不调用 `execute_task`。

## ROS 接口

### 语音识别

默认服务名为 `/extract_keyword`，可通过参数覆盖。每次命令请求发送：

```text
start_recording = true
record_seconds = 5.0
```

使用响应中的 `success`、`keyword`、`transcript` 和 `error_message`。优先解析 `keyword`；`transcript` 只用于日志和错误提示，不在控制脚本中实现自由文本语义模型。

### 语音合成

默认服务名为 `/synthesize_speech`，可通过参数覆盖。每次播报发送：

```text
text = 播报文本
play_audio = true
```

TTS 服务不可用或响应失败时记录 warning 并继续主流程。导航任务已经开始后，TTS 故障不取消 move_base 目标。

## 播报内容

任务开始前使用任务描述生成固定播报，例如：

```text
准备执行任务1：请去取药台取药并送至病房A。
```

任务成功时播报 `任务1已完成。`；任务失败时播报 `任务1执行失败，请检查导航状态。`；无法识别时播报 `未识别到有效任务，请重新说出任务。`。语音服务错误播报 `语音服务暂不可用，请稍后重试。`，并保留详细 ROS 日志。

## 命令行参数

新脚本沿用原 runner 的导航参数，并增加：

- `--keyword-service`：默认 `/extract_keyword`。
- `--tts-service`：默认 `/synthesize_speech`。
- `--record-seconds`：默认 `5.0`。
- `--keyword-service-timeout`：等待识别服务的秒数。
- `--tts-service-timeout`：等待 TTS 服务的秒数。
- `--once`：识别并执行一条有效任务后退出，便于测试；默认持续等待。

## 错误处理

- `move_base` 不可用或 AMCL 初始化失败：启动失败并返回非零状态。
- 识别服务不可用、识别失败、keyword 为空或任务编号未知：不执行任务，继续等待下一次语音命令。
- TTS 服务不可用或调用失败：记录 warning，不阻塞语音识别循环；任务执行结果仍以导航结果为准。
- `execute_task` 返回失败：播报失败并继续等待下一条命令，不自动重试，避免重复执行具有副作用的任务。
- ROS shutdown 或 `Ctrl+C`：正常结束循环，不发送新的任务目标。

## 测试与验收

先添加 Windows 可运行的纯 Python 单元测试，再实现生产代码，覆盖：

1. `task1`、`task_1`、`任务1` 和 `1` 规范化为同一个任务编号。
2. `task1`～`task5` 映射到 `task_tests.yaml` 中正确的五个任务。
3. 未知 keyword 返回空选择，且不会误选任务。
4. 五个任务的开始、成功和失败播报文本稳定。
5. `--once` 和默认持续循环的控制语义可通过 fake service/runner 验证。
6. 现有 `tests/` 静态测试和新增测试全部通过。

在 Ubuntu ROS Noetic 环境中，验收命令为：

```bash
source /opt/ros/noetic/setup.bash
cd ~/service_robot
catkin_make
source devel/setup.bash
rosrun service_robot_navigation run_voice_tasks.py --help
```

真实语音闭环还需要先启动能够提供 `/extract_keyword` 的识别节点和 `/synthesize_speech` 的 TTS 节点，再启动 `sim_navigation.launch`，最后运行 `run_voice_tasks.py`。Windows 静态测试不能替代该 ROS/Gazebo/音频设备验证。

## 非目标

- 不在本次脚本中实现 ASR 录音、网络识别或语义模型。
- 不修改现有 `voice_keyword_extractor` 服务定义。
- 不把语音脚本改造成新的导航器或任务规划器。
- 不在任务失败后自动切换或连续执行其它任务。
