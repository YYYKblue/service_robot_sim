# Service Robot ROS/Gazebo Project Handoff

本项目运行于 Ubuntu 20.04、ROS Noetic 与 Gazebo，包含四全向轮机器人模型、室内 world、地图生成、定位导航、顺序任务测试、语音命令识别和云端语音合成。截至 2026-07-16，`main` 的位姿型方案已在 Ubuntu ROS/Gazebo 环境完成五项任务的连续顺序测试，并完成语音模块接入验证。当前结果为：

```text
Task test summary: 5/5 tasks passed
Voice command tasks: task1-task5 user-confirmed passed
```

所有 waypoint 都使用完整的 `[x, y, yaw]` 位姿。语音功能通过 `/extract_keyword` 将自然语言任务指令映射为 `task1`～`task5`，再由 `/synthesize_speech` 播报交互提示、任务开始和任务结果。位姿型 waypoint 与语音命令触发流程均已完成测试，本阶段项目完成。

## 1. 工作区结构

```text
service_robot/
├── README.md
├── docs/
│   └── ubuntu_voice_config_self_check.md
├── scripts/
│   └── world_to_map.py
├── src/
│   ├── cloud_tts/
│   │   ├── launch/
│   │   │   └── cloud_tts.launch
│   │   ├── scripts/
│   │   │   └── tts_service_node.py
│   │   └── srv/
│   │       └── SynthesizeSpeech.srv
│   ├── my_world/
│   │   ├── worlds/
│   │   │   └── indoor.world
│   │   └── 平面图.png
│   ├── service_robot_sim/
│   │   └── launch/
│   │       └── omni4_indoor.launch
│   ├── service_robot_navigation/
│   │   ├── launch/
│   │   │   ├── sim_mapping.launch
│   │   │   └── sim_navigation.launch
│   │   ├── config/
│   │   │   ├── costmap_common_params.yaml
│   │   │   ├── global_planner_params.yaml
│   │   │   ├── dwa_local_planner_params.yaml
│   │   │   └── task_tests.yaml
│   │   ├── maps/
│   │   │   ├── indoor.pgm
│   │   │   └── indoor.yaml
│   │   └── scripts/
│   │       ├── run_task_tests.py
│   │       ├── run_voice_tasks.py
│   │       └── save_map.sh
│   ├── service_robot_diff_navigation/
│   │   ├── launch/
│   │   │   ├── diff_sim.launch
│   │   │   ├── navigation.launch
│   │   │   └── diff_navigation.launch
│   │   ├── config/              # 与全向轮一致，仅保留差速必需参数差异
│   │   ├── maps/                # indoor 地图的严格副本
│   │   └── scripts/run_task_tests.py
│   ├── voice_keyword_extractor/
│   │   ├── launch/
│   │   │   └── voice_keyword.launch
│   │   ├── scripts/
│   │   │   └── keyword_service_node.py
│   │   └── srv/
│   │       └── ExtractKeyword.srv
│   ├── sweeper_robot_omni4_base_ros/
│       ├── urdf/
│       │   └── sweeper_robot_omni4_base.urdf
│       └── meshes/
│   └── sweeper_robot_diff2_submit_ros/
│       └── urdf/sweeper_robot_diff2_submit.urdf
└── tests/
    ├── test_robot_optimization_config.py
    ├── test_task_test_runner_config.py
    └── test_world_geometry.py
```

主要职责如下：

- `docs/ubuntu_voice_config_self_check.md`：Ubuntu 语音功能配置自查手册，覆盖 API Key、音频设备、ROS 服务、ASR 和 TTS 排障。
- `scripts/world_to_map.py`：从 Gazebo world 几何生成导航地图。
- `src/cloud_tts/`：云端语音合成功能包，提供 `/synthesize_speech` 服务。
- `src/my_world/worlds/indoor.world`：当前室内仿真场景；`src/my_world/平面图.png` 是场景平面图参考。
- `src/service_robot_sim/launch/omni4_indoor.launch`：四全向轮机器人室内仿真入口。
- `src/service_robot_navigation/launch/sim_mapping.launch` 与 `sim_navigation.launch`：建图和导航启动入口。
- `src/service_robot_navigation/config/task_tests.yaml`：五项顺序任务及其完整位姿 waypoint。
- `src/service_robot_navigation/maps/`：生成后的地图文件。
- `src/service_robot_navigation/scripts/run_task_tests.py`：顺序任务测试 runner；`run_voice_tasks.py`：语音命令任务 runner；`save_map.sh`：地图保存辅助脚本。
- `src/service_robot_diff_navigation/`：差速轮对比导航包；复用相同地图、任务点和主要导航参数，只关闭横向 DWA 速度并使用差速 AMCL 模型。
- `src/voice_keyword_extractor/`：语音录音、ASR 转写和任务关键词提取功能包，提供 `/extract_keyword` 服务。
- `src/sweeper_robot_omni4_base_ros/urdf/sweeper_robot_omni4_base.urdf` 与 `src/sweeper_robot_omni4_base_ros/meshes/`：机器人模型和网格资源。
- `src/sweeper_robot_diff2_submit_ros/urdf/sweeper_robot_diff2_submit.urdf`：外观与全向轮底盘统一、运动学保持差速的模型。
- `tests/`：覆盖两套模型、导航配置、任务 runner 和 world 几何的 Windows 本地静态回归。

