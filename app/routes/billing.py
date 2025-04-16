from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from bson import ObjectId
from datetime import datetime

from ..models import (
    BillingDetails, 
    BillingDetailsCreate, 
    BillingDetailsUpdate, 
    BankAccount, 
    BankAccountCreate, 
    BankAccountUpdate,
    Role
)
from ..database import billing_details_collection
from ..auth import get_current_user
from ..utils.object_id import PyObjectId

router = APIRouter(prefix="/billing", tags=["billing"])

# Helper function to check finance permissions
def check_finance_permissions(current_user: dict):
    allowed_roles = [Role.ADMIN, Role.FINANCE, Role.MANAGER]
    if current_user["role"] not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Requires admin, finance, or manager role."
        )

# Billing details CRUD operations
@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_billing_details(
    billing_data: BillingDetailsCreate,
    current_user: dict = Depends(get_current_user)
):
    # Check if user has permission to create billing details
    check_finance_permissions(current_user)
    
    # If GSTIN is provided but GST is not applicable, raise an error
    if billing_data.gstin and not billing_data.is_gst_applicable:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot provide GSTIN when GST is not applicable"
        )
    
    # Create new billing details
    new_billing = billing_data.dict(by_alias=True)
    new_billing["_id"] = ObjectId()
    new_billing["created_by"] = current_user["_id"]
    new_billing["created_at"] = datetime.utcnow()
    new_billing["updated_at"] = datetime.utcnow()
    
    # Add IDs and timestamps to bank accounts if they exist
    if new_billing.get("bank_accounts"):
        for i, account in enumerate(new_billing["bank_accounts"]):
            account["_id"] = str(ObjectId())
            account["created_at"] = datetime.utcnow()
            account["updated_at"] = datetime.utcnow()
            # If it's the first account or marked as default
            if i == 0 or account.get("is_default"):
                account["is_default"] = True
                # Ensure only one account is default
                for other in new_billing["bank_accounts"]:
                    if other != account:
                        other["is_default"] = False
    
    result = billing_details_collection.insert_one(new_billing)
    if result.inserted_id:
        return {"message": "Billing details created successfully", "id": str(result.inserted_id)}
    raise HTTPException(status_code=400, detail="Failed to create billing details")

