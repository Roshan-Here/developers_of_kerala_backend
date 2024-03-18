"""
config.py

This module contains the configuration settings for the application, including API version, secret key, algorithm, token expiration time, server name, host, project name, and CORS origins.

"""
import os
from dotenv import load_dotenv
from typing import Any, Dict, List, Optional, Union, ClassVar

from pydantic import AnyHttpUrl, EmailStr, HttpUrl, PostgresDsn, validator
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = str(os.environ.get("SECRET_KEY"))

    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # one day
    SERVER_NAME: str = "Kerala Devs"
    SERVER_HOST: AnyHttpUrl = "http://localhost:8000"

    PROJECT_NAME: str = "Kerala Devs"

    # BACKEND_CORS_ORIGINS is a JSON-formatted list of origins
    # e.g: '["http://localhost", "http://localhost:4200", "http://localhost:3000", \
    # "http://localhost:8080", "http://local.dockertoolbox.tiangolo.com"]'
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "https://www.keraladevs.com"]

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # MongoDB
    MONGODB_URI: str = os.environ.get("MONGODB_URI")
    MONGODB_NAME: str = os.environ.get("MONGODB_NAME")
        
    # Media (local storage)
    BASE_DIR :ClassVar[str] = os.path.abspath(os.path.dirname(__file__))
    MEDIA_URI :ClassVar[str] = os.path.join(BASE_DIR,f"media")
    # allowed formats
    ALLOWED_IMAGE_FORMATS : List[str] = ["jpg", "jpeg", "png", "gif"]

    # Digital Ocean Credentials 
    digital_ocean_bucket_id : str = os.environ.get("DIGITAL_OCEAN_BUCKET_ID")
    digital_ocean_bucket_secret : str = os.environ.get("DIGITAL_OCEAN_BUCKET_SECRET")
    region_name : str = os.environ.get("REGION_NAME")
    endpoint_url : str = os.environ.get("ENDPOINT_URL")
    bucket_name : str = os.environ.get("BUCKET_NAME")
    
    
    class Config:
        case_sensitive = True


settings = Settings()
