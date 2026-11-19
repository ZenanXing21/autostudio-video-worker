import sys
import types


def test_local_video_result_returns_path_without_url(monkeypatch, tmp_path):
    monkeypatch.setitem(sys.modules, "runpod", types.SimpleNamespace(serverless=types.SimpleNamespace(start=lambda _: None)))
    sys.modules.pop("handler", None)
    import handler as worker
    from app.config import Settings
    from app.storage import storage_from_settings

    source = tmp_path / "comfy.mp4"
    source.write_bytes(b"mp4")

    class FakeComfy:
        def ready(self):
            return True

        def nodes(self):
            return set()

        def execute(self, graph, task_id, timeout):
            return source

    monkeypatch.setattr(worker, "settings", Settings(s3_bucket="", local_output_dir=tmp_path / "outputs"))
    monkeypatch.setattr(worker, "storage", storage_from_settings(worker.settings))
    monkeypatch.setattr(worker, "comfy", FakeComfy())
    monkeypatch.setattr(worker, "build_prompt", lambda *args: {})
    monkeypatch.setattr(worker, "validate_graph", lambda *args: None)

    job = {"id": "job-1", "input": {"task_type": "video_generation", "mode": "t2v", "prompt": "hello"}}
    result = worker.handler(job)
    assert result["status"] == "completed"
    assert result["video_url"] is None
    assert result["output_path"] == str(tmp_path / "outputs" / "job-1.mp4")
    assert (tmp_path / "outputs" / "job-1.mp4").read_bytes() == b"mp4"
    assert worker.handler(job)["cached"] is True


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


def test_initialize_without_s3_bucket(monkeypatch, tmp_path):
    monkeypatch.setitem(sys.modules, "runpod", types.SimpleNamespace(serverless=types.SimpleNamespace(start=lambda _: None)))
    sys.modules.pop("handler", None)
    import handler as worker
    from app.config import Settings
    from app.storage import LocalStorage

    class FakeComfy:
        def ensure_models(self):
            pass

        def start(self):
            pass

        def nodes(self):
            return set()

    monkeypatch.setattr(worker, "settings", Settings(s3_bucket="", local_output_dir=tmp_path / "outputs"))
    monkeypatch.setattr(worker, "comfy", FakeComfy())
    monkeypatch.setattr(worker, "check_gpu", lambda: "test GPU")
    monkeypatch.setattr(worker, "validate_graph", lambda *args: None)

    worker.initialize()

    assert isinstance(worker.storage, LocalStorage)
    assert (tmp_path / "outputs").is_dir()
