from enum import Enum, auto

class Role(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    DATA_OPERATOR = "data_operator"
    OPERATIONS_MANAGER = "operations_manager"
    INTERN = "intern"
    FINANCE = "finance"
    
# Export all models
from .user import User, TokenData
from .profile import (
    Profile,
    ProfileCreate,
    ProfileUpdate,
    ProfilePublic,
    Platform,
    ContentOrientation,
    ContactDetail,
    CostingDetail
)
from .billing import (
    BillingDetails, 
    BillingDetailsCreate, 
    BillingDetailsUpdate, 
    BankAccount, 
    BankAccountCreate, 
    BankAccountUpdate
)
from .brand import (
    Brand,
    BrandCreate,
    BrandUpdate,
    BrandPublic,
    POC,
    POCCreate
) 