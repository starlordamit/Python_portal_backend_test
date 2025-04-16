from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from . import Role

class User(BaseModel):
    id: str = Field(alias="_id")
    email: EmailStr
    username: str
    role: Role
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    
class TokenData(BaseModel):
    email: str
    role: Optional[Role] = None 