## 2. Ubuntu 构建与运行

项目在 Ubuntu 20.04 + ROS Noetic 环境中构建：

```bash
source /opt/ros/noetic/setup.bash
cd ~/service_robot
rosdep install --from-paths src --ignore-src -r -y
catkin_make
source devel/setup.bash
```

终端 1 启动 Gazebo、定位与导航：

```bash
cd ~/service_robot
source devel/setup.bash
roslaunch service_robot_navigation sim_navigation.launch
```

终端 2 运行五项顺序任务：

```bash
cd ~/service_robot
source devel/setup.bash
python3 src/service_robot_navigation/scripts/run_task_tests.py
```

### 2.1 语音命令任务执行

语音任务脚本复用上述 waypoint runner，但任务不再按 1～5 顺序执行，而是由 `voice_keyword_extractor` 返回的 `task1`～`task5` 触发。当前语音模块已成功接入，五个任务均可通过语音命令触发对应导航流程。默认接口为：

```text
/extract_keyword       voice_keyword_extractor/ExtractKeyword
/synthesize_speech     cloud_tts/SynthesizeSpeech
```

语音语义映射如下。用户不需要一字不差复述，只要语义明确表达目标，关键词服务会把 ASR 文本归一化为固定任务编号；表达不清或与五项任务无关时返回 `unknown`。

| 语音意图 | 返回 keyword | 执行任务 |
| --- | --- | --- |
| 去取药台取药并送至病房 A | `task1` | `task_1_take_medicine_to_ward_a` |
| 去取药台取药并送至病房 B | `task2` | `task_2_take_medicine_to_ward_b` |
| 在长柜台服务区依次服务三个人 | `task3` | `task_3_long_counter_service` |
| 去横向错位通道进行测试 | `task4` | `task_4_staggered_channel` |
| 通过狭窄区域到停靠点 | `task5` | `task_5_narrow_area_to_dock` |

启动顺序：

```bash
# 终端 1：Gazebo、AMCL、move_base
roslaunch service_robot_navigation sim_navigation.launch

# 终端 2：云端 TTS 服务
roslaunch cloud_tts cloud_tts.launch

# 终端 3：语音识别与关键词提取服务
roslaunch voice_keyword_extractor voice_keyword.launch

# 终端 4：持续等待语音任务命令
python3 src/service_robot_navigation/scripts/run_voice_tasks.py
```

例如说“请去取药台取药并送至病房A”，识别服务返回 `task1` 后，脚本会播报准备信息，执行 `task_1_take_medicine_to_ward_a`，完成后播报结果。可用 `--once` 在识别并执行一条有效任务后退出：

```bash
python3 src/service_robot_navigation/scripts/run_voice_tasks.py --once
```

脚本进入等待状态后，会先播报“你需要我执行什么任务？”，听到这句话后再说任务指令。若识别节点没有启动，会播报“语音识别服务未启动，请检查语音节点。”；若识别请求失败，会播报“语音识别失败，请重新说一遍。”。

脚本默认使用 5 秒录音、`/extract_keyword` 和 `/synthesize_speech`；可通过 `--record-seconds`、`--keyword-service` 和 `--tts-service` 覆盖。当前仓库已包含并安装 `keyword_service_node.py`，它会将语音转写结果映射为 `task1`～`task5`；运行前仍需配置该节点所需的录音设备、ASR/LLM API Key 和网络环境。

首次配置语音节点时，在 Ubuntu 环境安装其非 ROS Python 依赖：

```bash
python3 -m pip install -r src/voice_keyword_extractor/requirements.txt
python3 -m pip install -r src/cloud_tts/requirements.txt
```

当前语音节点依赖以下环境变量。不要在日志或截图中暴露真实 Key：

