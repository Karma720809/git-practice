"""환경변수 기반 설정.

비밀값(봇 토큰 등)은 코드/리포에 절대 포함하지 않고 환경변수 또는 .env 로만 받는다.
mcp-icon-generator 의 dotenv 패턴을 python-dotenv 로 대응.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

try:  # .env 자동 로드(설치돼 있으면)
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # python-dotenv 없이도 OS 환경변수만으로 동작
    pass


# 슬랙 진단 메시지에서 확인된 Slack Claude user id (멘션 대상 기본값).
DEFAULT_CLAUDE_USER_ID = "U0B6TG36A3Z"


class ConfigError(RuntimeError):
    """필수 설정 누락 시 발생."""


@dataclass(frozen=True)
class BridgeConfig:
    """브릿지 동작에 필요한 설정값 묶음."""

    bot_token: str
    channel_id: str
    claude_user_id: str = DEFAULT_CLAUDE_USER_ID
    reply_timeout_sec: float = 180.0
    poll_interval_sec: float = 3.0

    @classmethod
    def from_env(cls) -> "BridgeConfig":
        """환경변수에서 설정을 읽는다. 필수값 누락 시 ConfigError."""
        bot_token = os.environ.get("SLACK_BOT_TOKEN", "").strip()
        channel_id = os.environ.get("BRIDGE_CHANNEL_ID", "").strip()

        missing = [
            name
            for name, value in (
                ("SLACK_BOT_TOKEN", bot_token),
                ("BRIDGE_CHANNEL_ID", channel_id),
            )
            if not value
        ]
        if missing:
            raise ConfigError(
                "필수 환경변수가 없습니다: "
                + ", ".join(missing)
                + ". slack-bridge/.env.example 를 참고해 설정하세요."
            )

        return cls(
            bot_token=bot_token,
            channel_id=channel_id,
            claude_user_id=os.environ.get(
                "CLAUDE_USER_ID", DEFAULT_CLAUDE_USER_ID
            ).strip()
            or DEFAULT_CLAUDE_USER_ID,
            reply_timeout_sec=_float_env("REPLY_TIMEOUT_SEC", 180.0),
            poll_interval_sec=_float_env("POLL_INTERVAL_SEC", 3.0),
        )


def _float_env(name: str, default: float) -> float:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} 값이 숫자가 아닙니다: {raw!r}") from exc
