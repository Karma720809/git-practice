"""고수준 오케스트레이션: Routine 발화 → GitHub 메일박스 댓글로 답변 수신."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from .client import RoutineBridgeClient
from .config import RoutineBridgeConfig


def ask(
    text: str,
    *,
    config: Optional[RoutineBridgeConfig] = None,
    client: Optional[RoutineBridgeClient] = None,
) -> dict:
    """text 를 Routine 에 전달해 세션을 띄우고, 메일박스 이슈에 달릴 답변 댓글을 기다려 반환한다.

    반환:
        {
            "session_id":  Routine 이 새로 띈 Claude Code 세션 id,
            "session_url": 그 세션을 볼 수 있는 URL,
            "fire_time":   /fire 호출 직전에 기록한 UTC ISO 타임스탬프(폴링 기준점),
            "reply_comment_id": 답변으로 인식한 GitHub 댓글 id,
            "reply":       답변 댓글 본문,
        }
    """
    config = config or RoutineBridgeConfig.from_env()
    client = client or RoutineBridgeClient(
        fire_url=config.fire_url,
        bearer_token=config.bearer_token,
        github_token=config.github_token,
        beta_header=config.beta_header,
    )

    fire_time = datetime.now(timezone.utc).isoformat()
    fired = client.fire(text)

    reply = client.wait_for_reply(
        config.github_owner,
        config.github_repo,
        config.mailbox_issue_number,
        fire_time,
        timeout=config.reply_timeout_sec,
        interval=config.poll_interval_sec,
    )

    return {
        "session_id": fired.get("claude_code_session_id"),
        "session_url": fired.get("claude_code_session_url"),
        "fire_time": fire_time,
        "reply_comment_id": reply["id"],
        "reply": reply["body"],
    }
