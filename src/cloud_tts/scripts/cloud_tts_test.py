def synthesize_text(text: str, output_path: str) -> str:
    """
    调用云端 TTS，将音频保存到 output_path。
    成功后返回音频文件路径。
    """
