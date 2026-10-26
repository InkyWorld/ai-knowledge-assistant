from app.agent.history import repair_tool_pairs, trim_to_last_turns


def test_dangling_tool_use_gets_synthetic_result():
    messages = [
        {"role": "user", "content": "q"},
        {"role": "assistant", "content": [{"type": "tool_use", "id": "t1", "name": "rag_search", "input": {}}]},
        {"role": "user", "content": "нове питання"},          # процесс прервали до tool_result
    ]
    fixed = repair_tool_pairs(messages)
    assert fixed[2]["content"][0]["tool_use_id"] == "t1" and fixed[2]["content"][0]["is_error"]


def test_complete_pairs_untouched():
    messages = [
        {"role": "user", "content": "q"},
        {"role": "assistant", "content": [{"type": "tool_use", "id": "t1", "name": "x", "input": {}}]},
        {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "t1", "content": "ok"}]},
    ]
    assert repair_tool_pairs(messages) == messages


def test_trim_keeps_whole_turns():
    messages = []
    for i in range(10):
        messages += [{"role": "user", "content": f"q{i}"}, {"role": "assistant", "content": [{"type": "text", "text": "a"}]}]
    trimmed = trim_to_last_turns(messages, k=3)
    assert trimmed[0]["content"] == "q7" and len(trimmed) == 6