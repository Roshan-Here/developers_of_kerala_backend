"""
blog.py
This Module is for creating and retriving Blog Model
"""

from pydantic import BaseModel,Field
from typing import Optional,List


class BlogModel(BaseModel):
    Title : Optional[str] = None
    Content : Optional[str] = None
    Author : Optional[str]
    images : List[str] = None
    
    class Config:
        json_schema_extra = {
            "example":{
                "Title":"Title of Blog",
                "Content":"Content of Blog",
                "Author":"Author automatically fech if-> logged in",
                "images":"List of images url",
            }
        }
    
    
def retrive_blog(data)->dict:
    return{
        "id" : str(data["_id"]),
        "Title" : data["Title"],
        "Content" : data["Content"],
        "Author" : data["Author"],
        "images": data["images"]
    }