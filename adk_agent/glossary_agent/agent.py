"""第3回 宿題（発展 a）: 演習と同じ指示とツールで、エージェントの組み立てだけを ADK で書き直す。

動かし方（リポジトリの直下で）:
    PYTHONPATH=. uv run --with google-adk adk run adk_agent/glossary_agent
"""

from google.adk.agents import Agent

from app import tools
from app.agent import INSTRUCTIONS
from app.config import MODEL

root_agent = Agent(
    model=MODEL,  # 演習と同じモデル（既定は gemini-3.5-flash-lite、AIE_MODEL で切り替え）
    name="glossary_agent",
    description="AIE2026 の用語集と各回の要点を使って質問に答える学習支援エージェント",
    instruction=INSTRUCTIONS,  # app/agent.py と同じ指示文
    tools=[tools.search_glossary, tools.get_lecture_summary, tools.make_quiz],  # 関数をそのまま渡す
)