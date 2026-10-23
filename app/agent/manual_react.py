from dataclasses import dataclass, field

from app.agent.tools.registry import TOOLS, execute_tool
from app.core.clients import get_anthropic
from app.core.config import settings
from app.core.logs import logger
from app.domain.chat import ChatHistory
from app.prompts.agent import SYSTEM_AGENT


@dataclass
class AgentResult:
    answer: str
    steps: list[dict] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    stopped_by: str = "end_turn"


def _text(response) -> str:
    return "".join(b.text for b in response.content if b.type == "text").strip()


def run_agent(question: str, history: ChatHistory | None = None, max_steps: int = 6) -> AgentResult:
    client = get_anthropic()
    messages = (history.to_api_messages() if history else []) + [{"role": "user", "content": question}]
    result = AgentResult(answer="")

    for step in range(max_steps):
        response = client.messages.create(
            model=settings.anthropic_model, max_tokens=1500,
            system=SYSTEM_AGENT, tools=TOOLS, messages=messages,
        )
        result.input_tokens += response.usage.input_tokens
        result.output_tokens += response.usage.output_tokens

        if response.stop_reason != "tool_use":
            result.answer, result.stopped_by = _text(response), response.stop_reason or "unknown"
            return result

        thought = _text(response)
        messages.append({"role": "assistant", "content": response.content})
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            output, is_error = execute_tool(block.name, block.input)
            result.steps.append({"step": step, "thought": thought, "tool": block.name,
                                 "input": block.input, "is_error": is_error, "output_preview": output[:200]})
            logger.info("agent step=%s tool=%s error=%s", step, block.name, is_error)
            item = {"type": "tool_result", "tool_use_id": block.id, "content": output, "is_error": is_error}
            tool_results.append(item)
        messages.append({"role": "user", "content": tool_results})

    logger.warning("agent stopped: max_steps=%s", max_steps)
    result.answer, result.stopped_by = "Не вдалося завершити за ліміт кроків.", "max_steps"
    return result