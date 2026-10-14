import json
import logging
from datetime import datetime

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)


class S3Client:
    """Wrapper around boto3 S3 for archiving events."""

    def __init__(self):
        self._client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )
        self._bucket = settings.S3_BUCKET_NAME

    def upload_json(self, data: list[dict], key: str) -> str:
        """Upload JSON data to S3 and return the S3 path."""
        body = json.dumps(data, default=str).encode("utf-8")
        try:
            self._client.put_object(
                Bucket=self._bucket,
                Key=key,
                Body=body,
                ContentType="application/json",
            )
            path = f"s3://{self._bucket}/{key}"
            logger.info("Uploaded %d events to %s", len(data), path)
            return path
        except (BotoCoreError, ClientError) as exc:
            logger.error("S3 upload failed: %s", exc)
            raise

    @staticmethod
    def build_archive_key(archive_date: datetime) -> str:
        return f"archives/{archive_date.strftime('%Y/%m/%d')}/events_{archive_date.strftime('%H%M%S')}.json"


s3_client = S3Client()
