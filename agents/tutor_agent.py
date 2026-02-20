"""
weAID 과외선생님 페르소나 에이전트
교육, 학습, 과외 전문 AI
"""
import json
from .base_agent import BaseAgent


class TutorAgent(BaseAgent):
    """
    📚 과외선생님 페르소나
    수학, 과학, 국어, 영어 등 모든 과목 개인 과외
    """

    def __init__(self):
        system_prompt = """당신은 weAID의 과외선생님 페르소나입니다. 이름은 "선생님"이며 📚 이모지를 사용합니다.

당신은 친절하고 인내심 있는 개인 과외 선생님입니다. 학생의 수준에 맞춰 모든 과목을 가르칩니다.

## 전문 분야
- 수학: 산술, 대수, 기하, 미적분, 통계
- 과학: 물리, 화학, 생물, 지구과학
- 국어: 문법, 독해, 작문, 문학
- 영어: 문법, 독해, 회화, 작문
- 사회/역사: 한국사, 세계사, 지리, 경제
- 예체능: 음악 이론, 미술 이론

## 교육 방식
1. 먼저 학생의 현재 수준을 파악합니다
2. 개념을 쉬운 예시와 함께 단계별로 설명합니다
3. 연습 문제를 출제하고 풀이를 도와줍니다
4. 틀린 부분은 왜 틀렸는지 친절하게 설명합니다
5. 항상 격려하고 칭찬으로 학습 동기를 높입니다

## 응답 스타일
- 친근하고 격려적인 말투 사용
- 어려운 개념은 일상적인 예시로 설명
- 단계별로 나누어 설명 (Step 1, Step 2...)
- 중요한 공식이나 규칙은 강조 표시
- 항상 "이해가 되셨나요?", "더 궁금한 점이 있으신가요?" 등으로 마무리

## 주의사항
- 답만 주지 말고 풀이 과정을 자세히 설명합니다
- 학생이 스스로 생각할 수 있도록 힌트를 먼저 제공합니다
- 정확한 수학/과학 지식을 바탕으로 답변합니다"""

        super().__init__(
            agent_id="tutoragent",
            name="선생님",
            role="과외선생님",
            emoji="📚",
            color="#4CAF50",
            system_prompt=system_prompt,
            capabilities=["수학 과외", "과학 과외", "국어 과외", "영어 과외", "역사 과외"],
        )

    def get_tools(self) -> list[dict]:
        """과외선생님 전용 도구 (수학 계산기, 문제 생성기)."""
        return [
            {
                "name": "generate_practice_problems",
                "description": "특정 주제에 맞는 연습 문제를 생성합니다",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "subject": {
                            "type": "string",
                            "description": "과목 (수학, 과학, 국어, 영어 등)",
                        },
                        "topic": {
                            "type": "string",
                            "description": "세부 주제 (예: 이차방정식, 세포분열 등)",
                        },
                        "difficulty": {
                            "type": "string",
                            "enum": ["초급", "중급", "고급"],
                            "description": "문제 난이도",
                        },
                        "count": {
                            "type": "integer",
                            "description": "생성할 문제 수 (1-5)",
                        },
                    },
                    "required": ["subject", "topic"],
                },
            },
            {
                "name": "create_study_plan",
                "description": "학습 계획표를 작성합니다",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "subject": {"type": "string", "description": "과목"},
                        "goal": {"type": "string", "description": "학습 목표"},
                        "duration_weeks": {"type": "integer", "description": "기간(주)"},
                    },
                    "required": ["subject", "goal"],
                },
            },
        ]

    def _handle_tool_call(self, tool_name: str, tool_input: dict) -> str:
        if tool_name == "generate_practice_problems":
            subject = tool_input.get("subject", "")
            topic = tool_input.get("topic", "")
            difficulty = tool_input.get("difficulty", "중급")
            count = tool_input.get("count", 3)
            return json.dumps({
                "subject": subject,
                "topic": topic,
                "difficulty": difficulty,
                "count": count,
                "instruction": f"{subject} {topic} {difficulty} 연습 문제 {count}개를 단계적으로 생성해주세요. 각 문제에 풀이 힌트를 포함하세요.",
            }, ensure_ascii=False)

        if tool_name == "create_study_plan":
            return json.dumps({
                "subject": tool_input.get("subject", ""),
                "goal": tool_input.get("goal", ""),
                "weeks": tool_input.get("duration_weeks", 4),
                "instruction": "체계적인 주간 학습 계획표를 작성해주세요.",
            }, ensure_ascii=False)

        return super()._handle_tool_call(tool_name, tool_input)

    def get_greeting(self) -> str:
        return "안녕하세요! 📚 저는 weAID의 과외선생님입니다. 수학, 과학, 국어, 영어 등 어떤 과목이든 도와드릴게요. 오늘은 어떤 것을 공부할까요?"
