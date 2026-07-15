#!/usr/bin/env python3

import base64
import os
import pathlib
import subprocess
import time
from typing import Tuple

import rospy
from openai import OpenAI

from voice_keyword_extractor.srv import (
    ExtractKeyword,
    ExtractKeywordResponse,
)


ALLOWED_KEYWORDS = {
    "task1",
    "task2",
    "task3",
    "task4",
    "task5",
    "unknown",
}

AUDIO_PATH = "/tmp/voice_keyword.wav"

SYSTEM_PROMPT = """
你是 RoboCup 家庭服务机器人的关键词提取模块。

请根据用户说的话，只从下面五个任务编号中返回一个：
task1
task2
task3
task4
task5
unknown

映射规则：
1. 请去取药台取药并送至病房A、去药台给病房A送药 -> task1
2. 请去取药台取药并送至病房B、去药台给病房B送药 -> task2
3. 请在长柜台服务区依次服务三个人、去长柜台依次服务三个人 -> task3
4. 请去横向错位通道进行测试、测试横向错位通道 -> task4
5. 请通过狭窄区域到停靠点、经过狭窄区域去停靠点 -> task5
6. 其他内容、没有明确表达任务、无法理解 -> unknown

输出规则：
1. 只输出一个任务编号。
2. 不要输出解释。
3. 不要输出标点。
4. 不要输出 Markdown。
""".strip()


def record_audio(record_seconds: float, output_path: str) -> None:
    """
    使用 arecord 从 PulseAudio 默认输入设备录音。
    输出格式：16kHz、单声道、16位 PCM WAV。
    """
    if record_seconds < 1.0 or record_seconds > 10.0:
        raise ValueError("record_seconds must be between 1 and 10")

    command = [
        "arecord",
        "-D", "pulse",
        "-f", "S16_LE",
        "-r", "16000",
        "-c", "1",
        "-d", str(int(round(record_seconds))),
        output_path,
    ]

    rospy.loginfo(
        "Recording audio for %.1f seconds: %s",
        record_seconds,
        output_path,
    )

    try:
        completed = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=record_seconds + 8.0,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("recording timeout") from exc
    except FileNotFoundError as exc:
        raise RuntimeError("arecord command not found") from exc

    if completed.returncode != 0:
        stderr_text = completed.stderr.decode(
            "utf-8",
            errors="replace",
        ).strip()
        raise RuntimeError(
            f"arecord failed: {stderr_text or completed.returncode}"
        )

    if not os.path.isfile(output_path):
        raise RuntimeError("audio file was not created")

    file_size = os.path.getsize(output_path)

    if file_size < 1000:
        raise RuntimeError(
            f"audio file is too small: {file_size} bytes"
        )

    rospy.loginfo(
        "Recording completed, file size: %d bytes",
        file_size,
    )


def transcribe_audio(audio_path: str) -> str:
    """
    调用阿里云百炼 Qwen3-ASR-Flash，将本地 WAV 转写为文本。
    """
    api_key = os.getenv("DASHSCOPE_API_KEY")
    base_url = os.getenv("QWEN_BASE_URL")
    model = os.getenv("QWEN_ASR_MODEL", "qwen3-asr-flash")

    if not api_key:
        raise RuntimeError("DASHSCOPE_API_KEY is not set")

    if not base_url:
        raise RuntimeError("QWEN_BASE_URL is not set")

    file_path = pathlib.Path(audio_path)

    if not file_path.exists():
        raise RuntimeError(f"audio file does not exist: {audio_path}")

    audio_base64 = base64.b64encode(
        file_path.read_bytes()
    ).decode("utf-8")

    data_uri = f"data:audio/wav;base64,{audio_base64}"

    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
        timeout=60.0,
        max_retries=1,
    )

    rospy.loginfo("Calling Qwen ASR model: %s", model)

    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_audio",
                            "input_audio": {
                                "data": data_uri
                            },
                        }
                    ],
                }
            ],
            stream=False,
            extra_body={
                "asr_options": {
                    "language": "zh",
                    "enable_itn": True,
                }
            },
        )
    except Exception as exc:
        raise RuntimeError(f"Qwen ASR API failed: {exc}") from exc

    if not completion.choices:
        raise RuntimeError("Qwen ASR returned no choices")

    transcript = completion.choices[0].message.content or ""
    transcript = transcript.strip()

    if not transcript:
        raise RuntimeError("Qwen ASR returned empty transcript")

    rospy.loginfo("ASR transcript: %s", transcript)

    return transcript


