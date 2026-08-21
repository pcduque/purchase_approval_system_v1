import boto3
from botocore.exceptions import ClientError


class S3EvidenceRepository:
    def __init__(self, bucket_name: str) -> None:
        self._bucket_name = bucket_name
        self._client = boto3.client("s3")

    def upload_pdf(self, key: str, pdf_bytes: bytes) -> None:
        try:
            self._client.put_object(
                Bucket=self._bucket_name,
                Key=key,
                Body=pdf_bytes,
                ContentType="application/pdf",
            )
        except ClientError as exc:
            raise RuntimeError("S3 could not upload evidence PDF") from exc

    def get_pdf(self, key: str) -> bytes:
        try:
            response = self._client.get_object(Bucket=self._bucket_name, Key=key)
        except ClientError as exc:
            raise RuntimeError("S3 could not get evidence PDF") from exc

        return response["Body"].read()
