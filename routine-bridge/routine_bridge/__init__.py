"""Routines API 트리거 + GitHub 메일박스 브릿지.

Slack 멘션 트리거는 게이트웨이의 봇 발신 메시지 필터링에 걸려 외부 에이전트
(OpenClaw 등)의 호출이 묻힐 수 있다. Routines 의 API 트리거(/fire)는 Anthropic
API 로 직접 세션을 띄우므로 그 문제와 무관하게 동작한다. 결과는 동기 응답으로
오지 않으므로, Routine 의 프롬프트가 GitHub 메일박스 이슈에 댓글로 답을 남기게
하고 이 모듈이 그 댓글을 폴링해서 가져온다.

기본 사용:

    from routine_bridge import ask
    result = ask("이 함수 리뷰해줘:\\n\\ndef f(): ...")
    print(result["reply"])
"""

from .bridge import ask
from .client import RoutineBridgeClient
from .config import RoutineBridgeConfig

__all__ = ["ask", "RoutineBridgeClient", "RoutineBridgeConfig"]
