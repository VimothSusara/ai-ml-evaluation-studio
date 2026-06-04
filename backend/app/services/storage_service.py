import boto3
from botocore.client import Config
from app.core.config import get_settings

settings = get_settings()

class StorageService:
    def __init__(self) -> None:
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name=settings.S3_REGION,
            config=Config(signature_version="s3v4"),
        )

    def ensure_bucket(self, bucket: str) -> None:
        existing = [b["Name"] for b in self.client.list_buckets().get("Buckets", [])]
        if bucket not in existing:
            self.client.create_bucket(Bucket=bucket)
        
    def upload_bytes(self, bucket: str, key: str, content: bytes, content_type: str) -> None:
        self.client.put_object(Bucket=bucket, Key=key, Body=content, ContentType=content_type)

    def download_bytes(self, bucket: str, key: str) -> bytes:
        obj = self.client.get_object(Bucket=bucket, Key=key)
        return obj["Body"].read()

    def generate_presigned_download_url(
        self,
        bucket: str,
        key: str,
        expires_in: int = 3600,
        filename: str | None = None,
    ) -> str:
        params: dict = {"Bucket": bucket, "Key": key}
        if filename:
            params["ResponseContentDisposition"] = f'attachment; filename="{filename}"'
        return self.client.generate_presigned_url(
            "get_object",
            Params=params,
            ExpiresIn=expires_in,
        )