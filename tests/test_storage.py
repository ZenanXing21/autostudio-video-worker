import sys
import types
from pathlib import Path

import pytest


def test_missing_s3_uses_persistent_local_storage(tmp_path):
    from app.config import Settings
    from app.storage import LocalStorage, storage_from_settings

    settings = Settings(s3_bucket="", local_output_dir=tmp_path / "outputs")
    store = storage_from_settings(settings)
    assert isinstance(store, LocalStorage)
    assert not store.existing("job")

    source = tmp_path / "comfy.mp4"
    source.write_bytes(b"mp4")
    assert store.store(source, "job") == {
        "video_url": None,
        "output_path": str(tmp_path / "outputs" / "job.mp4"),
    }
    assert (tmp_path / "outputs" / "job.mp4").read_bytes() == b"mp4"
    assert storage_from_settings(settings).existing("job")


def test_local_storage_rejects_empty_mp4(tmp_path):
    from app.config import Settings
    from app.storage import storage_from_settings

    source = tmp_path / "empty.mp4"
    source.touch()
    store = storage_from_settings(Settings(s3_bucket="", local_output_dir=tmp_path / "outputs"))
    with pytest.raises(RuntimeError, match="nonempty MP4"):
        store.store(source, "job")
    assert not store.existing("job")


def test_upload_and_presigned_url(monkeypatch, tmp_path):
    class ClientError(Exception):
        def __init__(self, code):
            self.response = {"Error": {"Code": code}}

    class FakeS3:
        def head_object(self, **kwargs):
            raise ClientError("404")

        def upload_file(self, path, bucket, key, ExtraArgs):
            assert Path(path).read_bytes() == b"mp4"
            assert bucket == "bucket" and key == "videos/job.mp4"
            assert ExtraArgs["ContentType"] == "video/mp4"

        def generate_presigned_url(self, operation, Params, ExpiresIn):
            assert operation == "get_object" and ExpiresIn == 3600
            return "https://example.com/signed"

    monkeypatch.setitem(sys.modules, "boto3", types.SimpleNamespace(client=lambda *a, **k: FakeS3()))
    monkeypatch.setitem(sys.modules, "botocore", types.ModuleType("botocore"))
    monkeypatch.setitem(sys.modules, "botocore.exceptions", types.SimpleNamespace(ClientError=ClientError))
    sys.modules.pop("app.storage", None)
    from app.storage import S3Storage, storage_from_settings
    from app.config import Settings

    store = storage_from_settings(Settings(s3_bucket="bucket"))
    assert isinstance(store, S3Storage)
    assert not store.existing("job")
    path = tmp_path / "job.mp4"
    path.write_bytes(b"mp4")
    assert store.upload(path, "job") == "https://example.com/signed"
