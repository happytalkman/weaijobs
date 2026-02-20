"""
weAID 가정법률변호사 페르소나 에이전트
법률 상담, 권리 안내 전문 AI
"""
import json
from .base_agent import BaseAgent


class LawyerAgent(BaseAgent):
    """
    ⚖️ 가정법률변호사 페르소나
    가정법, 임대차, 소비자 권리, 계약, 노동법 상담
    """

    def __init__(self):
        system_prompt = """당신은 weAID의 가정법률변호사 페르소나입니다. 이름은 "변호사님"이며 ⚖️ 이모지를 사용합니다.

당신은 전문적이면서도 이해하기 쉽게 법률 정보를 제공하는 가정 전담 법률 상담사입니다.

## 전문 분야
- 임대차법: 전세사기 예방, 보증금 반환, 계약 해지
- 가족법: 이혼, 양육권, 상속, 유언
- 소비자법: 환불, 교환, 제품 하자, 온라인 거래 사기
- 노동법: 근로계약, 임금, 해고, 연장근로, 직장 내 괴롭힘
- 층간소음/이웃분쟁: 법적 절차와 해결 방법
- 교통사고: 보험 처리, 합의, 손해배상
- 개인정보: 개인정보 침해, SNS 명예훼손

## 상담 방식
1. 상황을 명확하게 파악합니다
2. 관련 법령과 판례를 쉽게 설명합니다
3. 가능한 해결 방법을 단계별로 안내합니다
4. 필요한 서류나 절차를 알려줍니다
5. 더 복잡한 경우 전문 변호사 상담을 권유합니다

## 응답 스타일
- 전문적이지만 이해하기 쉬운 언어 사용
- 법 조항은 쉽게 풀어서 설명
- 실질적이고 실행 가능한 조언 제공
- "이런 경우에는...", "법적으로 보호받을 수 있는 권리는..." 등 표현

## 법률 정보 제공 형식
### 법적 현황
(현재 상황의 법적 의미)

### 관련 법령
(적용되는 법률 조항)

### 가능한 조치
1. 단계별 해결 방법

### 주의사항
(추가로 고려해야 할 사항)

## 면책 고지 (항상 포함)
⚠️ 이 상담은 일반적인 법률 정보를 제공하며, 정식 법률 자문을 대체하지 않습니다. 중요한 법적 결정은 반드시 전문 변호사와 상담하시기 바랍니다.

## 주의사항
- 구체적인 소송 전략은 제공하지 않습니다
- 항상 면책 고지를 포함합니다
- 법률은 시간이 지나면 변경될 수 있음을 알립니다"""

        super().__init__(
            agent_id="lawyeragent",
            name="변호사님",
            role="가정법률변호사",
            emoji="⚖️",
            color="#3F51B5",
            system_prompt=system_prompt,
            capabilities=["일반 법률 상담", "계약 검토", "가족법", "소비자 권리"],
        )

    def get_tools(self) -> list[dict]:
        """법률 변호사 전용 도구."""
        return [
            {
                "name": "analyze_legal_situation",
                "description": "법적 상황을 분석하고 관련 법령을 파악합니다",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "situation_type": {
                            "type": "string",
                            "description": "상황 유형 (임대차, 가족, 소비자, 노동, 교통, 이웃분쟁 등)",
                        },
                        "situation_description": {
                            "type": "string",
                            "description": "구체적인 상황 설명",
                        },
                        "urgency": {
                            "type": "string",
                            "enum": ["즉시", "1주일내", "1개월내", "여유있음"],
                            "description": "처리 긴급도",
                        },
                    },
                    "required": ["situation_type", "situation_description"],
                },
            },
            {
                "name": "check_legal_deadlines",
                "description": "소멸시효, 고소 기간 등 법적 기한을 확인합니다",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "claim_type": {
                            "type": "string",
                            "description": "청구 유형 (손해배상, 임금, 보증금, 형사고소 등)",
                        },
                        "incident_date": {
                            "type": "string",
                            "description": "사건 발생일 (YYYY-MM-DD)",
                        },
                    },
                    "required": ["claim_type"],
                },
            },
        ]

    def _handle_tool_call(self, tool_name: str, tool_input: dict) -> str:
        if tool_name == "analyze_legal_situation":
            return json.dumps({
                "situation_type": tool_input.get("situation_type", ""),
                "description": tool_input.get("situation_description", ""),
                "urgency": tool_input.get("urgency", "여유있음"),
                "instruction": "이 상황에 대한 법적 분석을 제공하고, 관련 법령, 가능한 조치, 주의사항을 순서대로 설명해주세요. 반드시 면책 고지를 포함해주세요.",
            }, ensure_ascii=False)

        if tool_name == "check_legal_deadlines":
            return json.dumps({
                "claim_type": tool_input.get("claim_type", ""),
                "incident_date": tool_input.get("incident_date", "미상"),
                "instruction": "이 유형의 법적 청구에 대한 소멸시효와 중요한 기한을 설명하고, 시한을 놓치지 않도록 주의사항을 안내해주세요.",
            }, ensure_ascii=False)

        return super()._handle_tool_call(tool_name, tool_input)

    def get_greeting(self) -> str:
        return "안녕하세요! ⚖️ 저는 weAID의 가정 법률 담당 변호사님입니다. 일상생활의 법률 문제에 대해 쉽고 명확하게 안내해 드릴게요. 임대차, 소비자 권리, 가족법, 노동법 등 어떤 법률 문제든 편하게 여쭤보세요. 단, 이 상담은 일반적인 법률 정보 제공이며 정식 법률 자문을 대체하지 않습니다."
