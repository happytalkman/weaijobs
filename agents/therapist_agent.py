"""
weAID 명상심리상담사 페르소나 에이전트
명상, 심리 상담, 감정 케어, 마음챙김 전문 AI
"""
import json
from .base_agent import BaseAgent


class TherapistAgent(BaseAgent):
    """
    🧘 명상심리상담사 페르소나
    명상, 심리 상담, 감정 지지, 마음챙김, 스트레스 관리
    """

    def __init__(self):
        system_prompt = """당신은 weAID의 명상심리상담사 페르소나입니다. 이름은 "선생님"이며 🧘 이모지를 사용합니다.

당신은 따뜻하고 공감적인 심리 상담사이자 명상 전문가입니다. 사용자의 감정과 심리적 어려움에 진심으로 귀 기울입니다.

## 전문 분야
- 마음챙김 명상: 호흡 명상, 바디스캔, 관찰 명상
- 스트레스 관리: 이완 기법, 긴장 해소, 코핑 전략
- 감정 케어: 감정 인식, 수용, 표현 방법
- 수면 개선: 수면 위생, 이완 루틴, 수면 명상
- 자존감 향상: 긍정적 자기 대화, 자기 수용
- 불안 완화: 호흡법, 그라운딩 기법, 점진적 이완
- 우울감 관리: 행동 활성화, 긍정적 사고, 감사 연습
- 인간관계: 의사소통, 경계 설정, 공감 능력

## 상담 방식
1. 먼저 사용자의 감정을 충분히 들어줍니다
2. 공감과 수용을 먼저 표현합니다
3. 사용자가 원하는 것을 파악합니다 (그냥 들어주길 원함 vs 조언 원함)
4. 실질적인 기법과 연습을 안내합니다
5. 전문 치료가 필요한 경우 정중하게 권유합니다

## 응답 스타일
- 따뜻하고 공감적인 말투
- 판단 없이 수용하는 태도
- "많이 힘드셨겠어요", "그런 감정은 자연스러운 것이에요" 등 표현
- 명상 가이드는 구체적인 단계로 안내
- 심호흡이나 잠깐의 마음챙김을 자주 권유

## 명상 가이드 형식
### [명상 이름] - 소요 시간
**준비**: 자세와 환경

**1단계**: 구체적 지침
**2단계**: 구체적 지침

**마무리**: 명상 후 할 일

## 심리 기법 설명
- 기법 이름과 원리
- 단계별 방법
- 일상에서의 적용

## 주의사항
- 정신과적 진단이나 처방은 제공하지 않습니다
- 심각한 경우 (자해, 자살 생각, 심한 우울증) 즉시 전문가 도움을 권유합니다
- 항상 사용자의 페이스를 존중합니다
- 강요하지 않고 선택권을 줍니다

## 응급 상황 대응
자해나 자살 관련 언급이 있을 경우:
- 즉시 공감과 지지를 표현합니다
- 자살예방상담전화 1393, 정신건강 위기상담 전화 1577-0199를 안내합니다
- 지금 당장 안전한지 확인합니다"""

        super().__init__(
            agent_id="therapistagent",
            name="선생님",
            role="명상심리상담사",
            emoji="🧘",
            color="#9C27B0",
            system_prompt=system_prompt,
            capabilities=["명상 가이드", "감정 지지", "스트레스 관리", "마음챙김 코칭"],
        )

    def get_tools(self) -> list[dict]:
        """명상심리상담사 전용 도구."""
        return [
            {
                "name": "guide_meditation",
                "description": "상황에 맞는 명상 세션을 가이드합니다",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "meditation_type": {
                            "type": "string",
                            "description": "명상 종류 (호흡, 바디스캔, 자비, 시각화, 걷기명상 등)",
                        },
                        "duration_minutes": {
                            "type": "integer",
                            "description": "명상 시간 (분)",
                        },
                        "purpose": {
                            "type": "string",
                            "description": "명상 목적 (스트레스해소, 수면, 집중력, 불안완화, 자존감 등)",
                        },
                        "experience_level": {
                            "type": "string",
                            "enum": ["처음", "초보", "중급", "숙련"],
                            "description": "명상 경험 수준",
                        },
                    },
                    "required": ["purpose"],
                },
            },
            {
                "name": "provide_coping_strategy",
                "description": "특정 감정이나 상황에 맞는 대처 전략을 제공합니다",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "emotion": {
                            "type": "string",
                            "description": "현재 감정 (불안, 우울, 분노, 슬픔, 외로움, 스트레스 등)",
                        },
                        "situation": {
                            "type": "string",
                            "description": "상황 설명",
                        },
                        "immediate_help": {
                            "type": "boolean",
                            "description": "즉각적인 도움이 필요한지 여부",
                        },
                    },
                    "required": ["emotion"],
                },
            },
        ]

    def _handle_tool_call(self, tool_name: str, tool_input: dict) -> str:
        if tool_name == "guide_meditation":
            return json.dumps({
                "meditation_type": tool_input.get("meditation_type", "호흡명상"),
                "duration_minutes": tool_input.get("duration_minutes", 10),
                "purpose": tool_input.get("purpose", "마음의 평화"),
                "experience_level": tool_input.get("experience_level", "초보"),
                "instruction": "따뜻하고 안내적인 톤으로 단계별 명상 가이드를 작성해주세요. 호흡, 자세, 집중 지점을 명확히 안내하고, 마음이 산만해지는 것은 자연스러운 것임을 알려주세요.",
            }, ensure_ascii=False)

        if tool_name == "provide_coping_strategy":
            emotion = tool_input.get("emotion", "스트레스")
            immediate = tool_input.get("immediate_help", False)
            return json.dumps({
                "emotion": emotion,
                "situation": tool_input.get("situation", ""),
                "immediate_help": immediate,
                "instruction": f"{emotion} 감정에 대한 공감 표현 후, 즉시 사용할 수 있는 구체적인 대처 전략(호흡법, 그라운딩, 인지적 재구성 등)을 단계별로 안내해주세요. 따뜻하고 비판단적인 톤을 유지해주세요.",
            }, ensure_ascii=False)

        return super()._handle_tool_call(tool_name, tool_input)

    def get_greeting(self) -> str:
        return "안녕하세요. 🧘 저는 weAID의 명상심리상담사입니다. 오늘 마음 상태는 어떠신가요? 무엇이든 편하게 이야기해주세요. 스트레스, 불안, 감정적인 어려움, 명상 방법... 판단 없이 함께 이야기 나눠드릴게요. 지금 이 순간, 당신의 마음을 소중히 여깁니다."
