import os
import shutil
import uuid
from pathlib import Path

from .config import Settings


def _validate_mp4(path: Path) -> None:
    if path.suffix.lower() != ".mp4" or path.stat().st_size == 0:
        raise RuntimeError("ComfyUI did not create a nonempty MP4")


class LocalStorage:
    def __init__(self, settings: Settings):
        self.output_dir = settings.local_output_dir.resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def path(self, task_id: str) -> Path:
        return self.output_dir / f"{task_id}.mp4"

    def existing(self, task_id: str) -> bool:
        path = self.path(task_id)
        return path.is_file() and path.stat().st_size > 0

    def reference(self, task_id: str) -> dict:
        return {"video_url": None, "output_path": str(self.path(task_id))}

    def store(self, source: Path, task_id: str) -> dict:
        _validate_mp4(source)
        destination = self.path(task_id)
        temporary = destination.with_name(f".{destination.name}.{uuid.uuid4().hex}.tmp")
        try:
            shutil.copyfile(source, temporary)
            os.replace(temporary, destination)
        finally:
            temporary.unlink(missing_ok=True)
        return self.reference(task_id)


class S3Storage:
    def __init__(self, settings: Settings):
        import boto3

        self.settings = settings
        self.client = boto3.client("s3", endpoint_url=settings.s3_endpoint, region_name=settings.s3_region)

    def key(self, task_id: str) -> str:
        return f"{self.settings.s3_prefix}/{task_id}.mp4"

    def existing(self, task_id: str) -> bool:
        from botocore.exceptions import ClientError

        try:
            self.client.head_object(Bucket=self.settings.s3_bucket, Key=self.key(task_id))
            return True
        except ClientError as exc:
            if exc.response["Error"]["Code"] in ("404", "NoSuchKey", "NotFound"):
                return False
            raise

    def url(self, task_id: str) -> str:
        return self.client.generate_presigned_url(
            "get_object", Params={"Bucket": self.settings.s3_bucket, "Key": self.key(task_id)},
            ExpiresIn=3600,
        )

    def upload(self, path: Path, task_id: str) -> str:
        _validate_mp4(path)
        self.client.upload_file(str(path), self.settings.s3_bucket, self.key(task_id),
                                ExtraArgs={"ContentType": "video/mp4"})
        return self.url(task_id)

    def reference(self, task_id: str) -> dict:
        return {"video_url": self.url(task_id)}

    def store(self, path: Path, task_id: str) -> dict:
        return {"video_url": self.upload(path, task_id)}


def storage_from_settings(settings: Settings) -> LocalStorage | S3Storage:
    if not settings.s3_bucket:
        return LocalStorage(settings)
    return S3Storage(settings)
