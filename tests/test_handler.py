import sys
import types


def test_invalid_job_returns_failure(monkeypatch):
    monkeypatch.setitem(sys.modules, "runpod", types.SimpleNamespace(serverless=types.SimpleNamespace(start=lambda _: None)))
    monkeypatch.setitem(sys.modules, "boto3", types.SimpleNamespace(client=lambda *a, **k: None))
    monkeypatch.setitem(sys.modules, "botocore", types.ModuleType("botocore"))
    monkeypatch.setitem(sys.modules, "botocore.exceptions", types.SimpleNamespace(ClientError=Exception))
    sys.modules.pop("app.storage", None)
    sys.modules.pop("handler", None)
    from handler import handler

    result = handler({"id": "job-1", "input": {"task_type": "video_generation", "mode": "t2v"}})
    assert result["status"] == "failed"
    assert result["task_id"] == "job-1"
    assert "prompt" in result["error"]
