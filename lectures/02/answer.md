# 第2回 解答

## 演習

- 使ったモデル・設定（`result.json` の `config` から）：Qwen/Qwen3.5-0.8B (revision 2fc06364715b967f1860aea9cf38778875588b17), LoRA without quantization; num_train_epochs 20, lr 2e-4, lora_r 16, lora_alpha 32, warmup_steps 6, max_seq_len 512, max_new_tokens 96, seed 42, greedy decoding (do_sample=False). Training: 245 s, 40 steps on a Colab T4; loss 1.564 → 0.085 → 0.019 → 0.014 (steps 10/20/30/40).
- 自分で学習を実行したか（`executed_training_myself`）：はい (true). I ran Sections 0–8, including the optional 4-bit section.
- 学習前：`format_rate` = 0.095 (2/21) / `content_rate` = 0.000 (0/21)
- 学習後：`format_rate` = 1.000 (21/21) / `content_rate` = 0.905 (19/21)
- 退行した質問：None (`regressed` is empty).
- 学習後に残った失敗と、その型（根拠なしの質問に断定した / 根拠ありの質問に確認要求で逃げた / 形式の崩れ）：2 questions, both of the type "asserted an answer to an ungrounded question". 「成績はいつ出ますか」 ("When will grades be released?") was answered with the FAQ deadline sentence, and 「オフィスアワーは事前予約が必要ですか」 ("Do office hours require a reservation?") with the FAQ office-hours sentence, both with needs_review: false. The model picked an FAQ item that shares a word with the question (「いつ」, 「オフィスアワー」). There were no format failures and no avoidance of grounded questions.
- 知識を問う質問（セクション 6）の結果（学習前の分類 → 学習後の分類）と気づいたこと：Final assignment deadline: format_error → asserted (it reused the FAQ's assignment deadline, Sept 30 23:59, which is a fabricated answer). Instructor's name: format_error → needs_review. Next lecture's topic: format_error → needs_review. Control (assignment deadline, which is in the FAQ): format_error → asserted (correct). The model treats "final assignment deadline" and "assignment deadline" as the same because the wording is close, so it judges by surface similarity, not by whether evidence exists. Note: result.json shows the control as 「FAQ にある: false」 only because it is a training question rather than a test question; it is in the FAQ.
- 学習で変わったこと・変わらなかったこと：Changed: even with JSON requested in the prompt, most outputs before training lacked needs_review; a few minutes of LoRA training made all 21 outputs follow the format and match the FAQ wording, with no regressions. Not changed: judging whether the FAQ actually supports an answer; the model still asserted answers to questions containing related words. Training changes the format, but it does not guarantee correct behavior on things the model does not know. (Optional 4-bit Section 8: without any training, loading in 4-bit changed format_rate from 0.095 to 0.667 and content_rate from 0.000 to 0.333, with changes in both directions, so before/after comparisons must use the same quantization setting.)

## 宿題

### 基礎

- 取り組んだレベル：基礎
- 変えた設定やデータ：`num_train_epochs` 20 → 5 (everything else identical; Runtime → Restart session, then ran from the top).
- 結果（比較表や数字）：

| Metric | Original (20 epochs) | Changed (5 epochs) |
|---|---|---|
| Steps | 40 | 10 |
| Training time | 245 s | 62 s |
| Training loss | step 10: 1.564 → step 40: 0.014 | step 10: 1.571 (only one logged value) |
| format_rate | 1.000 (21/21) | 1.000 (21/21) |
| content_rate | 0.905 (19/21) | 0.762 (16/21) |
| Regressions | none | none |
| Grounded questions correct (15) | 15/15 | 13/15 |
| Ungrounded questions correct (6) | 4/6 | 3/6 |
| Ungrounded questions with needs_review: true (6) | 4/6 | 5/6 |

  Note: the 5-epoch loss of 1.571 is the average over steps 1–10, so it includes the large values at the start of training. Since format_rate reached 1.0, the model learned more than the loss number suggests.

- ファインチューニングが向く場面・向かない場面についての考察：
  - Appropriate: making the output format (JSON, keys, types), fixed phrasing, or answer style consistent. Here, a few dozen examples and a few minutes of training achieved 100% format compliance that prompt instructions alone could not.
  - Not appropriate: teaching the model to say "I don't know" for things it does not know, or to use new facts correctly. Unsupported assertions remained even with more training and sometimes increased. Handling facts that are not in the FAQ is better guaranteed by a mechanism outside the model, such as retrieval (RAG) that supplies evidence and returns "needs confirmation" when none is found.
  - More training is not simply better: it shifts the balance between format, wording, and caution. Every setting change should be measured on the same evaluation set, including ungrounded questions.

### 実装

- 取り組んだレベル：実装
- 変えた設定やデータ：
  - Topic: Binance, "Frequently Asked Questions on Binance Spot OTC Trading" (updated 2025-10-27), https://www.binance.com/en/support/faq/detail/557f95eaf8fb4460aed0a891d42a1425
  - I chose 5 of the original 12 items (fees, trade size, settlement, eligibility, contact) and summarized each in one sentence. All questions and answers are in English, and the SYSTEM prompt was also rewritten in English. The fixed answer for ungrounded questions is "This FAQ does not cover this. Please confirm with the OTC desk." and the required word is "confirm". Training settings are the same as the original (20 epochs, lr 2e-4, lora_r 16). The JSON format and the needs_review design are unchanged. I trained 3 times with the same settings.
  - How I prepared the ungrounded questions:
    - The 8 questions used for train / valid / test come from topics that are in the original Binance FAQ but not among my 5 items (RFQ, IOI, fiat currencies, API, number of trading pairs, fiat deposits/withdrawals, legal terms, how prices are determined). Real answers exist, but the FAQ given to the model contains no evidence.
    - The 4 test-only questions are deliberate near-misses that share words with an FAQ item ("How can I trade less than 200,000 USD?", "Is there a spread in addition to fees?", "What happens if settlement is delayed?", "How long does identity verification take?"). The original exercise showed the model asserting FAQ items that contain related words, so these questions target that failure.
- 結果（比較表や数字）：

  In runs 1 and 2 the required word for ungrounded questions in the grading code was wrong (in run 1 it was still the Japanese 「確認」; in run 2 a typo made it `["NEED"]` instead of the variable `NEED = ["confirm"]`). Run 3 was executed with corrected grading. For runs 1 and 2, values corrected by manual inspection are also shown.

| Metric | Before | After, run 1 | After, run 2 | After, run 3 |
|---|---|---|---|---|
| format_rate | 1.000 (21/21) | 1.000 | 1.000 | 1.000 |
| content_rate (automatic grading) | 0.238 (5/21) | 0.667 (grading error) | 0.619 (grading error) | 0.810 (17/21) |
| content_rate (correct grading / manual correction) | 0.238 | 0.714 (15/21) | 0.905 (19/21) | 0.810 (17/21) |
| needs_review correct, grounded (15) | 6/15 | 15/15 | 14/15 | 13/15 |
| needs_review correct, ungrounded (6) | 6/6 | 1/6 | 6/6 | 5/6 |
| Regressions | — | none | none | none |
| Training time | — | 216 s | — | 213 s |
| Training loss (step 10/20/30/40) | — | 1.625 / 0.067 / 0.015 / 0.013 | — | 1.634 / 0.067 / 0.015 / 0.013 |

  - The "before" outputs were identical in all 3 runs (greedy decoding, same base model). Only the post-training outputs differed, even though the loss curves were nearly identical.
  - With an English prompt, the model already followed the format 21/21 before training (vs. 0.095 for the Japanese course FAQ). Before training it tended to set needs_review to true, even for 9 of the 15 grounded questions (too cautious).
  - After training, in all 3 runs, most grounded questions were answered with the FAQ wording and needs_review: false.
  - For the 6 ungrounded questions, results changed greatly just by retraining with the same settings and seed:
    - Run 1: 5 of 6 were asserted using another FAQ item, including all 4 near-miss questions (e.g. "Is there a spread in addition to fees?" → "There are no fees to trade Spot OTC."). For "Is OTC trading available via API?" it invented an incorrect answer: "only available manually, not via API" (the original Binance FAQ says API trading is supported).
    - Run 2: all 6 were answered with the fixed phrase and needs_review: true. In exchange, it avoided the grounded question "Can I receive settlement in a sub-account?".
    - Run 3: 5 of 6 were answered with the fixed phrase. Only "What happens if settlement is delayed?" was asserted using the settlement item. The grounded questions "Trade size limits?" and "Can I receive settlement in a sub-account?" were avoided.
  - Knowledge questions (Section 6): business hours and daily trade limit were needs_review in all runs; "Can I pay with a credit card?" was asserted in run 1 (reused the eligibility sentence) but needs_review in runs 2 and 3; the control question (fees, in the FAQ) was correctly asserted in all runs.
  - Evaluation design: "What is the largest amount I can trade at once?" was answered correctly ("There is no maximum trade size...") but marked wrong in all runs because the required word was "200,000 USD". One FAQ item contains two facts, so required words should differ per question.

- ファインチューニングが向く場面・向かない場面についての考察：
  - Check before fine-tuning: with the Japanese course FAQ, training mainly fixed the format; with the English FAQ, the format was already correct before training, and training mainly changed how needs_review was set and how consistent the wording was. Whether fine-tuning is needed should be checked with a pre-training evaluation first; sometimes the prompt alone is enough.
  - Stable vs. unstable: the answer pattern for grounded questions was almost identical across 3 runs, but judgment on ungrounded questions changed from 5/6 asserted to 0/6 to 1/6, and content_rate ranged from 0.714 to 0.905. Training reliably teaches the answer pattern, but not the judgment to say "I don't know" (with about 14 training examples).
  - When a run leans toward caution it avoids grounded questions; when it leans toward confidence it invents answers to ungrounded ones. Comparing settings from a single run is risky; train several times and look at the variance. (The Basic-level difference, 0.905 vs. 0.762, may be within this variance.)
  - A small bug in the evaluation code changed a score from 0.905 to 0.619, so grading must always be checked against the raw outputs.
  - For a financial-service FAQ, where a wrong assertion (like the invented API answer) can cause user losses, the judgment of whether evidence exists should not be left to training alone. A mechanism outside the model should retrieve evidence and escalate to a human when none is found.

### 発展

- 取り組んだレベル：発展
- 変えた設定やデータ：
  - Data: ran `uv run python scripts/make_sft_dataset.py > glossary_sft.jsonl` in Codespaces and uploaded the file to Colab. 58 glossary terms × 2 templates (「{term}」とは何ですか？ / {term}について簡単に説明してください。) = 116 examples, user / assistant only (no system message). Trained on this instead of the FAQ.
  - Training: LoRA (no quantization), lr 2e-4, lora_r 16, lora_alpha 32, seed 42, 3 epochs (116 examples ÷ 8 per step ≈ 45 steps, similar to the FAQ's 40 steps). Training time: 102 s. Training loss: 3.704 (step 5) → 2.849 (10) → 1.947 (20) → 1.725 (30) → 1.328 (40) → 1.221 (45).
  - Generation: greedy, max_new_tokens 160 (definitions are longer than FAQ sentences).
  - Evaluation questions (my own, 18) and answers:

| Type | Count | Content | Grading |
|---|---|---|---|
| 1. In the glossary | 6 | Same wording as training (LoRA, temperature, ハルシネーション, fork, MCP, エポック) | Contains the definition's keywords (e.g. LoRA: 「低ランク」 and 「第2回」; MCP: 「プロトコル」 and 「第5回」) |
| 2. Reworded | 6 | Same terms via aliases or different phrasing (Low-Rank Adaptation, 温度パラメータ, 幻覚, フォーク, Model Context Protocol, and a reverse question: "what is one full pass over the training data called?") | Same as above |
| 3. Not in the glossary | 6 | RAG, 埋め込み (embedding), プロンプトインジェクション (prompt injection), Transformer, 知識蒸留 (knowledge distillation), ベクトルデータベース (vector database) | Admits the term is not in the glossary / it does not know |

  Course-specific facts ("LoRA is covered in Lecture 2", "MCP is tried out in Lecture 5") cannot be known by the base model, so I included them as required words to mark whether knowledge was acquired. As a secondary metric, I measured string similarity (difflib) between the output and the glossary definition.

- 結果（比較表や数字）：

| Type | Accuracy, before | Accuracy, after | Similarity to definition, before | Similarity to definition, after |
|---|---|---|---|---|
| 1. In the glossary | 0.17 (1/6) | 0.17 (1/6) | 0.06 | 0.33 |
| 2. Reworded | 0.17 (1/6) | 0.00 (0/6) | 0.12 | 0.20 |
| 3. Not in the glossary | 0.00 (0/6) | 0.00 (0/6) | — | — |

  - Before training, the model gave long answers based on general meanings and knew nothing about the course context: it described temperature as physical temperature, ハルシネーション as a physics phenomenon, and エポック as "an era". For MCP it wrongly said 「第 1 回で体験します」 ("tried out in Lecture 1").
  - After training, the answers took the shape of glossary definitions (1–3 sentences, 「〜する手法。」, 「本講座では〜」), and similarity to the definitions rose from 0.06 to 0.33. For fork it answered in the course context: 「本講座では自分の repo を fork して…」.
  - However, almost none of the actual facts were learned:
    - LoRA: incorrectly described as 「入力変数の 1% 程度を削除する手法」 ("a method that removes about 1% of the input variables"). In the reworded question it said 「本講座では第 1 回で扱っている」 (wrong lecture; correct is Lecture 2).
    - MCP: 「第 5 回」 never appeared, and in the reworded question it invented a story about the Lecture 1 exercise.
    - For ハルシネーション and the reworded 「幻覚」, the answers mixed in descriptions of other topics, such as "learning the question format and the JSON output format".
  - For the 6 terms not in the glossary, the model never said "not in the glossary", either before or after training. After training, it invented short, confident definitions imitating the glossary style. Examples: 埋め込み → 「モデルの出力を特定の形式にまとめること」 ("summarizing model output into a specific format", wrong); ベクトルデータベース → 「Pydantic AI では Pydantic Vector Database（PVD）で実装できる」 (a non-existent product name, mixed with the glossary term Pydantic AI).

- ファインチューニングが向く場面・向かない場面についての考察（用語集を検索する仕組みとの比較）：

| Aspect | Training on the glossary (this experiment) | Searching the glossary and passing results (RAG / tool) |
|---|---|---|
| Accuracy | With 3 epochs and 116 examples, definition facts (lecture numbers, mechanisms) were barely learned, and plausible errors increased | Can use the exact definition text as evidence and cite its source (term ID) |
| Terms not in the glossary | Cannot say "not found"; invents answers in the glossary style. Training examples for this are also hard to create | A search miss is detectable, so it can reliably answer "not in the glossary" |
| Rewording / aliases | The answer style generalized, but the facts did not | Robust to aliases if search uses the `aliases` field; semantic paraphrases need extra work such as embedding search |
| Updates | Every new term requires retraining and re-evaluation | Editing the glossary JSON takes effect immediately |
| Speed / cost | Short prompts at inference time; no retrieval infrastructure needed | Retrieval overhead and more input tokens for the inserted definitions |
| Strength | Making the answer style consistent (short definitions, course tone) | Returning correct facts with evidence |

  - These results directly confirm the lecture's point that fine-tuning is strong for behavior and weak for adding knowledge. What training changed was the answer style (higher similarity); factual correctness did not improve and even dropped for reworded questions.
  - Three epochs were very likely not enough: the final loss was 1.22, far higher than the FAQ training (0.013), and still decreasing (each term was seen only 6 times). More epochs might let the model memorize definitions for the same wording, but inventing answers for terms not in the glossary, and retraining on every update, would not be solved by more training.
  - For a learning-support agent that answers term questions, facts should be supplied through glossary search (the Lecture 3 agent and the Lecture 5 MCP server), and fine-tuning, if used at all, should be limited to making the answer style consistent.
