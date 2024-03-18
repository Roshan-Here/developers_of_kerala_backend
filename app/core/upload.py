"""
upload.py

This Module contains some basic fuctions to upload to Specific Cloud platforms
"""

import os
import boto3
from fastapi import HTTPException
from dotenv import load_dotenv
from app.core.config import settings

load_dotenv()

digital_ocean_bucket_id = settings.digital_ocean_bucket_id
digital_ocean_bucket_secret = settings.digital_ocean_bucket_secret
region_name = settings.region_name
endpoint_url = settings.endpoint_url
bucket_name = settings.bucket_name

# print(f"{digital_ocean_bucket_id, digital_ocean_bucket_secret, region_name, endpoint_url, bucket_name}")

s3_client = boto3.client(
    's3',
    region_name=region_name,
    endpoint_url=endpoint_url,
    aws_access_key_id=digital_ocean_bucket_id,
    aws_secret_access_key=digital_ocean_bucket_secret,
)

def digital_ocean_upload(upload_location,custom_path,s3_client=s3_client,bucket_name=bucket_name):
    """
    simply upload each files to cloud
    # refer https://github.com/Roshan-Here/FastAPI/blob/2056a0daf83e3db9051f79cbd7126d5baa95a34b/api/config/config.py#L78
    """
    try:
        print(f"Uploading....{custom_path}")
        s3_client.upload_file(
            upload_location,
            bucket_name,
            custom_path,
            ExtraArgs={'ACL': 'public-read'}
            )
    except Exception as e:
        raise HTTPException(    
            status_code=400,
            detail={
                "status":"error",
                "messsage":str(e),
            }
        )