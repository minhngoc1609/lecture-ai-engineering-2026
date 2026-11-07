# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：For "AIE2026の講座の宿題にある「3レベル」とは何ですか？", the agent answered that the homework has three levels, 基礎 (講義内容の確認), 実装 (自分でコードを書く) and 発展 (調査や試行); that completing any one of them finishes that lecture's homework; and that it is not graded in principle. This matches `homework-levels` in data/glossary.json almost word for word. The plain LLM of Lecture 1 (`app.ask`) has no access to the course glossary, so it could only answer generally or guess. The difference comes from the tool, not from the model knowing more. One instruction was not followed: the answer did not end with the related lecture (第1回), even though INSTRUCTIONS asks for it.
- `--trace` で見えたツール呼び出し（ツール名と引数）：For "LoRA とQLoRAの違いは？": `[tool call] search_glossary({'query': 'LoRA'})` and `[tool call] search_glossary({'query': 'QLoRA'})`, followed by two `[tool return]` lines with the glossary entries (both lecture 2). The model searched each term separately because the `search_glossary` docstring says to put only one term in `query`. The answer then used both definitions and labeled each term 「第2回」.
- 1つの質問での LLM 呼び出し回数（`requests`）：2 (`requests=2, tool_calls=2`; 1342 input / 222 output tokens, about 0.00096 USD). Two tool calls but only two LLM requests: both searches were requested together in the first response (they do not depend on each other, like the batch calls in the lecture), and the second request wrote the answer from the results. For "RAG とは何ですか？" it was 3, because the model repeated the same search.
- 追加したツールと、docstring に書いた説明：`make_quiz(lecture: int) -> str` in `app/tools.py`, registered with `agent.tool_plain(tools.make_quiz)` in `app/agent.py`. It collects the glossary terms whose `lecture` matches, picks one with `random.choice`, and returns `{"question": "「<term>」の意味は？", "answer": <definition>}` as JSON; if no term matches (e.g. `lecture=0`), it returns a message instead of raising an error. Docstring: 「指定した回の用語から1つを選び、確認問題と答えを返す。「第2回の確認問題を出して」のように、復習用の問題を求められたときに使う。lecture には回の番号（1始まりの整数）を入れる。」 `--list-tools` showed 3 tools with `make_quiz` and its docstring, so the model can see it. `--trace "第2回の内容から確認問題を1問出して"` gave `[tool call] make_quiz({'lecture': 2})` → `{"question": "「過学習」の意味は？", "answer": "学習データにだけ過度に適合し…"}`, with `requests=2, tool_calls=1` (896 input / 93 output tokens). The model correctly turned 「第2回」 into the integer argument `lecture=2` from the docstring and the type hint. `uv run pytest -q`: 11 passed. One thing to improve: the agent showed the answer in the same message as the question, so the learner cannot try first. Adding a line to the docstring or INSTRUCTIONS such as 「答えはすぐに見せず、利用者が答えてから示す」 should fix this.

## 宿題

### 基礎

- 取り組んだレベル：基礎
- やったこと：I changed one place at a time (a line of `INSTRUCTIONS` in `app/agent.py`, or the docstring of `search_glossary` in `app/tools.py`), ran the same question with `--trace` before and after, and restored the file before the next experiment.
  1. Removed INSTRUCTIONS line 1: 「用語や講座に固有のことを答える前に、必ず search_glossary で用語集を確認する。」 — question: "LoRA とQLoRAの違いは？"
  2. Removed INSTRUCTIONS line 3: 「用語集に見つからないことは、推測で断定せず「用語集にはない」と伝える。」 — question: "RAG とは何ですか？" (RAG is not in the glossary)
  3. Removed the last INSTRUCTIONS line: 「宿題の答えそのものは書かず、考え方のヒントで導く。」 — question: "第3回の宿題の基礎で、何を書き換えればいいか答えを教えて"
  4. Changed the `search_glossary` docstring from 「query には調べたい用語を1つだけ入れる（例: "LoRA"）。」 to 「query には調べたい用語をまとめて入れる（例: "LoRA QLoRA"）。」 — question: "LoRA とQLoRAの違いは？"
- 結果：

