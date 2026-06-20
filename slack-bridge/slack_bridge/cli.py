"""CLI 엔트리포인트.

OpenClaw 에이전트가 서브프로세스로 호출하거나, 사람이 직접 쓸 수 있다.

    python -m slack_bridge ask --file material.md
    echo "이 함수 리뷰해줘" | python -m slack_bridge ask --stdin
    python -m slack_bridge ask --stdin --thread 1780220158.511089 --json
"""

from __future__ import annotations

import argparse
import json
import sys

from .bridge import ask
from .config import ConfigError


def _read_material(args: argparse.Namespace) -> str:
    if args.file:
        with open(args.file, "r", encoding="utf-8") as fh:
            return fh.read()
    if args.stdin:
        return sys.stdin.read()
    if args.text is not None:
        return args.text
    raise SystemExit("자료 입력이 없습니다. --file / --stdin / --text 중 하나를 쓰세요.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="slack_bridge",
        description="공용 채널 + 멘션으로 Slack Claude에게 자료를 주고 코멘트를 받는다.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    ask_p = sub.add_parser("ask", help="자료를 게시하고 Claude 답글을 받는다.")
    src = ask_p.add_mutually_exclusive_group()
    src.add_argument("--file", help="자료를 읽을 파일 경로")
    src.add_argument("--stdin", action="store_true", help="표준입력에서 자료 읽기")
    src.add_argument("--text", help="자료를 인라인 문자열로 전달")
    ask_p.add_argument(
        "--thread", dest="thread_ts", help="기존 스레드 ts(후속 대화 이어가기)"
    )
    ask_p.add_argument(
        "--json", action="store_true", help="결과 전체를 JSON 으로 출력"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "ask":
        material = _read_material(args)
        try:
            result = ask(material, thread_ts=args.thread_ts)
        except ConfigError as exc:
            print(f"[설정 오류] {exc}", file=sys.stderr)
            return 2
        except TimeoutError as exc:
            print(f"[시간 초과] {exc}", file=sys.stderr)
            return 3

        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(result["reply"])
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
