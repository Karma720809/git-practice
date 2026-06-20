"""고수준 오케스트레이션: 자료 게시 → Claude 답글 수신."""

from __future__ import annotations

from typing import Optional

from .client import SlackBridgeClient
from .config import BridgeConfig


def ask(
    material: str,
    thread_ts: Optional[str] = None,
    *,
    config: Optional[BridgeConfig] = None,
    client: Optional[SlackBridgeClient] = None,
) -> dict:
    """자료(material)를 공용 채널에 올려 Claude를 멘션하고 답글을 받아 반환한다.

    thread_ts 를 넘기면 기존 스레드에서 후속 대화를 이어간다(왕복 컨텍스트 유지).

    반환:
        {
            "thread_ts":  대화 스레드 루트 ts(후속 ask 에 재사용),
            "request_ts": 이번에 게시한 요청 메시지 ts,
            "reply_ts":   Claude 답글 ts,
            "reply":      Claude 답글 본문,
        }
    """
    config = config or BridgeConfig.from_env()
    client = client or SlackBridgeClient(
        token=config.bot_token, claude_user_id=config.claude_user_id
    )

    request_ts = client.post_material(config.channel_id, material, thread_ts=thread_ts)
    # 첫 호출이면 방금 올린 메시지가 스레드 루트가 된다.
    root_ts = thread_ts or request_ts

    reply = client.wait_for_reply(
        config.channel_id,
        root_ts,
        request_ts,
        timeout=config.reply_timeout_sec,
        interval=config.poll_interval_sec,
    )

    return {
        "thread_ts": root_ts,
        "request_ts": request_ts,
        "reply_ts": reply["ts"],
        "reply": reply["text"],
    }
