"""
weAID Orchestrator Agent
온톨로지 기반 의도 분류 및 페르소나 라우팅 오케스트레이터

Palantir Foundry 온톨로지 스타일:
  - SPARQL로 S-P-O 트리플 쿼리하여 적절한 페르소나를 선택
  - Claude tool_use로 의도 분류 수행
  - Agentic loop로 복잡한 요청 처리
"""
import json
import anthropic
from typing import Optional
from config.settings import settings
from knowledge.ontology_manager import ontology_manager
from .tutor_agent import TutorAgent
from .trainer_agent import TrainerAgent
from .chef_agent import ChefAgent
from .lawyer_agent import LawyerAgent
from .therapist_agent import TherapistAgent
from .base_agent import BaseAgent


class OrchestratorAgent:
    """
    weAID 오케스트레이터

    역할:
    1. 사용자 발화를 받아 온톨로지(SPARQL)로 키워드 매칭
    2. Claude tool_use로 의도를 정확히 분류
    3. 적절한 페르소나 에이전트로 라우팅
    4. 세션 및 대화 기록 관리

    S-P-O Routing:
      Command --[processedBy]--> [TutorAgent|TrainerAgent|ChefAgent|LawyerAgent|TherapistAgent]
    """

    # 페르소나 에이전트 레지스트리
    AGENTS: dict[str, BaseAgent] = {
        "tutor": TutorAgent(),
        "trainer": TrainerAgent(),
        "chef": ChefAgent(),
        "lawyer": LawyerAgent(),
        "therapist": TherapistAgent(),
    }

    # 온톨로지 agent_id -> 레지스트리 키 매핑
    AGENT_ID_MAP = {
        "tutoragent": "tutor",
        "traineragent": "trainer",
        "chefagent": "chef",
        "lawyeragent": "lawyer",
        "therapistagent": "therapist",
    }

    # Claude tool_use 라우팅 도구 정의
    ROUTING_TOOL = {
        "name": "route_to_persona",
        "description": """사용자의 발화를 분석하여 가장 적합한 weAID 페르소나를 선택합니다.

페르소나 선택 기준:
- tutor(과외선생님): 학습, 공부, 과목 질문, 수학/과학/영어/국어/역사, 숙제, 시험
- trainer(홈트레이닝코치): 운동, 다이어트, 건강, 체력, 근육, 스트레칭, 홈트, 칼로리
- chef(요리사): 요리, 레시피, 음식, 재료, 식단, 끓이기, 볶기, 굽기, 영양
- lawyer(가정법률변호사): 법률, 법, 권리, 계약, 임대, 이혼, 상속, 소비자, 노동, 분쟁
- therapist(명상심리상담사): 명상, 스트레스, 불안, 우울, 마음, 감정, 수면, 힘들다, 심리
""",
        "input_schema": {
            "type": "object",
            "properties": {
                "persona": {
                    "type": "string",
                    "enum": ["tutor", "trainer", "chef", "lawyer", "therapist"],
                    "description": "선택된 페르소나 ID",
                },
                "confidence": {
                    "type": "number",
                    "description": "선택 신뢰도 (0.0 ~ 1.0)",
                },
                "intent_summary": {
                    "type": "string",
                    "description": "사용자 의도 요약 (한국어)",
                },
                "reasoning": {
                    "type": "string",
                    "description": "이 페르소나를 선택한 이유",
                },
            },
            "required": ["persona", "confidence", "intent_summary"],
        },
    }

    def __init__(self):
        self._client: Optional[anthropic.Anthropic] = None
        self._sessions: dict[str, dict] = {}  # session_id -> session data
        self._ontology_loaded = False

    def _get_client(self) -> anthropic.Anthropic:
        if self._client is None:
            self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        return self._client

    def _ensure_ontology(self):
        """온톨로지가 로드되지 않은 경우 로드합니다."""
        if not self._ontology_loaded:
            self._ontology_loaded = ontology_manager.load()

    def _get_session(self, session_id: str) -> dict:
        """세션 데이터를 반환합니다 (없으면 생성)."""
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "session_id": session_id,
                "history": [],  # 전체 대화 기록
                "current_persona": None,
                "persona_histories": {k: [] for k in self.AGENTS.keys()},
                "command_count": 0,
            }
        return self._sessions[session_id]

    async def route_by_ontology(self, text: str) -> Optional[str]:
        """
        SPARQL 키워드 매칭으로 1차 라우팅을 수행합니다.
        온톨로지의 S-P-O 트리플:
          ?persona weaid:hasKeyword ?keyword
        """
        self._ensure_ontology()
        matched = ontology_manager.find_persona_by_keyword(text)
        if matched:
            top = matched[0]
            return self.AGENT_ID_MAP.get(top["agent_id"])
        return None

    async def route_by_claude(self, text: str, ontology_hint: Optional[str] = None) -> dict:
        """
        Claude tool_use로 정확한 의도 분류를 수행합니다.
        온톨로지 키워드 매칭 결과를 힌트로 활용합니다.
        """
        client = self._get_client()

        hint_text = ""
        if ontology_hint:
            agent = self.AGENTS.get(ontology_hint)
            if agent:
                hint_text = f"\n\n[온톨로지 1차 분류 결과: {agent.role}({ontology_hint}) - 참고용]"

        system = f"""당신은 weAID 생활지능파트너의 의도 분류 오케스트레이터입니다.
사용자의 발화를 분석하여 가장 적합한 페르소나를 선택해야 합니다.{hint_text}

반드시 route_to_persona 도구를 사용하여 응답하세요."""

        try:
            response = client.messages.create(
                model=settings.claude_model,
                max_tokens=512,
                system=system,
                messages=[{"role": "user", "content": text}],
                tools=[self.ROUTING_TOOL],
                tool_choice={"type": "any"},
            )

            for block in response.content:
                if block.type == "tool_use" and block.name == "route_to_persona":
                    return block.input

        except Exception as e:
            print(f"[Orchestrator] Claude 라우팅 오류: {e}")

        # fallback: 온톨로지 결과 또는 기본값
        return {
            "persona": ontology_hint or "therapist",
            "confidence": 0.5,
            "intent_summary": text[:100],
            "reasoning": "기본 라우팅",
        }

    async def process(
        self,
        user_text: str,
        session_id: str = "default",
        force_persona: Optional[str] = None,
    ) -> dict:
        """
        사용자 발화를 처리하고 응답을 반환합니다.

        Args:
            user_text: 사용자 입력 텍스트
            session_id: 세션 ID
            force_persona: 강제 페르소나 지정 (None이면 자동 라우팅)

        Returns:
            {
                "response": str,          # 응답 텍스트
                "persona": str,           # 사용된 페르소나 ID
                "persona_name": str,      # 페르소나 이름
                "persona_role": str,      # 페르소나 역할
                "persona_emoji": str,     # 이모지
                "persona_color": str,     # 색상
                "confidence": float,      # 라우팅 신뢰도
                "intent": str,            # 감지된 의도
                "session_id": str,        # 세션 ID
            }
        """
        session = self._get_session(session_id)
        session["command_count"] += 1

        # ── 1단계: 온톨로지 기반 키워드 라우팅 (SPARQL) ──────────────────
        if force_persona and force_persona in self.AGENTS:
            persona_id = force_persona
            routing_result = {
                "persona": persona_id,
                "confidence": 1.0,
                "intent_summary": user_text,
                "reasoning": "사용자가 직접 페르소나를 선택함",
            }
        else:
            ontology_hint = await self.route_by_ontology(user_text)

            # ── 2단계: Claude tool_use 의도 분류 (정밀 라우팅) ──────────────
            routing_result = await self.route_by_claude(user_text, ontology_hint)
            persona_id = routing_result.get("persona", "therapist")

        # ── 3단계: 온톨로지에 명령 트리플 추가 ───────────────────────────
        command_id = f"cmd_{session_id}_{session['command_count']}"
        # agent_id 형식: "TutorAgent" etc.
        agent_ontology_id = f"{persona_id.capitalize()}Agent"
        self._ensure_ontology()
        try:
            ontology_manager.add_command_triple(
                session_id, command_id, agent_ontology_id, user_text
            )
        except Exception:
            pass

        # ── 4단계: 페르소나 에이전트로 응답 생성 ─────────────────────────
        agent = self.AGENTS.get(persona_id, self.AGENTS["therapist"])
        persona_history = session["persona_histories"].get(persona_id, [])

        response_text = await agent.respond(user_text, persona_history)

        # ── 5단계: 대화 기록 업데이트 ────────────────────────────────────
        session["persona_histories"][persona_id].append(
            {"role": "user", "content": user_text}
        )
        session["persona_histories"][persona_id].append(
            {"role": "assistant", "content": response_text}
        )

        # 히스토리 길이 제한
        max_hist = settings.max_history * 2
        if len(session["persona_histories"][persona_id]) > max_hist:
            session["persona_histories"][persona_id] = \
                session["persona_histories"][persona_id][-max_hist:]

        session["current_persona"] = persona_id
        session["history"].append({
            "role": "user",
            "content": user_text,
            "persona": persona_id,
        })
        session["history"].append({
            "role": "assistant",
            "content": response_text,
            "persona": persona_id,
        })

        return {
            "response": response_text,
            "persona": persona_id,
            "persona_name": agent.name,
            "persona_role": agent.role,
            "persona_emoji": agent.emoji,
            "persona_color": agent.color,
            "confidence": routing_result.get("confidence", 0.8),
            "intent": routing_result.get("intent_summary", user_text[:50]),
            "session_id": session_id,
        }

    def get_all_personas_info(self) -> list[dict]:
        """모든 페르소나 정보를 반환합니다."""
        return [agent.to_dict() for agent in self.AGENTS.values()]

    def get_session_history(self, session_id: str) -> list[dict]:
        """세션의 전체 대화 기록을 반환합니다."""
        session = self._sessions.get(session_id, {})
        return session.get("history", [])

    def clear_session(self, session_id: str):
        """세션을 초기화합니다."""
        if session_id in self._sessions:
            del self._sessions[session_id]


# 싱글턴 오케스트레이터
orchestrator = OrchestratorAgent()
