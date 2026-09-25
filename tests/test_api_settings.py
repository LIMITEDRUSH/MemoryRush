import json

import pytest
from streamlit.testing.v1 import AppTest
from test_chat_ui import APP, button

from app.model_settings import get_provider
from memoryrush.api import APIConfig
from memoryrush.bank import MemoryBank

SECRET = "fixture-only-session-token"


def widget(app, kind, label):
    return next(w for w in getattr(app, kind) if w.label == label)


def test_api_settings_are_opt_in_and_do_not_persist_secret(tmp_path, monkeypatch):
    monkeypatch.setenv("MEMORYRUSH_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("MEMORYRUSH_PROVIDER", "llama.cpp")
    monkeypatch.setattr(
        "urllib.request.OpenerDirector.open",
        lambda *a, **k: pytest.fail("Settings must never contact the API"),
    )
    app = AppTest.from_string(
        "from app.model_settings import settings_dialog\n"
        "from memoryrush.bank import MemoryBank\n"
        "settings_dialog(MemoryBank())\n"
    ).run()
    widget(app, "selectbox", "模型接口").select("api").run()
    widget(app, "text_input", "模型 ID").set_value("fixture-model")
    widget(app, "text_input", "API Base URL / 完整地址").set_value("https://models.example.test/v1")
    widget(app, "text_input", "API Key（仅本次浏览器会话）").set_value(SECRET)
    button(app, "保存并使用").click().run()
    assert not app.exception
    assert MemoryBank().setting("provider") == ""
    assert app.error and "确认" in app.error[0].value
    app.checkbox[0].check()
    button(app, "保存并使用").click().run()
    bank = MemoryBank()
    assert not app.exception
    assert bank.setting("provider") == "api"
    config = json.loads(bank.setting("api_config"))
    assert config["model"] == "fixture-model"
    assert SECRET not in bank.path.read_bytes().decode("latin1")
    assert app.session_state["api_credentials"][config["endpoint"]] == SECRET
    button(app, "清除本次会话中的 API 密钥").click().run()
    assert "api_credentials" not in app.session_state


def test_missing_api_key_keeps_history_accessible_and_disables_send(tmp_path, monkeypatch):
    monkeypatch.setenv("MEMORYRUSH_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("TEST_MISSING_API_KEY", raising=False)
    bank = MemoryBank()
    config = APIConfig("https://models.example.test", "fixture", key_env="TEST_MISSING_API_KEY")
    bank.setting("provider", "api")
    bank.setting("api_config", json.dumps(config.public_dict()))
    bank.setting("api_approved", config.endpoint)
    app = AppTest.from_file(str(APP)).run()
    assert not app.exception
    assert app.chat_input[0].disabled
    assert any("密钥" in w.value for w in app.warning)
    assert button(app, "设置") and button(app, "已读文章")


def test_session_key_is_not_forwarded_to_changed_endpoint(tmp_path, monkeypatch):
    bank = MemoryBank(tmp_path / "test.db")
    config = APIConfig("https://different.example.test", "fixture", key_env="TEST_MISSING_API_KEY")
    bank.setting("provider", "api")
    bank.setting("api_config", json.dumps(config.public_dict()))
    bank.setting("api_approved", config.endpoint)
    monkeypatch.delenv("TEST_MISSING_API_KEY", raising=False)
    monkeypatch.setattr(
        "app.model_settings.st.session_state",
        {
            "api_credentials": {
                "https://original.example.test/chat/completions": SECRET,
            }
        },
    )
    with pytest.raises(ValueError, match="密钥"):
        get_provider(bank)
