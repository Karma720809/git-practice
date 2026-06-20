"""WebClient 목으로 게시+폴링 로직을 검증한다 (실제 Slack 호출 없음)."""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from slack_bridge.bridge import ask  # noqa: E402
from slack_bridge.client import SlackBridgeClient, _build_mention_text  # noqa: E402
from slack_bridge.config import BridgeConfig, ConfigError  # noqa: E402

CLAUDE = "U0B6TG36A3Z"


class FakeWebClient:
    """chat_postMessage / conversations_replies 만 흉내내는 가짜."""

    def __init__(self, replies_sequence):
        # replies_sequence: conversations_replies 가 호출될 때마다 순서대로 반환할
        # messages 리스트들의 시퀀스.
        self._replies_sequence = list(replies_sequence)
        self._reply_calls = 0
        self.posted = []
        self._ts_counter = 1000.0

    def chat_postMessage(self, **kwargs):
        self._ts_counter += 1
        ts = f"{self._ts_counter:.6f}"
        self.posted.append({"ts": ts, **kwargs})
        return {"ts": ts}

    def conversations_replies(self, channel, ts):
        idx = min(self._reply_calls, len(self._replies_sequence) - 1)
        self._reply_calls += 1
        return {"messages": self._replies_sequence[idx]}


def _client(fake, **kwargs):
    return SlackBridgeClient(
        token="x",
        claude_user_id=CLAUDE,
        web_client=fake,
        sleep=lambda _s: None,
        monotonic=kwargs.get("monotonic", _fake_clock()),
    )


def _fake_clock(step=1.0):
    state = {"t": 0.0}

    def now():
        state["t"] += step
        return state["t"]

    return now


def test_mention_prefix():
    assert _build_mention_text(CLAUDE, "hello") == f"<@{CLAUDE}> hello"


def test_post_material_adds_mention_and_returns_ts():
    fake = FakeWebClient([[]])
    client = _client(fake)
    ts = client.post_material("C1", "리뷰 부탁")
    assert ts == fake.posted[0]["ts"]
    assert fake.posted[0]["text"] == f"<@{CLAUDE}> 리뷰 부탁"
    assert "thread_ts" not in fake.posted[0]


def test_post_material_uses_thread_ts_when_given():
    fake = FakeWebClient([[]])
    client = _client(fake)
    client.post_material("C1", "후속", thread_ts="999.0")
    assert fake.posted[0]["thread_ts"] == "999.0"


def test_wait_for_reply_returns_first_claude_reply_after_request():
    # 1st poll: 답글 없음 -> 2nd poll: Claude 답글 도착.
    messages_round2 = [
        {"user": "U_OTHER", "ts": "1001.5", "text": "남이 쓴 글"},
        {"user": CLAUDE, "ts": "1001.7", "text": "여기 코멘트입니다"},
    ]
    fake = FakeWebClient([[], messages_round2])
    client = _client(fake)
    reply = client.wait_for_reply(
        "C1", "1001.0", "1001.0", timeout=100, interval=1
    )
    assert reply == {"ts": "1001.7", "text": "여기 코멘트입니다"}


def test_wait_for_reply_ignores_messages_at_or_before_request():
    # Claude 의 오래된 메시지(after 이하)는 무시해야 한다.
    messages = [
        {"user": CLAUDE, "ts": "1000.0", "text": "예전 답글"},  # after == 1001.0 이하
        {"user": CLAUDE, "ts": "1002.0", "text": "새 답글"},
    ]
    fake = FakeWebClient([messages])
    client = _client(fake)
    reply = client.wait_for_reply(
        "C1", "1001.0", "1001.0", timeout=100, interval=1
    )
    assert reply["text"] == "새 답글"


def test_wait_for_reply_times_out():
    fake = FakeWebClient([[]])  # 영원히 빈 답글
    client = _client(fake)
    with pytest.raises(TimeoutError):
        client.wait_for_reply("C1", "1001.0", "1001.0", timeout=2, interval=1)


def test_ask_orchestrates_post_then_reply():
    fake = FakeWebClient(
        [
            [],  # 첫 폴링: 아직 없음
            None,  # 자리표시자 (아래에서 교체)
        ]
    )
    # 게시 후 ts 를 알아야 답글 ts 를 그보다 크게 만들 수 있으므로 동적 구성.
    config = BridgeConfig(
        bot_token="x",
        channel_id="C1",
        claude_user_id=CLAUDE,
        reply_timeout_sec=100,
        poll_interval_sec=1,
    )

    # 게시 시 ts 는 1001.000000 이 된다(_ts_counter 초기 1000 +1). 그보다 큰 답글.
    fake._replies_sequence = [
        [],
        [{"user": CLAUDE, "ts": "1001.500000", "text": "오케이 코멘트"}],
    ]
    client = _client(fake)
    result = ask("자료입니다", config=config, client=client)

    assert result["reply"] == "오케이 코멘트"
    assert result["thread_ts"] == result["request_ts"] == "1001.000000"
    assert result["reply_ts"] == "1001.500000"
    assert fake.posted[0]["text"] == f"<@{CLAUDE}> 자료입니다"


def test_config_from_env_requires_token_and_channel(monkeypatch):
    monkeypatch.delenv("SLACK_BOT_TOKEN", raising=False)
    monkeypatch.delenv("BRIDGE_CHANNEL_ID", raising=False)
    with pytest.raises(ConfigError):
        BridgeConfig.from_env()


def test_config_from_env_reads_values(monkeypatch):
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-abc")
    monkeypatch.setenv("BRIDGE_CHANNEL_ID", "C999")
    monkeypatch.setenv("REPLY_TIMEOUT_SEC", "42")
    monkeypatch.delenv("CLAUDE_USER_ID", raising=False)
    cfg = BridgeConfig.from_env()
    assert cfg.bot_token == "xoxb-abc"
    assert cfg.channel_id == "C999"
    assert cfg.reply_timeout_sec == 42.0
    assert cfg.claude_user_id == CLAUDE
