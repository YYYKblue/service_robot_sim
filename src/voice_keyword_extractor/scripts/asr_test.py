#!/usr/bin/env python3

import os
import sys
from pathlib import Path

import dashscope


AUDIO_PATH = Path("/tmp/voice_keyword_test.wav")
MODEL_NAME = "qwen3-asr-flash"


def extract_text(response) -> str:
    """
    尽量兼容 DashScope SDK 返回对象和字典两种形式。
    """
    try:
        return response.output.choices[0].message.content.strip()
    except (AttributeError, IndexError, TypeError):
        pass

    try:
        return response["output"]["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError, AttributeError):
        pass

    return ""


def main() -> int:
    api_key = os.getenv("DASHSCOPE_API_KEY")

    if not api_key:
        print("错误：没有检测到环境变量 DASHSCOPE_API_KEY。")
        print("请先执行：export DASHSCOPE_API_KEY='你的百炼API Key'")
        return 1

    if not AUDIO_PATH.is_file():
        print(f"错误：音频文件不存在：{AUDIO_PATH}")
        print("请先运行 record_test.py 生成测试录音。")
        return 1

    file_size = AUDIO_PATH.stat().st_size
    if file_size <= 44:
        print(f"错误：音频文件异常，文件大小只有 {file_size} 字节。")
        return 1

    print(f"音频文件：{AUDIO_PATH}")
    print(f"文件大小：{file_size} bytes")
    print(f"使用模型：{MODEL_NAME}")
    print("正在调用百炼 ASR，请稍候……")

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "audio": str(AUDIO_PATH.resolve())
                }
            ],
        }
    ]

    try:
        response = dashscope.MultiModalConversation.call(
            api_key=api_key,
            model=MODEL_NAME,
            messages=messages,
            result_format="message",
            asr_options={
                "language": "zh",
                "enable_itn": True,
            },
        )
    except Exception as exc:
        print(f"调用 ASR 时发生异常：{type(exc).__name__}: {exc}")
        return 1

    status_code = getattr(response, "status_code", None)

    if status_code is not None and status_code != 200:
        request_id = getattr(response, "request_id", "")
        code = getattr(response, "code", "")
        message = getattr(response, "message", "")

        print("ASR 调用失败。")
        print(f"HTTP 状态码：{status_code}")
        print(f"错误码：{code}")
        print(f"错误信息：{message}")
        print(f"Request ID：{request_id}")
        return 1

    transcript = extract_text(response)

    if not transcript:
        print("ASR 调用完成，但没有解析到识别文本。")
        print("原始响应如下：")
        print(response)
        return 1

    print("\n识别结果：")
    print(transcript)

    return 0


if __name__ == "__main__":
    sys.exit(main())
