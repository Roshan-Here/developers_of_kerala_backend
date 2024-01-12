from typing import Optional, List, Annotated
from pydantic import BaseModel, Field, EmailStr
from enum import Enum


class OpeningStatus(str, Enum):
    active = "active"
    closed = "closed"
    paused = "paused"


PyObjectId = Annotated[str, Field(alias="_id", default=None)]


class Opening(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    skills_needed: List[str] = Field(...)
    qualification_required: str = Field(...)
    job_role: str = Field(...)
    job_description: str = Field(...)
    no_of_openings: int = Field(..., ge=1)
    status: OpeningStatus = Field(..., default=OpeningStatus.active)

    class Config:
        populate_by_name = (True,)
        arbitrary_types_allowed = (True,)
        json_schema_extra = (
            {
                "example": {
                    "skills_needed": ["Python", "FastAPI"],
                    "qualification_required": "Bachelor's Degree",
                    "job_role": "Backend Developer",
                    "job_description": "Develop and maintain backend services",
                    "no_of_openings": 1,
                    "status": "active",
                }
            },
        )


class CompanyProfile(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: Optional[str] = Field(default=None)
    full_name: Optional[str] = Field(default=None)
    profile_pic: Optional[str] = Field(default=None)  # s3 address for profile pic
    contact: Optional[EmailStr] = Field(default=None)
    industry: Optional[str] = Field(default=None)
    detail_intro: Optional[str] = Field(default=None)
    location: Optional[str] = Field(default=None)  # get from google maps api
    openings: Optional[List[Opening]] = Field(default=None)
    socials: Optional[dict] = Field(default=None)  # e.g., {"LinkedIn": "<link>", etc}
    website: Optional[str] = Field(default=None)

    class Config:
        populate_by_name = (True,)
        arbitrary_types_allowed = (True,)
        json_schema_extra = (
            {
                "example": {
                    "name": "Company Name",
                    "full_name": "Full Company Name",
                    "profile_pic": "s3://bucket/profile_pic.jpg",
                    "contact": "contact@company.com",
                    "industry": "Tech",
                    "detail_intro": "Detailed introduction about the company",
                    "location": "Location from Google Maps API",
                    "openings": [],
                    "socials": {"LinkedIn": "<link>"},
                    "website": "https://company.com",
                }
            },
        )


class UpdateCompanyProfileModel(BaseModel):
    """
    A set of optional updates to be made to a document in the database.
    """

    name: Optional[str] = None
    full_name: Optional[str] = None
    profile_pic: Optional[str] = None
    contact: Optional[EmailStr] = None
    industry: Optional[str] = None
    detail_intro: Optional[str] = None
    location: Optional[str] = None
    openings: Optional[List[str]] = None
    socials: Optional[dict] = None
    website: Optional[str] = None

    class Config:
        arbitrary_types_allowed = (True,)
        json_encoders = ({ObjectId: str},)
        json_schema_extra = (
            {
                "example": {
                    "name": "Company Name",
                    "full_name": "Full Company Name",
                    "profile_pic": "s3://bucket/profile_pic.jpg",
                    "contact": "contact@company.com",
                    "industry": "Tech",
                    "detail_intro": "Detailed introduction about the company",
                    "location": "Location from Google Maps API",
                    "openings": [],
                    "socials": {"LinkedIn": "<link>"},
                    "website": "https://company.com",
                }
            },
        )
