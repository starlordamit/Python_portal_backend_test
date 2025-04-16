from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime

from ..utils.object_id import PyObjectId

class POCBase(BaseModel):
    name: str
    phone: str
    email: EmailStr
    designation: str

class POCCreate(POCBase):
    pass

class POC(POCBase):
    id: PyObjectId = Field(default=None, alias="_id")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "phone": "+1234567890",
                "email": "john.doe@example.com",
                "designation": "Marketing Manager"
            }
        }

class BrandBase(BaseModel):
    name: str
    website: Optional[str] = None
    instagram: Optional[str] = None
    linkedin: Optional[str] = None
    logo_url: Optional[str] = None
    billing_details_id: Optional[PyObjectId] = None

class BrandCreate(BrandBase):
    pocs: Optional[List[POCCreate]] = []

class BrandUpdate(BaseModel):
    name: Optional[str] = None
    website: Optional[str] = None
    instagram: Optional[str] = None
    linkedin: Optional[str] = None
    logo_url: Optional[str] = None
    billing_details_id: Optional[PyObjectId] = None

class Brand(BrandBase):
    id: PyObjectId = Field(alias="_id")
    pocs: List[POC] = []
    created_by: PyObjectId
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "name": "Example Brand",
                "website": "https://example.com",
                "instagram": "https://instagram.com/examplebrand",
                "linkedin": "https://linkedin.com/company/examplebrand",
                "logo_url": "https://example.com/logo.png",
                "billing_details_id": "5f8a7b9c1d2e3f4a5b6c7d8e",
                "pocs": [
                    {
                        "name": "John Doe",
                        "phone": "+1234567890",
                        "email": "john.doe@example.com",
                        "designation": "Marketing Manager"
                    }
                ]
            }
        }

class BrandPublic(BaseModel):
    """Public version of Brand with limited fields visible to non-privileged roles"""
    id: PyObjectId = Field(alias="_id")
    name: str
    website: Optional[str] = None
    instagram: Optional[str] = None
    linkedin: Optional[str] = None
    logo_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True 