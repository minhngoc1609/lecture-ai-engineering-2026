"""第3回 宿題（実装）: save_learning_log と承認の流れのテスト。API キー不要（TestModel を使う）。"""

from pydantic_ai import DeferredToolRequests, DeferredToolResults, ToolDenied
from pydantic_ai.messages import ToolReturnPart
from pydantic_ai.models.test import TestModel

from app import tools
from app.agent import agent


def _use_tmp_log_dir(monkeypatch, tmp_path):
    log_dir = tmp_path / "learning_log"
    monkeypatch.setattr(tools, "LOG_DIR", log_dir)
    return log_dir


def test_save_writes_markdown(monkeypatch, tmp_path):
    log_dir = _use_tmp_log_dir(monkeypatch, tmp_path)
    msg = tools.save_learning_log("LoRAの復習", "- 重みは固定\n- 小さな行列だけ学習", 2)
    files = list(log_dir.glob("*.md"))
    assert "保存しました" in msg and len(files) == 1
    text = files[0].read_text(encoding="utf-8")
    assert text.startswith("# LoRAの復習") and "第2回" in text and "小さな行列" in text


def test_title_cannot_escape_folder(monkeypatch, tmp_path):
    log_dir = _use_tmp_log_dir(monkeypatch, tmp_path)
    tools.save_learning_log("../../etc/passwd", "test")
    files = list(log_dir.glob("*.md"))
    assert len(files) == 1 and files[0].parent == log_dir
    assert not (tmp_path / "etc").exists()


def test_same_log_is_not_saved_twice(monkeypatch, tmp_path):
    log_dir = _use_tmp_log_dir(monkeypatch, tmp_path)
    tools.save_learning_log("復習", "同じ内容")
    msg = tools.save_learning_log("復習", "同じ内容")
    assert "すでにあります" in msg and len(list(log_dir.glob("*.md"))) == 1


def test_empty_and_too_long_are_rejected(monkeypatch, tmp_path):
    log_dir = _use_tmp_log_dir(monkeypatch, tmp_path)
    assert "空です" in tools.save_learning_log("t", "   ")
    assert "長すぎます" in tools.save_learning_log("t", "あ" * (tools.MAX_LOG_CHARS + 1))
    assert not log_dir.exists() or not list(log_dir.glob("*.md"))


def _request_save():
    model = TestModel(call_tools=["save_learning_log"])
    result = agent.run_sync("今日の学びを記録して", model=model)
    return model, result


def test_save_stops_for_approval_without_writing(monkeypatch, tmp_path):
    log_dir = _use_tmp_log_dir(monkeypatch, tmp_path)
    _, result = _request_save()
    assert isinstance(result.output, DeferredToolRequests)
    assert [c.tool_name for c in result.output.approvals] == ["save_learning_log"]
    assert not log_dir.exists()  # 承認されるまで何も書かれない


def test_approved_save_writes_file(monkeypatch, tmp_path):
    log_dir = _use_tmp_log_dir(monkeypatch, tmp_path)
    model, first = _request_save()
    call = first.output.approvals[0]
    results = DeferredToolResults(approvals={call.tool_call_id: True})
    second = agent.run_sync(message_history=first.all_messages(), deferred_tool_results=results, model=model)
    assert isinstance(second.output, str)
    assert len(list(log_dir.glob("*.md"))) == 1


def test_denied_save_writes_nothing_and_tells_model(monkeypatch, tmp_path):
    log_dir = _use_tmp_log_dir(monkeypatch, tmp_path)
    model, first = _request_save()
    call = first.output.approvals[0]
    results = DeferredToolResults(approvals={call.tool_call_id: ToolDenied("利用者が保存を許可しませんでした。")})
    second = agent.run_sync(message_history=first.all_messages(), deferred_tool_results=results, model=model)
    assert not log_dir.exists() or not list(log_dir.glob("*.md"))
    returns = [p for m in second.all_messages() for p in m.parts if isinstance(p, ToolReturnPart) and p.tool_name == "save_learning_log"]
    assert returns and "許可しませんでした" in str(returns[0].content)