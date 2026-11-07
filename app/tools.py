"""第3回: エージェントに持たせるツール。

ここに書いた関数の docstring と型ヒントが、そのままモデルへの「ツールの説明文」になる。
説明文を書き換えると、モデルがツールを使うかどうか・どんな引数で呼ぶかが変わる。
"""

import json
import random
import re
from datetime import datetime
from functools import cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
LOG_DIR = Path(__file__).resolve().parent.parent / "learning_log"
MAX_LOG_CHARS = 4000
MAX_RESULTS = 3


@cache
def load_glossary() -> list[dict]:
    with open(DATA_DIR / "glossary.json", encoding="utf-8") as f:
        return json.load(f)["terms"]


def _normalize(text: str) -> str:
    return text.casefold().replace(" ", "").replace("　", "")


def _names(entry: dict) -> list[str]:
    return [_normalize(entry["term"]), _normalize(entry["id"])] + [
        _normalize(a) for a in entry["aliases"]
    ]


def search_glossary(query: str) -> str:
    """講座の用語集から用語を検索し、定義と、どの回で扱うかを返す。

    AIエンジニアリングの用語や、この講座（AIE2026）に固有の言葉について
    答える前に使うこと。query には調べたい用語を1つだけ入れる（例: "LoRA"）。
    """
    q = _normalize(query)
    if not q:
        return "検索語が空です。調べたい用語を1つ指定してください。"
    glossary = load_glossary()

    exact = [e for e in glossary if q in _names(e)]
    # 「r」のような短い別名が何にでも当たらないよう、名前側が短いものは除く
    partial = [
        e for e in glossary
        if e not in exact and any(q in n or (len(n) >= 3 and n in q) for n in _names(e))
    ]
    in_definition = [
        e for e in glossary
        if e not in exact and e not in partial and q in _normalize(e["definition"])
    ]
    hits = (exact + partial + in_definition)[:MAX_RESULTS]

    if not hits:
        return f"用語集に「{query}」は見つかりませんでした。"
    return json.dumps(
        [
            {
                "term": e["term"],
                "lecture": e["lecture"],
                "definition": e["definition"],
                "related": e["related"],
            }
            for e in hits
        ],
        ensure_ascii=False,
    )


def get_lecture_summary(lecture: int) -> str:
    """指定した回（1始まりの整数）の講義の要点を返す。

    「第3回では何を学ぶ？」のように、回の内容や関係を聞かれたときに使う。
    """
    path = DATA_DIR / "lectures" / f"{lecture:02d}.md"
    if not path.exists():
        available = sorted(p.stem for p in (DATA_DIR / "lectures").glob("*.md"))
        return f"第{lecture}回の要点はまだありません。用意されている回: {', '.join(available)}"
    return path.read_text(encoding="utf-8")


def make_quiz(lecture: int) -> str:
    """指定した回の用語から1つを選び、確認問題と答えを返す。

    「第2回の確認問題を出して」のように、復習用の問題を求められたときに使う。
    lecture には回の番号（1始まりの整数）を入れる。
    """
    terms = [e for e in load_glossary() if e["lecture"] == lecture]
    if not terms:
        return f"第{lecture}回の用語は用語集にありません。"
    e = random.choice(terms)
    return json.dumps(
        {"question": f"「{e['term']}」の意味は？", "answer": e["definition"]},
        ensure_ascii=False,
    )


def _safe_slug(text: str) -> str:
    """ファイル名に使える文字だけを残す（"../" などでフォルダの外に出ないようにする）。"""
    slug = re.sub(r"[^\w\-]+", "-", text, flags=re.UNICODE).strip("-_")
    return slug[:40] or "log"


def save_learning_log(title: str, content: str, lecture: int | None = None) -> str:
    """学習の記録を learning_log/ フォルダに Markdown ファイルとして保存する。

    利用者が「今日学んだことを記録して」「この内容をメモに残して」のように、
    記録の保存をはっきり頼んだときだけ使う。頼まれていないのに使わない。
    title には記録の短い題名、content には保存する本文（要点を箇条書きなど）、
    lecture には関係する回の番号（分からなければ省略）を入れる。
    ファイルに書き込む操作なので、実行の前に利用者の承認が必要。
    """
    if not content.strip():
        return "保存する内容が空です。何を記録するか指定してください。"
    if len(content) > MAX_LOG_CHARS:
        return f"内容が長すぎます（{len(content)}字）。{MAX_LOG_CHARS}字以内に要約してください。"
    LOG_DIR.mkdir(exist_ok=True)
    body = f"# {title}\n\n"
    if lecture is not None:
        body += f"- 関係する回: 第{lecture}回\n"
    body += f"- 保存日時: {datetime.now():%Y-%m-%d %H:%M}\n\n{content.strip()}\n"
    # 同じ題名・同じ本文がすでに保存されていれば、二重に作らない（冪等性）
    for existing in LOG_DIR.glob("*.md"):
        text = existing.read_text(encoding="utf-8")
        if text.startswith(f"# {title}\n") and text.rstrip().endswith(content.strip()):
            return f"同じ記録がすでにあります: learning_log/{existing.name}（新しくは作りませんでした）"
    stem = f"{datetime.now():%Y-%m-%d}_{_safe_slug(title)}"
    path = LOG_DIR / f"{stem}.md"
    n = 2
    while path.exists():  # 既存のファイルは上書きしない
        path = LOG_DIR / f"{stem}_{n}.md"
        n += 1
    path.write_text(body, encoding="utf-8")
    return f"保存しました: learning_log/{path.name}"