def normalize_keyword(raw_result: str) -> str:
    """
    清理模型输出并进行白名单校验。
    """
    keyword = (raw_result or "").strip().lower()

    keyword = keyword.replace("`", "")
    keyword = keyword.replace('"', "")
    keyword = keyword.replace("'", "")
    keyword = keyword.replace(".", "")
    keyword = keyword.replace("。", "")
    keyword = keyword.replace(",", "")
    keyword = keyword.replace("，", "")
    keyword = keyword.strip()

    if keyword not in ALLOWED_KEYWORDS:
        return "unknown"

    return keyword


def extract_keyword(transcript: str) -> Tuple[str, str]:
    """
    调用 DeepSeek V4 Flash，把识别文本映射到受控关键词。
    返回：
        keyword：清理并校验后的关键词
        raw_result：模型原始输出
    """
    api_key = os.getenv("DEEPSEEK_API_KEY")
    base_url = os.getenv(
        "DEEPSEEK_BASE_URL",
        "https://api.deepseek.com",
    )
    model = os.getenv(
        "DEEPSEEK_MODEL",
        "deepseek-v4-flash",
    )

    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY is not set")

    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
        timeout=60.0,
        max_retries=1,
    )

    rospy.loginfo(
        "Calling DeepSeek keyword model: %s",
        model,
    )

    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": transcript,
                },
            ],
            temperature=0,
            max_tokens=10,
            stream=False,
            extra_body={
                "thinking": {
                    "type": "disabled"
                }
            },
        )
    except Exception as exc:
        raise RuntimeError(
            f"DeepSeek API failed: {exc}"
        ) from exc

    if not completion.choices:
        raise RuntimeError("DeepSeek returned no choices")

    raw_result = (
        completion.choices[0].message.content or ""
    ).strip()

    if not raw_result:
        raise RuntimeError("DeepSeek returned empty content")

    keyword = normalize_keyword(raw_result)

    rospy.loginfo(
        "Keyword result: raw=%s, normalized=%s",
        raw_result,
        keyword,
    )

    return keyword, raw_result


def build_failure_response(
    start_time: float,
    error_message: str,
    transcript: str = "",
    raw_result: str = "",
) -> ExtractKeywordResponse:
    """
    统一构造失败响应，确保异常不会使 ROS 节点退出。
    """
    rospy.logerr(error_message)

    return ExtractKeywordResponse(
        success=False,
        keyword="unknown",
        transcript=transcript,
        raw_result=raw_result,
        error_message=error_message,
        processing_time=float(time.time() - start_time),
    )


def handle_extract_keyword(request) -> ExtractKeywordResponse:
    """
    ROS Service 回调：
    录音 -> ASR -> LLM关键词提取 -> 返回响应。
    """
    start_time = time.time()
    transcript = ""
    raw_result = ""

    if not request.start_recording:
        return build_failure_response(
            start_time,
            "start_recording is false",
        )

    record_seconds = float(request.record_seconds)

    if record_seconds < 1.0 or record_seconds > 10.0:
        return build_failure_response(
            start_time,
            "record_seconds must be between 1 and 10",
        )

    try:
        if os.path.exists(AUDIO_PATH):
            os.remove(AUDIO_PATH)

        record_audio(
            record_seconds=record_seconds,
            output_path=AUDIO_PATH,
        )

        transcript = transcribe_audio(AUDIO_PATH)

        keyword, raw_result = extract_keyword(transcript)

        return ExtractKeywordResponse(
            success=True,
            keyword=keyword,
            transcript=transcript,
            raw_result=raw_result,
            error_message="",
            processing_time=float(time.time() - start_time),
        )

    except Exception as exc:
        return build_failure_response(
            start_time=start_time,
            error_message=str(exc),
            transcript=transcript,
            raw_result=raw_result,
        )


def main() -> None:
    rospy.init_node("keyword_service_node")

    rospy.Service(
        "/extract_keyword",
        ExtractKeyword,
        handle_extract_keyword,
    )

    rospy.loginfo(
        "Real service /extract_keyword is ready."
    )

    rospy.spin()


if __name__ == "__main__":
    main()
