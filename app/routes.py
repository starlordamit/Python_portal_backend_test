from datetime import datetime, timedelta
from typing import List
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.models import User, UserCreate, UserUpdate, UserInDB, Token, PasswordReset, LoginCredentials
from app.auth import (
    authenticate_user, create_access_token, get_password_hash,
    get_current_active_user, get_current_admin, get_user_by_email
)
from app.database import users_collection

router = APIRouter()

# Helper function to convert ObjectId to string
def user_helper(user) -> dict:
    return {
        "_id": str(user["_id"]),
        "email": user["email"],
        "full_name": user["full_name"],
        "role": user["role"],
        "is_active": user["is_active"],
        "created_at": user["created_at"],
        "updated_at": user.get("updated_at")
    }

# Legacy form-based login for backward compatibility
@router.post("/login-form", response_model=Token)
async def login_form(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user["email"], "role": user["role"]}, 
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# New JSON-based login for better performance
@router.post("/login", response_model=Token)
async def login_json(credentials: LoginCredentials):
    """
    Login with email and password using JSON.
    This endpoint is optimized for performance and accepts JSON data.
    """
    # Get preconfigured expiration time
    from app.auth import ACCESS_TOKEN_EXPIRE_MINUTES
    
    user = await authenticate_user(credentials.email, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create token with preconfigured expiration time
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"], "role": user["role"]}, 
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/users", response_model=User)
async def create_user(user: UserCreate, current_user = Depends(get_current_admin)):
    """
    Create a new user (admin only).
    """
    # Check if user already exists
    user_exists = await get_user_by_email(user.email)
    if user_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with email {user.email} already exists"
        )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    user_data = {
        "_id": str(ObjectId()),
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "hashed_password": hashed_password,
        "is_active": True,
        "created_at": datetime.utcnow()
    }
    
    result = users_collection.insert_one(user_data)
    new_user = users_collection.find_one({"_id": user_data["_id"]})
    return user_helper(new_user)

@router.get("/users", response_model=List[User])
async def get_users(current_user = Depends(get_current_admin)):
    """
    Get all users (admin only).
    """
    users = []
    for user in users_collection.find():
        users.append(user_helper(user))
    return users

@router.get("/users/me", response_model=User)
async def get_current_user_info(current_user = Depends(get_current_active_user)):
    """
    Get current user info.
    """
    return user_helper(current_user)

@router.get("/users/{user_id}", response_model=User)
async def get_user(user_id: str, current_user = Depends(get_current_admin)):
    """
    Get a user by ID (admin only).
    """
    user = users_collection.find_one({"_id": user_id})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    return user_helper(user)

@router.put("/users/{user_id}", response_model=User)
async def update_user(user_id: str, user_update: UserUpdate, current_user = Depends(get_current_admin)):
    """
    Update a user (admin only).
    """
    # Check if user exists
    existing_user = users_collection.find_one({"_id": user_id})
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Prepare update data
    update_data = {k: v for k, v in user_update.dict(exclude_unset=True).items() if v is not None}
    if update_data:
        update_data["updated_at"] = datetime.utcnow()
        users_collection.update_one(
            {"_id": user_id}, {"$set": update_data}
        )
    
    updated_user = users_collection.find_one({"_id": user_id})
    return user_helper(updated_user)

@router.patch("/users/{user_id}/activate", response_model=User)
async def activate_user(user_id: str, current_user = Depends(get_current_admin)):
    """
    Activate a user (admin only).
    """
    existing_user = users_collection.find_one({"_id": user_id})
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    users_collection.update_one(
        {"_id": user_id},
        {"$set": {"is_active": True, "updated_at": datetime.utcnow()}}
    )
    
    updated_user = users_collection.find_one({"_id": user_id})
    return user_helper(updated_user)

@router.patch("/users/{user_id}/deactivate", response_model=User)
async def deactivate_user(user_id: str, current_user = Depends(get_current_admin)):
    """
    Deactivate a user (admin only).
    """
    existing_user = users_collection.find_one({"_id": user_id})
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    users_collection.update_one(
        {"_id": user_id},
        {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
    )
    
    updated_user = users_collection.find_one({"_id": user_id})
    return user_helper(updated_user)

@router.post("/users/{user_id}/reset-password", response_model=User)
async def reset_user_password(
    user_id: str, 
    password_reset: PasswordReset, 
    current_user = Depends(get_current_admin)
):
    """
    Reset a user's password (admin only).
    """
    existing_user = users_collection.find_one({"_id": user_id})
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    hashed_password = get_password_hash(password_reset.new_password)
    users_collection.update_one(
        {"_id": user_id},
        {"$set": {"hashed_password": hashed_password, "updated_at": datetime.utcnow()}}
    )
    
    updated_user = users_collection.find_one({"_id": user_id})
    return user_helper(updated_user) 