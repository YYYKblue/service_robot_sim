#!/usr/bin/env python3

import os
import subprocess
import sys

OUTPUT_PATH = "/tmp/voice_keyword_test.wav"
RECORD_SECONDS = 5

command = [
    "arecord",
    "-D", "pulse",
    "-f", "S16_LE",
    "-r", "16000",
    "-c", "1",
    "-d", str(RECORD_SECONDS),
    OUTPUT_PATH,
]

print(f"开始录音 {RECORD_SECONDS} 秒，请说话……")

try:
    subprocess.run(command, check=True, timeout=RECORD_SECONDS + 5)
except subprocess.TimeoutExpired:
    print("录音超时")
    sys.exit(1)
except subprocess.CalledProcessError as exc:
    print(f"录音失败：{exc}")
    sys.exit(1)

if not os.path.isfile(OUTPUT_PATH):
    print("录音文件没有生成")
    sys.exit(1)

file_size = os.path.getsize(OUTPUT_PATH)
print(f"录音完成：{OUTPUT_PATH}")
print(f"文件大小：{file_size} bytes")

if file_size < 1000:
    print("文件过小，可能没有正常录音")
    sys.exit(1)
