"""
weAID Base Agent
모든 페르소나 에이전트의 기본 클래스
Claude API를 사용한 agentic AI 기반
"""
import anthropic
from abc import ABC, abstractmethod
from typing import Optional
from config.settings import settings


class BaseAgent(ABC):
    """
    Agentic AI 기본 에이전트 클래스
    Claude API를 통해 각 페르소나의 역할을 수행합니다.
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        role: str,
        emoji: str,
        color: str,
        system_prompt: str,
        capabilities: list[str] = None,
    ):
        self.agent_id = agent_id
        self.name = name
        self.role = role
        self.emoji = emoji
        self.color = color
        self.system_prompt = system_prompt
        self.capabilities = capabilities or []

        # Claude 클라이언트
        self._client: Optional[anthropic.Anthropic] = None

    def _get_client(self) -> anthropic.Anthropic:
        """Claude API 클라이언트를 반환합니다 (lazy initialization)."""
        if self._client is None:
            self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        return self._client

    def get_tools(self) -> list[dict]:
        """이 에이전트가 사용하는 Claude tool_use 도구 목록 (서브클래스에서 오버라이드)."""
        return []

    async def respond(
        self,
        user_message: str,
        conversation_history: list[dict] = None,
        stream: bool = False,
    ) -> str:
        """
        사용자 메시지에 대한 응답을 생성합니다.

        Args:
            user_message: 사용자 입력 텍스트
            conversation_history: 이전 대화 기록 (messages 형식)
            stream: 스트리밍 여부

        Returns:
            생성된 응답 텍스트
        """
        client = self._get_client()
        messages = list(conversation_history or [])

        # 현재 메시지 추가
        messages.append({"role": "user", "content": user_message})

        # 메시지 수 제한
        if len(messages) > settings.max_history * 2:
            messages = messages[-(settings.max_history * 2):]

        try:
            tools = self.get_tools()
            kwargs = {
                "model": settings.claude_model,
                "max_tokens": 4096,
                "system": self.system_prompt,
                "messages": messages,
            }
            if tools:
                kwargs["tools"] = tools

            response = client.messages.create(**kwargs)

            # tool_use 처리 (agentic loop)
            while response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        tool_result = self._handle_tool_call(
                            block.name, block.input
                        )
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": tool_result,
                        })

                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})

                kwargs["messages"] = messages
                response = client.messages.create(**kwargs)

            # 텍스트 응답 추출
            text_parts = []
            for block in response.content:
                if hasattr(block, "text"):
                    text_parts.append(block.text)

            return "\n".join(text_parts) if text_parts else "응답을 생성할 수 없습니다."

        except anthropic.AuthenticationError:
            return "⚠️ API 키가 설정되지 않았습니다. .env 파일에 ANTHROPIC_API_KEY를 설정해주세요."
        except anthropic.RateLimitError:
            return "⚠️ 요청이 너무 많습니다. 잠시 후 다시 시도해주세요."
        except Exception as e:
            return f"⚠️ 응답 생성 중 오류가 발생했습니다: {str(e)}"

    def _handle_tool_call(self, tool_name: str, tool_input: dict) -> str:
        """Tool call 처리 (서브클래스에서 필요시 오버라이드)."""
        return f"도구 '{tool_name}' 처리 결과"

    def get_greeting(self) -> str:
        """페르소나 인사말을 반환합니다."""
        return f"안녕하세요! 저는 weAID의 {self.role} {self.name}입니다. 무엇을 도와드릴까요?"

    def to_dict(self) -> dict:
        """에이전트 정보를 딕셔너리로 반환합니다."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "role": self.role,
            "emoji": self.emoji,
            "color": self.color,
            "capabilities": self.capabilities,
        }
