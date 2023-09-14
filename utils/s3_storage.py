import fnmatch
import os
import io
import re
import json
import boto3
import botocore
from utils import Storage
from PIL import Image


class S3Storage(Storage):
    def __init__ (self, aws_access_key_id, aws_secret_access_key, endpoint_url, region_name, bucket_name, s3_prefix):
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.endpoint_url = endpoint_url
        self.region_name = region_name
        self.bucket_name = bucket_name

        self.session = boto3.session.Session(aws_access_key_id=aws_access_key_id,
                                        aws_secret_access_key=aws_secret_access_key)
        self.s3_resource = self.session.resource(
            's3',
            config=botocore.client.Config(signature_version='s3v4'),
            endpoint_url=endpoint_url,
            region_name=region_name)

        self.bucket = self.s3_resource.Bucket(bucket_name)
        self.s3_prefix = s3_prefix

    def make_dirs(self, dir_path):
        pass

    def list_files(self, dir_path, pattern):
        filter = self.bucket.objects.filter(Prefix=os.path.join(self.s3_prefix, dir_path))
        filenames = [f.key for f in filter.all()]
        if self.s3_prefix:
            filenames = [fn.replace(f"{self.s3_prefix}/", "", 1) for fn in filenames]
        regex = fnmatch.translate(pattern)
        reobj = re.compile(regex)
        filtered_files = [f for f in filenames if reobj.match(f)]
        return filtered_files

    def write_json(self, data, file_path):
        key = os.path.join(self.s3_prefix, file_path)
        body = bytes(json.dumps(data).encode('UTF-8'))
        self.bucket.put_object(Key=key, Body=body)

    def read_json(self, file_path):
        key = os.path.join(self.s3_prefix, file_path)
        file_content = self.bucket.Object(key).get()['Body'].read().decode('utf-8')
        return json.loads(file_content)

    def write_image(self, image: Image, file_path):
        key = os.path.join(self.s3_prefix, file_path)
        img_bytes = io.BytesIO()
        image.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        self.bucket.put_object(Key=key, Body=img_bytes)

    def read_file(self, file_path):
        key = os.path.join(self.s3_prefix, file_path)
        return self.bucket.Object(key).get()['Body']







#
#
# def write_image_json(self, status, progress):
#
#
#
# session = boto3.session.Session(aws_access_key_id=aws_access_key_id,
#                                 aws_secret_access_key=aws_secret_access_key)
#
#
#
# def upload_directory_to_s3(local_directory, s3_prefix):
#     for root, dirs, files in os.walk(local_directory):
#         for filename in files:
#             file_path = os.path.join(root, filename)
#             relative_path = os.path.relpath(file_path, local_directory)
#             s3_key = os.path.join(s3_prefix, relative_path)
#             print(f"{file_path} -> {s3_key}")
#             bucket.upload_file(file_path, s3_key)
#
#
# def list_objects(prefix):
#     filter = bucket.objects.filter(Prefix=prefix)
#     for obj in filter.all():
#         print(obj.key)
