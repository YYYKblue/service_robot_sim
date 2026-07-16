# Ubuntu 语音功能配置自查手册

适用项目：service_robot

适用环境：Ubuntu 20.04、ROS Noetic、Catkin 工作空间

本文结合附件《一些说明.docx》和当前项目代码整理。附件中的部分接口属于旧版本，执行命令时以本文和当前代码为准。

## 1. 当前代码与附件文档的差异

| 项目 | 附件文档中的旧版本 | 当前项目代码 |
| --- | --- | --- |
| 语音识别服务 | /extract_voice_keyword | /extract_keyword |
| 识别结果 | coke、medicine、water、milk | task1～task5、unknown |
| 任务入口 | 根据旧关键词进入任务 | 根据 task1～task5 选择导航任务 |
| Python 依赖 | 一个总 requirements.txt | 两个功能包分别维护依赖文件 |
| TTS 音频格式 | 文档同时提到 WAV/MP3 | 当前默认使用 WAV 和 aplay |

当前任务映射如下：

| 任务编号 | 语义 |
| --- | --- |
| task1 | 请去取药台取药并送至病房 A |
| task2 | 请去取药台取药并送至病房 B |
| task3 | 请在长柜台服务区依次服务三个人 |
| task4 | 请去横向错位通道进行测试 |
| task5 | 请通过狭窄区域到停靠点 |

相关代码：

- 识别节点：src/voice_keyword_extractor/scripts/keyword_service_node.py
- TTS 节点：src/cloud_tts/scripts/tts_service_node.py
- 语音任务入口：src/service_robot_navigation/scripts/run_voice_tasks.py
- 任务配置：src/service_robot_navigation/config/task_tests.yaml

## 2. 每个 Ubuntu 终端加载环境

当前 README 假设工作空间位于 ~/service_robot。如果你的实际路径是 ~/catkin_ws，需要把下面命令中的路径替换成实际路径。

每个新终端都执行：

~~~bash
source /opt/ros/noetic/setup.bash
source ~/service_robot/devel/setup.bash

if [ -f ~/.voice_api_keys.sh ]; then
    source ~/.voice_api_keys.sh
fi
~~~

检查 ROS 发行版和工作空间：

~~~bash
echo "ROS_DISTRO=$(printenv ROS_DISTRO 2>/dev/null || echo UNSET)"
echo "ROS_MASTER_URI=$(printenv ROS_MASTER_URI 2>/dev/null || echo UNSET)"
rospack find voice_keyword_extractor
rospack find cloud_tts
rospack find service_robot_navigation
~~~

预期：

~~~text
ROS_DISTRO=noetic
~~~

三个 rospack find 命令都应返回有效路径，不能出现 package not found。

## 3. 检查 Python 依赖

当前仓库有两个 Python 依赖文件：

~~~bash
cd ~/service_robot

python3 -m pip install --user \
    -r src/voice_keyword_extractor/requirements.txt

python3 -m pip install --user \
    -r src/cloud_tts/requirements.txt
~~~

检查导入：

~~~bash
python3 -c \
"import rospy, rospkg, openai, dashscope, requests, yaml; print('Python依赖正常')"
~~~

如果出现 ModuleNotFoundError，先记录缺少的模块，不要直接修改 ROS 包代码。

## 4. 检查 API Key 和环境变量

当前真实语音识别节点至少需要以下变量：

~~~text
DASHSCOPE_API_KEY   阿里云 Qwen ASR 和云端 TTS 使用
QWEN_BASE_URL       Qwen ASR 的 OpenAI 兼容接口地址，当前代码强制要求非空
DEEPSEEK_API_KEY    将 ASR 转写文本映射为 task1～task5
~~~

可选变量包括：

~~~text
QWEN_ASR_MODEL
DEEPSEEK_BASE_URL
DEEPSEEK_MODEL
TTS_BASE_URL
TTS_MODEL
TTS_VOICE
~~~

可以使用 ~/.voice_api_keys.sh 统一保存变量。不要把真实 Key 提交到 Git，也不要把真实 Key 粘贴到聊天记录中。

检查文件语法和权限：

~~~bash
test -f ~/.voice_api_keys.sh && echo "Key 文件存在" || echo "Key 文件不存在"
bash -n ~/.voice_api_keys.sh
stat -c '%a %n' ~/.voice_api_keys.sh
~~~

权限建议为 600：

~~~bash
chmod 600 ~/.voice_api_keys.sh
~~~

只检查变量是否存在，不打印变量内容：

~~~bash
for name in DASHSCOPE_API_KEY QWEN_BASE_URL DEEPSEEK_API_KEY; do
    if printenv "$name" >/dev/null 2>&1; then
        echo "$name=SET"
    else
        echo "$name=MISSING"
    fi
done
~~~

如果使用 .bashrc 自动加载，检查：

~~~bash
grep -nE 'voice_api_keys|/opt/ros/noetic|service_robot/devel' ~/.bashrc
~~~

## 5. 检查麦克风和扬声器

