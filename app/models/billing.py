from pydantic import BaseModel, Field, HttpUrl, constr, EmailStr, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from ..utils.object_id import PyObjectId
from ..models import Role # Import Role enum

class BankAccount(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    account_number: str
    ifsc_code: str
    account_holder_name: str
    bank_name: str
    branch_name: Optional[str] = None
    is_default: bool = False
    is_verified: bool = False
    cancelled_cheque_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class BillingDetailsBase(BaseModel):
    party_legal_name: str
    is_gst_applicable: bool = False
    gstin: Optional[str] = None
    pan_card: str
    state: str
    city: str
    address: str
    pincode: str
    is_individual: bool = True
    is_pancard_verified: bool = False
    is_gst_verified: bool = False
    is_msme: bool = False
    gst_certificate_url: Optional[str] = None
    msme_certificate_url: Optional[str] = None
    pan_card_url: Optional[str] = None

class BillingDetailsCreate(BillingDetailsBase):
    bank_accounts: Optional[List[BankAccount]] = []

class BillingDetailsUpdate(BaseModel):
    party_legal_name: Optional[str] = None
    is_gst_applicable: Optional[bool] = None
    gstin: Optional[str] = None
    pan_card: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    pincode: Optional[str] = None
    is_individual: Optional[bool] = None
    is_pancard_verified: Optional[bool] = None
    is_gst_verified: Optional[bool] = None
    is_msme: Optional[bool] = None
    gst_certificate_url: Optional[str] = None
    msme_certificate_url: Optional[str] = None
    pan_card_url: Optional[str] = None

class BillingDetails(BillingDetailsBase):
    id: PyObjectId = Field(alias="_id")
    bank_accounts: List[BankAccount] = []
    created_by: PyObjectId
    created_at: datetime
    updated_at: datetime
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "_id": "5f85f36d6dfecacc68428a46",
                "party_legal_name": "Example Company Ltd",
                "is_gst_applicable": True,
                "gstin": "27AADCB2230M1ZT",
                "pan_card": "AADCB2230M",
                "state": "Maharashtra",
                "city": "Mumbai",
                "address": "123 Example Street, Andheri East",
                "pincode": "400069",
                "is_individual": False,
                "is_pancard_verified": True,
                "is_gst_verified": True,
                "is_msme": False,
                "gst_certificate_url": "https://example.com/gst.pdf",
                "msme_certificate_url": None,
                "pan_card_url": "https://example.com/pan.pdf",
                "bank_accounts": [
                    {
                        "_id": "5f85f36d6dfecacc68428a47",
                        "account_number": "1234567890",
                        "ifsc_code": "SBIN0001234",
                        "account_holder_name": "Example Company Ltd",
                        "bank_name": "State Bank of India",
                        "branch_name": "Andheri East",
                        "is_default": True,
                        "is_verified": True,
                        "cancelled_cheque_url": "https://example.com/cheque.pdf",
                        "created_at": "2023-01-01T00:00:00",
                        "updated_at": "2023-01-01T00:00:00"
                    }
                ],
                "created_by": "5f85f36d6dfecacc68428a45",
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00"
            }
        }

class BankAccountCreate(BaseModel):
    account_number: str
    ifsc_code: str
    account_holder_name: str
    bank_name: str
    branch_name: Optional[str] = None
    is_default: bool = False
    cancelled_cheque_url: Optional[str] = None

class BankAccountUpdate(BaseModel):
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    account_holder_name: Optional[str] = None
    bank_name: Optional[str] = None
    branch_name: Optional[str] = None
    is_default: Optional[bool] = None
    is_verified: Optional[bool] = None
    cancelled_cheque_url: Optional[str] = None

class BillingDetailsPublic(BillingDetailsBase):
    id: PyObjectId = Field(alias="_id")
    bank_accounts: Optional[List[BankAccount]] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True

    @field_validator('gstin')
    def validate_gstin(cls, v):
        if v and len(v) != 15:
            raise ValueError('GSTIN must be 15 characters long')
        return v
    
    @field_validator('pan_card')
    def validate_pan(cls, v):
        if v and len(v) != 10:
            raise ValueError('PAN card must be 10 characters long')
        return v 