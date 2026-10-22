"""第1回: 素のLLMに質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする
    uv run python -m app.ask --chat     # 会話履歴を保ったまま続けて質問する（宿題: 実装）

単発モードはツールも会話履歴も持たない「素の」呼び出し。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse

from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def print_usage(response) -> None:
    """入力トークン数と出力トークン数を表示する。"""
    usage = response.usage_metadata
    if usage is None:
        print("\n[tokens] (usage_metadata なし)")
        return
    print(
        f"\n[tokens] 入力={usage.prompt_token_count} "
        f"出力={usage.candidates_token_count} "
        f"合計={usage.total_token_count}"
    )


def ask(question: str) -> str:
    client = genai.Client(api_key=get_api_key())
    response = client.models.generate_content(model=MODEL, contents=question)

    # 第1回 演習: 入力トークン数と出力トークン数を表示する
    print_usage(response)

    return response.text


def chat_loop() -> None:
    """会話履歴を保ったまま、続けて質問できるモード（宿題: 実装）。

    API 自体は前の発言を覚えていない（stateless）。
    client.chats が履歴を保持し、毎回これまでの会話をまとめて送っている。
    """
    client = genai.Client(api_key=get_api_key())
    chat = client.chats.create(model=MODEL)
    print("会話モード。exit / quit / 空行で終了。\n")

    while True:
        try:
            question = input("あなた> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if question in ("", "exit", "quit"):
            break

        try:
            response = chat.send_message(question)
        except errors.APIError as e:
            # エラーでも会話は終了せず、もう一度入力できるようにする
            print(api_error_message(e.code, e.message))
            continue

        print(f"\nAI> {response.text}")
        print_usage(response)
        print(f"[履歴] {len(chat.get_history())} 件\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    parser.add_argument(
        "--chat", action="store_true", help="会話履歴を保ったまま続けて質問する"
    )
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    try:
        if args.chat:
            chat_loop()
        else:
            print(f"[質問] {args.question}\n")
            print(ask(args.question))
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()