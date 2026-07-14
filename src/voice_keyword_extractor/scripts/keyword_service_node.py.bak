#!/usr/bin/env python3

import time
import rospy

from voice_keyword_extractor.srv import (
    ExtractKeyword,
    ExtractKeywordResponse,
)


def handle_extract_keyword(request):
    start_time = time.time()

    if not request.start_recording:
        return ExtractKeywordResponse(
            success=False,
            keyword="unknown",
            transcript="",
            raw_result="",
            error_message="start_recording is false",
            processing_time=time.time() - start_time,
        )

    rospy.loginfo(
        "Mock recording started, duration: %.1f seconds",
        request.record_seconds,
    )

    # 第一版先固定模拟“我想要一杯可乐”
    transcript = "我想要一杯可乐"
    keyword = "coke"

    return ExtractKeywordResponse(
        success=True,
        keyword=keyword,
        transcript=transcript,
        raw_result=keyword,
        error_message="",
        processing_time=time.time() - start_time,
    )


def main():
    rospy.init_node("keyword_service_node")
    rospy.Service(
        "/extract_voice_keyword",
        ExtractKeyword,
        handle_extract_keyword,
    )

    rospy.loginfo("Service /extract_voice_keyword is ready.")
    rospy.spin()


if __name__ == "__main__":
    main()
