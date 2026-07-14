#!/usr/bin/env python3

import os
import re
import sys
from openai import OpenAI

ALLOWED_KEYWORDS = (
    "coke",
    "medicine",
    "water",
    "milk",
    "unknown",
)

api_key = os.getenv("DEEPSEEK_API_KEY")
base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
model = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")

if not api_key:
    print("错误：未设置 DEEPSEEK_API_KEY")
    sys.exit(1)

print(f"Base URL: {base_url}")
print(f"Model: {model}")

client = OpenAI(
    api_key=api_key,
    base_url=base_url,
)

system_prompt = """
你是RoboCup家庭服务机器人的关键词分类器。

根据用户文本，只允许返回以下一个英文关键词：
coke
medicine
water
milk
unknown

映射规则：
- 可乐、汽水、可口可乐 -> coke
- 药、药品、药物、吃药 -> medicine
- 水、饮用水、矿泉水 -> water
- 牛奶 -> milk
- 其他内容或无法判断 -> unknown

只返回一个英文关键词，不要解释，不要标点，不要Markdown。
""".strip()


def normalize_keyword(raw_result: str) -> str:
    normalized = raw_result.strip().lower()

    matches = re.findall(
        r"\b(coke|medicine|water|milk|unknown)\b",
        normalized,
    )

    if len(matches) == 1:
        return matches[0]

    return "unknown"


test_texts = [
    "我想要一杯可乐",
    "请帮我拿一下药品",
    "我想喝水",
    "给我一盒牛奶",
    "我想要一个苹果",
]

for text in test_texts:
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
            max_tokens=20,
            extra_body={
                "thinking": {
                    "type": "disabled"
                }
            },
        )

        message = response.choices[0].message
        raw_result = message.content or ""
        keyword = normalize_keyword(raw_result)

        print(f"输入：{text}")
        print(f"原始输出：{raw_result!r}")
        print(f"最终关键词：{keyword}")
        print(f"结束原因：{response.choices[0].finish_reason}")
        print("-" * 40)

    except Exception as exc:
        print(f"输入：{text}")
        print(f"调用失败：{type(exc).__name__}: {exc}")
        print("-" * 40)
