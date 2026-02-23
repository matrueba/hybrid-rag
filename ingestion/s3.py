import os
import boto3
import logging
import tempfile
from botocore.exceptions import ClientError
from settings import load_settings

logger = logging.getLogger(__name__)

class S3Client:
    """Client for downloading documents from S3 compatible object storage."""

    def __init__(self):
        self.settings = load_settings()
        
        # Determine whether to use an alternative endpoint (e.g. MinIO, Supabase storage, Cloudflare R2)
        endpoint_url = self.settings.s3_endpoint_url
        if not endpoint_url or endpoint_url.strip() == "":
            endpoint_url = None
            
        try:
            self.s3 = boto3.client(
                's3',
                endpoint_url=endpoint_url,
                aws_access_key_id=self.settings.s3_access_key,
                aws_secret_access_key=self.settings.s3_secret_key,
                region_name=self.settings.s3_region
            )
            self.bucket_name = self.settings.s3_bucket_name
            if not self.bucket_name:
                raise ValueError("S3_BUCKET_NAME is not configured")
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            raise

    def get_bucket_name(self) -> str:
        return self.bucket_name

    def download_folder(self, prefix: str, target_dir: str) -> None:
        """
        Download all objects matching the prefix from the configured S3 bucket to a local directory.
        
        Args:
            prefix: The S3 object prefix (essentially the folder path)
            target_dir: Local path to download files to
        """
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        # Enforce no leading slash for prefix if it exists to match AWS norms, but accept as is.
        if prefix.startswith('/'):
            prefix = prefix[1:]

        logger.info(f"Listing objects in bucket '{self.bucket_name}' with prefix '{prefix}'")

        try:
            paginator = self.s3.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.bucket_name, Prefix=prefix)
            
            downloaded_count = 0
            
            for page in pages:
                if 'Contents' not in page:
                    continue
                    
                for obj in page['Contents']:
                    key = obj['Key']
                    
                    # Skip 'directories'
                    if key.endswith('/'):
                        continue
                        
                    # Calculate relative path
                    rel_path = os.path.relpath(key, prefix) if prefix else key
                    if rel_path.startswith('..'):
                        # If prefix doesn't match directory structure properly
                        rel_path = os.path.basename(key)
                        
                    local_file_path = os.path.join(target_dir, rel_path)
                    
                    # Ensure local directory exists
                    os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
                    
                    logger.debug(f"Downloading s3://{self.bucket_name}/{key} to {local_file_path}")
                    self.s3.download_file(self.bucket_name, key, local_file_path)
                    downloaded_count += 1
                    
            logger.info(f"Successfully downloaded {downloaded_count} files from S3.")
            
        except ClientError as e:
            logger.error(f"Error downloading from S3: {e}")
            raise
