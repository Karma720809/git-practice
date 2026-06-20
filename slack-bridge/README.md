# slack-bridge

외부 에이전트(OpenClaw 등)가 **봇↔봇 DM 없이** Slack에 연결된 Claude에게 자료를 주고
코멘트를 받아오게 해 주는 파이썬 브릿지.

## 왜 이렇게?

봇↔봇 직접 DM은 막혀 있습니다:

- 과거 DM 채널 참조값(`D0B72JQ09PV`)은 현재 유효하지 않음
- 봇↔봇 DM은 사전에 열린 합의 채널 + 상대 봇의 `im:open` 허용이 필요 → 미충족
- user id 직접 지정(`U0B6TG36A3Z`)도 `channel_not_found`로 실패

그래서 DM 대신 **공용 채널 + 멘션** 경로를 씁니다. 채널에 메시지를 올리는 데에는
열린 IM이 필요 없으므로 `channel_not_found` 문제가 근본적으로 사라집니다.

```
에이전트 → [slack-bridge] → chat.postMessage(공용채널, "<@Claude> 자료...")
                          ← conversations.replies 폴링 ← Claude 스레드 답글
```

## 동작 방식

1. `post_material` — 자료 앞에 `<@CLAUDE_USER_ID>` 멘션을 붙여 공용 채널에 게시.
   게시된 메시지가 대화 스레드의 루트가 됩니다.
2. `wait_for_reply` — `conversations.replies`로 스레드를 폴링하며, 요청 메시지보다
   나중에(`ts > request_ts`) 올라온 **Claude의 첫 답글**을 찾습니다.
3. 답글 본문을 에이전트에게 반환합니다.

`thread_ts`를 다시 넘기면 같은 스레드에서 후속 대화를 이어갈 수 있습니다.

## 설치

```bash
cd slack-bridge
pip install -r requirements.txt
```

## Slack 앱 설정

브릿지가 사용할 Slack 앱(봇)에 다음 Bot Token Scope를 부여하세요:

- `chat:write` — 채널에 메시지 게시
- `channels:history`, `channels:read` — 공용 채널 답글 폴링
- (비공개 채널을 쓸 경우) `groups:history`, `groups:read`

그다음:

1. 공용 채널을 하나 만들고, **브릿지 봇과 Slack Claude 봇을 둘 다 초대**합니다.
   (둘 다 채널 멤버여야 멘션과 응답이 동작합니다.)
2. 채널 ID(`C...`)와 Slack Claude의 user id를 확인합니다.
3. `.env.example`를 `.env`로 복사하고 값을 채웁니다.

```bash
cp .env.example .env
# SLACK_BOT_TOKEN, BRIDGE_CHANNEL_ID 등을 채우세요
```

> `.env`와 토큰은 절대 커밋하지 마세요(`.gitignore`에 포함).

## 사용법

### CLI

```bash
# 파일로 자료 전달
python -m slack_bridge ask --file material.md

# 표준입력
echo "이 함수 리뷰해줘: def f(): ..." | python -m slack_bridge ask --stdin

# 인라인 텍스트 + 전체 결과 JSON 출력
python -m slack_bridge ask --text "설계안 검토 부탁" --json

# 기존 스레드에서 후속 대화 이어가기
python -m slack_bridge ask --stdin --thread 1780220158.511089
```

기본 출력은 Claude 답글 본문만 stdout으로 내보냅니다. `--json`은 다음을 출력합니다:

```json
{
  "thread_ts": "1780220158.511089",
  "request_ts": "1780220158.511089",
  "reply_ts": "1780220170.000100",
  "reply": "코멘트 본문..."
}
```

종료 코드: `0` 성공, `2` 설정 오류, `3` 답글 시간 초과.

### 파이썬 라이브러리

```python
from slack_bridge import ask

result = ask("이 PR 설계 검토해줘:\n\n...")
print(result["reply"])

# 같은 스레드로 후속 질문
follow_up = ask("그럼 보안 측면은?", thread_ts=result["thread_ts"])
```

## 테스트

```bash
cd slack-bridge
python -m pytest
```

테스트는 `slack_sdk.WebClient`를 가짜로 대체해 실제 Slack 호출 없이
게시 멘션·답글 폴링·타임아웃·설정 로딩을 검증합니다.

## 환경변수

| 변수 | 필수 | 기본값 | 설명 |
|------|------|--------|------|
| `SLACK_BOT_TOKEN` | ✅ | — | 브릿지 봇 OAuth 토큰(`xoxb-...`) |
| `BRIDGE_CHANNEL_ID` | ✅ | — | 자료를 올릴 공용 채널 ID |
| `CLAUDE_USER_ID` | | `U0B6TG36A3Z` | 멘션할 Slack Claude user id |
| `REPLY_TIMEOUT_SEC` | | `180` | 답글 대기 최대 시간(초) |
| `POLL_INTERVAL_SEC` | | `3` | 폴링 주기(초) |
