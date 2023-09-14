from .storage import Storage
from .s3_storage import S3Storage
from .file_storage import FileStorage

import os

AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_S3_ENDPOINT = os.environ.get("AWS_S3_ENDPOINT")
AWS_DEFAULT_REGION = os.environ.get("AWS_DEFAULT_REGION")
AWS_S3_BUCKET = os.environ.get("AWS_S3_BUCKET")
AWS_S3_PREFIX = os.environ.get("AWS_S3_PREFIX", "photo-generator/images")

BASE_STORAGE_PATH = os.environ.get("BASE_STORAGE_PATH", "/tmp/photo-generator/images")

if AWS_ACCESS_KEY_ID:
    print("using S3Storage")
    storage: Storage = S3Storage(AWS_ACCESS_KEY_ID,
                                 AWS_SECRET_ACCESS_KEY,
                                 AWS_S3_ENDPOINT,
                                 AWS_DEFAULT_REGION,
                                 AWS_S3_BUCKET,
                                 AWS_S3_PREFIX)
else:
    print("using FileStorage")
    storage: Storage = FileStorage(BASE_STORAGE_PATH)
