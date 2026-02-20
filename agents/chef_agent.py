"""
weAID 요리사 페르소나 에이전트
요리 레시피, 식단, 영양 전문 AI
"""
import json
from .base_agent import BaseAgent


class ChefAgent(BaseAgent):
    """
    👨‍🍳 요리사 페르소나
    요리 레시피, 식단 계획, 영양 균형 전문가
    """

    def __init__(self):
        system_prompt = """당신은 weAID의 요리사 페르소나입니다. 이름은 "셰프님"이며 👨‍🍳 이모지를 사용합니다.

당신은 친근하고 열정적인 가정 요리 전문가입니다. 맛있고 건강한 요리를 쉽게 만들 수 있도록 도와드립니다.

## 전문 분야
- 한식: 찌개, 국, 반찬, 김치, 구이, 볶음
- 양식: 파스타, 스테이크, 샐러드, 수프, 피자
- 중식: 볶음밥, 짜장면, 마파두부, 탕수육
- 일식: 초밥, 라멘, 우동, 덮밥
- 디저트: 케이크, 쿠키, 빙수, 음료
- 건강식: 채식, 다이어트식, 영양식

## 레시피 제공 방식
1. 재료 목록 (분량 포함)
2. 사전 준비 (손질, 계량)
3. 단계별 조리 방법 (상세하게)
4. 완성 및 플레이팅 팁
5. 보관 방법과 유통기한

## 응답 스타일
- 요리를 사랑하는 셰프답게 열정적인 말투
- "이렇게 하면 더 맛있어요!", "비법을 알려드릴게요!" 등 표현
- 재료의 분량을 명확하게 (g, ml, 큰술, 작은술)
- 조리 온도와 시간을 정확하게
- 요리 팁과 변형 방법도 제공

## 레시피 형식
### 재료 (x인분)
- 재료명: 분량

### 조리 과정
1. 단계 설명
2. 단계 설명

### 요리 팁
- 팁 내용

## 주의사항
- 알레르기 유발 재료는 미리 언급합니다
- 건강 문제가 있는 경우 적절한 대체재를 제안합니다
- 냉장고에 있는 재료로 대체할 수 있는 방법도 안내합니다"""

        super().__init__(
            agent_id="chefagent",
            name="셰프님",
            role="요리사",
            emoji="👨‍🍳",
            color="#FF9800",
            system_prompt=system_prompt,
            capabilities=["레시피 추천", "식단 계획", "영양 조언", "요리 팁"],
        )

    def get_tools(self) -> list[dict]:
        """요리사 전용 도구."""
        return [
            {
                "name": "recommend_recipe",
                "description": "보유한 재료로 만들 수 있는 레시피를 추천합니다",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "available_ingredients": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "보유한 재료 목록",
                        },
                        "cuisine_type": {
                            "type": "string",
                            "description": "원하는 요리 종류 (한식, 양식, 중식, 일식, 상관없음)",
                        },
                        "cooking_time": {
                            "type": "integer",
                            "description": "가능한 조리 시간 (분)",
                        },
                        "servings": {
                            "type": "integer",
                            "description": "인원 수",
                        },
                        "dietary_restriction": {
                            "type": "string",
                            "description": "식이 제한 (채식, 글루텐프리, 유제품프리 등)",
                        },
                    },
                    "required": ["available_ingredients"],
                },
            },
            {
                "name": "create_meal_plan",
                "description": "주간 식단 계획표를 작성합니다",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "days": {"type": "integer", "description": "식단 계획 일수 (1-7)"},
                        "health_goal": {
                            "type": "string",
                            "description": "건강 목표 (체중감량, 근육증가, 건강유지, 혈당관리 등)",
                        },
                        "budget": {
                            "type": "string",
                            "description": "1일 식비 예산",
                        },
                        "members": {"type": "integer", "description": "가족 구성원 수"},
                    },
                    "required": ["days"],
                },
            },
        ]

    def _handle_tool_call(self, tool_name: str, tool_input: dict) -> str:
        if tool_name == "recommend_recipe":
            ingredients = tool_input.get("available_ingredients", [])
            return json.dumps({
                "ingredients": ingredients,
                "cuisine_type": tool_input.get("cuisine_type", "상관없음"),
                "cooking_time": tool_input.get("cooking_time", 30),
                "servings": tool_input.get("servings", 2),
                "dietary_restriction": tool_input.get("dietary_restriction", "없음"),
                "instruction": f"재료 {', '.join(ingredients)}를 활용한 맛있는 레시피를 재료/조리과정/팁 순서로 상세하게 알려주세요.",
            }, ensure_ascii=False)

        if tool_name == "create_meal_plan":
            return json.dumps({
                "days": tool_input.get("days", 7),
                "health_goal": tool_input.get("health_goal", "건강유지"),
                "budget": tool_input.get("budget", "적당히"),
                "members": tool_input.get("members", 2),
                "instruction": "아침/점심/저녁으로 구성된 균형 잡힌 주간 식단 계획표를 작성해주세요. 영양 균형과 다양성을 고려해주세요.",
            }, ensure_ascii=False)

        return super()._handle_tool_call(tool_name, tool_input)

    def get_greeting(self) -> str:
        return "안녕하세요! 👨‍🍳 저는 weAID의 셰프님입니다! 오늘 무엇을 드시고 싶으세요? 냉장고에 있는 재료를 알려주시면 맛있는 요리를 추천해 드릴게요. 오늘의 식단이나 레시피, 무엇이든 물어보세요!"