识别代码使用 arecord -D pulse 录音，TTS 配置使用 aplay 播放。

检查命令和设备：

~~~bash
command -v arecord
command -v aplay

arecord -l
aplay -l

pactl list short sources
pactl list short sinks
~~~

单独录音测试：

~~~bash
arecord -D pulse \
    -f S16_LE \
    -r 16000 \
    -c 1 \
    -d 5 \
    /tmp/voice_keyword.wav

ls -lh /tmp/voice_keyword.wav
aplay /tmp/voice_keyword.wav
~~~

判断方法：

- arecord 或 aplay 不存在：检查 alsa-utils 是否安装。
- Unknown PCM pulse：检查 PulseAudio/ALSA 插件配置。
- 录音文件不存在或很小：识别节点无法获得有效语音。
- 录音能够回放但系统没有声音：继续检查默认输出设备、音量和扬声器连接。

## 6. 安装系统依赖并编译

附件文档建议安装以下系统工具：

~~~bash
sudo apt update
sudo apt install -y alsa-utils mpg123 python3-pip
~~~

当前默认 TTS 输出是 WAV，因此实际播放主要依赖 aplay；mpg123 是 MP3 播放备用工具。

编译当前工作空间：

~~~bash
cd ~/service_robot
source /opt/ros/noetic/setup.bash
catkin_make
source devel/setup.bash
~~~

编译后再次确认包路径：

~~~bash
rospack find voice_keyword_extractor
rospack find cloud_tts
rospack find service_robot_navigation
~~~

## 7. 启动 ROS 和两个语音功能包

建议使用多个终端。每个终端都要先执行第 2 节的环境加载命令。

### 终端 1：ROS Master

~~~bash
roscore
~~~

### 终端 2：语音识别节点

~~~bash
roslaunch voice_keyword_extractor voice_keyword.launch
~~~

预期日志：

~~~text
Real service /extract_keyword is ready.
~~~

### 终端 3：TTS 节点

~~~bash
roslaunch cloud_tts cloud_tts.launch
~~~

预期日志：

~~~text
TTS 服务已启动：/synthesize_speech
~~~

检查两个 ROS 服务：

~~~bash
rosservice list | grep -E '/(extract_keyword|synthesize_speech)$'

rosservice type /extract_keyword
rosservice type /synthesize_speech

rosservice info /extract_keyword
rosservice info /synthesize_speech
~~~

当前正确的服务名是：

~~~text
/extract_keyword
/synthesize_speech
~~~

如果只出现 /extract_voice_keyword，说明启动了旧版本或 mock 节点。

## 8. 单独测试 TTS

先不要启动完整任务，直接调用 TTS 服务：

~~~bash
rosservice call /synthesize_speech \
"{text: '测试声音，语音链路检查。', play_audio: true}"
~~~

正常日志顺序应为：

~~~text
开始调用 TTS
云端合成成功
音频已保存
开始播放音频
音频播放完成
~~~

检查音频文件：

~~~bash
ls -lh /tmp/cloud_tts/cloud_tts_output.wav
file /tmp/cloud_tts/cloud_tts_output.wav
aplay -v /tmp/cloud_tts/cloud_tts_output.wav
~~~

### TTS 日志定位

如果启动时出现：

~~~text
MISSING_API_KEY
~~~

说明 TTS 节点所在终端没有加载 DASHSCOPE_API_KEY。

如果出现：

~~~text
未配置 TTS_BASE_URL，使用 DashScope 默认地址。
~~~

这是提示，不是错误。当前代码允许不配置 TTS_BASE_URL。

如果日志停在：

~~~text
开始调用 TTS
~~~

说明 ROS 请求已经到达 TTS 节点，但还没有完成云端合成。此时优先检查：

1. DASHSCOPE_API_KEY 是否有效。
2. Ubuntu 是否能够访问云端接口。
3. TTS_MODEL 和 TTS_VOICE 是否可用。
4. TTS 节点终端后续是否出现 API_REQUEST_FAILED。

这时还没有进入音频播放阶段，不能先把问题判断为扬声器故障。

如果已经出现 音频已保存，但没有声音，再执行：

~~~bash
aplay -v /tmp/cloud_tts/cloud_tts_output.wav
~~~

如果出现 PLAYER_NOT_FOUND，说明缺少 aplay。如果出现 PLAYBACK_FAILED，检查 ALSA 设备和默认音频输出。

## 9. 单独测试语音识别

直接调用识别服务时，服务本身不会先播报提示音。执行命令后应立即说话，因为当前默认录音时间是 5 秒：

~~~bash
rosservice call /extract_keyword \
"{start_recording: true, record_seconds: 5.0}"
~~~

测试语音示例：

~~~text
请去取药台取药并送至病房A
~~~

预期返回：

~~~text
success: True
keyword: "task1"
transcript: "请去取药台取药并送至病房A"
~~~

识别服务内部流程是：

~~~text
arecord 录音
    ↓
