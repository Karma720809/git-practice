# routine-bridge

외부 에이전트(OpenClaw 등)가 **Slack 게이트웨이의 봇 메시지 필터링을 거치지 않고**
Claude Code 세션을 직접 깨워 자료를 주고 결과를 받아오게 해 주는 파이썬 브릿지.

## 왜 Slack 대신 이걸 쓰나

Slack 멘션 트리거(`slack-bridge`)는 OpenClaw 같은 봇이 채널에 `<@Claude>`를
멘션해도, 게이트웨이가 **봇 발신 메시지(`bot_id` 있는 이벤트)를 필터링**하도록
구성돼 있어서 트리거가 발동하지 않을 위험이 있다(봇↔봇 무한루프 방지용 안전장치).

Claude Code on the web의 **Routines API 트리거**는 Anthropic API로 바로
`POST`해서 새 세션을 띄우는 방식이라 그 게이트웨이/필터링과 완전히 분리돼 있다.
다만 `/fire`는 비동기라 응답을 바로 안 주므로, 세션이 끝나면 GitHub의 고정된
"메일박스" 이슈에 댓글로 결과를 남기게 하고, 이 브릿지가 그 댓글을 폴링한다.

```
OpenClaw → POST /fire (text) → 새 Claude Code 세션 시작
                                      │
                                      ▼
                         세션이 작업 후 메일박스 이슈에 댓글
                                      │
routine-bridge ← GET issues/{n}/comments (폴링) ←┘
```

## 설정 단계

### 1. claude.ai에서 Routine 만들기 (claude.ai/code/routines)

1. **New routine** 클릭
2. **프롬프트** 작성 — 예시:

   ```
   다음은 외부 에이전트(OpenClaw)가 보낸 요청이다: {{text}}

   이 요청을 처리한 뒤, 결과를 karma720809/git-practice 리포의
   이슈 #2 에 댓글로 남겨라. (예: `gh issue comment 2 --repo karma720809/git-practice --body "..."`)
   댓글 본문에는 결과만 깔끔하게 적고, 이 지시문이나 메타 설명은 포함하지 마라.
   ```

3. **리포지토리**: `karma720809/git-practice` 선택
4. **트리거**: **API** 선택 → 저장
5. 저장 후 모달에서 **URL과 bearer 토큰**을 확인하고 토큰을 안전한 곳에 저장
   (토큰은 한 번만 표시되고 다시 못 봄)
6. Connectors 탭에서 GitHub 관련 connector가 필요하면 추가 (보통 리포 클론 시
   기본 `git`/`gh` 인증이 따라오므로 별도 추가 없이도 `gh issue comment`가 될
   수 있음 — 안 되면 GitHub connector를 추가)

### 2. GitHub 메일박스 이슈

이미 만들어져 있음: **karma720809/git-practice#2**
("[mailbox] OpenClaw ↔ Claude Routine 브릿지"). 닫거나 제목을 바꾸지 말 것.

### 3. 이 패키지 설치 및 설정

```bash
cd routine-bridge
pip install -r requirements.txt
cp .env.example .env
# ROUTINE_FIRE_URL, ROUTINE_BEARER_TOKEN, GITHUB_TOKEN, MAILBOX_ISSUE_NUMBER 채우기
```

`GITHUB_TOKEN`은 해당 이슈를 읽을 수 있는 PAT(`repo` 또는 `public_repo` 스코프)면 된다.

## 사용법

### CLI

```bash
python -m routine_bridge ask --file material.md
echo "이 함수 리뷰해줘: def f(): ..." | python -m routine_bridge ask --stdin
python -m routine_bridge ask --text "설계안 검토 부탁" --json
```

종료 코드: `0` 성공, `2` 설정 오류, `3` 답글 시간 초과.

### 파이썬 라이브러리

```python
from routine_bridge import ask

result = ask("이 PR 설계 검토해줘:\n\n...")
print(result["reply"])
print(result["session_url"])  # 실행된 세션을 직접 확인할 수 있는 링크
```

## 테스트

```bash
cd routine-bridge
python -m pytest
```

`requests.Session`을 가짜로 대체해 실제 네트워크 호출 없이 fire 호출, 댓글
폴링, 타임아웃, 설정 로딩을 검증한다.

## 환경변수

| 변수 | 필수 | 기본값 | 설명 |
|------|------|--------|------|
| `ROUTINE_FIRE_URL` | ✅ | — | Routine의 API 트리거 `/fire` URL |
| `ROUTINE_BEARER_TOKEN` | ✅ | — | 같은 화면에서 발급되는 bearer 토큰 |
| `GITHUB_TOKEN` | ✅ | — | 메일박스 이슈 댓글을 읽을 PAT |
| `MAILBOX_ISSUE_NUMBER` | ✅ | — | 메일박스로 쓸 이슈 번호 (현재 `2`) |
| `GITHUB_OWNER` | | `karma720809` | 메일박스 리포 소유자 |
| `GITHUB_REPO` | | `git-practice` | 메일박스 리포 이름 |
| `REPLY_TIMEOUT_SEC` | | `600` | 답글 대기 최대 시간(초) |
| `POLL_INTERVAL_SEC` | | `5` | 폴링 주기(초) |
