from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from bson.objectid import ObjectId
from datetime import datetime

from app.auth import get_current_user
from app.database import profiles_collection, billing_details_collection, brands_collection
from app.models.profile import Profile
from app.models.billing import BillingDetailsPublic
from app.utils.object_id import PyObjectId
from app.models import Role

router = APIRouter(
    prefix="/billing-connections",
    tags=["billing-connections"]
)

@router.get("/profile-billing/{profile_id}", response_description="Get billing details for a profile", status_code=status.HTTP_200_OK)
async def get_profile_billing(
    profile_id: str,
    current_user: dict = Depends(get_current_user)
):
    # Only admin, manager, data_operator, or profile owner can see billing details
    allowed_roles = [Role.ADMIN, Role.MANAGER, Role.DATA_OPERATOR, Role.INTERN]
    if current_user["role"] not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access billing information"
        )
    
    # Get profile to check ownership and extract billing_details_id
    profile = await profiles_collection.find_one({"_id": ObjectId(profile_id)})
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile with ID {profile_id} not found"
        )
    
    # If data operator, check if they have access to this profile
    if current_user["role"] == Role.DATA_OPERATOR and str(profile["created_by"]) != current_user["_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access billing for profiles you created"
        )
    
    # If profile doesn't have billing details
    if not profile.get("billing_details_id"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No billing details associated with this profile"
        )
    
    # Get billing details
    billing_details = await billing_details_collection.find_one({"_id": ObjectId(profile["billing_details_id"])})
    if not billing_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated billing details not found"
        )
    
    return {
        "profile_id": profile_id,
        "profile_username": profile.get("username"),
        "billing_details": billing_details
    }

@router.patch("/connect-profile-billing/{profile_id}/{billing_id}", response_description="Connect billing details to profile", status_code=status.HTTP_200_OK)
async def connect_profile_billing(
    profile_id: str,
    billing_id: str,
    current_user: dict = Depends(get_current_user)
):
    # Only admin and manager can connect billing details
    if current_user["role"] not in [Role.ADMIN, Role.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin and manager can connect billing details"
        )
    
    # Check if profile exists
    profile = await profiles_collection.find_one({"_id": ObjectId(profile_id)})
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile with ID {profile_id} not found"
        )
    
    # Check if billing details exist
    billing_details = await billing_details_collection.find_one({"_id": ObjectId(billing_id)})
    if not billing_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Billing details with ID {billing_id} not found"
        )
    
    # Update profile with billing details
    update_result = await profiles_collection.update_one(
        {"_id": ObjectId(profile_id)},
        {"$set": {
            "billing_details_id": ObjectId(billing_id),
            "updated_at": datetime.utcnow()
        }}
    )
    
    if update_result.modified_count == 1:
        return {"message": f"Successfully connected profile {profile_id} with billing details {billing_id}"}
    else:
        return {"message": "No changes made"}

@router.patch("/disconnect-profile-billing/{profile_id}", response_description="Disconnect billing details from profile", status_code=status.HTTP_200_OK)
async def disconnect_profile_billing(
    profile_id: str,
    current_user: dict = Depends(get_current_user)
):
    # Only admin and manager can disconnect billing details
    if current_user["role"] not in [Role.ADMIN, Role.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin and manager can disconnect billing details"
        )
    
    # Check if profile exists
    profile = await profiles_collection.find_one({"_id": ObjectId(profile_id)})
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile with ID {profile_id} not found"
        )
    
    # Check if profile has billing details
    if not profile.get("billing_details_id"):
        return {"message": "Profile has no billing details to disconnect"}
    
    # Update profile to remove billing details
    update_result = await profiles_collection.update_one(
        {"_id": ObjectId(profile_id)},
        {"$unset": {"billing_details_id": ""},
         "$set": {"updated_at": datetime.utcnow()}}
    )
    
    if update_result.modified_count == 1:
        return {"message": f"Successfully disconnected billing details from profile {profile_id}"}
    else:
        return {"message": "No changes made"}

# Brand-related billing connection routes

