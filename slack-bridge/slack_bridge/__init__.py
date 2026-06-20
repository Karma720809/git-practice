"""Slack 공용 채널 + 멘션 브릿지.

OpenClaw 같은 외부 에이전트가 봇↔봇 DM(channel_not_found) 없이도, 공용 채널에
자료를 올리고 Slack Claude를 멘션해 답글(코멘트)을 받아오게 해 주는 모듈.

기본 사용:

    from slack_bridge import ask
    result = ask("이 함수 리뷰해줘:\\n\\ndef f(): ...")
    print(result["reply"])
"""

from .bridge import ask
from .client import SlackBridgeClient
from .config import BridgeConfig

__all__ = ["ask", "SlackBridgeClient", "BridgeConfig"]