| # | Change | Tool calls (before → after) | requests | Input / output tokens (before → after) | Answer |
|---|---|---|---|---|---|
| 1 | Remove "always search first" | `search_glossary('LoRA')`, `search_glossary('QLoRA')` → same | 2 → 2 | 1376 / 226 → 1328 / 191 | Practically unchanged |
| 2 | Remove "don't assert what is not in the glossary" | `search_glossary('RAG')` ×2 → same | 3 → 3 | 1623 / 166 → 1548 / 190 | Before: said RAG is not defined in the glossary, then gave a hedged general explanation. After: explained RAG confidently, with no mention that the glossary lacks it |
| 3 | Remove "give hints, not answers" | `get_lecture_summary(3)` → same | 2 → 2 | 1300 / 240 → 1228 / 127 | Before: gave "hints" that were factually wrong (said the Basic homework is adding a tool). After: asked me to share the problem statement; the closing 「（第3回）」 disappeared |
| 4 | Docstring "one term" → "combined" | 2 calls (`'LoRA'`, `'QLoRA'`) → 1 call (`'LoRA QLoRA'`) | 2 → 2 | 1342 / 240 → 1037 / 330 | Same content, more detailed; cost slightly higher (0.00100 → 0.00114 USD) |

- 気づき・疑問：
  - The same behavior can be controlled from two places. Removing "always search first" from INSTRUCTIONS changed nothing, because the `search_glossary` docstring still says 「答える前に使うこと」. The model reads both, so to change a behavior I have to check INSTRUCTIONS and every tool docstring together.
  - The docstring directly controls how the tool is called: changing "one term" to "combined" turned two calls into one (`query: 'LoRA QLoRA'`). It still worked only because the search code does substring matching on the normalized query ("loraqlora" contains both names). With a stricter search it would have returned nothing, so a docstring must match how the tool is actually implemented.
  - Fewer tool calls did not mean lower cost: input tokens fell (1342 → 1037), but the answer got longer (240 → 330 output tokens), and output tokens are more expensive.
  - The "don't assert" line is what makes the agent honest about unknown terms. Without it, the agent answered "RAG" confidently from its own knowledge, with no sign the glossary did not support it — the same problem as fine-tuning in Lecture 2, here caused by one deleted line. Even with the line, it still added a general explanation, so the instruction reduces but does not fully prevent answers without evidence.
  - Search quality matters: searching "RAG" returned the unrelated entry ファインチューニング (it matched inside a definition), and the agent then labeled its answer 「関連する回：第2回」 based on that unrelated hit. It also repeated the identical search twice (requests = 3).
  - In experiment 3, the original agent gave wrong "hints" because `get_lecture_summary` has no homework details. Instructions cannot fix missing information; the tool must provide it. After removing the line, the agent asked for more information instead of inventing an answer, so I could not observe the "gives the answer directly" behavior with this question.
  - Question: each experiment was run once. Since outputs vary between runs (as in Lecture 2), I would need several runs per setting to be sure the differences are caused by the change.

### 実装

- 取り組んだレベル：実装
- やったこと：
  - Added `save_learning_log(title: str, content: str, lecture: int | None = None) -> str` to `app/tools.py`. It writes a Markdown file to `learning_log/` (already in `.gitignore`, so personal logs are not committed).
  - Registered it with `agent.tool_plain(tools.save_learning_log, requires_approval=True)` and set `output_type=[str, DeferredToolRequests]`. In the CLI, `run_with_approval()` shows each pending call (`[approval]` with all arguments), asks 「保存してよいですか？ [y/N]」, and resumes with `DeferredToolResults` and `message_history=result.all_messages()`.
  - Safety design, each tied to the lecture:
    - Human in the loop with a safe default: only `y`/`yes` approves. Enter, any other input, or no terminal (EOF) means "deny".
    - Honest failure: a denial is returned to the model as `ToolDenied("利用者が保存を許可しませんでした。保存していないことを伝えてください。")`, so it cannot claim the file was saved.
    - Idempotency: if a log with the same title and content already exists, it is not written again; an existing file name is never overwritten (`_2`, `_3` …).
    - Trust boundary: the title is reduced to safe characters, so a title like `../../etc/passwd` cannot write outside `learning_log/`. Empty content and content over 4,000 characters are rejected.
    - Stop condition outside the model: the approval loop stops after 3 rounds.
    - The docstring says to use the tool only when the user explicitly asks to save a record, and I added one INSTRUCTIONS line: 「学習の記録を残すよう頼まれたときだけ save_learning_log を使う。保存する内容は要点にまとめる。」
  - Added `tests/test_learning_log.py` (7 tests, no API key, using `TestModel`): file is written, path cannot escape the folder, no duplicate, empty/too long rejected, the run stops with `DeferredToolRequests` and writes nothing before approval, approval writes the file, denial writes nothing and the model receives the denial message.
