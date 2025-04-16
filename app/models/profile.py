from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from enum import Enum
from ..utils.object_id import PyObjectId

class Platform(str, Enum):
    YOUTUBE = "youtube"
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"
    FACEBOOK = "facebook"
    TWITTER = "twitter"

class ContentOrientation(str, Enum):
    SHORTS = "shorts"
    LONG = "long"
    LONG_SHORTS = "long_shorts"
    REELS = "reels"

class ContactDetail(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

class CostingDetail(BaseModel):
    content_type: str
    price: float
    currency: str = "INR"
    description: Optional[str] = None

class ProfileBase(BaseModel):
    platform: Platform
    content_orientation: Optional[ContentOrientation] = None
    username: str
    profile_url: str
    region: Optional[str] = None
    language: Optional[str] = None
    followers: Optional[int] = None
    er_rate: Optional[float] = None  # Engagement rate
    is_betting_allowed: Optional[bool] = False
    male_audience: Optional[float] = None  # Percentage of male audience
    bio_phone: Optional[str] = None  # Added bio phone
    bio_email: Optional[EmailStr] = None  # Added bio email
    contact_details: Optional[List[ContactDetail]] = []
    costing: Optional[List[CostingDetail]] = []
    billing_details_id: Optional[PyObjectId] = None
    
class ProfileCreate(ProfileBase):
    pass
    
class ProfileUpdate(BaseModel):
    platform: Optional[Platform] = None
    content_orientation: Optional[ContentOrientation] = None
    username: Optional[str] = None
    profile_url: Optional[str] = None
    region: Optional[str] = None
    language: Optional[str] = None
    followers: Optional[int] = None
    er_rate: Optional[float] = None
    is_betting_allowed: Optional[bool] = None
    male_audience: Optional[float] = None
    bio_phone: Optional[str] = None  # Added bio phone
    bio_email: Optional[EmailStr] = None  # Added bio email
    contact_details: Optional[List[ContactDetail]] = None
    costing: Optional[List[CostingDetail]] = None
    billing_details_id: Optional[PyObjectId] = None
    
class Profile(ProfileBase):
    id: PyObjectId = Field(alias="_id")
    created_by: PyObjectId
    created_at: datetime
    updated_at: datetime
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "_id": "5f85f36d6dfecacc68428a46",
                "platform": "instagram",
                "content_orientation": "reels",
                "username": "exampleuser",
                "profile_url": "https://instagram.com/exampleuser",
                "region": "India",
                "language": "English",
                "followers": 100000,
                "er_rate": 3.5,
                "is_betting_allowed": False,
                "male_audience": 65.5,
                "bio_phone": "+9112345678",
                "bio_email": "bio@example.com",
                "contact_details": [
                    {
                        "name": "John Doe",
                        "email": "john@example.com",
                        "phone": "+1234567890"
                    }
                ],
                "costing": [
                    {
                        "content_type": "Reel",
                        "price": 5000,
                        "currency": "INR",
                        "description": "30-second promotional reel"
                    }
                ],
                "billing_details_id": "5f85f36d6dfecacc68428a47",
                "created_by": "5f85f36d6dfecacc68428a45",
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00"
            }
        }

class ProfilePublic(BaseModel):
    """Public version of Profile with limited fields visible to non-privileged roles"""
    id: PyObjectId = Field(alias="_id")
    platform: Platform
    content_orientation: Optional[ContentOrientation] = None
    username: str
    profile_url: str
    region: Optional[str] = None
    language: Optional[str] = None
    followers: Optional[int] = None
    er_rate: Optional[float] = None
    is_betting_allowed: Optional[bool] = None
    male_audience: Optional[float] = None
    bio_phone: Optional[str] = None  # Added bio phone
    bio_email: Optional[EmailStr] = None  # Added bio email
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True 