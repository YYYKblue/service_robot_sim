#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import time
from pathlib import Path
from typing import Any, Dict

import dashscope
import requests
import rospy
import yaml
from dashscope.audio.http_tts.http_speech_synthesizer import (
    HttpSpeechSynthesizer,
)

from cloud_tts.srv import (
    SynthesizeSpeech,
    SynthesizeSpeechResponse,
)


class TtsError(RuntimeError):
    """带统一错误码的 TTS 异常。"""

    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def load_config() -> Dict[str, Any]:
    """读取功能包内的 YAML 配置文件。"""
    package_path = Path(__file__).resolve().parent.parent
    config_path = package_path / "config" / "tts_config.yaml"

    if not config_path.is_file():
        raise TtsError(
            "CONFIG_NOT_FOUND",
            f"配置文件不存在：{config_path}",
        )

    try:
        with config_path.open("r", encoding="utf-8") as file:
            config = yaml.safe_load(file)
    except yaml.YAMLError as error:
        raise TtsError(
            "CONFIG_INVALID",
            f"配置文件格式错误：{error}",
        ) from error

    if not isinstance(config, dict):
        raise TtsError(
            "CONFIG_INVALID",
            "配置文件内容为空或不是有效字典。",
        )

    return config


def validate_environment() -> str:
    """检查 API Key，并设置可选的专属服务地址。"""
    api_key = os.getenv("DASHSCOPE_API_KEY")

    if not api_key:
        raise TtsError(
            "MISSING_API_KEY",
            "未找到环境变量 DASHSCOPE_API_KEY。",
        )

    base_url = os.getenv("TTS_BASE_URL", "").strip()

    if base_url:
        dashscope.base_http_api_url = base_url
        rospy.loginfo("使用百炼专属服务地址：%s", base_url)
    else:
        rospy.loginfo("未配置 TTS_BASE_URL，使用 DashScope 默认地址。")

    return api_key


def validate_text(text: str, max_length: int) -> str:
    """检查待合成文本是否合法。"""
    cleaned_text = text.strip()

    if not cleaned_text:
        raise TtsError(
            "EMPTY_TEXT",
            "输入文本为空。",
        )

    if len(cleaned_text) > max_length:
        raise TtsError(
            "TEXT_TOO_LONG",
            f"文本长度为 {len(cleaned_text)}，超过限制 {max_length}。",
        )

    return cleaned_text


def build_output_path(config: Dict[str, Any]) -> Path:
    """创建输出目录，并生成本次使用的音频路径。"""
    output_config = config["output"]

    output_directory = Path(output_config["directory"]).expanduser()
    filename = output_config["filename"]

    try:
        output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )
    except OSError as error:
        raise TtsError(
            "OUTPUT_DIRECTORY_FAILED",
            f"无法创建音频目录：{error}",
        ) from error

    return output_directory / filename


def call_tts_api(
    text: str,
    config: Dict[str, Any],
    api_key: str,
) -> str:
    """调用阿里云 CosyVoice，返回临时音频下载地址。"""
    audio_config = config["audio"]

    model = os.getenv(
        "TTS_MODEL",
        config["model"],
    )

    voice = os.getenv(
        "TTS_VOICE",
        config["voice"],
    )

    rospy.loginfo(
        "开始调用 TTS，model=%s, voice=%s, text=%s",
        model,
        voice,
        text,
    )

    try:
        result = HttpSpeechSynthesizer.call(
            model=model,
            text=text,
            voice=voice,
            format=audio_config["format"],
            sample_rate=int(audio_config["sample_rate"]),
            volume=int(audio_config["volume"]),
            rate=float(audio_config["rate"]),
            pitch=float(audio_config["pitch"]),
            language_hints=["zh"],
            stream=False,
            api_key=api_key,
        )
    except Exception as error:
        raise TtsError(
            "API_REQUEST_FAILED",
            f"调用云端 TTS 失败：{error}",
        ) from error

    audio_url = getattr(result, "audio_url", None)

    if not audio_url:
        raise TtsError(
            "EMPTY_AUDIO_URL",
            f"云端接口未返回音频地址，原始结果：{result}",
        )

    rospy.loginfo("云端合成成功，已获得音频下载地址。")
    return audio_url


