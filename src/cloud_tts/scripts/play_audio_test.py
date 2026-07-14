#!/usr/bin/env python3

import os
import subprocess
import sys


def play_audio(audio_path: str) -> None:
    if not os.path.isfile(audio_path):
        raise FileNotFoundError(f"音频文件不存在：{audio_path}")

    extension = os.path.splitext(audio_path)[1].lower()

    if extension == ".wav":
        command = ["aplay", audio_path]
    elif extension == ".mp3":
        command = ["mpg123", "-q", audio_path]
    else:
        raise ValueError(f"暂不支持该音频格式：{extension}")

    subprocess.run(command, check=True)


def main():
    if len(sys.argv) != 2:
        print("用法：python3 play_audio_test.py <音频路径>")
        sys.exit(1)

    try:
        play_audio(sys.argv[1])
        print("音频播放完成")
    except Exception as error:
        print(f"播放失败：{error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