@router.get("/", response_model=List[BillingDetails])
async def get_billing_details(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    # Check if user has permission to view billing details
    check_finance_permissions(current_user)
    
    billing_details = list(billing_details_collection.find().skip(skip).limit(limit))
    return billing_details

@router.get("/{billing_id}", response_model=BillingDetails)
async def get_billing_detail(
    billing_id: str,
    current_user: dict = Depends(get_current_user)
):
    # Check if user has permission to view billing details
    check_finance_permissions(current_user)
    
    # Convert string ID to ObjectId
    try:
        object_id = ObjectId(billing_id)
        billing_detail = billing_details_collection.find_one({"_id": object_id})
        if not billing_detail:
            raise HTTPException(status_code=404, detail="Billing details not found")
        
        return billing_detail
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Invalid billing ID format: {str(e)}")

@router.put("/{billing_id}", response_model=dict)
async def update_billing_details(
    billing_id: str,
    billing_data: BillingDetailsUpdate,
    current_user: dict = Depends(get_current_user)
):
    # Check if user has permission to update billing details
    if current_user["role"] not in [Role.ADMIN, Role.FINANCE]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Requires admin or finance role."
        )
    
    # If GSTIN is provided but GST is not applicable, raise an error
    if billing_data.gstin and billing_data.is_gst_applicable is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot provide GSTIN when GST is not applicable"
        )
    
    # Convert Pydantic model to dict and exclude unset fields
    update_data = billing_data.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    try:
        object_id = ObjectId(billing_id)
        result = billing_details_collection.update_one(
            {"_id": object_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Billing details not found")
        
        return {"message": "Billing details updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Invalid billing ID format: {str(e)}")

@router.delete("/{billing_id}")
async def delete_billing_details(
    billing_id: str,
    current_user: dict = Depends(get_current_user)
):
    # Only admin and finance can delete billing details
    if current_user["role"] not in [Role.ADMIN, Role.FINANCE]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Requires admin or finance role."
        )
    
    try:
        object_id = ObjectId(billing_id)
        result = billing_details_collection.delete_one({"_id": object_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Billing details not found")
        
        return {"message": "Billing details deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Invalid billing ID format: {str(e)}")

# Bank account operations
@router.post("/{billing_id}/bank-accounts", response_model=dict)
async def add_bank_account(
    billing_id: str,
    account_data: BankAccountCreate,
    current_user: dict = Depends(get_current_user)
):
    # Check if user has permission to add bank accounts
    if current_user["role"] not in [Role.ADMIN, Role.FINANCE]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Requires admin or finance role."
        )
    
    # Check if billing details exist
    try:
        object_id = ObjectId(billing_id)
        billing = billing_details_collection.find_one({"_id": object_id})
        if not billing:
            raise HTTPException(status_code=404, detail="Billing details not found")
        
        # Create new bank account
        new_account = account_data.dict()
        new_account["_id"] = str(ObjectId())
        new_account["is_verified"] = False
        new_account["created_at"] = datetime.utcnow()
        new_account["updated_at"] = datetime.utcnow()
        
        # If this is the first account or set as default
        if not billing.get("bank_accounts") or new_account["is_default"]:
            new_account["is_default"] = True
            # Update existing accounts to not be default
            if billing.get("bank_accounts"):
                billing_details_collection.update_one(
                    {"_id": object_id},
                    {"$set": {"bank_accounts.$[].is_default": False}}
                )
        
        # Add the new account
        result = billing_details_collection.update_one(
            {"_id": object_id},
            {"$push": {"bank_accounts": new_account}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="Failed to add bank account")
        
        return {"message": "Bank account added successfully", "id": new_account["_id"]}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Invalid billing ID format: {str(e)}")

@router.put("/{billing_id}/bank-accounts/{account_id}", response_model=dict)
async def update_bank_account(
    billing_id: str,
    account_id: str,
    account_data: BankAccountUpdate,
    current_user: dict = Depends(get_current_user)
):
    # Check if user has permission to update bank accounts
    if current_user["role"] not in [Role.ADMIN, Role.FINANCE]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Requires admin or finance role."
        )
    
    # Convert Pydantic model to dict and exclude unset fields
    update_data = account_data.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    try:
        object_id = ObjectId(billing_id)
        # Update the bank account
        result = billing_details_collection.update_one(
            {
                "_id": object_id,
                "bank_accounts._id": account_id
            },
            {
                "$set": {
                    f"bank_accounts.$.{key}": value
                    for key, value in update_data.items()
                }
            }
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Billing details or bank account not found")
        
        # If setting this account as default, update others to not be default
        if update_data.get("is_default") is True:
            billing_details_collection.update_one(
                {
                    "_id": object_id,
                    "bank_accounts._id": {"$ne": account_id}
                },
                {
                    "$set": {"bank_accounts.$[].is_default": False}
                }
            )
        
        return {"message": "Bank account updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Invalid ID format: {str(e)}")

@router.delete("/{billing_id}/bank-accounts/{account_id}")
async def delete_bank_account(
    billing_id: str,
    account_id: str,
    current_user: dict = Depends(get_current_user)
):
    # Check if user has permission to delete bank accounts
    if current_user["role"] not in [Role.ADMIN, Role.FINANCE]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Requires admin or finance role."
        )
    
    try:
        object_id = ObjectId(billing_id)
        # Get the billing details to check if the account exists
        billing = billing_details_collection.find_one(
            {
                "_id": object_id,
                "bank_accounts._id": account_id
            }
        )
        
        if not billing:
            raise HTTPException(status_code=404, detail="Billing details or bank account not found")
        
        # Check if this is the only bank account
        if len(billing.get("bank_accounts", [])) == 1:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete the only bank account. Add another account first."
            )
        
        # Find the account to check if it's the default
        is_default = False
        for account in billing.get("bank_accounts", []):
            if account.get("_id") == account_id and account.get("is_default"):
                is_default = True
                break
        
        # Remove the bank account
        result = billing_details_collection.update_one(
            {"_id": object_id},
            {"$pull": {"bank_accounts": {"_id": account_id}}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="Failed to delete bank account")
        
        # If the deleted account was the default, set a new default
        if is_default:
            # Find another account and set it as default
            billing_details_collection.update_one(
                {"_id": object_id},
                {"$set": {"bank_accounts.0.is_default": True}}
            )
        
        return {"message": "Bank account deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Invalid ID format: {str(e)}")

@router.patch("/{billing_id}/bank-accounts/{account_id}/set-default")
async def set_default_bank_account(
    billing_id: str,
    account_id: str,
    current_user: dict = Depends(get_current_user)
):
    # Check if user has permission to update bank accounts
    if current_user["role"] not in [Role.ADMIN, Role.FINANCE]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Requires admin or finance role."
        )
    
    try:
        object_id = ObjectId(billing_id)
        # Set all accounts to not default
        billing_details_collection.update_one(
            {"_id": object_id},
            {"$set": {"bank_accounts.$[].is_default": False}}
        )
        
        # Set this account as default
        result = billing_details_collection.update_one(
            {
                "_id": object_id,
                "bank_accounts._id": account_id
            },
            {"$set": {"bank_accounts.$.is_default": True}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Billing details or bank account not found")
        
        return {"message": "Bank account set as default successfully"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Invalid ID format: {str(e)}")

@router.patch("/{billing_id}/bank-accounts/{account_id}/verify")
async def verify_bank_account(
    billing_id: str,
    account_id: str,
    current_user: dict = Depends(get_current_user)
):
    # Only admin and finance can verify bank accounts
    if current_user["role"] not in [Role.ADMIN, Role.FINANCE]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Requires admin or finance role."
        )
    
    try:
        object_id = ObjectId(billing_id)
        result = billing_details_collection.update_one(
            {
                "_id": object_id,
                "bank_accounts._id": account_id
            },
            {"$set": {"bank_accounts.$.is_verified": True}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Billing details or bank account not found")
        
        return {"message": "Bank account verified successfully"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Invalid ID format: {str(e)}")

@router.patch("/{billing_id}/verify-gst")
async def verify_gst(
    billing_id: str,
    current_user: dict = Depends(get_current_user)
):
    # Only admin and finance can verify GST
    if current_user["role"] not in [Role.ADMIN, Role.FINANCE]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Requires admin or finance role."
        )
    
    try:
        object_id = ObjectId(billing_id)
        billing = billing_details_collection.find_one({"_id": object_id})
        if not billing:
            raise HTTPException(status_code=404, detail="Billing details not found")
        
        if not billing.get("gstin"):
            raise HTTPException(status_code=400, detail="No GSTIN provided in billing details")
        
        result = billing_details_collection.update_one(
            {"_id": object_id},
            {"$set": {"is_gst_verified": True}}
        )
        
        return {"message": "GST verified successfully"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Invalid billing ID format: {str(e)}")

@router.patch("/{billing_id}/verify-pan")
async def verify_pan(
    billing_id: str,
    current_user: dict = Depends(get_current_user)
):
    # Only admin and finance can verify PAN
    if current_user["role"] not in [Role.ADMIN, Role.FINANCE]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Requires admin or finance role."
        )
    
    try:
        object_id = ObjectId(billing_id)
        billing = billing_details_collection.find_one({"_id": object_id})
        if not billing:
            raise HTTPException(status_code=404, detail="Billing details not found")
        
        if not billing.get("pan_card"):
            raise HTTPException(status_code=400, detail="No PAN card provided in billing details")
        
        result = billing_details_collection.update_one(
            {"_id": object_id},
            {"$set": {"is_pancard_verified": True}}
        )
        
        return {"message": "PAN card verified successfully"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Invalid billing ID format: {str(e)}")

@router.patch("/{billing_id}/set-msme-status")
async def set_msme_status(
    billing_id: str,
    is_msme: str = Query(..., description="Set to 'true' to enable MSME status or 'false' to disable"),
    current_user: dict = Depends(get_current_user)
):
    """
    Set the MSME status of a billing detail.
    
    Args:
        billing_id: ID of the billing detail
        is_msme: 'true' or 'false' string to set MSME status
        current_user: Current user from authentication
        
    Returns:
        Success message
    """
    # Only admin and finance can change MSME status
    if current_user["role"] not in [Role.ADMIN, Role.FINANCE]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Requires admin or finance role."
        )
    
    # Safely convert string to boolean
    is_msme_bool = is_msme.lower() == "true"
    
    try:
        # Validate MongoDB ObjectId
        if not ObjectId.is_valid(billing_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid billing ID format"
            )
        
        # Find the billing details
        object_id = ObjectId(billing_id)
        billing = billing_details_collection.find_one({"_id": object_id})
        if not billing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Billing details not found"
            )
        
        # Check MSME certificate if setting to true
        if is_msme_bool and not billing.get("msme_certificate_url"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MSME certificate URL must be provided to set MSME status to true"
            )
        
        # Update the MSME status
        result = billing_details_collection.update_one(
            {"_id": object_id},
            {"$set": {
                "is_msme": is_msme_bool,
                "updated_at": datetime.utcnow()
            }}
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_304_NOT_MODIFIED,
                detail="No changes made to MSME status"
            )
        
        return {"message": f"MSME status set to {is_msme_bool} successfully"}
    except HTTPException:
        # Reraise HTTP exceptions
        raise
    except Exception as e:
        # Log the error for debugging
        print(f"Error in set_msme_status: {type(e).__name__}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        ) 