# 第1回 解答

## 演習

- 講座に固有の質問（宿題の3レベル）へのモデルの回答（要約でよい）：Neither gemini-3.5-flash-lite nor gemini-3.8-flash said "I don't know" (3 runs each). Both guessed AIE2026 was something like an "AI engineer training program 2026" and described three generic difficulty levels (e.g. Basic / Standard / Advanced, with examples like fill-in-the-blank exercises, accuracy tuning, RAG or SOTA methods). 3.8-flash gave longer, more structured answers and in one run guessed the course was "affiliated with Matsuo Lab". Both added disclaimers such as "please check the official course materials".

- 用語集の正しい意味と比べて気づいたこと：  The glossary defines the levels as 基礎 (review the lecture), 実装 (write your own code) and 発展 (investigation and experimentation); completing any one of them finishes the homework, and as a rule it is not graded. The "three stages" framing matched by coincidence, but the content was invented. 3.8-flash even confidently stated the opposite of the truth ("Level 1 is required", "Level 2+ for a higher evaluation"). The stronger model was more convincing, not more correct. Answers also varied between runs.

- 表示できたトークン数（入力 / 出力）：   "LoRAとは何ですか？" on gemini-3.5-flash-lite: input 7 / output 511–660 (3 runs). The one-sentence version: input 14 / output 49–51.


## 宿題

- 取り組んだレベル：基礎 / 実装 / 発展（all three）

- やったこと：
  - **基礎:** Ran "LoRAとは何ですか？" and the 3-levels question 3 times each on gemini-3.5-flash-lite and gemini-3.8-flash (switched with `AIE_MODEL`), saved outputs to `lectures/01/logs/`, and compared them.
  - **実装:** Added a `--chat` mode to `app/ask.py` using `client.chats.create()`, so the conversation history is kept and resent every turn. It prints input/output tokens and history length each turn.
  - **発展:** Wrote `app/bench.py` to measure response time, input/output/thinking tokens and output tokens per second for 2 models × 3 questions (short / long / course-specific) × 3 runs, saved to `lectures/01/logs/bench.csv`, with waits between calls to respect RPM limits.

- 結果：
  - **基礎:** For LoRA, both models were mostly correct every time, but examples, numbers and wording changed each run; flash-lite had small typos (e.g. "ファストリーニング" instead of ファインチューニング). 3.8-flash was more detailed (origin: Microsoft 2021, low-rank decomposition, distinction from IoT "LoRa"). For the 3-levels question, see 演習 above. 3.8-flash once returned **503 (model overloaded)**.
  - **実装:** Turn 1 "私の名前はミンです。" → input 6 / output 20, history 2. Turn 2 "私の名前は何ですか？" → the model answered "ミンさんです！", input 33 / output 4, history 4. Input tokens in turn 2 ≈ previous question (6) + previous answer (20) + new question (~7), confirming the whole history is resent.
  - **発展:** gemini-3.5-flash-lite, 3 runs each, all successful:

  - **発展:** 
      | Question | Avg time | Avg output tokens | Avg output tok/s |
    |---|---|---|---|
    | short (one sentence) | 0.84 s | 50 | ~59 |
    | long (LoRA) | 3.08 s | 609 | ~198 |
    | course (3 levels) | 2.74 s | 527 | ~193 |

    Input tokens were 7–21; thinking tokens were 0.
    gemini-3.8-flash: almost every call failed — 503 (overloaded, 3.5–11 s) and repeated 504 Gateway Timeout (~58.5 s), even for the one-sentence question. No 429 occurred. Speed and tokens could not be measured.

- 気づき・疑問：
  - An LLM does not say "I don't know" for things outside its knowledge; it fills the gap with plausible general knowledge. A more capable model does not fix this, so course-specific facts need an external source (to be addressed with the glossary-search agent in Lecture 3).
  - The API is stateless: "memory" in chat mode is just resending the whole history, so input tokens (and cost / tokens-per-minute usage) grow with every turn.
  - On the free tier, 3.8-flash (5 RPM, ~10–20 requests/day, occasional 503) is only practical for a few trials; repeated experiments are realistic only with flash-lite. 
  - Question: Do failed 503/504 calls officially count toward the free-tier daily quota? Would setting temperature (now deprecated) still change the output variation?