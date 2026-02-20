"""
weAID 홈트레이닝코치 페르소나 에이전트
운동, 체력, 건강 전문 AI
"""
import json
from .base_agent import BaseAgent


class TrainerAgent(BaseAgent):
    """
    💪 홈트레이닝코치 페르소나
    가정에서 할 수 있는 운동 루틴, 체력 관리, 건강 코칭
    """

    def __init__(self):
        system_prompt = """당신은 weAID의 홈트레이닝코치 페르소나입니다. 이름은 "코치님"이며 💪 이모지를 사용합니다.

당신은 열정적이고 동기부여를 잘 하는 개인 트레이너입니다. 가정에서 최소한의 기구로 할 수 있는 효과적인 운동을 알려줍니다.

## 전문 분야
- 홈 트레이닝: 맨몸 운동, 덤벨 운동, 밴드 운동
- 체중 관리: 다이어트 운동, 칼로리 소모 운동
- 근력 강화: 근육 부위별 운동 (가슴, 등, 어깨, 팔, 허벅지, 복근)
- 유연성: 스트레칭, 요가, 필라테스
- 심폐 기능: 유산소 운동, HIIT
- 자세 교정: 올바른 운동 자세 지도

## 코칭 방식
1. 사용자의 체력 수준과 목표를 먼저 파악합니다
2. 개인에 맞는 운동 루틴을 설계합니다
3. 각 운동의 정확한 자세와 방법을 설명합니다
4. 세트, 반복 횟수, 휴식 시간을 명확하게 안내합니다
5. 운동 전 워밍업, 후 쿨다운을 항상 포함합니다

## 응답 스타일
- 에너지 넘치고 응원하는 말투
- "화이팅!", "잘 하고 계세요!" 등 격려 표현 사용
- 운동명은 한국어와 영어 병기 (예: 푸쉬업(Push-up))
- 세트/반복/휴식을 명확히 표기
- 주의사항과 부상 예방 팁 포함

## 운동 루틴 형식
### 워밍업 (5분)
- 동작: 방법, 시간/횟수

### 본 운동
- 1. 운동명: 세트 x 반복, 휴식

### 쿨다운 (5분)
- 스트레칭 동작

## 주의사항
- 부상 위험이 있는 경우 반드시 경고합니다
- 건강 문제가 있는 경우 의사 상담을 권유합니다
- 무리한 운동보다 꾸준한 운동을 강조합니다"""

        super().__init__(
            agent_id="traineragent",
            name="코치님",
            role="홈트레이닝코치",
            emoji="💪",
            color="#FF5722",
            system_prompt=system_prompt,
            capabilities=["운동 계획", "건강 코칭", "영양 조언", "부상 예방"],
        )

    def get_tools(self) -> list[dict]:
        """홈트레이닝코치 전용 도구."""
        return [
            {
                "name": "create_workout_plan",
                "description": "개인화된 운동 루틴을 생성합니다",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "fitness_level": {
                            "type": "string",
                            "enum": ["초보", "중급", "고급"],
                            "description": "운동 수준",
                        },
                        "goal": {
                            "type": "string",
                            "description": "운동 목표 (체중감량, 근력강화, 유연성향상, 건강유지 등)",
                        },
                        "duration_minutes": {
                            "type": "integer",
                            "description": "운동 시간 (분)",
                        },
                        "equipment": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "사용 가능한 기구 목록 (없으면 빈 배열)",
                        },
                        "target_muscle": {
                            "type": "string",
                            "description": "중점 운동 부위 (선택사항)",
                        },
                    },
                    "required": ["fitness_level", "goal"],
                },
            },
            {
                "name": "calculate_calories",
                "description": "운동별 칼로리 소모량을 계산합니다",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "exercise": {"type": "string", "description": "운동 종류"},
                        "duration_minutes": {"type": "integer", "description": "운동 시간"},
                        "weight_kg": {"type": "number", "description": "체중(kg)"},
                    },
                    "required": ["exercise", "duration_minutes"],
                },
            },
        ]

    def _handle_tool_call(self, tool_name: str, tool_input: dict) -> str:
        if tool_name == "create_workout_plan":
            return json.dumps({
                "fitness_level": tool_input.get("fitness_level", "중급"),
                "goal": tool_input.get("goal", "건강유지"),
                "duration_minutes": tool_input.get("duration_minutes", 30),
                "equipment": tool_input.get("equipment", []),
                "target_muscle": tool_input.get("target_muscle", "전신"),
                "instruction": "워밍업 → 본운동(세트/반복 포함) → 쿨다운 순서로 상세한 운동 루틴을 작성해주세요.",
            }, ensure_ascii=False)

        if tool_name == "calculate_calories":
            exercise = tool_input.get("exercise", "")
            duration = tool_input.get("duration_minutes", 30)
            weight = tool_input.get("weight_kg", 70)
            # MET values (간단한 추정)
            met_map = {
                "걷기": 3.5, "달리기": 8.0, "자전거": 6.0, "수영": 7.0,
                "푸쉬업": 4.0, "스쿼트": 5.0, "줄넘기": 10.0, "요가": 2.5,
            }
            met = 5.0  # 기본값
            for k, v in met_map.items():
                if k in exercise:
                    met = v
                    break
            calories = round(met * weight * duration / 60, 1)
            return json.dumps({
                "exercise": exercise,
                "duration_minutes": duration,
                "weight_kg": weight,
                "estimated_calories": calories,
                "note": "이 값은 추정치이며 개인차가 있습니다.",
            }, ensure_ascii=False)

        return super()._handle_tool_call(tool_name, tool_input)

    def get_greeting(self) -> str:
        return "안녕하세요! 💪 저는 weAID의 홈트레이닝코치입니다! 오늘도 함께 건강하게 운동해봐요! 목표가 무엇인지 알려주세요. 딱 맞는 운동 루틴을 만들어 드릴게요. 화이팅!"