```bash
export DASHSCOPE_API_KEY=...
export QWEN_BASE_URL=...
export DEEPSEEK_API_KEY=...
```

可选覆盖项：

```bash
export QWEN_ASR_MODEL=qwen3-asr-flash
export DEEPSEEK_BASE_URL=https://api.deepseek.com
export DEEPSEEK_MODEL=deepseek-v4-flash
export TTS_MODEL=cosyvoice-v3-flash
export TTS_VOICE=longanhuan_v3
```

语音链路的最小自查命令：

```bash
rosservice list | grep -E 'extract_keyword|synthesize_speech'

rosservice call /synthesize_speech \
  "{text: '测试声音，语音链路检查。', play_audio: true}"

rosservice call /extract_keyword \
  "{start_recording: true, record_seconds: 5.0}"
```

如果需要系统化排查语音配置，先看 `docs/ubuntu_voice_config_self_check.md`。

### 2.2 差速轮对比导航

全向轮和差速轮使用相同的 indoor world、地图、出生位姿和五项任务。两套仿真不能同时启动，因为都使用 `/cmd_vel`、`/odom`、`/scan` 和相同的 TF 名称。

```bash
# 终端 1：差速 Gazebo、AMCL、move_base
roslaunch service_robot_diff_navigation diff_navigation.launch

# 终端 2：运行与全向轮完全相同的五项任务
python3 src/service_robot_diff_navigation/scripts/run_task_tests.py
```

差速轮车头定义为 `+X`，左右轮位于 `y=±0.198 m`，不支持 `linear.y`。同一点位下的失败结果应保留为底盘运动学对比证据，不通过修改 waypoint 消除差异。

## 3. 已完成的优化

### 3.1 机器人模型

- 对车轮 mesh 做了轻量化，降低 Gazebo 模型加载与渲染负担。
- `/cmd_vel`、`/odom` 等接口 topic 由插件提供，不再用可见硬件模型表达接口。
- 雷达调整到机器人中心位置，使扫描几何与底盘中心一致。
- 机器人正前方增加指向 `+X` 的橙色箭头，便于在 Gazebo/RViz 中判断朝向。
- 关闭 Gazebo 激光可视化，保留传感器数据并减少渲染开销。

### 3.2 导航参数

代价地图参数：

```yaml
robot_radius: 0.25
footprint_padding: 0.0
inflation_radius: 0.26
cost_scaling_factor: 12.0
```

机器人半径为 0.25 m，膨胀半径为 0.26 m，即在实体半径外只保留约 1 cm 的额外代价缓冲。这是为当前仿真场景通行性做的折中，不代表真实机器人安全余量。

GlobalPlanner 参数：

```yaml
default_tolerance: 0.20
use_grid_path: false
```

DWA 参数：

```yaml
xy_goal_tolerance: 0.18
yaw_goal_tolerance: 0.20
min_vel_theta: 0.05
latch_xy_goal_tolerance: true
```

这些值共同控制窄通道中的全局规划可达性、局部运动和完整位姿终点验收。

### 3.3 顺序任务脚本

`run_task_tests.py` 已具备以下行为：

- 启动后等待 `move_base` action server 可用。
- 等待并完成 AMCL 初始化后再开始任务。
- 按 YAML 中定义的任务和 waypoint 顺序逐点执行。
- 对尚未满足的 waypoint，在发目标前调用 clear-costmaps，清理可能残留的代价地图状态。
- 发送 goal 前 precheck 当前 AMCL 位姿；若已满足 XY/yaw 容差，则直接跳过 goal 并将该 waypoint 判定为成功。
- waypoint 超时时先读取 action state，再 cancel 目标，避免取消动作覆盖真实终态。
- 对非成功状态输出 action state、当前/目标位姿和最终误差等诊断信息。
- 已发送 goal 时，以 `move_base` action 返回 `SUCCEEDED` 为成功标准；`SUCCEEDED` 后的 AMCL XY/yaw 误差只记录摘要和诊断，不再推翻成功。
- 任一 waypoint 失败后立即 fail-fast，不继续执行后续任务。

## 4. 五项位姿任务与验收结果

| 任务 | 完整位姿 waypoint 顺序 | 顺序任务结果 | 语音命令结果 |
| --- | --- | --- | --- |
| Task 1 | `take_medicine -> ward_a` | PASS | PASS |
| Task 2 | `take_medicine -> ward_b` | PASS | PASS |
| Task 3 | `long_counter_left -> long_counter_middle -> long_counter_right` | PASS | PASS |
| Task 4 | `staggered_entry -> staggered_mid -> staggered_exit` | PASS | PASS |
| Task 5 | `narrow_entry -> narrow_mid -> narrow_exit -> dock` | PASS | PASS |

