from types import SimpleNamespace as NS

import app.agent.graph as graph


def _tool_call():
    return NS(content=[NS(type="tool_use", id="t1", name="calculator", input={"expression": "1+1"})],
              stop_reason="tool_use", usage=NS(input_tokens=10, output_tokens=5))


def _final():
    return NS(content=[NS(type="text", text="Найкраща відповідь")], stop_reason="end_turn",
              usage=NS(input_tokens=10, output_tokens=5))


class LoopingClient:
    def __init__(self):
        self.messages, self.calls = self, 0

    def create(self, **kwargs):
        self.calls += 1
        return _final() if kwargs.get("tool_choice") == {"type": "none"} else _tool_call()


def test_loop_is_stopped_gracefully(monkeypatch):
    client = LoopingClient()
    monkeypatch.setattr(graph, "get_anthropic", lambda: client)
    monkeypatch.setattr(graph, "execute_tool", lambda name, args: ("2", False))
    state = graph.build_agent_graph().invoke(graph.new_turn_input("порахуй"), {"recursion_limit": 30})
    assert graph.final_text(state) == "Найкраща відповідь"
    assert client.calls <= 4