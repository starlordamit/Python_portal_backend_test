from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from bson import ObjectId
from datetime import datetime

from ..models import (
    Brand,
    BrandCreate,
    BrandUpdate,
    BrandPublic,
    POC,
    POCCreate,
    Role
)
from ..database import brands_collection, billing_details_collection
from ..auth import get_current_user
from ..utils.object_id import PyObjectId

router = APIRouter(prefix="/brands", tags=["brands"])

# Helper function to check admin/manager permissions for create/update/delete operations
def check_admin_manager_permissions(current_user: dict):
    allowed_roles = [Role.ADMIN, Role.MANAGER]
    if current_user["role"] not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Requires admin or manager role."
        )

# Helper function to check if a user has full view permissions
def has_full_view_permissions(current_user: dict) -> bool:
    allowed_roles = [Role.ADMIN, Role.MANAGER, Role.FINANCE]
    return current_user["role"] in allowed_roles

# Creates a BrandPublic model for limited visibility
def filter_brand_for_public(brand: dict) -> dict:
    """Filter out sensitive information for non-privileged roles"""
    return {
        "_id": brand["_id"],
        "name": brand["name"],
        "website": brand.get("website"),
        "instagram": brand.get("instagram"),
        "linkedin": brand.get("linkedin"),
        "logo_url": brand.get("logo_url"),
        "created_at": brand["created_at"],
        "updated_at": brand["updated_at"]
    }

# BRAND CRUD OPERATIONS
@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_brand(
    brand_data: BrandCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new brand.
    Only admin and manager roles can create brands.
    """
    # Check if user has permission to create brands
    check_admin_manager_permissions(current_user)
    
    # Validate billing_details_id if provided
    if brand_data.billing_details_id:
        billing_id = brand_data.billing_details_id
        try:
            object_id = ObjectId(billing_id)
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
    
    # Create new brand
    new_brand = brand_data.dict(by_alias=True)
    new_brand["_id"] = ObjectId()
    new_brand["created_by"] = current_user["_id"]
    new_brand["created_at"] = datetime.utcnow()
    new_brand["updated_at"] = datetime.utcnow()
    
    # Add IDs and timestamps to POCs if they exist
    if new_brand.get("pocs"):
        for poc in new_brand["pocs"]:
            poc["_id"] = str(ObjectId())
            poc["created_at"] = datetime.utcnow()
            poc["updated_at"] = datetime.utcnow()
    
    result = brands_collection.insert_one(new_brand)
    if result.inserted_id:
        return {"message": "Brand created successfully", "id": str(result.inserted_id)}
    
    raise HTTPException(status_code=400, detail="Failed to create brand")

@router.get("/", response_model=List[Brand])
async def get_brands(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all brands.
    All roles can view brands, but sensitive information is filtered for non-privileged roles.
    """
    # Fetch brands with pagination
    brands = list(brands_collection.find().skip(skip).limit(limit))
    
    # Filter brands based on user role
    if not has_full_view_permissions(current_user):
        # Filter out sensitive information for non-privileged roles
        brands = [filter_brand_for_public(brand) for brand in brands]
    
    return brands

@router.get("/{brand_id}", response_model=Brand)
async def get_brand(
    brand_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific brand by ID.
    All roles can view, but sensitive information is filtered for non-privileged roles.
    """
    try:
        # Convert string ID to ObjectId
        object_id = ObjectId(brand_id)
        brand = brands_collection.find_one({"_id": object_id})
        
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")
        
        # Filter brand if user doesn't have full view permissions
        if not has_full_view_permissions(current_user):
            brand = filter_brand_for_public(brand)
        
        return brand
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Invalid brand ID format: {str(e)}")

@router.put("/{brand_id}", response_model=dict)
async def update_brand(
    brand_id: str,
    brand_data: BrandUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Update a brand.
    Only admin and manager roles can update brands.
    """
    # Check if user has permission to update brands
    check_admin_manager_permissions(current_user)
    
    # Validate billing_details_id if provided
    if brand_data.billing_details_id:
        billing_id = brand_data.billing_details_id
        try:
            object_id = ObjectId(billing_id)
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
    
    # Convert Pydantic model to dict and exclude unset fields
    update_data = brand_data.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    try:
        # Convert string ID to ObjectId
        object_id = ObjectId(brand_id)
        result = brands_collection.update_one(
            {"_id": object_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Brand not found")
        
        return {"message": "Brand updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Invalid brand ID format: {str(e)}")

@router.delete("/{brand_id}")
async def delete_brand(
    brand_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a brand.
    Only admin role can delete brands.
    """
    # Only admin can delete brands
    if current_user["role"] != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Requires admin role."
        )
    
    try:
        # Convert string ID to ObjectId
        object_id = ObjectId(brand_id)
        result = brands_collection.delete_one({"_id": object_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Brand not found")
        
        return {"message": "Brand deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Invalid brand ID format: {str(e)}")

# POC OPERATIONS
@router.post("/{brand_id}/pocs", response_model=dict)
async def add_poc(
    brand_id: str,
    poc_data: POCCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Add a new POC to a brand.
    Only admin and manager roles can add POCs.
    """
    # Check if user has permission to add POCs
    check_admin_manager_permissions(current_user)
    
    try:
        # Convert string ID to ObjectId
        object_id = ObjectId(brand_id)
        brand = brands_collection.find_one({"_id": object_id})
        
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")
        
        # Create new POC
        new_poc = poc_data.dict()
        new_poc["_id"] = str(ObjectId())
        new_poc["created_at"] = datetime.utcnow()
        new_poc["updated_at"] = datetime.utcnow()
        
        # Add the POC to the brand
        result = brands_collection.update_one(
            {"_id": object_id},
            {"$push": {"pocs": new_poc}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="Failed to add POC")
        
        return {"message": "POC added successfully", "id": new_poc["_id"]}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Invalid brand ID format: {str(e)}")

@router.put("/{brand_id}/pocs/{poc_id}", response_model=dict)
async def update_poc(
    brand_id: str,
    poc_id: str,
    poc_data: POCCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Update a POC.
    Only admin and manager roles can update POCs.
    """
    # Check if user has permission to update POCs
    check_admin_manager_permissions(current_user)
    
    # Convert Pydantic model to dict
    update_data = poc_data.dict()
    update_data["updated_at"] = datetime.utcnow()
    
    try:
        # Convert string ID to ObjectId
        object_id = ObjectId(brand_id)
        
        # Prepare update fields using dot notation for nested documents
        update_fields = {}
        for key, value in update_data.items():
            update_fields[f"pocs.$.{key}"] = value
        
        # Update the POC in the brand
        result = brands_collection.update_one(
            {"_id": object_id, "pocs._id": poc_id},
            {"$set": update_fields}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Brand or POC not found")
        
        return {"message": "POC updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Invalid ID format: {str(e)}")

@router.delete("/{brand_id}/pocs/{poc_id}")
async def delete_poc(
    brand_id: str,
    poc_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a POC from a brand.
    Only admin and manager roles can delete POCs.
    """
    # Check if user has permission to delete POCs
    check_admin_manager_permissions(current_user)
    
    try:
        # Convert string ID to ObjectId
        object_id = ObjectId(brand_id)
        
        # Remove the POC from the brand
        result = brands_collection.update_one(
            {"_id": object_id},
            {"$pull": {"pocs": {"_id": poc_id}}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Brand not found")
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="POC not found")
        
        return {"message": "POC deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Invalid ID format: {str(e)}") 