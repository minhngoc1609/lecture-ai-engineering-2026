"""宿題（発展）: 応答時間とトークン数を、モデル・質問ごとに計測する。

使い方:
    uv run python -m app.bench
"""

import csv
import os
import time

from google import genai
from google.genai import errors

from app.config import get_api_key

MODELS = ["gemini-3.5-flash-lite", "gemini-3.8-flash"]
QUESTIONS = {
    "short": "LoRAとは何ですか？一文で答えてください。",
    "long": "LoRAとは何ですか？",
    "course": "AIE2026の講座の宿題にある「3レベル」とは何ですか？",
}
N = 3  # 各組み合わせの実行回数
WAIT = {"gemini-3.5-flash-lite": 5, "gemini-3.8-flash": 15}  # RPM 対策の待ち時間（秒）
OUT = "lectures/01/logs/bench.csv"


def main() -> None:
    client = genai.Client(api_key=get_api_key())
    rows = []
    for model in MODELS:
        for qid, question in QUESTIONS.items():
            for i in range(1, N + 1):
                t0 = time.perf_counter()
                try:
                    r = client.models.generate_content(model=model, contents=question)
                    sec = time.perf_counter() - t0
                    u = r.usage_metadata
                    out_tok = u.candidates_token_count or 0
                    row = [model, qid, i, "ok", round(sec, 2),
                           u.prompt_token_count, out_tok,
                           u.thoughts_token_count or 0,
                           round(out_tok / sec, 1) if sec > 0 else ""]
                except errors.APIError as e:
                    sec = time.perf_counter() - t0
                    row = [model, qid, i, f"error {e.code}", round(sec, 2), "", "", "", ""]
                rows.append(row)
                print(row)
                time.sleep(WAIT[model])

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["model", "question", "run", "status", "sec",
                    "in_tok", "out_tok", "thought_tok", "out_tok_per_sec"])
        w.writerows(rows)
    print(f"\n保存しました: {OUT}")


if __name__ == "__main__":
    main()