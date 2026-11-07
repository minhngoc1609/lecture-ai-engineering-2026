"""ADK 版エージェントに1つ質問し、ツール呼び出しを --trace と同じ形で表示する（比較用）。

使い方（リポジトリの直下で）:
    PYTHONPATH=. uv run --with google-adk python -m adk_agent.trace "LoRAとQLoRAの違いは？"
"""

import asyncio
import sys

from google.adk.runners import InMemoryRunner
from google.genai import types

from adk_agent.glossary_agent.agent import root_agent


async def main(question: str) -> None:
    runner = InMemoryRunner(agent=root_agent)
    session = await runner.session_service.create_session(app_name=runner.app_name, user_id="student")
    message = types.Content(role="user", parts=[types.Part(text=question)])
    answer, trace, llm_calls, tokens_in, tokens_out = [], [], 0, 0, 0
    async for event in runner.run_async(user_id="student", session_id=session.id, new_message=message):
        if event.usage_metadata:  # LLM の応答1回ごとに付く
            llm_calls += 1
            tokens_in += event.usage_metadata.prompt_token_count or 0
            tokens_out += event.usage_metadata.candidates_token_count or 0
        for call in event.get_function_calls():
            trace.append(f"[tool call]   {call.name}({dict(call.args or {})})")
        for resp in event.get_function_responses():
            trace.append(f"[tool return] {resp.name} -> {str(resp.response)[:120]}…")
        if event.is_final_response() and event.content and event.content.parts:
            answer += [p.text for p in event.content.parts if p.text]
    print(f"[model] {root_agent.model}")
    print("\n".join(answer))
    print("\n--- trace (ADK) ---")
    print("\n".join(trace))
    print(f"[usage] llm_calls={llm_calls}, tool_calls={sum(l.startswith('[tool call]') for l in trace)}, "
          f"input_tokens={tokens_in}, output_tokens={tokens_out}")


if __name__ == "__main__":
    asyncio.run(main(" ".join(sys.argv[1:]) or "LoRAとQLoRAの違いは？"))