import pytest
from app.interviewer.agent import interviewer_agent

@pytest.mark.asyncio
async def test_interviewer_calls_evaluator():
    events = []
    # Send a single turn. The interviewer might first select_questions, then we send another message.
    async for event in interviewer_agent.run_async("I am ready for the interview. Start the first question, and I will answer: 'I would use a database'."):
        events.append(event)
        
    tool_called = False
    for event in events:
        if hasattr(event, "output") and isinstance(event.output, dict):
            parts = event.output.get("parts", [])
            for part in parts:
                if "function_call" in part:
                    if part["function_call"].get("name") == "evaluator_agent":
                        tool_called = True
                        break
    
    assert tool_called, "The interviewer_agent failed to call the evaluator_agent tool."
