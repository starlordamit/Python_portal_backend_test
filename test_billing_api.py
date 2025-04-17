"""
Test script for the Billing API endpoints with filtering and pagination support.
"""
import requests
import json
import time
import sys

# Base URLs
BASE_URL = "http://localhost:5002/api"
AUTH_URL = f"{BASE_URL}/auth"
BILLING_URL = f"{BASE_URL}/billing"

# Admin credentials
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "admin"

# ANSI color codes for better output formatting
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"
BLUE = "\033[94m"
YELLOW = "\033[93m"

def get_token():
    """Get admin token for authentication"""
    login_data = {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    }
    response = requests.post(f"{AUTH_URL}/login", json=login_data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"{RED}Failed to login: {response.text}{RESET}")
        sys.exit(1)

def print_response(action, response):
    """Format and print API response"""
    print(f"{BLUE}[{action}]{RESET}")
    try:
        if response.status_code in [200, 201]:
            print(f"{GREEN}Status: {response.status_code}{RESET}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            return response.json()
        else:
            print(f"{RED}Status: {response.status_code}{RESET}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"{RED}Error parsing response: {e}{RESET}")
        print(f"Raw response: {response.text}")
        return None

def main():
    print(f"{YELLOW}=== Starting Billing API Tests ==={RESET}")
    
    # Get admin token
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Create multiple billing details for testing filtering and pagination
    billing_ids = []
    
    # Create first billing detail (GST applicable, individual)
    billing_data_1 = {
        "party_legal_name": "Test Company A",
        "is_gst_applicable": True,
        "is_individual": True,
        "is_msme": False,
        "address_line_1": "123 Test Street",
        "city": "Test City",
        "state": "Test State",
        "postal_code": "123456",
        "country": "India",
        "pan_card": "ABCDE1234F",
        "gstin": "22ABCDE1234F1Z5",
        "bank_accounts": [
            {
                "account_number": "1234567890",
                "ifsc_code": "TEST0001",
                "account_holder_name": "Test User",
                "bank_name": "Test Bank",
                "is_default": True
            }
        ]
    }
    
    response = requests.post(f"{BILLING_URL}/", headers=headers, json=billing_data_1)
    result = print_response("Create Billing Detail 1", response)
    if result:
        billing_ids.append(result["_id"])
    
    # Create second billing detail (Not GST applicable, not individual)
    billing_data_2 = {
        "party_legal_name": "Test Corporation B",
        "is_gst_applicable": False,
        "is_individual": False,
        "is_msme": True,
        "address_line_1": "456 Corp Avenue",
        "city": "Business City",
        "state": "Business State",
        "postal_code": "654321",
        "country": "India",
        "pan_card": "FGHIJ5678K",
        "bank_accounts": [
            {
                "account_number": "0987654321",
                "ifsc_code": "TEST0002",
                "account_holder_name": "Test Corp",
                "bank_name": "Corp Bank",
                "is_default": True
            }
        ]
    }
    
    response = requests.post(f"{BILLING_URL}/", headers=headers, json=billing_data_2)
    result = print_response("Create Billing Detail 2", response)
    if result:
        billing_ids.append(result["_id"])
    
    # Allow time for data to be processed
    time.sleep(1)
    
    # Test 1: Get all billing details with pagination
    print(f"\n{YELLOW}=== Testing Pagination ==={RESET}")
    response = requests.get(f"{BILLING_URL}/?skip=0&limit=5", headers=headers)
    print_response("Get All Billing Details (Paginated)", response)
    
    # Test 2: Filter by is_gst_applicable
    print(f"\n{YELLOW}=== Testing Filtering ==={RESET}")
    response = requests.get(f"{BILLING_URL}/?is_gst_applicable=true", headers=headers)
    print_response("Filter Billing Details (GST Applicable)", response)
    
    # Test 3: Filter by is_individual
    response = requests.get(f"{BILLING_URL}/?is_individual=false", headers=headers)
    print_response("Filter Billing Details (Not Individual)", response)
    
    # Test 4: Filter by is_msme
    response = requests.get(f"{BILLING_URL}/?is_msme=true", headers=headers)
    print_response("Filter Billing Details (MSME)", response)
    
    # Test 5: Search by party_legal_name
    print(f"\n{YELLOW}=== Testing Search ==={RESET}")
    response = requests.get(f"{BILLING_URL}/?search=Corporation", headers=headers)
    print_response("Search Billing Details (Corporation)", response)
    
    # Test 6: Search by PAN
    response = requests.get(f"{BILLING_URL}/?search=FGHIJ", headers=headers)
    print_response("Search Billing Details (PAN)", response)
    
    # Test 7: Multiple filters combined
    print(f"\n{YELLOW}=== Testing Combined Filters ==={RESET}")
    response = requests.get(f"{BILLING_URL}/?is_individual=false&is_msme=true", headers=headers)
    print_response("Combined Filters (Not Individual & MSME)", response)
    
    # Test 8: Sorting
    print(f"\n{YELLOW}=== Testing Sorting ==={RESET}")
    response = requests.get(f"{BILLING_URL}/?sort_by=party_legal_name&sort_order=1", headers=headers)
    print_response("Sort by Party Name (Ascending)", response)
    
    # Clean up: Delete created billing details
    print(f"\n{YELLOW}=== Cleaning Up ==={RESET}")
    for billing_id in billing_ids:
        response = requests.delete(f"{BILLING_URL}/{billing_id}", headers=headers)
        print_response(f"Delete Billing Detail {billing_id}", response)
    
    print(f"\n{GREEN}=== Billing API Tests Completed ==={RESET}")

if __name__ == "__main__":
    main() 