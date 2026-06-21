"""환경변수 기반 설정.

비밀값(bearer 토큰, GitHub 토큰 등)은 코드/리포에 절대 포함하지 않고 환경변수
또는 .env 로만 받는다. slack-bridge 의 패턴을 그대로 따른다.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

try:  # .env 자동 로드(설치돼 있으면)
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # python-dotenv 없이도 OS 환경변수만으로 동작
    pass


DEFAULT_GITHUB_OWNER = "karma720809"
DEFAULT_GITHUB_REPO = "git-practice"
DEFAULT_BETA_HEADER = "experimental-cc-routine-2026-04-01"


class ConfigError(RuntimeError):
    """필수 설정 누락 시 발생."""


@dataclass(frozen=True)
class RoutineBridgeConfig:
    """브릿지 동작에 필요한 설정값 묶음."""

    fire_url: str
    bearer_token: str
    github_token: str
    mailbox_issue_number: int
    github_owner: str = DEFAULT_GITHUB_OWNER
    github_repo: str = DEFAULT_GITHUB_REPO
    beta_header: str = DEFAULT_BETA_HEADER
    reply_timeout_sec: float = 600.0
    poll_interval_sec: float = 5.0

    @classmethod
    def from_env(cls) -> "RoutineBridgeConfig":
        """환경변수에서 설정을 읽는다. 필수값 누락 시 ConfigError."""
        fire_url = os.environ.get("ROUTINE_FIRE_URL", "").strip()
        bearer_token = os.environ.get("ROUTINE_BEARER_TOKEN", "").strip()
        github_token = os.environ.get("GITHUB_TOKEN", "").strip()
        mailbox_issue_raw = os.environ.get("MAILBOX_ISSUE_NUMBER", "").strip()

        missing = [
            name
            for name, value in (
                ("ROUTINE_FIRE_URL", fire_url),
                ("ROUTINE_BEARER_TOKEN", bearer_token),
                ("GITHUB_TOKEN", github_token),
                ("MAILBOX_ISSUE_NUMBER", mailbox_issue_raw),
            )
            if not value
        ]
        if missing:
            raise ConfigError(
                "필수 환경변수가 없습니다: "
                + ", ".join(missing)
                + ". routine-bridge/.env.example 를 참고해 설정하세요."
            )

        try:
            mailbox_issue_number = int(mailbox_issue_raw)
        except ValueError as exc:
            raise ConfigError(
                f"MAILBOX_ISSUE_NUMBER 값이 정수가 아닙니다: {mailbox_issue_raw!r}"
            ) from exc

        return cls(
            fire_url=fire_url,
            bearer_token=bearer_token,
            github_token=github_token,
            mailbox_issue_number=mailbox_issue_number,
            github_owner=os.environ.get("GITHUB_OWNER", "").strip()
            or DEFAULT_GITHUB_OWNER,
            github_repo=os.environ.get("GITHUB_REPO", "").strip()
            or DEFAULT_GITHUB_REPO,
            reply_timeout_sec=_float_env("REPLY_TIMEOUT_SEC", 600.0),
            poll_interval_sec=_float_env("POLL_INTERVAL_SEC", 5.0),
        )


def _float_env(name: str, default: float) -> float:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} 값이 숫자가 아닙니다: {raw!r}") from exc
