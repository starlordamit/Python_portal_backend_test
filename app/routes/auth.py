from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from typing import Annotated
from pydantic import BaseModel, EmailStr

from ..auth import (
    authenticate_user, 
    create_access_token, 
    get_current_active_user, 
    get_current_admin,
    get_password_hash,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from ..models import User, Role
from ..database import users_collection
from datetime import datetime
from bson import ObjectId

router = APIRouter()

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: Role = Role.DATA_OPERATOR

@router.post("/login")
async def login_for_access_token(login_data: LoginRequest):
    user = await authenticate_user(login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"], "role": user["role"]},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(
    register_data: RegisterRequest,
    current_user: dict = Depends(get_current_admin)
):
    # Check if email already exists
    existing_user = users_collection.find_one({"email": register_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    new_user = {
        "_id": str(ObjectId()),
        "email": register_data.email,
        "full_name": register_data.full_name,
        "hashed_password": get_password_hash(register_data.password),
        "role": register_data.role,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = users_collection.insert_one(new_user)
    if not result.inserted_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )
    
    return {"message": "User created successfully", "id": str(result.inserted_id)}

@router.get("/me", response_model=dict)
async def read_users_me(current_user: dict = Depends(get_current_active_user)):
    return {
        "id": current_user["_id"],
        "email": current_user["email"],
        "username": current_user.get("full_name", current_user["email"]),
        "full_name": current_user.get("full_name", ""),
        "role": current_user["role"],
        "is_active": current_user["is_active"],
        "created_at": current_user.get("created_at", ""),
        "updated_at": current_user.get("updated_at", "")
    }

@router.get("/users/me", response_model=dict)
async def read_users_me_alt(current_user: dict = Depends(get_current_active_user)):
    # This is an alternative endpoint for /me to support frontend expectations
    return {
        "id": current_user["_id"],
        "email": current_user["email"],
        "username": current_user.get("full_name", current_user["email"]),
        "full_name": current_user.get("full_name", ""),
        "role": current_user["role"],
        "is_active": current_user["is_active"],
        "created_at": current_user.get("created_at", ""),
        "updated_at": current_user.get("updated_at", "")
    }

@router.get("/users", response_model=list)
async def get_all_users(current_user: dict = Depends(get_current_admin)):
    users = list(users_collection.find({}, {"hashed_password": 0}))
    # Convert ObjectId to string for JSON serialization
    for user in users:
        user["_id"] = str(user["_id"])
    return users

@router.post("/change-role/{user_id}")
async def change_user_role(
    user_id: str,
    new_role: Role,
    current_user: dict = Depends(get_current_admin)
):
    # Only admin can change roles
    result = users_collection.update_one(
        {"_id": user_id},
        {"$set": {"role": new_role, "updated_at": datetime.utcnow()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    if result.modified_count == 0:
        raise HTTPException(status_code=304, detail="User role not modified")
    
    return {"message": f"User role updated to {new_role}"}

@router.post("/deactivate/{user_id}")
async def deactivate_user(
    user_id: str,
    current_user: dict = Depends(get_current_admin)
):
    # Only admin can deactivate users
    result = users_collection.update_one(
        {"_id": user_id},
        {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    if result.modified_count == 0:
        raise HTTPException(status_code=304, detail="User status not modified")
    
    return {"message": "User deactivated successfully"}

class UpdateUserRequest(BaseModel):
    email: EmailStr
    full_name: str
    role: Role
    is_active: bool

class CreateUserRequest(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: Role = Role.DATA_OPERATOR
    is_active: bool = True

@router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: CreateUserRequest,
    current_user: dict = Depends(get_current_admin)
):
    # Check if email already exists
    existing_user = users_collection.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    new_user = {
        "_id": str(ObjectId()),
        "email": user_data.email,
        "full_name": user_data.full_name,
        "hashed_password": get_password_hash(user_data.password),
        "role": user_data.role,
        "is_active": user_data.is_active,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = users_collection.insert_one(new_user)
    if not result.inserted_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )
    
    return {"message": "User created successfully", "id": str(result.inserted_id)}

@router.put("/users/{user_id}", response_model=dict)
async def update_user(
    user_id: str,
    user_data: UpdateUserRequest,
    current_user: dict = Depends(get_current_admin)
):
    # Check if email already exists and belongs to a different user
    if user_data.email:
        existing_user = users_collection.find_one({"email": user_data.email, "_id": {"$ne": user_id}})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered to another user"
            )
    
    # Update user
    update_data = user_data.model_dump()
    update_data["updated_at"] = datetime.utcnow()
    
    result = users_collection.update_one(
        {"_id": user_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User updated successfully", "id": user_id} 