Task 4 和 Task 5 的中转点用于强制机器人通过指定区域，当前这些中转点也都包含 yaw。上表只记录用户在 Ubuntu ROS/Gazebo 中确认的测试结果；不据此推断连续运行轮数、总耗时或各 waypoint 的具体误差。

## 5. World 与地图维护

当前场景文件：

```text
src/my_world/worlds/indoor.world
```

地图生成工具：

```text
scripts/world_to_map.py
```

`world_to_map.py` 依赖 Pillow。由于它是仓库根目录脚本，当前 `rosdep` 不会自动为它补齐该依赖，首次使用前先安装：

```bash
sudo apt update
sudo apt install -y python3-pil
```

然后从项目根目录完整执行：

```bash
cd ~/service_robot
python3 scripts/world_to_map.py \
  src/my_world/worlds/indoor.world \
  src/service_robot_navigation/maps/indoor \
  --xmin -0.25 \
  --xmax 14.25 \
  --ymin -0.25 \
  --ymax 10.25 \
  --resolution 0.05 \
  --min-obstacle-z 0.05 \
  --max-obstacle-z 1.5
```

命令会生成：

- `src/service_robot_navigation/maps/indoor.pgm`
- `src/service_robot_navigation/maps/indoor.yaml`

修改 `indoor.world` 并重新生成地图后，应重新检查 `task_tests.yaml` 中每个 waypoint 与新场景几何、障碍物和可通行区域是否一致。

## 6. Debug 与回归建议

在 RViz 中重点观察：

- `/map`
- `/move_base/global_costmap/costmap`
- `/move_base/local_costmap/costmap`
- `/move_base/GlobalPlanner/plan`
- `/move_base/DWAPlannerROS/local_plan`

常用检查命令：

```bash
rostopic echo /amcl_pose
rostopic echo /move_base/status
rostopic echo /move_base/result
rostopic echo /cmd_vel
rosservice call /move_base/clear_costmaps
```

建议按以下顺序判断：

1. global costmap 已堵死时，先检查 world 几何、生成地图和 inflation，不要先反复调整局部规划器。
2. global plan 有路但机器人不走时，检查 local costmap、laser 数据和 DWA 行为。
3. 已接近目标但无法成功时，检查 XY/yaw 实际误差与对应容差。
4. 任何 world、map、导航参数或 waypoint 发生变化后，都应重新运行五项任务的完整顺序回归。

## 7. Windows 本地静态测试

在 Windows PowerShell 中运行：

```powershell
cd D:\service_robot
python -m unittest discover -s tests -v
```

当前 `main` 分支共 `18` 项静态测试，覆盖：

- URDF 模型与关键可视化/接口约束；
- 代价地图、GlobalPlanner 和 DWA 导航参数；
- 五项任务的完整 `[x, y, yaw]` 位姿配置；
- runner 工具函数、action 状态、timeout 处理和失败诊断；
- 包依赖与脚本安装约束；
- world 中错位墙体等几何约束。

这些测试只验证仓库中的静态配置和脚本契约，不能替代 Ubuntu ROS/Gazebo 中的构建、启动和运行验证。

## 8. 当前结论

- 位姿型五项任务全部通过。
- 语音模块已成功接入：`run_voice_tasks.py` 可在播报“你需要我执行什么任务？”后录音，请求 `/extract_keyword` 得到 `task1`～`task5`，再执行对应导航任务，并通过 `/synthesize_speech` 播报任务开始和结果。
- 五个任务的语音命令触发测试均已通过，本阶段项目完成。
- Task 1、Task 2 只定义业务起点和终点，由全局规划器选择路线。
- Task 3 使用三个长柜台点：`long_counter_left`、`long_counter_middle`、`long_counter_right`。
- Task 4、Task 5 使用完整位姿中转点，强制机器人通过指定区域。
- waypoint 有两条成功路径：precheck 已满足 XY/yaw 容差时直接跳过 goal 并成功；已发送 goal 时，以 `move_base` action 返回 `SUCCEEDED` 为成功标准，之后的 AMCL 误差只记录摘要和诊断，不再推翻成功。
- 当前窄通道参数服务于仿真通行性，不可直接作为真实机器人安全参数。
- world、地图、导航参数、机器人尺寸、waypoint，以及 runner、launch、定位/传感器配置或依赖发生行为性变化时，应重新执行完整五任务回归；是否重新调参以运行证据为准。
