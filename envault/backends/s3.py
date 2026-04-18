import boto3
from botocore.exceptions import ClientError

from envault.backends.base import BaseBackend


class S3Backend(BaseBackend):
    """Stores encrypted env files in an AWS S3 bucket."""

    def __init__(self, bucket: str, prefix: str = "envault/", region: str = "us-east-1"):
        self.bucket = bucket
        self.prefix = prefix
        self.client = boto3.client("s3", region_name=region)

    def _full_key(self, key: str) -> str:
        return f"{self.prefix}{key}.enc"

    def upload(self, key: str, data: bytes) -> None:
        self.client.put_object(Bucket=self.bucket, Key=self._full_key(key), Body=data)

    def download(self, key: str) -> bytes:
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=self._full_key(key))
            return response["Body"].read()
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                raise FileNotFoundError(f"Key '{key}' not found in S3 backend.")
            raise

    def list_keys(self) -> list[str]:
        paginator = self.client.get_paginator("list_objects_v2")
        keys = []
        for page in paginator.paginate(Bucket=self.bucket, Prefix=self.prefix):
            for obj in page.get("Contents", []):
                raw = obj["Key"][len(self.prefix):]
                if raw.endswith(".enc"):
                    keys.append(raw[:-4])
        return keys

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=self._full_key(key))

    def exists(self, key: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=self._full_key(key))
            return True
        except ClientError:
            return False
