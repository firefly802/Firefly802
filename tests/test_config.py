import os
import sys
import importlib

# ensure project root is on sys.path so modules package can be imported
top = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if top not in sys.path:
    sys.path.insert(0, top)


def test_email_creds_from_env(monkeypatch, tmp_path, capsys):
    # Set environment variables temporarily
    monkeypatch.setenv("EMAIL_ACCOUNT", "test@example.com")
    monkeypatch.setenv("EMAIL_PASSWORD", "pass123")
    # reload config to pick up env changes
    config = importlib.reload(importlib.import_module('modules.config'))
    assert config.EMAIL_ACCOUNT == "test@example.com"
    assert config.EMAIL_PASSWORD == "pass123"
    assert config.IMAP_SERVER == "imap.gmail.com"
