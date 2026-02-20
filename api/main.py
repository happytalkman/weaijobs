"""
weAID FastAPI Backend
생활지능파트너 REST API + WebSocket 서버

Endpoints:
    GET  /              - 웹 UI 홈페이지
    GET  /api/personas  - 페르소나 목록
    GET  /api/ontology  - 온톨로지 정보
    POST /api/chat      - 텍스트 채팅
    POST /api/voice     - 음성 입력 처리
    GET  /api/tts       - 텍스트 → 음성 변환
    WS   /ws/{session}  - WebSocket 실시간 채팅
"""
import uuid
import asyncio
from typing import Optional
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from config.settings import settings
from agents.orchestrator import orchestrator
from knowledge.ontology_manager import ontology_manager
from voice.speech_to_text import stt
from voice.text_to_speech import tts

BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI(
    title="weAID API",
    description="생활지능파트너 weAID REST API",
    version=settings.app_version,
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일
static_dir = BASE_DIR / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# =============================================================================
# Request / Response Models
# =============================================================================

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    persona: Optional[str] = None  # 페르소나 강제 지정


class ChatResponse(BaseModel):
    response: str
    persona: str
    persona_name: str
    persona_role: str
    persona_emoji: str
    persona_color: str
    confidence: float
    intent: str
    session_id: str


class TTSRequest(BaseModel):
    text: str
    session_id: Optional[str] = None


# =============================================================================
# Startup
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 온톨로지를 로드합니다."""
    print("🚀 weAID 서버 시작...")
    loaded = ontology_manager.load()
    if loaded:
        triple_count = ontology_manager.get_triple_count()
        print(f"✅ 온톨로지 로드 완료: {triple_count}개 S-P-O 트리플")
        personas = ontology_manager.get_all_personas()
        print(f"📋 페르소나: {len(personas)}개 로드됨")
        for p in personas:
            print(f"   {p['emoji']} {p['role']} ({p['agent_id']})")
    else:
        print("⚠️ 온톨로지 로드 실패 - 기본 설정으로 실행")
    print(f"🌐 서버 실행 중: http://{settings.host}:{settings.port}")


# =============================================================================
# Web UI
# =============================================================================

@app.get("/", response_class=HTMLResponse)
async def get_home():
    """메인 웹 UI를 제공합니다."""
    ui_path = BASE_DIR / "ui" / "index.html"
    if ui_path.exists():
        return ui_path.read_text(encoding="utf-8")
    return HTMLResponse("<h1>weAID UI를 찾을 수 없습니다. ui/index.html을 확인하세요.</h1>")


# =============================================================================
# API Endpoints
# =============================================================================

@app.get("/api/health")
async def health_check():
    """서버 상태 확인."""
    return {
        "status": "healthy",
        "name": settings.app_name,
        "subtitle": settings.app_subtitle,
        "version": settings.app_version,
        "ontology_triples": ontology_manager.get_triple_count(),
    }


@app.get("/api/personas")
async def get_personas():
    """모든 페르소나 목록을 반환합니다."""
    # 온톨로지에서 페르소나 정보 조회 (SPARQL S-P-O)
    ontology_personas = ontology_manager.get_all_personas()
    agent_info = orchestrator.get_all_personas_info()

    # 온톨로지 정보와 에이전트 정보 병합
    result = []
    for agent in agent_info:
        persona_data = {**agent}
        # 온톨로지에서 추가 정보 보강
        for op in ontology_personas:
            if op.get("role") == agent.get("role"):
                persona_data["domain"] = ontology_manager.get_persona_domain(op["uri"])
                persona_data["ontology_keywords"] = ontology_manager.get_persona_keywords(op["uri"])[:5]
                break
        result.append(persona_data)

    return {"personas": result, "count": len(result)}


@app.get("/api/ontology")
async def get_ontology_info():
    """온톨로지 구조 정보를 반환합니다 (Palantir Foundry 스타일)."""
    personas = ontology_manager.get_all_personas()
    system_info = ontology_manager.get_system_info()
    triple_count = ontology_manager.get_triple_count()

    # 각 페르소나의 도메인과 기능 조회
    detailed_personas = []
    for p in personas:
        domain = ontology_manager.get_persona_domain(p["uri"])
        capabilities = ontology_manager.get_persona_capabilities(p["uri"])
        keywords = ontology_manager.get_persona_keywords(p["uri"])
        detailed_personas.append({
            **p,
            "domain": domain,
            "capabilities": capabilities,
            "keywords": keywords,
        })

    return {
        "ontology": {
            "namespace": "http://weaid.ai/ontology#",
            "format": "RDF/OWL2",
            "style": "Palantir Foundry Ontology (S-P-O Triple)",
            "total_triples": triple_count,
        },
        "system": system_info,
        "object_types": [
            "AISystem", "Persona", "TutorPersona", "TrainerPersona",
            "ChefPersona", "LawyerPersona", "TherapistPersona",
            "User", "Session", "Command", "Domain", "KnowledgeItem",
            "Response", "Capability",
        ],
        "links": [
            "hasPersona", "belongsToDomain", "hasKnowledge",
            "initiates", "containsCommand", "processedBy",
            "generatesResponse", "hasCapability", "handlesIntent",
        ],
        "personas": detailed_personas,
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    텍스트 채팅 처리

    S-P-O 라우팅:
    1. SPARQL 키워드 매칭: ?persona weaid:hasKeyword ?keyword
    2. Claude tool_use 의도 분류
    3. Command --[processedBy]--> Persona
    """
    session_id = request.session_id or str(uuid.uuid4())

    if not request.message.strip():
        raise HTTPException(status_code=400, detail="메시지를 입력해주세요.")

    result = await orchestrator.process(
        user_text=request.message,
        session_id=session_id,
        force_persona=request.persona,
    )

    return ChatResponse(**result)


@app.post("/api/voice/transcribe")
async def transcribe_voice(audio: UploadFile = File(...)):
    """
    음성 파일을 텍스트로 변환합니다.
    """
    if not stt.is_available:
        raise HTTPException(
            status_code=503,
            detail="음성 인식 서비스를 사용할 수 없습니다. 브라우저 음성 인식을 사용하세요.",
        )

    audio_bytes = await audio.read()
    text = await stt.transcribe_audio_bytes(audio_bytes)

    if not text:
        raise HTTPException(status_code=422, detail="음성을 인식할 수 없습니다.")

    return {"text": text, "language": stt.language}


@app.post("/api/voice/chat")
async def voice_chat(
    audio: UploadFile = File(...),
    session_id: Optional[str] = Query(None),
    persona: Optional[str] = Query(None),
):
    """
    음성 입력 → STT → AI 처리 → TTS 응답 (올인원)
    """
    session_id = session_id or str(uuid.uuid4())

    # STT
    audio_bytes = await audio.read()
    text = await stt.transcribe_audio_bytes(audio_bytes)

    if not text:
        raise HTTPException(status_code=422, detail="음성을 인식할 수 없습니다.")

    # AI 처리
    result = await orchestrator.process(
        user_text=text,
        session_id=session_id,
        force_persona=persona,
    )

    # TTS
    audio_base64 = await tts.synthesize_base64(result["response"])

    return {
        **result,
        "input_text": text,
        "audio_base64": audio_base64,
    }


@app.get("/api/tts")
async def text_to_speech_endpoint(text: str = Query(..., description="변환할 텍스트")):
    """텍스트를 음성으로 변환합니다 (MP3 스트리밍)."""
    if not tts.is_available:
        raise HTTPException(
            status_code=503,
            detail="TTS 서비스를 사용할 수 없습니다. 브라우저 TTS를 사용하세요.",
        )

    audio_bytes = await tts.synthesize(text)
    if not audio_bytes:
        raise HTTPException(status_code=500, detail="음성 생성에 실패했습니다.")

    return StreamingResponse(
        iter([audio_bytes]),
        media_type="audio/mpeg",
        headers={"Content-Disposition": "attachment; filename=response.mp3"},
    )


@app.get("/api/session/{session_id}/history")
async def get_session_history(session_id: str):
    """세션의 대화 기록을 반환합니다."""
    history = orchestrator.get_session_history(session_id)
    return {"session_id": session_id, "history": history, "count": len(history)}


@app.delete("/api/session/{session_id}")
async def clear_session(session_id: str):
    """세션을 초기화합니다."""
    orchestrator.clear_session(session_id)
    return {"message": f"세션 {session_id}이 초기화되었습니다."}


# =============================================================================
# WebSocket - 실시간 채팅
# =============================================================================

class ConnectionManager:
    def __init__(self):
        self.active: dict[str, WebSocket] = {}

    async def connect(self, ws: WebSocket, session_id: str):
        await ws.accept()
        self.active[session_id] = ws

    def disconnect(self, session_id: str):
        self.active.pop(session_id, None)

    async def send(self, session_id: str, data: dict):
        ws = self.active.get(session_id)
        if ws:
            await ws.send_json(data)


manager = ConnectionManager()


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket 실시간 채팅."""
    await manager.connect(websocket, session_id)
    try:
        # 연결 시 환영 메시지
        await manager.send(session_id, {
            "type": "connected",
            "session_id": session_id,
            "message": f"weAID에 연결되었습니다! 무엇이든 물어보세요.",
            "personas": orchestrator.get_all_personas_info(),
        })

        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "chat")

            if msg_type == "chat":
                user_text = data.get("message", "").strip()
                force_persona = data.get("persona")

                if not user_text:
                    continue

                # AI 처리
                result = await orchestrator.process(
                    user_text=user_text,
                    session_id=session_id,
                    force_persona=force_persona,
                )

                await manager.send(session_id, {
                    "type": "response",
                    **result,
                })

            elif msg_type == "clear":
                orchestrator.clear_session(session_id)
                await manager.send(session_id, {
                    "type": "cleared",
                    "message": "대화가 초기화되었습니다.",
                })

            elif msg_type == "ping":
                await manager.send(session_id, {"type": "pong"})

    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        print(f"[WebSocket] 오류: {e}")
        manager.disconnect(session_id)
