"""
Test script for the Profile API endpoints with filtering and pagination support.
"""
import requests
import json
import time
import sys
import random

# Base URLs
BASE_URL = "http://localhost:5002/api"
AUTH_URL = f"{BASE_URL}/auth"
BILLING_URL = f"{BASE_URL}/billing"
PROFILES_URL = f"{BASE_URL}/profiles"

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

def create_billing_detail(headers):
    """Create a billing detail and return its ID"""
    billing_data = {
        "party_legal_name": f"Profile Test Company {random.randint(1000, 9999)}",
        "is_gst_applicable": True,
        "is_individual": True,
        "address_line_1": "123 Test Street",
        "city": "Test City",
        "state": "Test State",
        "postal_code": "123456",
        "country": "India",
        "pan_card": f"ABCDE{random.randint(1000, 9999)}F",
        "gstin": f"22ABCDE{random.randint(1000, 9999)}F1Z5",
        "bank_accounts": [
            {
                "account_number": f"{random.randint(10000000, 99999999)}",
                "ifsc_code": "TEST0001",
                "account_holder_name": "Test User",
                "bank_name": "Test Bank",
                "is_default": True
            }
        ]
    }
    
    response = requests.post(f"{BILLING_URL}/", headers=headers, json=billing_data)
    result = print_response("Create Billing Detail", response)
    if result:
        return result["_id"]
    return None

def main():
    print(f"{YELLOW}=== Starting Profile API Tests ==={RESET}")
    
    # Get admin token
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Create a billing detail first (required for profile)
    billing_id = create_billing_detail(headers)
    if not billing_id:
        print(f"{RED}Failed to create billing detail, cannot proceed with profile tests{RESET}")
        sys.exit(1)
    
    # Create multiple profiles for testing filtering and pagination
    profile_ids = []
    platforms = ["YouTube", "Instagram", "TikTok", "Twitter"]
    
    print(f"\n{YELLOW}=== Creating Test Profiles ==={RESET}")
    for i in range(4):
        followers = random.randint(1000, 100000)
        engagement_rate = round(random.uniform(1.0, 10.0), 2)
        
        profile_data = {
            "platform": platforms[i],
            "username": f"testuser_{platforms[i].lower()}_{random.randint(100, 999)}",
            "followers": followers,
            "engagement_rate": engagement_rate,
            "currency": "INR",
            "content_categories": ["Tech", "Lifestyle"] if i % 2 == 0 else ["Fashion", "Travel"],
            "billing_details_id": billing_id,
            "contact_details": {
                "email": f"profile{i+1}@example.com",
                "phone": f"+91987654{random.randint(1000, 9999)}"
            },
            "costing_details": {
                "base_rate": round(followers * 0.01, 2),
                "pricing_model": "CPM" if i % 2 == 0 else "Fixed"
            }
        }
        
        response = requests.post(f"{PROFILES_URL}/", headers=headers, json=profile_data)
        result = print_response(f"Create Profile {i+1} - {platforms[i]}", response)
        if result:
            profile_ids.append(result["_id"])
    
    # Allow time for data to be processed
    time.sleep(1)
    
    # Test 1: Get all profiles with pagination
    print(f"\n{YELLOW}=== Testing Pagination ==={RESET}")
    response = requests.get(f"{PROFILES_URL}/?skip=0&limit=2", headers=headers)
    print_response("Get All Profiles (Paginated - First Page)", response)
    
    response = requests.get(f"{PROFILES_URL}/?skip=2&limit=2", headers=headers)
    print_response("Get All Profiles (Paginated - Second Page)", response)
    
    # Test 2: Filter by platform
    print(f"\n{YELLOW}=== Testing Platform Filtering ==={RESET}")
    response = requests.get(f"{PROFILES_URL}/?platform=YouTube", headers=headers)
    print_response("Filter Profiles (Platform: YouTube)", response)
    
    response = requests.get(f"{PROFILES_URL}/?platform=Instagram", headers=headers)
    print_response("Filter Profiles (Platform: Instagram)", response)
    
    # Test 3: Filter by followers range
    print(f"\n{YELLOW}=== Testing Followers Range Filtering ==={RESET}")
    response = requests.get(f"{PROFILES_URL}/?min_followers=50000", headers=headers)
    print_response("Filter Profiles (Min Followers: 50000)", response)
    
    response = requests.get(f"{PROFILES_URL}/?max_followers=50000", headers=headers)
    print_response("Filter Profiles (Max Followers: 50000)", response)
    
    # Test 4: Filter by engagement rate
    print(f"\n{YELLOW}=== Testing Engagement Rate Filtering ==={RESET}")
    response = requests.get(f"{PROFILES_URL}/?min_engagement_rate=5.0", headers=headers)
    print_response("Filter Profiles (Min Engagement Rate: 5.0)", response)
    
    # Test 5: Search by username
    print(f"\n{YELLOW}=== Testing Search ==={RESET}")
    # Extract a substring from one of the created usernames to search for
    if profile_ids:
        response = requests.get(f"{PROFILES_URL}/{profile_ids[0]}", headers=headers)
        profile = response.json()
        search_term = profile["username"][5:10] if len(profile["username"]) > 10 else profile["username"]
        
        response = requests.get(f"{PROFILES_URL}/?search={search_term}", headers=headers)
        print_response(f"Search Profiles (Username containing: {search_term})", response)
    
    # Test 6: Multiple filters combined
    print(f"\n{YELLOW}=== Testing Combined Filters ==={RESET}")
    response = requests.get(f"{PROFILES_URL}/?platform=Instagram&min_followers=10000", headers=headers)
    print_response("Combined Filters (Platform: Instagram & Min Followers: 10000)", response)
    
    # Test 7: Sorting
    print(f"\n{YELLOW}=== Testing Sorting ==={RESET}")
    response = requests.get(f"{PROFILES_URL}/?sort_by=followers&sort_order=-1", headers=headers)
    print_response("Sort by Followers (Descending)", response)
    
    # Clean up: Delete created profiles
    print(f"\n{YELLOW}=== Cleaning Up Profiles ==={RESET}")
    for profile_id in profile_ids:
        response = requests.delete(f"{PROFILES_URL}/{profile_id}", headers=headers)
        print_response(f"Delete Profile {profile_id}", response)
    
    # Clean up: Delete billing detail
    print(f"\n{YELLOW}=== Cleaning Up Billing Detail ==={RESET}")
    response = requests.delete(f"{BILLING_URL}/{billing_id}", headers=headers)
    print_response(f"Delete Billing Detail {billing_id}", response)
    
    print(f"\n{GREEN}=== Profile API Tests Completed ==={RESET}")

if __name__ == "__main__":
    main() 