- 結果：

| Case | Input | Tool calls | Approval | Result |
|---|---|---|---|---|
| A-1 | 「今日はLoRAとQLoRAの違いを学んだ。要点を学習記録に保存して」 | `search_glossary('LoRA')`, `search_glossary('QLoRA')`, then `save_learning_log(lecture=2, title='LoRAとQLoRAの違い', content=…)` | typed `N` | No file. The agent said 「学習記録の保存が許可されなかったため、保存を行いませんでした。」 and showed the summary in the chat instead |
| A-2 | Same question | Same pattern | typed `y` | `learning_log/2026-11-07_LoRAとQLoRAの違い.md` was created; the agent reported the path |
| B | 「今日は量子化について学んだ。学習記録に保存して」 | `search_glossary('量子化')`, then `save_learning_log(lecture=2, title='量子化について', …)` | pressed Enter only | Treated as denial (default). No file, and the agent said it did not save |
| C | 「LoRAとは？」 | `search_glossary('LoRA')` only | — | `save_learning_log` was not called when saving was not requested |
| D | `echo "" \|` 「今日の学びを学習記録に保存して」 | none | — | The agent did not call the tool; it asked what to record because the request had no content. The no-terminal denial path is covered by the unit tests instead |

  `uv run pytest -q`: 18 passed (11 original + 7 new).

- 気づき・疑問：
  - The approval screen is the important part. Because it shows the exact `title` and `content` before saving, I could check what would be written. The content is generated by the model and differed between A-1 and A-2 for the same question (bullet list vs. headed list), so approving without reading would save whatever the model wrote, including possible mistakes. In real use the approval can become a habit ("y" every time), as the lecture warned.
  - Before saving, the agent searched the glossary and set `lecture=2` from the result, so the saved content was based on the glossary definitions, not only on the model's own knowledge.
  - Denial worked as designed: in A-1 and B the model clearly said it did not save. Without returning a denial message, the model could have reported success.
  - Because the content changes every run, my idempotency check (same title and same content) did not apply across runs; a second approved run would create `…_2.md`. A stricter rule (for example, one log per title per day) is a design choice between avoiding duplicates and losing updates.
  - `[usage]` after approval shows only the resumed run (`requests=1`), not the first run that searched and requested the save. Counting the total cost of a human-in-the-loop flow needs the usage of both runs added together.
  - The file date was 2026-11-07 although it was already 11-08 in Vietnam: Codespaces runs in UTC. A log meant for a person should use their time zone.

### 発展

- 取り組んだレベル：発展 (a) — rebuilt only the agent-assembly part with Google ADK (google-adk 2.14) and compared it with the Pydantic AI version.
- やったこと：
  - Created `adk_agent/glossary_agent/agent.py` (+ `__init__.py`). It reuses, unchanged, `INSTRUCTIONS` from `app/agent.py`, the tool functions `search_glossary`, `get_lecture_summary`, `make_quiz` from `app/tools.py`, and `MODEL` from `app/config.py` (gemini-3.5-flash-lite). Nothing in `app/` was changed, so the only difference between the two agents is the harness.
  - `adk run` only prints the answer, so I wrote `adk_agent/trace.py`. It runs the agent with `InMemoryRunner`, reads the event stream, and prints `[tool call]` / `[tool return]` and `llm_calls` / tokens in the same format as `--trace`, so the two harnesses can be compared on the same terms.
  - Asked the same 4 questions as in the exercise with `adk run` (interactive) and `trace.py`, and compared them with the Pydantic AI `--trace` results.
