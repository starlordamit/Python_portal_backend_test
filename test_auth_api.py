import requests
import json
import time
import os

# --- Configuration ---
BASE_URL = "http://localhost:5002/api"
AUTH_URL = f"{BASE_URL}/auth"

# Admin credentials (ensure these match your setup or .env)
admin_credentials = {
    "email": os.getenv("ADMIN_EMAIL", "admin@example.com"),
    "password": os.getenv("ADMIN_PASSWORD", "12345678")
}

# --- Helper Functions ---

def get_token(email, password):
    """Logs in a user and returns the access token."""
    print(f"\nAttempting login for: {email}")
    credentials = {"email": email, "password": password}
    try:
        response = requests.post(
            f"{AUTH_URL}/login",
            json=credentials,
            timeout=10 # Add timeout
        )
        if response.status_code == 200:
            token = response.json()["access_token"]
            print(f"Login successful for {email}.")
            return token
        else:
            print(f"Failed login for {email}: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Login request failed for {email}: {e}")
        return None

def print_response(endpoint_name, response):
    """Prints formatted response details."""
    print(f"\n--- Test: {endpoint_name} ---")
    print(f"URL: {response.url}")
    print(f"Method: {response.request.method}")
    print(f"Status Code: {response.status_code}")
    try:
        # Attempt to pretty-print JSON, fall back to text if not JSON
        print(f"Response Body:\n{json.dumps(response.json(), indent=2)}")
    except json.JSONDecodeError:
        print(f"Response Body (non-JSON):\n{response.text}")
    print("-" * (len(endpoint_name) + 12)) # Separator line
    return response.status_code < 400 # Return True if successful (status < 400)

# --- Main Test Execution ---

if __name__ == "__main__":
    print("=== Starting Auth API Tests ===")
    test_user_id = None
    test_user_email = f"testuser_{int(time.time())}@example.com"
    test_user_password = "testpassword123"
    test_user_full_name = "Test User One"

    # 1. Test Admin Login
    print("\n--- Test 1: Admin Login ---")
    admin_token = get_token(admin_credentials["email"], admin_credentials["password"])
    if not admin_token:
        print("CRITICAL: Admin login failed. Cannot proceed with admin-required tests.")
        # Optionally exit here if admin login is mandatory for subsequent tests
        # exit(1)
    else:
        admin_headers = {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }

    # 2. Test Failed Logins
    print("\n--- Test 2: Failed Logins ---")
    get_token(admin_credentials["email"], "wrongpassword") # Wrong password
    get_token("nonexistent@example.com", admin_credentials["password"]) # Wrong email

    # 3. Test GET /me for Admin
    if admin_token:
        print("\n--- Test 3: GET /me (Admin) ---")
        resp_me_admin = requests.get(f"{AUTH_URL}/me", headers=admin_headers)
        if print_response("GET /auth/me (Admin)", resp_me_admin):
            if resp_me_admin.json().get("email") != admin_credentials["email"]:
                print("ERROR: /auth/me (Admin) returned incorrect email.")
            if resp_me_admin.json().get("role") != "admin":
                 print("ERROR: /auth/me (Admin) returned incorrect role.")
        else:
            print("ERROR: Failed to get /auth/me for Admin.")

    # 4. Test User Registration (Requires Admin)
    if admin_token:
        print("\n--- Test 4: Register New User (Admin Action) ---")
        new_user_data = {
            "email": test_user_email,
            "full_name": test_user_full_name,
            "password": test_user_password,
            "role": "data_operator" # Example role
        }
        resp_register = requests.post(f"{AUTH_URL}/register", headers=admin_headers, json=new_user_data)
        if print_response("POST /auth/register", resp_register):
            test_user_id = resp_register.json().get("id")
            if not test_user_id:
                print("ERROR: Registration response did not contain user ID.")
            else:
                print(f"Successfully registered user: {test_user_email} with ID: {test_user_id}")
        else:
            print(f"ERROR: Failed to register user {test_user_email}.")
            test_user_id = None # Ensure we don't try to use it later
    else:
        print("\n--- Skipping Test 4: Register New User (Admin token not available) ---")


    # 5. Test Login for New User
    test_user_token = None
    if test_user_id: # Only try if registration seemed successful
        print("\n--- Test 5: Login as New User ---")
        test_user_token = get_token(test_user_email, test_user_password)
        if not test_user_token:
            print(f"ERROR: Failed to log in as newly registered user {test_user_email}.")
    else:
        print("\n--- Skipping Test 5: Login as New User (User not registered) ---")


    # 6. Test GET /me for New User
    if test_user_token:
        print("\n--- Test 6: GET /me (New User) ---")
        test_user_headers = {
            "Authorization": f"Bearer {test_user_token}",
            "Content-Type": "application/json"
        }
        resp_me_new_user = requests.get(f"{AUTH_URL}/me", headers=test_user_headers)
        if print_response("GET /auth/me (New User)", resp_me_new_user):
            if resp_me_new_user.json().get("email") != test_user_email:
                 print("ERROR: /auth/me (New User) returned incorrect email.")
            if resp_me_new_user.json().get("role") != "data_operator":
                 print("ERROR: /auth/me (New User) returned incorrect role.")
        else:
            print("ERROR: Failed to get /auth/me for New User.")
    else:
         print("\n--- Skipping Test 6: GET /me (New User token not available) ---")

    # 7. Cleanup (Deletion) - Currently no endpoint
    print("\n--- Test 7: Cleanup ---")
    if test_user_id:
        print(f"NOTE: Test user '{test_user_email}' (ID: {test_user_id}) was created.")
        print("Recommendation: Implement a DELETE /users/{user_id} endpoint (admin only) for cleanup.")
        # Example (if endpoint existed):
        # if admin_token:
        #     print(f"Attempting to delete test user {test_user_id}...")
        #     resp_delete = requests.delete(f"{BASE_URL}/users/{test_user_id}", headers=admin_headers) # Assuming a /users endpoint
        #     print_response(f"DELETE /users/{test_user_id}", resp_delete)
        # else:
        #     print("Cannot delete test user - admin token not available.")
    else:
        print("No test user to clean up.")


    print("\n=== Auth API Tests Complete ===") 