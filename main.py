"""
weAID - 생활지능파트너
메인 진입점

실행 방법:
    python main.py              # 웹 서버 실행 (기본)
    python main.py --cli        # CLI 모드 (터미널 대화)
    python main.py --host 0.0.0.0 --port 8001
"""
import sys
import asyncio
import argparse
import uvicorn


def run_server(host: str = "0.0.0.0", port: int = 8001, reload: bool = False):
    """FastAPI 웹 서버를 실행합니다."""
    print(f"""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║   🏠  weAID - 생활지능파트너                             ║
║        Living Intelligence AI Partner                    ║
║                                                          ║
║   📚 과외선생님  💪 홈트코치  👨‍🍳 요리사                 ║
║   ⚖️ 법률변호사  🧘 명상상담사                           ║
║                                                          ║
║   ⚡ RDF/OWL2 Ontology (S-P-O Triple)                   ║
║   🤖 Agentic AI (Claude API)                            ║
║                                                          ║
║   🌐 http://{host}:{port}                               ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """)

    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


async def run_cli():
    """CLI 모드: 터미널에서 직접 weAID와 대화합니다."""
    from agents.orchestrator import orchestrator
    from knowledge.ontology_manager import ontology_manager

    print("""
╔══════════════════════════════════════════════════════════╗
║          weAID CLI - 생활지능파트너                      ║
╚══════════════════════════════════════════════════════════╝
    """)

    # 온톨로지 로드
    loaded = ontology_manager.load()
    if loaded:
        print(f"✅ 온톨로지 로드: {ontology_manager.get_triple_count()}개 S-P-O 트리플")
    else:
        print("⚠️ 온톨로지 없이 실행 중")

    print("\n페르소나 목록:")
    for p in orchestrator.get_all_personas_info():
        print(f"  {p['emoji']} {p['role']} ({p['agent_id']})")

    print("\n명령:")
    print("  /quit       - 종료")
    print("  /tutor      - 과외선생님 강제 선택")
    print("  /trainer    - 홈트코치 강제 선택")
    print("  /chef       - 요리사 강제 선택")
    print("  /lawyer     - 법률변호사 강제 선택")
    print("  /therapist  - 명상상담사 강제 선택")
    print("  /auto       - 자동 라우팅")
    print("  /clear      - 대화 초기화\n")

    session_id = "cli_session"
    force_persona = None

    while True:
        try:
            user_input = input("나 > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nweAID를 종료합니다. 감사합니다!")
            break

        if not user_input:
            continue

        # 명령어 처리
        if user_input.startswith("/"):
            cmd = user_input.lower()
            if cmd == "/quit" or cmd == "/exit":
                print("weAID를 종료합니다. 감사합니다!")
                break
            elif cmd in ("/tutor", "/trainer", "/chef", "/lawyer", "/therapist"):
                force_persona = cmd[1:]
                print(f"  ✅ {force_persona} 페르소나로 전환됩니다.")
            elif cmd == "/auto":
                force_persona = None
                print("  ✅ 자동 라우팅으로 전환됩니다.")
            elif cmd == "/clear":
                orchestrator.clear_session(session_id)
                print("  ✅ 대화가 초기화되었습니다.")
            else:
                print(f"  ⚠️ 알 수 없는 명령어: {user_input}")
            continue

        # AI 처리
        print("  🔄 처리 중...")
        result = await orchestrator.process(
            user_text=user_input,
            session_id=session_id,
            force_persona=force_persona,
        )

        persona_label = f"{result['persona_emoji']} {result['persona_role']}"
        conf = int(result['confidence'] * 100)
        print(f"\n{persona_label} [{conf}%] > {result['response']}\n")


def main():
    parser = argparse.ArgumentParser(
        description="weAID - 생활지능파트너",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python main.py                    # 웹 서버 실행 (기본)
  python main.py --cli              # CLI 모드
  python main.py --port 9000        # 포트 변경
  python main.py --reload           # 개발 모드 (자동 재시작)
        """,
    )
    parser.add_argument("--cli", action="store_true", help="CLI 모드로 실행")
    parser.add_argument("--host", default="0.0.0.0", help="서버 호스트 (기본: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8001, help="서버 포트 (기본: 8001)")
    parser.add_argument("--reload", action="store_true", help="개발 모드 (파일 변경 시 자동 재시작)")

    args = parser.parse_args()

    if args.cli:
        asyncio.run(run_cli())
    else:
        run_server(host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
