"""MinIO client wrapper for raw and parquet storage."""

from minio import Minio

from worker.core.config import settings


def get_minio_client() -> Minio:
    """Create and return a configured MinIO client."""
    return Minio(
        endpoint=settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
    )


def ensure_bucket(client: Minio, bucket_name: str) -> None:
    """Create bucket if it does not exist."""
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)


def upload_raw(client: Minio, object_name: str, file_path: str) -> None:
    """Upload a file to the raw bucket."""
    ensure_bucket(client, settings.minio_bucket_raw)
    client.fput_object(
        bucket_name=settings.minio_bucket_raw,
        object_name=object_name,
        file_path=file_path,
    )


def upload_parquet(client: Minio, object_name: str, file_path: str) -> None:
    """Upload a Parquet file to the parquet bucket."""
    ensure_bucket(client, settings.minio_bucket_parquet)
    client.fput_object(
        bucket_name=settings.minio_bucket_parquet,
        object_name=object_name,
        file_path=file_path,
    )