Qwen ASR 转写为文本
    ↓
DeepSeek 判断任务编号
    ↓
返回 task1～task5
~~~

### ASR 日志定位

| 日志或现象 | 优先检查 |
| --- | --- |
| arecord command not found | alsa-utils 是否安装 |
| arecord failed | 麦克风、PulseAudio、arecord -D pulse |
| DASHSCOPE_API_KEY is not set | 当前终端是否 source Key 文件 |
| QWEN_BASE_URL is not set | 是否配置 Qwen OpenAI 兼容接口地址 |
| Qwen ASR API failed | Qwen Key、地址、模型和网络 |
| DEEPSEEK_API_KEY is not set | DeepSeek Key 是否加载 |
| DeepSeek API failed | DeepSeek 地址、模型、Key 和网络 |
| success: True 但 keyword: unknown | 检查 transcript 和说话内容是否明确 |

## 10. 启动导航并运行语音任务

### 终端 4：启动导航仿真

~~~bash
roslaunch service_robot_navigation sim_navigation.launch
~~~

检查导航：

~~~bash
rosnode list | grep move_base
rostopic echo -n 1 /amcl_pose
~~~

### 终端 5：启动语音任务脚本

~~~bash
cd ~/service_robot
source /opt/ros/noetic/setup.bash
source devel/setup.bash
source ~/.voice_api_keys.sh

python3 src/service_robot_navigation/scripts/run_voice_tasks.py --once
~~~

正常顺序是：

~~~text
等待 move_base
等待 /extract_keyword
等待 /synthesize_speech
播报：你需要我执行什么任务？
录音 5 秒
识别任务编号
播报：准备执行任务...
执行对应导航任务
播报任务完成或失败
~~~

只有在听到：

~~~text
你需要我执行什么任务？
~~~

之后，才开始说任务指令。

如果一直没有提示音，检查：

~~~bash
rosservice list | grep /synthesize_speech
~~~

如果导航或识别服务没有准备好，脚本可能还没有进入真正的等待指令阶段。

完整脚本默认行为：

- 录音 5 秒。
- 使用 /extract_keyword。
- 使用 /synthesize_speech。
- 执行第一条有效任务后退出，因为指定了 --once。

如果希望持续等待多个任务：

~~~bash
python3 src/service_robot_navigation/scripts/run_voice_tasks.py
~~~

## 11. 完整故障定位表

| 现象 | 说明 | 下一步 |
| --- | --- | --- |
| ROS 服务列表中没有服务 | 节点没有启动或环境未加载 | 检查 roscore、source、roslaunch 日志 |
| TTS 服务已启动但调用失败 | 启动配置正常，云端请求可能失败 | 查看 error_message 和 TTS 节点后续日志 |
| 日志停在 开始调用 TTS | 问题还在云端合成阶段 | 检查 API Key、网络、模型和地址 |
| 音频文件生成但没有声音 | 问题在本地播放链路 | 手动执行 aplay -v |
| ASR 返回 arecord failed | 录音设备异常 | 检查 arecord -l、PulseAudio 和麦克风 |
| ASR 返回 Qwen 错误 | ASR 云端接口异常 | 检查 DASHSCOPE_API_KEY、QWEN_BASE_URL |
| ASR 返回 DeepSeek 错误 | 任务映射接口异常 | 检查 DEEPSEEK_API_KEY 和模型 |
| 返回 unknown | 没有映射到有效任务 | 查看 transcript，说清楚病房/区域/停靠点 |
| 完整脚本没有播报提示 | 可能仍在等待导航或语音服务 | 检查 move_base 和两个 ROS 服务 |

## 12. 建议反馈给开发人员的自查结果

如果需要继续定位问题，建议只反馈以下信息，不要发送真实 API Key：

~~~bash
echo "ROS_DISTRO=$(printenv ROS_DISTRO 2>/dev/null || echo UNSET)"
rospack find voice_keyword_extractor
rospack find cloud_tts
rosservice list | grep -E '/(extract_keyword|synthesize_speech)$'
command -v arecord
command -v aplay
arecord -l
aplay -l
~~~

同时提供：

1. TTS 节点从启动到失败的完整日志。
2. /synthesize_speech 的返回内容。
3. /extract_keyword 的返回内容。
4. 失败时对应终端的最后 20～30 行日志。

## 13. 相关代码

- [项目 README](../README.md)
- [语音任务入口](../src/service_robot_navigation/scripts/run_voice_tasks.py)
- [顺序任务入口](../src/service_robot_navigation/scripts/run_task_tests.py)
- [语音识别节点](../src/voice_keyword_extractor/scripts/keyword_service_node.py)
- [语音识别服务定义](../src/voice_keyword_extractor/srv/ExtractKeyword.srv)
- [TTS 节点](../src/cloud_tts/scripts/tts_service_node.py)
- [TTS 配置](../src/cloud_tts/config/tts_config.yaml)
- [TTS 服务定义](../src/cloud_tts/srv/SynthesizeSpeech.srv)

