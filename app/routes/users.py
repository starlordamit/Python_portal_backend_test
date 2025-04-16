from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from bson import ObjectId
from datetime import datetime

from ..models import UserUpdate, User, TokenData
from ..database import get_database
from ..auth import get_current_user

router = APIRouter(
    prefix="/api/auth/users",
    tags=["users"]
)

@router.patch("/{user_id}", response_model=User)
async def update_user_partial(
    user_id: str,
    user_update: UserUpdate,
    current_user: TokenData = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    Partially update a user. Only provided fields will be updated.
    Admin can update any user's information.
    Regular users can only update their own email and full_name.
    """
    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid user ID format"
        )
    
    # Convert string ID to ObjectId
    user_obj_id = ObjectId(user_id)
    
    # Get existing user
    user = await db.users.find_one({"_id": user_obj_id})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check permissions
    if current_user.role != "admin" and str(user["_id"]) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update other users"
        )
    
    # Prepare update data
    update_data = user_update.dict(exclude_unset=True)  # Only include set fields
    
    # Regular users can only update email and full_name
    if current_user.role != "admin":
        allowed_fields = {"email", "full_name"}
        update_data = {k: v for k, v in update_data.items() if k in allowed_fields}
    
    # Prevent last admin from being demoted
    if "role" in update_data and update_data["role"] != "admin":
        admin_count = await db.users.count_documents({"role": "admin"})
        if admin_count <= 1 and user["role"] == "admin":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the last admin"
            )
    
    # Check email uniqueness if email is being updated
    if "email" in update_data:
        existing_user = await db.users.find_one({
            "email": update_data["email"],
            "_id": {"$ne": user_obj_id}
        })
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Add updated_at timestamp
    update_data["updated_at"] = datetime.utcnow()
    
    # Perform update
    result = await db.users.update_one(
        {"_id": user_obj_id},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_304_NOT_MODIFIED,
            detail="User not modified"
        )
    
    # Get and return updated user
    updated_user = await db.users.find_one({"_id": user_obj_id})
    return updated_user 