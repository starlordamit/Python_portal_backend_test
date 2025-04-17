import requests
import json
import time
from datetime import datetime

# Base URLs
AUTH_URL = "http://localhost:5002/api/auth"
PROFILES_URL = "http://localhost:5002/api/profiles"
BILLING_URL = "http://localhost:5002/api/billing"

# Admin credentials for testing
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "admin123"

# Colors for output formatting
GREEN = "\033[32m"
RED = "\033[31m"
RESET = "\033[0m"
BLUE = "\033[34m"
YELLOW = "\033[33m"

# Helper function to get admin token
def get_token():
    login_data = {
        "username": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    }
    response = requests.post(f"{AUTH_URL}/login", data=login_data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"{RED}Failed to get token: {response.text}{RESET}")
        exit(1)

# Helper function to print response
def print_response(action, response):
    print(f"\n{BLUE}=== {action} ==={RESET}")
    print(f"Status Code: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)
    
    if 200 <= response.status_code < 300:
        print(f"{GREEN}✓ Success{RESET}")
    else:
        print(f"{RED}✗ Failed{RESET}")
    print("\n" + "-" * 80)

# Main testing function
def run_tests():
    print(f"{YELLOW}Starting Profile API Tests...{RESET}")
    
    # Get admin token
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Step 1: Create billing details first (we need this for the profile)
    print(f"{YELLOW}Step 1: Creating billing details...{RESET}")
    billing_data = {
        "account_number": "1234567890",
        "ifsc_code": "HDFC0001234",
        "bank_name": "HDFC Bank",
        "branch_name": "Mumbai Branch",
        "account_holder_name": "Test Account",
        "account_type": "Savings",
        "party_legal_name": "Test Company Ltd",
        "party_address": "123 Test Street, Mumbai",
        "party_pan": "ABCDE1234F",
        "party_gst": "27ABCDE1234F1Z5",
        "msme_registered": True,
        "msme_registration_number": "UDYAM-MH-01-0123456"
    }
    
    billing_response = requests.post(
        f"{BILLING_URL}/",
        headers=headers,
        json=billing_data
    )
    print_response("Create Billing Details", billing_response)
    
    if billing_response.status_code != 201:
        print(f"{RED}Failed to create billing details. Exiting tests.{RESET}")
        return
    
    billing_id = billing_response.json()["id"]
    
    # Step 2: Create a profile
    print(f"{YELLOW}Step 2: Creating a profile...{RESET}")
    profile_data = {
        "platform": "Instagram",
        "username": "testuser",
        "display_name": "Test User",
        "followers": 10000,
        "engagement_rate": 3.5,
        "content_type": ["Fashion", "Lifestyle"],
        "contact_details": {
            "email": "testuser@example.com",
            "phone": "9876543210"
        },
        "billing_details_id": billing_id,
        "costing_details": {
            "post": 5000,
            "story": 2000,
            "reel": 8000,
            "video": 10000
        },
        "notes": "Test profile for API testing"
    }
    
    profile_response = requests.post(
        PROFILES_URL,
        headers=headers,
        json=profile_data
    )
    print_response("Create Profile", profile_response)
    
    if profile_response.status_code != 201:
        print(f"{RED}Failed to create profile. Exiting tests.{RESET}")
        # Clean up
        requests.delete(f"{BILLING_URL}/{billing_id}", headers=headers)
        return
    
    profile_id = profile_response.json()["id"]
    
    # Step 3: Get all profiles
    print(f"{YELLOW}Step 3: Getting all profiles...{RESET}")
    get_profiles_response = requests.get(
        PROFILES_URL,
        headers=headers
    )
    print_response("Get All Profiles", get_profiles_response)
    
    # Step 4: Get profiles with filter
    print(f"{YELLOW}Step 4: Getting profiles with filter...{RESET}")
    get_filtered_profiles_response = requests.get(
        f"{PROFILES_URL}?platform=Instagram&followers_min=5000",
        headers=headers
    )
    print_response("Get Filtered Profiles", get_filtered_profiles_response)
    
    # Step 5: Get a specific profile
    print(f"{YELLOW}Step 5: Getting specific profile...{RESET}")
    get_profile_response = requests.get(
        f"{PROFILES_URL}/{profile_id}",
        headers=headers
    )
    print_response("Get Specific Profile", get_profile_response)
    
    # Step 6: Update the profile
    print(f"{YELLOW}Step 6: Updating profile...{RESET}")
    update_data = {
        "username": "updateduser",
        "followers": 15000,
        "contact_details": {
            "email": "updateduser@example.com",
            "phone": "9876543210"
        },
        "notes": "Updated test profile"
    }
    
    update_profile_response = requests.put(
        f"{PROFILES_URL}/{profile_id}",
        headers=headers,
        json=update_data
    )
    print_response("Update Profile", update_profile_response)
    
    # Step 7: Get the updated profile
    print(f"{YELLOW}Step 7: Getting updated profile...{RESET}")
    get_updated_profile_response = requests.get(
        f"{PROFILES_URL}/{profile_id}",
        headers=headers
    )
    print_response("Get Updated Profile", get_updated_profile_response)
    
    # Step 8: Delete the profile
    print(f"{YELLOW}Step 8: Deleting profile...{RESET}")
    delete_profile_response = requests.delete(
        f"{PROFILES_URL}/{profile_id}",
        headers=headers
    )
    print_response("Delete Profile", delete_profile_response)
    
    # Step 9: Clean up - Delete billing details
    print(f"{YELLOW}Step 9: Cleaning up - Deleting billing details...{RESET}")
    delete_billing_response = requests.delete(
        f"{BILLING_URL}/{billing_id}",
        headers=headers
    )
    print_response("Delete Billing Details", delete_billing_response)
    
    print(f"{GREEN}Profile API Tests Completed!{RESET}")

if __name__ == "__main__":
    run_tests() 