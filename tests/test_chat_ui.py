from pathlib import Path

from streamlit.testing.v1 import AppTest

from memoryrush.bank import MemoryBank

APP = Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py"


def button(app, label):
    return next(b for b in app.button if b.label == label)


def test_chat_entry_history_and_rerun_do_not_duplicate(tmp_path, monkeypatch):
    monkeypatch.setenv("MEMORYRUSH_DATA_DIR", str(tmp_path))
    # An empty bank takes the evidence-insufficient path without contacting a model.
    monkeypatch.setenv("MEMORYRUSH_PROVIDER", "llama.cpp")
    app = AppTest.from_file(str(APP)).run()
    assert not app.exception
    assert len(app.chat_input) == 1
    assert not app.tabs  # Primary entry is the conversation, not a dashboard.
    assert MemoryBank().sessions() == []
    app.chat_input[0].set_value("我想理解记忆衰减").run()
    assert not app.exception
    bank = MemoryBank()
    session = bank.sessions()[0]["session_id"]
    assert len(bank.turns(session)) == 1
    assert len(app.chat_message) == 2
    app.run()
    assert len(bank.turns(session)) == 1
    button(app, "新对话").click().run()
    assert not app.exception
    assert len(app.chat_message) == 0
    assert len(bank.sessions()) == 1  # A blank draft is not a database conversation.
    app.chat_input[0].set_value("另一个问题").run()
    assert len(bank.sessions()) == 2
    button(app, "我想理解记忆衰减").click().run()
    assert not app.exception
    assert len(app.chat_message) == 2
    assert "我想理解记忆衰减" in [t.value for t in app.text]
    assert "另一个问题" not in [t.value for t in app.text]
    button(app, "记忆面板").click().run()
    assert not app.exception
    assert [tab.label for tab in app.tabs] == ["本次召回", "记忆"]


def test_pasted_reading_and_source_view_are_accessible(tmp_path, monkeypatch):
    monkeypatch.setenv("MEMORYRUSH_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("MEMORYRUSH_PROVIDER", "preview")
    # AppTest does not emulate browser fragment reruns; keep the dialog mounted
    # explicitly while testing its widgets, then reopen the full conversation.
    app = AppTest.from_string(
        "from app.streamlit_app import paste_dialog\n"
        "from memoryrush.bank import MemoryBank\n"
        "from memoryrush.providers import DeterministicPreviewProvider\n"
        "paste_dialog(MemoryBank(), DeterministicPreviewProvider())\n"
    ).run()
    next(t for t in app.text_area if t.label == "文章正文").set_value(
        "# UI fixture\n\nMemory strength changes over time."
    ).run()
    button(app, "发送到对话").click().run()
    assert not app.exception
    bank = MemoryBank()
    session = bank.sessions()[0]["session_id"]
    assert len(bank.turns(session)) == 1
    assert bank.turns(session)[0]["reading"]["title"] == "UI fixture"
    app = AppTest.from_file(str(APP)).run()
    assert len(bank.artifacts()) == 1
    button(app, "查看阅读记录").click().run()
    assert not app.exception
    assert any(t.label == "文章记录" for t in app.selectbox)
