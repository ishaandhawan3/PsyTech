import boto3
import logging
from botocore.exceptions import ClientError

class S3Bucket:
    def __init__(self, bucket_name, region=None):
        """
        Initialize S3 client for a specific bucket
        :param bucket_name: S3 bucket name
        :param region: AWS region name (default: current EC2 region)
        """
        self.bucket_name = bucket_name
        self.client = boto3.client('s3', region_name=region) if region else boto3.client('s3')
        logging.basicConfig(level=logging.INFO)
        
    def upload_file(self, local_path, s3_key):
        """
        Upload local file to S3
        :param local_path: Path to local file
        :param s3_key: Destination key in S3
        """
        try:
            self.client.upload_file(local_path, self.bucket_name, s3_key)
            logging.info(f"Uploaded {local_path} to s3://{self.bucket_name}/{s3_key}")
            return True
        except ClientError as e:
            logging.error(f"Upload failed: {e.response['Error']['Message']}")
            return False
        except Exception as e:
            logging.error(f"Unexpected upload error: {str(e)}")
            return False

    def download_file(self, s3_key, local_path):
        """
        Download file from S3 to local
        :param s3_key: Source key in S3
        :param local_path: Local destination path
        """
        try:
            self.client.download_file(self.bucket_name, s3_key, local_path)
            logging.info(f"Downloaded s3://{self.bucket_name}/{s3_key} to {local_path}")
            return True
        except ClientError as e:
            logging.error(f"Download failed: {e.response['Error']['Message']}")
            return False
        except Exception as e:
            logging.error(f"Unexpected download error: {str(e)}")
            return False

    def read_file(self, s3_key):
        """
        Read file contents from S3 as string
        :param s3_key: Key of file in S3
        :return: File contents as string or None
        """
        try:
            response = self.client.get_object(Bucket=self.bucket_name, Key=s3_key)
            content = response['Body'].read().decode('utf-8')
            logging.info(f"Read {len(content)} bytes from s3://{self.bucket_name}/{s3_key}")
            return content
        except ClientError as e:
            logging.error(f"Read failed: {e.response['Error']['Message']}")
            return None
        except Exception as e:
            logging.error(f"Unexpected read error: {str(e)}")
            return None

    def write_file(self, s3_key, content):
        """
        Write string content to S3 file
        :param s3_key: Destination key in S3
        :param content: String content to write
        """
        try:
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=content.encode('utf-8')
            )
            logging.info(f"Wrote {len(content)} bytes to s3://{self.bucket_name}/{s3_key}")
            return True
        except ClientError as e:
            logging.error(f"Write failed: {e.response['Error']['Message']}")
            return False
        except Exception as e:
            logging.error(f"Unexpected write error: {str(e)}")
            return False

    def list_objects(self, prefix=''):
        """
        List objects in bucket with optional prefix
        :param prefix: Filter objects starting with prefix
        :return: List of object keys or empty list
        """
        try:
            paginator = self.client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.bucket_name, Prefix=prefix)
            
            return [obj['Key'] for page in pages for obj in page.get('Contents', [])]
        except ClientError as e:
            logging.error(f"Listing failed: {e.response['Error']['Message']}")
            return []
        except Exception as e:
            logging.error(f"Unexpected listing error: {str(e)}")
            return []

# Usage Example
if __name__ == "__main__":
    # Initialize for your bucket
    s3 = S3Bucket(bucket_name="parentgenie-dev")
    
    # Upload a local file
    # s3.upload_file("/tmp/local-file.txt", "folder/remote-file.txt")
    
    # Download from S3
    # s3.download_file("folder/remote-file.txt", "/tmp/downloaded-file.txt")
    
    # Write string directly to S3
    # s3.write_file("folder/new-file.txt", "Hello S3 from EC2!")
    
    # Read file content directly
    # content = s3.read_file("folder/new-file.txt")
    # print(f"Read content: {content[:50]}...")
    
    # List objects
    # print("Objects in bucket:")
    # for obj_key in s3.list_objects(prefix="folder/"):
        # print(f"- {obj_key}")