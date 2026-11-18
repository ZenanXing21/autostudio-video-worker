from pathlib import Path

import boto3
from botocore.exceptions import ClientError

from .config import Settings


class ObjectStorage:
    def __init__(self, settings: Settings):
        if not settings.s3_bucket:
            raise RuntimeError("S3_BUCKET is required")
        self.settings = settings
        self.client = boto3.client("s3", endpoint_url=settings.s3_endpoint, region_name=settings.s3_region)

    def key(self, task_id: str) -> str:
        return f"{self.settings.s3_prefix}/{task_id}.mp4"

    def existing(self, task_id: str) -> bool:
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
        if path.suffix.lower() != ".mp4" or path.stat().st_size == 0:
            raise RuntimeError("ComfyUI did not create a nonempty MP4")
        self.client.upload_file(str(path), self.settings.s3_bucket, self.key(task_id),
                                ExtraArgs={"ContentType": "video/mp4"})
        return self.url(task_id)
