from typing import Optional, List, Dict, Any, Annotated
from pydantic import BaseModel, EmailStr, Field, validator, HttpUrl, GetJsonSchemaHandler
from datetime import datetime
from enum import Enum
from bson import ObjectId
from pydantic.json_schema import JsonSchemaValue

class Role(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    FINANCE = "finance"
    OPERATIONS_MANAGER = "operations_manager"
    INTERN = "intern"
    DATA_OPERATOR = "data_operator"

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    
class UserCreate(UserBase):
    password: str
    role: Role = Role.INTERN
    
    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[Role] = None
    is_active: Optional[bool] = None

class UserInDB(UserBase):
    id: str = Field(alias="_id")
    role: Role
    hashed_password: str
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        populate_by_name = True

class User(UserBase):
    id: str = Field(alias="_id")
    role: Role
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        populate_by_name = True

class LoginCredentials(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None

class PasswordReset(BaseModel):
    email: EmailStr
    new_password: str
    
    @validator('new_password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v

class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"

class Platform(str, Enum):
    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    LINKEDIN = "linkedin"
    OTHER = "other"

class ContactType(str, Enum):
    PERSONAL = "personal"
    BUSINESS = "business"
    MANAGER = "manager"
    AGENCY = "agency"
    OTHER = "other"

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema: Any, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
        return {"type": "string"}

class ContactInfo(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    preferred_contact_method: Optional[str] = Field(None, description="email, phone, or other")

class BillingDetails(BaseModel):
    payment_method: str = Field(..., description="credit_card, bank_transfer, or other")
    billing_address: str
    tax_id: Optional[str] = None
    custom_billing_info: Optional[Dict[str, Any]] = None

class ProfileBase(BaseModel):
    platform: str = Field(..., description="Social media platform or website")
    username: str
    profile_url: str
    contact_info: Optional[ContactInfo] = None
    billing_details_id: Optional[PyObjectId] = None
    status: str = Field("active", description="active, inactive, or pending")
    metadata: Optional[Dict[str, Any]] = None

class ProfileCreate(ProfileBase):
    pass

class ProfileUpdate(BaseModel):
    platform: Optional[str] = None
    username: Optional[str] = None
    profile_url: Optional[str] = None
    contact_info: Optional[ContactInfo] = None
    billing_details_id: Optional[PyObjectId] = None
    status: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class Profile(ProfileBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_by: PyObjectId
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str} 