from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional, Union, Dict, Any
from bson import ObjectId
from datetime import datetime

from ..models import (
    Profile, 
    ProfileCreate, 
    ProfileUpdate, 
    ProfilePublic,
    Platform, 
    ContentOrientation, 
    Role
)
from ..database import profiles_collection, billing_details_collection
from ..auth import get_current_user
from ..utils.object_id import PyObjectId

router = APIRouter(prefix="/profiles", tags=["profiles"])

# Helper functions for role-based access control
def check_create_profile_permission(current_user: dict):
    """Check if user has permission to create profiles"""
    allowed_roles = [Role.ADMIN, Role.MANAGER, Role.OPERATIONS_MANAGER, Role.INTERN, Role.DATA_OPERATOR]
    if current_user["role"] not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to create profiles"
        )

def check_update_profile_permission(current_user: dict, profile: dict):
    """Check if user has permission to update profiles"""
    # Admin and Manager have full update permissions
    if current_user["role"] in [Role.ADMIN, Role.MANAGER]:
        return
    
    # Data operator can only update profiles they created
    if current_user["role"] == Role.DATA_OPERATOR:
        if str(profile["created_by"]) != current_user["_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update profiles you created"
            )
    else:
        # Operations Manager and Intern cannot update profiles
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update profiles"
        )

def filter_profile_for_limited_roles(profile: dict, current_user: dict) -> dict:
    """Remove sensitive fields from profile for limited roles"""
    # Admin, Manager, and Finance can see all fields
    if current_user["role"] in [Role.ADMIN, Role.MANAGER, Role.FINANCE]:
        return profile
    
    # Data operators can see all fields of their own profiles
    if current_user["role"] == Role.DATA_OPERATOR and str(profile.get("created_by")) == current_user["_id"]:
        return profile
    
    # Operations Manager, Intern, and Data Operator (for other profiles)
    # Cannot see contact details
    filtered_profile = profile.copy()
    if "contact_details" in filtered_profile:
        del filtered_profile["contact_details"]
    if "costing" in filtered_profile:
        del filtered_profile["costing"]
    if "billing_details_id" in filtered_profile:
        del filtered_profile["billing_details_id"]
    
    return filtered_profile

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_profile(
    profile: ProfileCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new profile.
    Admin, Manager, Operations Manager, Intern, and Data Operator can create profiles.
    """
    # Check if user has permission to create profiles
    check_create_profile_permission(current_user)
    
    # Validate billing_details_id if provided
    if profile.billing_details_id:
        try:
            object_id = ObjectId(profile.billing_details_id)
            billing_details = billing_details_collection.find_one({"_id": object_id})
            if not billing_details:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Billing details not found"
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid billing details ID: {str(e)}"
            )
    
    # Create profile
    profile_dict = profile.dict(by_alias=True)
    profile_dict["_id"] = ObjectId()
    profile_dict["created_by"] = ObjectId(current_user["_id"])
    profile_dict["created_at"] = datetime.utcnow()
    profile_dict["updated_at"] = datetime.utcnow()
    
    result = profiles_collection.insert_one(profile_dict)
    if result.inserted_id:
        return {"message": "Profile created successfully", "id": str(result.inserted_id)}
    
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create profile")

@router.get("/", response_model=List[Union[Profile, ProfilePublic]])
async def get_profiles(
    platform: Optional[Platform] = None,
    content_orientation: Optional[ContentOrientation] = None,
    region: Optional[str] = None,
    language: Optional[str] = None,
    min_followers: Optional[int] = None,
    max_followers: Optional[int] = None,
    search: Optional[str] = None,
    is_betting_allowed: Optional[bool] = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all profiles with filtering and pagination.
    All roles can view profiles, but the fields visible depend on the role.
    """
    # Build the query
    query: Dict[str, Any] = {}
    
    # Apply filters
    if platform:
        query["platform"] = platform
    if content_orientation:
        query["content_orientation"] = content_orientation
    if region:
        query["region"] = region
    if language:
        query["language"] = language
    if min_followers is not None:
        query["followers"] = {"$gte": min_followers}
    if max_followers is not None:
        followers_query = query.get("followers", {})
        followers_query["$lte"] = max_followers
        query["followers"] = followers_query
    if is_betting_allowed is not None:
        query["is_betting_allowed"] = is_betting_allowed
    
    # Text search
    if search:
        query["$or"] = [
            {"username": {"$regex": search, "$options": "i"}},
            {"region": {"$regex": search, "$options": "i"}},
            {"language": {"$regex": search, "$options": "i"}}
        ]
    
    # Data operators can only view their created profiles
    if current_user["role"] == Role.DATA_OPERATOR:
        query["created_by"] = ObjectId(current_user["_id"])
    
    # Fetch profiles with pagination
    profiles = list(profiles_collection.find(query).skip(skip).limit(limit))
    
    # Filter profiles based on role
    filtered_profiles = [filter_profile_for_limited_roles(profile, current_user) for profile in profiles]
    
    return filtered_profiles

@router.get("/{profile_id}", response_model=Union[Profile, ProfilePublic])
async def get_profile(
    profile_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific profile by ID.
    All roles can view profiles, but the fields visible depend on the role.
    """
    try:
        # Convert string ID to ObjectId
        object_id = ObjectId(profile_id)
        profile = profiles_collection.find_one({"_id": object_id})
        
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
        
        # Filter profile based on role
        filtered_profile = filter_profile_for_limited_roles(profile, current_user)
        
        return filtered_profile
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Invalid profile ID format: {str(e)}")

@router.put("/{profile_id}", response_model=dict)
async def update_profile(
    profile_id: str,
    profile_update: ProfileUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Update a profile.
    Admin and Manager have full update permissions.
    Data Operator can only update profiles they created.
    Operations Manager and Intern cannot update profiles.
    """
    try:
        # Convert string ID to ObjectId
        object_id = ObjectId(profile_id)
        
        # Get the existing profile
        profile = profiles_collection.find_one({"_id": object_id})
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
        
        # Check if user has permission to update this profile
        check_update_profile_permission(current_user, profile)
        
        # Validate billing_details_id if provided
        if profile_update.billing_details_id:
            try:
                billing_id = ObjectId(profile_update.billing_details_id)
                billing_details = billing_details_collection.find_one({"_id": billing_id})
                if not billing_details:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Billing details not found"
                    )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid billing details ID: {str(e)}"
                )
        
        # Convert Pydantic model to dict and exclude unset fields
        update_data = profile_update.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        
        # Update the profile
        result = profiles_collection.update_one(
            {"_id": object_id},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            return {"message": "No changes were made to the profile"}
        
        return {"message": "Profile updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Update failed: {str(e)}")

@router.delete("/{profile_id}")
async def delete_profile(
    profile_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a profile.
    Only Admin role can delete profiles.
    """
    # Only admin can delete profiles
    if current_user["role"] != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to delete profiles"
        )
    
    try:
        # Convert string ID to ObjectId
        object_id = ObjectId(profile_id)
        
        # Delete the profile
        result = profiles_collection.delete_one({"_id": object_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
        
        return {"message": "Profile deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Invalid profile ID format: {str(e)}") 