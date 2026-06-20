"""slack_sdk WebClient 래퍼: 공용 채널에 멘션 게시 + 스레드 답글 폴링.

봇↔봇 DM(channel_not_found) 우회: 열린 IM 채널이 필요 없는 chat.postMessage(채널)
+ conversations.replies(폴링) 조합만 사용한다.
"""

from __future__ import annotations

import time
from typing import Callable, Optional

from slack_sdk import WebClient


def _build_mention_text(claude_user_id: str, text: str) -> str:
    """본문 앞에 Slack Claude 멘션을 붙인다."""
    return f"<@{claude_user_id}> {text}"


class SlackBridgeClient:
    """공용 채널 + 멘션 경로로 메시지를 주고받는 얇은 래퍼."""

    def __init__(
        self,
        token: str,
        claude_user_id: str,
        *,
        web_client: Optional[WebClient] = None,
        sleep: Callable[[float], None] = time.sleep,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        # web_client 주입은 테스트에서 목 대체용.
        self._web = web_client or WebClient(token=token)
        self._claude_user_id = claude_user_id
        self._sleep = sleep
        self._monotonic = monotonic

    def post_material(
        self, channel: str, text: str, thread_ts: Optional[str] = None
    ) -> str:
        """자료를 채널(또는 스레드)에 게시하고 게시된 메시지의 ts 를 반환.

        thread_ts 가 주어지면 같은 스레드에 후속 메시지로 게시한다.
        """
        kwargs = {
            "channel": channel,
            "text": _build_mention_text(self._claude_user_id, text),
        }
        if thread_ts:
            kwargs["thread_ts"] = thread_ts
        response = self._web.chat_postMessage(**kwargs)
        return response["ts"]

    def wait_for_reply(
        self,
        channel: str,
        thread_ts: str,
        after_ts: str,
        *,
        timeout: float,
        interval: float,
    ) -> dict:
        """Claude(claude_user_id)의 첫 답글이 올 때까지 스레드를 폴링한다.

        after_ts 이후(ts > after_ts)에 작성된, claude_user_id 가 보낸 첫 메시지를
        {"ts": ..., "text": ...} 형태로 반환. timeout 초과 시 TimeoutError.
        """
        after = float(after_ts)
        deadline = self._monotonic() + timeout

        while True:
            reply = self._find_reply(channel, thread_ts, after)
            if reply is not None:
                return reply
            if self._monotonic() >= deadline:
                raise TimeoutError(
                    f"{timeout:.0f}초 안에 Claude(<@{self._claude_user_id}>) 답글을 "
                    f"받지 못했습니다 (channel={channel}, thread_ts={thread_ts})."
                )
            self._sleep(interval)

    def _find_reply(
        self, channel: str, thread_ts: str, after: float
    ) -> Optional[dict]:
        response = self._web.conversations_replies(channel=channel, ts=thread_ts)
        for message in response.get("messages", []):
            if message.get("user") != self._claude_user_id:
                continue
            ts = message.get("ts")
            if ts is None or float(ts) <= after:
                continue
            return {"ts": ts, "text": message.get("text", "")}
        return None
