import sys
import types
from pathlib import Path


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
    from app.storage import ObjectStorage
    from app.config import Settings

    store = ObjectStorage(Settings(s3_bucket="bucket"))
    assert not store.existing("job")
    path = tmp_path / "job.mp4"
    path.write_bytes(b"mp4")
    assert store.upload(path, "job") == "https://example.com/signed"