def save_audio(
    audio_url: str,
    output_path: Path,
    timeout_seconds: int,
    minimum_audio_bytes: int,
) -> None:
    """下载云端返回的音频，并保存到本地。"""
    temporary_path = output_path.with_suffix(
        output_path.suffix + ".part"
    )

    try:
        response = requests.get(
            audio_url,
            timeout=timeout_seconds,
        )
        response.raise_for_status()
    except requests.Timeout as error:
        raise TtsError(
            "API_TIMEOUT",
            "下载合成音频超时。",
        ) from error
    except requests.RequestException as error:
        raise TtsError(
            "AUDIO_DOWNLOAD_FAILED",
            f"下载合成音频失败：{error}",
        ) from error

    audio_data = response.content

    if not audio_data:
        raise TtsError(
            "EMPTY_AUDIO",
            "下载到的音频内容为空。",
        )

    if len(audio_data) < minimum_audio_bytes:
        raise TtsError(
            "EMPTY_AUDIO",
            f"音频文件过小，仅 {len(audio_data)} 字节。",
        )

    try:
        with temporary_path.open("wb") as file:
            file.write(audio_data)

        temporary_path.replace(output_path)
    except OSError as error:
        raise TtsError(
            "SAVE_AUDIO_FAILED",
            f"保存音频失败：{error}",
        ) from error
    finally:
        if temporary_path.exists():
            try:
                temporary_path.unlink()
            except OSError:
                pass

    if not output_path.is_file():
        raise TtsError(
            "SAVE_AUDIO_FAILED",
            "保存结束后没有找到音频文件。",
        )

    rospy.loginfo(
        "音频已保存：%s，大小：%d 字节",
        output_path,
        output_path.stat().st_size,
    )


def play_audio(audio_path: Path, config: Dict[str, Any]) -> None:
    """调用系统播放器阻塞播放音频。"""
    extension = audio_path.suffix.lower()
    playback_config = config["playback"]

    if extension == ".wav":
        command = [
            playback_config["wav_player"],
            str(audio_path),
        ]
    elif extension == ".mp3":
        command = [
            playback_config["mp3_player"],
            "-q",
            str(audio_path),
        ]
    else:
        raise TtsError(
            "UNSUPPORTED_AUDIO_FORMAT",
            f"不支持播放格式：{extension}",
        )

    rospy.loginfo("开始播放音频：%s", audio_path)

    try:
        result = subprocess.run(
            command,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except FileNotFoundError as error:
        raise TtsError(
            "PLAYER_NOT_FOUND",
            f"找不到播放器命令：{command[0]}",
        ) from error
    except OSError as error:
        raise TtsError(
            "PLAYBACK_FAILED",
            f"无法启动播放器：{error}",
        ) from error

    if result.returncode != 0:
        error_text = result.stderr.strip()

        raise TtsError(
            "PLAYBACK_FAILED",
            error_text or f"播放器返回码：{result.returncode}",
        )

    rospy.loginfo("音频播放完成。")


class CloudTtsService:
    """ROS TTS 服务节点。"""

    def __init__(self) -> None:
        self.config = load_config()
        self.api_key = validate_environment()

        self.service = rospy.Service(
            "/synthesize_speech",
            SynthesizeSpeech,
            self.handle_synthesize,
        )

        rospy.loginfo("TTS 服务已启动：/synthesize_speech")

    def handle_synthesize(
        self,
        request,
    ) -> SynthesizeSpeechResponse:
        """处理一次 ROS TTS 服务请求。"""
        start_time = time.monotonic()

        try:
            max_text_length = int(
                self.config["limits"]["max_text_length"]
            )
            timeout_seconds = int(
                self.config["limits"]["request_timeout_seconds"]
            )
            minimum_audio_bytes = int(
                self.config["limits"]["minimum_audio_bytes"]
            )

            text = validate_text(
                request.text,
                max_text_length,
            )

            output_path = build_output_path(
                self.config,
            )

            audio_url = call_tts_api(
                text=text,
                config=self.config,
                api_key=self.api_key,
            )

            save_audio(
                audio_url=audio_url,
                output_path=output_path,
                timeout_seconds=timeout_seconds,
                minimum_audio_bytes=minimum_audio_bytes,
            )

            if request.play_audio:
                play_audio(
                    output_path,
                    self.config,
                )

            processing_time = (
                time.monotonic() - start_time
            )

            return SynthesizeSpeechResponse(
                success=True,
                audio_path=str(output_path),
                error_message="",
                processing_time=processing_time,
            )

        except TtsError as error:
            processing_time = (
                time.monotonic() - start_time
            )

            rospy.logerr(
                "TTS处理失败 [%s]：%s",
                error.code,
                error.message,
            )

            return SynthesizeSpeechResponse(
                success=False,
                audio_path="",
                error_message=(
                    f"{error.code}: {error.message}"
                ),
                processing_time=processing_time,
            )

        except Exception as error:
            processing_time = (
                time.monotonic() - start_time
            )

            rospy.logexception(
                "发生未处理异常：%s",
                error,
            )

            return SynthesizeSpeechResponse(
                success=False,
                audio_path="",
                error_message=(
                    f"INTERNAL_ERROR: {error}"
                ),
                processing_time=processing_time,
            )


def main() -> None:
    rospy.init_node("cloud_tts_service_node")

    try:
        CloudTtsService()
    except TtsError as error:
        rospy.logfatal(
            "TTS服务启动失败 [%s]：%s",
            error.code,
            error.message,
        )
        return
    except Exception as error:
        rospy.logfatal(
            "TTS服务启动失败：%s",
            error,
        )
        return

    rospy.spin()


if __name__ == "__main__":
    main()
