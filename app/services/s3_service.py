from urllib.parse import urlparse

import boto3
from botocore.exceptions import ClientError

from app.config import settings


def get_s3_client():
    if not settings.AWS_ACCESS_KEY_ID or not settings.AWS_SECRET_ACCESS_KEY or not settings.AWS_BUCKET_NAME:
        raise ValueError("AWS S3 configuration is missing. Set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_BUCKET_NAME in your environment.")

    return boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )


def _safe_key(filename: str, user_id: int) -> str:
    safe_name = filename.replace("\\", "/").split("/")[-1]
    return f"resumes/{user_id}/{safe_name}"


def upload_resume_to_s3(file_content: bytes, filename: str, user_id: int) -> str | None:
    try:
        s3 = get_s3_client()
        key = _safe_key(filename, user_id)
        s3.put_object(
            Bucket=settings.AWS_BUCKET_NAME,
            Key=key,
            Body=file_content,
            ContentType="application/pdf",
        )
        return f"https://{settings.AWS_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"
    except (ClientError, ValueError) as exc:
        raise RuntimeError(f"S3 upload failed: {exc}") from exc


def delete_resume_from_s3(file_url: str) -> bool:
    try:
        parsed = urlparse(file_url)
        if not parsed.netloc:
            return False
        bucket = settings.AWS_BUCKET_NAME
        key = parsed.path.lstrip("/")
        if parsed.netloc.startswith(bucket + "."):
            key = parsed.path.lstrip("/")
        s3 = get_s3_client()
        s3.delete_object(Bucket=bucket, Key=key)
        return True
    except Exception:
        return False


def generate_presigned_url(file_url: str, expires_in: int = 3600) -> str:
    try:
        parsed = urlparse(file_url)
        if not parsed.netloc:
            return file_url
        key = parsed.path.lstrip("/")
        s3 = get_s3_client()
        return s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.AWS_BUCKET_NAME, "Key": key},
            ExpiresIn=expires_in,
        )
    except Exception:
        return file_url


__all__ = ["upload_resume_to_s3", "delete_resume_from_s3", "generate_presigned_url"]
