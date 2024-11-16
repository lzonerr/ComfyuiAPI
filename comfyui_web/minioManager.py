import datetime
from minio import Minio
from minio.error import S3Error
from .loger import comfyui_loggerr
class MinioManager:
    def __init__(self, endpoint, access_key, secret_key, secure=False):
        """初始化 MinIO 客户端

        Args:
            endpoint (str): MinIO 服务器地址.
            access_key (str): MinIO 访问密钥.
            secret_key (str): MinIO 秘密密钥.
            secure (bool): 是否使用 HTTPS 连接.
        """
        self.client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )
        comfyui_loggerr.debug("MinIO client initialized.")

    def create_bucket(self, bucket_name):
        """创建一个新的 bucket（如果不存在）"""

        try:
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
                comfyui_loggerr.debug(f"Bucket '{bucket_name}' created.")
            else:
                comfyui_loggerr.debug(f"Bucket '{bucket_name}' already exists.")
        except S3Error as e:
            comfyui_loggerr.error(f"Error creating bucket: {e}")

    def delete_bucket(self, bucket_name):
        """删除指定的 bucket"""

        try:
            self.client.remove_bucket(bucket_name)
            comfyui_loggerr.debug(f"Bucket '{bucket_name}' deleted.")
        except S3Error as e:
            comfyui_loggerr.debug(f"Error deleting bucket: {e}")

    def upload_file(self, bucket_name, object_name, file_path, content_type):
        """上传文件到指定的 bucket"""

        try:
            self.client.fput_object(bucket_name, object_name, file_path, content_type)
            comfyui_loggerr.debug(f"File '{object_name}' uploaded to bucket '{bucket_name}'.")
            return object_name
        except S3Error as e:
            comfyui_loggerr.error(f"Error uploading file: {e}")

    def download_file(self, bucket_name, object_name, file_path):
        """从指定的 bucket 下载文件"""

        try:
            self.client.fget_object(bucket_name, object_name, file_path)
            comfyui_loggerr.debug(f"File '{object_name}' downloaded from bucket '{bucket_name}'.")
        except S3Error as e:
            comfyui_loggerr.error(f"Error downloading file: {e}")

    def list_objects(self, bucket_name):
        """列出指定 bucket 中的所有对象"""

        try:
            objects = self.client.list_objects(bucket_name)
            comfyui_loggerr.debug(f"Listing objects in bucket '{bucket_name}':")
            for obj in objects:
                comfyui_loggerr.debug(f" - {obj.object_name}")  # Use debug for detailed listing
        except S3Error as e:
            comfyui_loggerr.error(f"Error listing objects: {e}")

    def delete_object(self, bucket_name, object_name):
        """从指定 bucket 删除对象"""

        try:
            self.client.remove_object(bucket_name, object_name)
            comfyui_loggerr.debug(f"Object '{object_name}' deleted from bucket '{bucket_name}'.")
        except S3Error as e:
            comfyui_loggerr.error(f"Error deleting object: {e}")

    def generate_presigned_url(self, bucket_name, object_name, expiry_hours=24):
        """生成下载链接的预签名 URL"""

        try:
            url_expiry = datetime.timedelta(hours=expiry_hours)
            presigned_url = self.client.presigned_get_object(bucket_name, object_name, expires=url_expiry)
            comfyui_loggerr.debug(f"Generated presigned URL for object '{object_name}' in bucket '{bucket_name}'.")
            return presigned_url
        except S3Error as e:
            comfyui_loggerr.error(f"Error generating presigned URL: {e}")
            return None
