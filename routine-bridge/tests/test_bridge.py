"""requests.Session 목으로 fire+폴링 로직을 검증한다 (실제 네트워크 호출 없음)."""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from routine_bridge.bridge import ask  # noqa: E402
from routine_bridge.client import RoutineBridgeClient, RoutineFireError  # noqa: E402
from routine_bridge.config import ConfigError, RoutineBridgeConfig  # noqa: E402


class _FakeResponse:
    def __init__(self, status_code=200, json_body=None, text=""):
        self.status_code = status_code
        self._json_body = json_body if json_body is not None else {}
        self.text = text

    def json(self):
        return self._json_body

    def raise_for_status(self):
        if self.status_code >= 300:
            raise RuntimeError(f"http {self.status_code}")


class FakeHttp:
    """post(/fire) 1회 + get(comments) 여러 번을 흉내내는 가짜."""

    def __init__(self, fire_response, comments_sequence):
        self._fire_response = fire_response
        self._comments_sequence = list(comments_sequence)
        self._comments_calls = 0
        self.posted = []
        self.got = []

    def post(self, url, **kwargs):
        self.posted.append({"url": url, **kwargs})
        return self._fire_response

    def get(self, url, **kwargs):
        self.got.append({"url": url, **kwargs})
        idx = min(self._comments_calls, len(self._comments_sequence) - 1)
        self._comments_calls += 1
        return _FakeResponse(json_body=self._comments_sequence[idx])


def _client(fake, **kwargs):
    return RoutineBridgeClient(
        fire_url="https://api.example/fire",
        bearer_token="tok",
        github_token="gh",
        beta_header="beta-x",
        http=fake,
        sleep=lambda _s: None,
        monotonic=kwargs.get("monotonic", _fake_clock()),
    )


def _fake_clock(step=1.0):
    state = {"t": 0.0}

    def now():
        state["t"] += step
        return state["t"]

    return now


def test_fire_sends_bearer_and_beta_headers_and_text():
    fake = FakeHttp(
        _FakeResponse(
            json_body={
                "claude_code_session_id": "s1",
                "claude_code_session_url": "https://claude.ai/code/s1",
            }
        ),
        [[]],
    )
    client = _client(fake)
    result = client.fire("자료입니다")

    assert result["claude_code_session_id"] == "s1"
    sent = fake.posted[0]
    assert sent["headers"]["Authorization"] == "Bearer tok"
    assert sent["headers"]["anthropic-beta"] == "beta-x"
    assert sent["json"] == {"text": "자료입니다"}


def test_fire_raises_on_non_2xx():
    fake = FakeHttp(_FakeResponse(status_code=401, text="unauthorized"), [[]])
    client = _client(fake)
    with pytest.raises(RoutineFireError):
        client.fire("자료")


def test_wait_for_reply_returns_first_comment_after_polling():
    fake = FakeHttp(
        _FakeResponse(json_body={}),
        [
            [],  # 1차 폴링: 댓글 없음
            [{"id": 42, "body": "여기 코멘트입니다", "created_at": "2026-06-21T00:01:00Z"}],
        ],
    )
    client = _client(fake)
    reply = client.wait_for_reply(
        "o", "r", 2, "2026-06-21T00:00:00Z", timeout=100, interval=1
    )
    assert reply == {
        "id": 42,
        "body": "여기 코멘트입니다",
        "created_at": "2026-06-21T00:01:00Z",
    }
    # since 파라미터로 폴링 기준점을 넘겼는지 확인.
    assert fake.got[0]["params"]["since"] == "2026-06-21T00:00:00Z"


def test_wait_for_reply_times_out():
    fake = FakeHttp(_FakeResponse(json_body={}), [[]])  # 영원히 빈 댓글
    client = _client(fake)
    with pytest.raises(TimeoutError):
        client.wait_for_reply("o", "r", 2, "2026-06-21T00:00:00Z", timeout=2, interval=1)


def test_ask_orchestrates_fire_then_reply():
    fake = FakeHttp(
        _FakeResponse(
            json_body={
                "claude_code_session_id": "s9",
                "claude_code_session_url": "https://claude.ai/code/s9",
            }
        ),
        [
            [],
            [{"id": 7, "body": "오케이 코멘트", "created_at": "2026-06-21T00:05:00Z"}],
        ],
    )
    config = RoutineBridgeConfig(
        fire_url="https://api.example/fire",
        bearer_token="tok",
        github_token="gh",
        mailbox_issue_number=2,
        reply_timeout_sec=100,
        poll_interval_sec=1,
    )
    client = _client(fake)
    result = ask("자료입니다", config=config, client=client)

    assert result["session_id"] == "s9"
    assert result["session_url"] == "https://claude.ai/code/s9"
    assert result["reply"] == "오케이 코멘트"
    assert result["reply_comment_id"] == 7
    assert fake.posted[0]["json"] == {"text": "자료입니다"}


def test_config_from_env_requires_all_fields(monkeypatch):
    for name in (
        "ROUTINE_FIRE_URL",
        "ROUTINE_BEARER_TOKEN",
        "GITHUB_TOKEN",
        "MAILBOX_ISSUE_NUMBER",
    ):
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(ConfigError):
        RoutineBridgeConfig.from_env()


def test_config_from_env_reads_values(monkeypatch):
    monkeypatch.setenv("ROUTINE_FIRE_URL", "https://api.example/fire")
    monkeypatch.setenv("ROUTINE_BEARER_TOKEN", "tok")
    monkeypatch.setenv("GITHUB_TOKEN", "gh")
    monkeypatch.setenv("MAILBOX_ISSUE_NUMBER", "2")
    monkeypatch.setenv("REPLY_TIMEOUT_SEC", "42")
    monkeypatch.delenv("GITHUB_OWNER", raising=False)
    monkeypatch.delenv("GITHUB_REPO", raising=False)

    cfg = RoutineBridgeConfig.from_env()
    assert cfg.fire_url == "https://api.example/fire"
    assert cfg.mailbox_issue_number == 2
    assert cfg.reply_timeout_sec == 42.0
    assert cfg.github_owner == "karma720809"
    assert cfg.github_repo == "git-practice"


def test_config_from_env_rejects_non_integer_issue_number(monkeypatch):
    monkeypatch.setenv("ROUTINE_FIRE_URL", "https://api.example/fire")
    monkeypatch.setenv("ROUTINE_BEARER_TOKEN", "tok")
    monkeypatch.setenv("GITHUB_TOKEN", "gh")
    monkeypatch.setenv("MAILBOX_ISSUE_NUMBER", "not-a-number")
    with pytest.raises(ConfigError):
        RoutineBridgeConfig.from_env()
