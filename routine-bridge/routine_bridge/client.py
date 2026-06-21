"""HTTP 클라이언트: Routines API /fire 호출 + GitHub 메일박스 이슈 댓글 폴링.

Slack 멘션 트리거는 게이트웨이가 '봇 발신 메시지(bot_id)'를 필터링해 봇↔봇
무한루프를 막다 보니, 외부 에이전트가 보낸 멘션이 묻혀버리는 문제가 있었다.
Routines 의 API 트리거는 Anthropic API 로 직접 세션을 띄우므로 그 필터링과
무관하게 항상 동작한다. 응답은 동기로 오지 않으므로, 세션이 끝나면 미리 정해둔
GitHub 이슈(메일박스)에 댓글로 결과를 남기게 하고 그 댓글을 폴링해서 받는다.
"""

from __future__ import annotations

import time
from typing import Callable, Optional

import requests


class RoutineFireError(RuntimeError):
    """/fire 호출이 성공(2xx)하지 못했을 때 발생."""


class RoutineBridgeClient:
    """Routines API 호출 + GitHub 이슈 댓글 폴링을 담당하는 얇은 래퍼."""

    def __init__(
        self,
        fire_url: str,
        bearer_token: str,
        github_token: str,
        beta_header: str,
        *,
        http: Optional[requests.Session] = None,
        sleep: Callable[[float], None] = time.sleep,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        # http 주입은 테스트에서 목 대체용.
        self._http = http or requests.Session()
        self._fire_url = fire_url
        self._bearer_token = bearer_token
        self._github_token = github_token
        self._beta_header = beta_header
        self._sleep = sleep
        self._monotonic = monotonic

    def fire(self, text: str) -> dict:
        """Routines API 트리거를 호출해 새 Claude Code 세션을 시작시킨다.

        반환: {"claude_code_session_id": ..., "claude_code_session_url": ...}
        """
        response = self._http.post(
            self._fire_url,
            headers={
                "Authorization": f"Bearer {self._bearer_token}",
                "anthropic-beta": self._beta_header,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json={"text": text},
            timeout=30,
        )
        if response.status_code >= 300:
            raise RoutineFireError(
                f"routine fire 실패 (status={response.status_code}): {response.text}"
            )
        return response.json()

    def wait_for_reply(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        after_iso: str,
        *,
        timeout: float,
        interval: float,
    ) -> dict:
        """메일박스 이슈에 after_iso 시각 이후 달린 첫 댓글을 답변으로 받아온다.

        반환: {"id": ..., "body": ..., "created_at": ...}. timeout 초과 시 TimeoutError.
        """
        deadline = self._monotonic() + timeout

        while True:
            reply = self._find_reply(owner, repo, issue_number, after_iso)
            if reply is not None:
                return reply
            if self._monotonic() >= deadline:
                raise TimeoutError(
                    f"{timeout:.0f}초 안에 이슈 #{issue_number}에 답변 댓글이 "
                    f"달리지 않았습니다 ({owner}/{repo})."
                )
            self._sleep(interval)

    def _find_reply(
        self, owner: str, repo: str, issue_number: int, after_iso: str
    ) -> Optional[dict]:
        response = self._http.get(
            f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments",
            headers={
                "Authorization": f"Bearer {self._github_token}",
                "Accept": "application/vnd.github+json",
            },
            params={"since": after_iso},
            timeout=30,
        )
        response.raise_for_status()
        comments = response.json()
        if not comments:
            return None
        first = comments[0]
        return {
            "id": first["id"],
            "body": first["body"],
            "created_at": first["created_at"],
        }