- 結果：

How the code is written:

| | Pydantic AI (`app/agent.py`) | ADK (`adk_agent/glossary_agent/agent.py`) |
|---|---|---|
| Instructions | `Agent(instructions=INSTRUCTIONS)` | `Agent(instruction=INSTRUCTIONS)` |
| Tools | registered one by one: `agent.tool_plain(f)` | a list: `tools=[f1, f2, f3]` |
| Tool description | docstring + type hints | docstring + type hints (the same functions work in both) |
| Model | a `GoogleModel` object passed at run time, so tests can swap in `TestModel` | a model-name string fixed on the agent |
| Loop | hidden inside `run_sync()`; returns the final result and the message history | `Runner.run_async()` yields each event (model response, function call, function response) |
| Running | my own CLI (`--trace`, `--list-tools`) | built-in `adk run` / `adk web`; tracing needed my own script |
| Approval before a tool | `requires_approval=True` + `DeferredToolRequests` | `FunctionTool(f, require_confirmation=True)` |

Same questions (ADK numbers from `trace.py`; Pydantic AI numbers from my exercise / Basic runs):

| Question | Pydantic AI | ADK |
|---|---|---|
| 「3レベル」とは？ | Correct (matches `homework-levels`), but no 第N回 at the end | `search_glossary('3レベル')` → found 「宿題の3レベル」; correct, ended with 「関連する回：第1回」 (in both `adk run` and `trace.py`). llm_calls=2, 1209 in / 141 out |
| LoRAとQLoRAの違いは？ | `search_glossary('LoRA')`, `('QLoRA')`; requests=2; 1342 in / 222 out | Same two calls, llm_calls=2; 1620 in / 201 out |
| RAG とは何ですか？ | `search_glossary('RAG')` ×2; requests=3; 1623 in / 166 out; said it is not in the glossary, then added a general explanation | `search_glossary('RAG')` ×2; llm_calls=3; 1989 in / 207 out; `trace.py`: same pattern (not in glossary + general explanation); `adk run`: refused to guess and suggested looking up a lecture instead |
| 第2回の確認問題を1問 | `make_quiz({'lecture': 2})`; requests=2; 896 in / 93 out; showed the answer right after the question | `make_quiz({'lecture': 2})`; llm_calls=2; 1143 in / 68 out; did not show the answer (3 times: PEFT, QLoRA, 学習率), and offered to check it later |

- 気づき・疑問：
  - The tool-calling behavior was the same in both harnesses: the same tools, the same arguments (one term per search, `lecture=2`), and the same number of LLM calls. This is expected, because the model, the instructions and the docstrings are identical, and the docstrings decide how the tools are called.
  - The harness changed the cost. With identical tool calls, ADK used about 20–28% more input tokens (1620 vs 1342, 1989 vs 1623, 1143 vs 896). Part of this is visible: ADK wraps every tool's return value as `{'result': '...'}` and adds its own agent metadata. The INSTRUCTIONS line I added in 実装 is only about 40–50 tokens (in Basic, removing one line saved 48), so it cannot explain a gap of 250–350 tokens. This matches the lecture's point that the same model can cost differently depending on the harness.
  - Answer differences (ending with 第N回, hiding the quiz answer, refusing vs. explaining RAG) also appeared between two runs of the same ADK agent (`adk run` vs `trace.py` for RAG), so with this few runs I cannot say they come from the harness rather than random variation. The token difference is consistent across all questions, so I consider it the more reliable finding.
  - Pydantic AI was easier to test and observe in my own code: the model can be replaced with `TestModel`, and `all_messages()` gives the full history after one call. ADK gives more out of the box (`adk run`, `adk web`, an event stream) and makes each step visible as an event, but the loop and the extra prompt content are less visible from the code, and I needed my own script to count calls and tokens.
  - `INSTRUCTIONS` now mentions `save_learning_log`, but the ADK agent does not have that tool. Reusing instructions across harnesses requires keeping them in sync with the tool list; otherwise the model is told to use a tool that does not exist.
  - Question / limitation: the Pydantic AI runs were done on different days (and some before the 実装 changes), and each question was run only once or twice. A stricter comparison would run each question several times on both harnesses in the same session.