@router.get("/brand-billing/{brand_id}", response_description="Get billing details for a brand", status_code=status.HTTP_200_OK)
async def get_brand_billing(
    brand_id: str,
    current_user: dict = Depends(get_current_user)
):
    # Only admin, manager, data_operator, or brand owner can see billing details
    allowed_roles = [Role.ADMIN, Role.MANAGER, Role.DATA_OPERATOR, Role.INTERN]
    if current_user["role"] not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access billing information"
        )
    
    # Get brand to check ownership and extract billing_details_id
    brand = await brands_collection.find_one({"_id": ObjectId(brand_id)})
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand with ID {brand_id} not found"
        )
    
    # If data operator, check if they have access to this brand
    if current_user["role"] == Role.DATA_OPERATOR and str(brand["created_by"]) != current_user["_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access billing for brands you created"
        )
    
    # If brand doesn't have billing details
    if not brand.get("billing_details_id"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No billing details associated with this brand"
        )
    
    # Get billing details
    billing_details = await billing_details_collection.find_one({"_id": ObjectId(brand["billing_details_id"])})
    if not billing_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated billing details not found"
        )
    
    return {
        "brand_id": brand_id,
        "brand_name": brand.get("name", brand.get("company_name")),
        "billing_details": billing_details
    }

@router.patch("/connect-brand-billing/{brand_id}/{billing_id}", response_description="Connect billing details to brand", status_code=status.HTTP_200_OK)
async def connect_brand_billing(
    brand_id: str,
    billing_id: str,
    current_user: dict = Depends(get_current_user)
):
    # Only admin and manager can connect billing details
    if current_user["role"] not in [Role.ADMIN, Role.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin and manager can connect billing details"
        )
    
    # Check if brand exists
    brand = await brands_collection.find_one({"_id": ObjectId(brand_id)})
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand with ID {brand_id} not found"
        )
    
    # Check if billing details exist
    billing_details = await billing_details_collection.find_one({"_id": ObjectId(billing_id)})
    if not billing_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Billing details with ID {billing_id} not found"
        )
    
    # Update brand with billing details
    update_result = await brands_collection.update_one(
        {"_id": ObjectId(brand_id)},
        {"$set": {
            "billing_details_id": ObjectId(billing_id),
            "updated_at": datetime.utcnow()
        }}
    )
    
    if update_result.modified_count == 1:
        return {"message": f"Successfully connected brand {brand_id} with billing details {billing_id}"}
    else:
        return {"message": "No changes made"}

@router.patch("/disconnect-brand-billing/{brand_id}", response_description="Disconnect billing details from brand", status_code=status.HTTP_200_OK)
async def disconnect_brand_billing(
    brand_id: str,
    current_user: dict = Depends(get_current_user)
):
    # Only admin and manager can disconnect billing details
    if current_user["role"] not in [Role.ADMIN, Role.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin and manager can disconnect billing details"
        )
    
    # Check if brand exists
    brand = await brands_collection.find_one({"_id": ObjectId(brand_id)})
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand with ID {brand_id} not found"
        )
    
    # Check if brand has billing details
    if not brand.get("billing_details_id"):
        return {"message": "Brand has no billing details to disconnect"}
    
    # Update brand to remove billing details
    update_result = await brands_collection.update_one(
        {"_id": ObjectId(brand_id)},
        {"$unset": {"billing_details_id": ""},
         "$set": {"updated_at": datetime.utcnow()}}
    )
    
    if update_result.modified_count == 1:
        return {"message": f"Successfully disconnected billing details from brand {brand_id}"}
    else:
        return {"message": "No changes made"}

# Get entities using a billing details
@router.get("/billing-users/{billing_id}", response_description="Get profiles and brands using this billing details", status_code=status.HTTP_200_OK)
async def get_billing_users(
    billing_id: str,
    current_user: dict = Depends(get_current_user)
):
    # Only admin and manager can see all connections
    if current_user["role"] not in [Role.ADMIN, Role.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin and manager can view all billing connections"
        )
    
    # Check if billing details exist
    billing_details = await billing_details_collection.find_one({"_id": ObjectId(billing_id)})
    if not billing_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Billing details with ID {billing_id} not found"
        )
    
    # Find profiles using this billing details
    profiles_cursor = profiles_collection.find({"billing_details_id": ObjectId(billing_id)})
    profiles = await profiles_cursor.to_list(length=100)
    
    # Find brands using this billing details
    brands_cursor = brands_collection.find({"billing_details_id": ObjectId(billing_id)})
    brands = await brands_cursor.to_list(length=100)
    
    # Extract relevant information
    profiles_info = []
    for profile in profiles:
        profiles_info.append({
            "id": str(profile["_id"]),
            "username": profile.get("username"),
            "platform": profile.get("platform"),
            "created_at": profile.get("created_at"),
        })
    
    brands_info = []
    for brand in brands:
        brands_info.append({
            "id": str(brand["_id"]),
            "name": brand.get("name", brand.get("company_name")),
            "created_at": brand.get("created_at"),
        })
    
    return {
        "billing_id": billing_id,
        "profiles": profiles_info,
        "brands": brands_info,
        "total_profiles": len(profiles_info),
        "total_brands": len(brands_info)
    } 