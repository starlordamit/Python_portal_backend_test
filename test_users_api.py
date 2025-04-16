import requests
import json
import time
import os

# --- Configuration ---
BASE_URL = "http://localhost:5002/api"
AUTH_URL = f"{BASE_URL}/auth"
# **ASSUMPTION**: User routes are mounted under /api/users
# If tests fail with 404, these routes might not be registered in app/main.py
USERS_URL = f"{BASE_URL}/users"

# Admin credentials (ensure these match your setup or .env)
admin_credentials = {
    "email": os.getenv("ADMIN_EMAIL", "admin@example.com"),
    "password": os.getenv("ADMIN_PASSWORD", "12345678")
}

# --- Helper Functions (Reused from test_auth_api.py) ---

def get_token(email, password):
    """Logs in a user and returns the access token."""
    print(f"\nAttempting login for: {email}")
    credentials = {"email": email, "password": password}
    try:
        response = requests.post(
            f"{AUTH_URL}/login",
            json=credentials,
            timeout=10
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
        print(f"Response Body:\n{json.dumps(response.json(), indent=2)}")
    except json.JSONDecodeError:
        print(f"Response Body (non-JSON):\n{response.text}")
    print("-" * (len(endpoint_name) + 12))
    return response.status_code < 400

# --- Main Test Execution ---

if __name__ == "__main__":
    print("=== Starting Users API Tests ===")
    created_user_id = None
    # Generate unique details for the test user each time
    timestamp = int(time.time())
    test_user_email = f"usertest_{timestamp}@example.com"
    test_user_password = "password123"
    test_user_full_name = f"User Test {timestamp}"
    updated_full_name = f"User Test Updated {timestamp}"

    # 1. Get Admin Token (Required for most user operations)
    print("\n--- Test 1: Get Admin Token ---")
    admin_token = get_token(admin_credentials["email"], admin_credentials["password"])
    if not admin_token:
        print("CRITICAL: Admin login failed. Cannot proceed with Users API tests.")
        exit(1)

    admin_headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }

    # --- Tests Assuming Routes Exist at /api/users ---
    # Note: If these fail with 404, check app/main.py to ensure the router
    # from app/routes.py (containing user endpoints) is included.

    try:
        # 2. Create User (Admin Action)
        # NOTE: Using POST /api/auth/register as the primary create method
        print("\n--- Test 2: Create User via /auth/register ---")
        new_user_data = {
            "email": test_user_email,
            "full_name": test_user_full_name,
            "password": test_user_password,
            "role": "data_operator"
        }
        # Using /register endpoint from auth router as it's confirmed registered
        resp_create = requests.post(f"{AUTH_URL}/register", headers=admin_headers, json=new_user_data)
        if print_response("POST /auth/register", resp_create):
            created_user_id = resp_create.json().get("id")
            if not created_user_id:
                raise Exception("User creation response did not contain ID.")
            print(f"Created user ID: {created_user_id}")
        else:
            raise Exception(f"Failed to create user {test_user_email} via /auth/register.")

        # 3. List Users (Admin Action) - Assuming /api/users exists
        print("\n--- Test 3: List Users (Admin) ---")
        resp_list = requests.get(USERS_URL, headers=admin_headers)
        if print_response("GET /users", resp_list):
            users = resp_list.json()
            found = any(user.get('id') == created_user_id for user in users)
            if not found:
                print(f"WARNING: Created user {created_user_id} not found in user list.")
            else:
                print(f"Found created user {created_user_id} in list.")
        else:
            print("ERROR: Failed to list users. Are /api/users routes registered?")
            # Continue cautiously

        # 4. Get Specific User (Admin Action) - Assuming /api/users/{user_id} exists
        print("\n--- Test 4: Get Specific User (Admin) ---")
        resp_get = requests.get(f"{USERS_URL}/{created_user_id}", headers=admin_headers)
        if print_response(f"GET /users/{created_user_id}", resp_get):
            user_details = resp_get.json()
            if user_details.get("email") != test_user_email:
                print("ERROR: Specific user email mismatch.")
            if user_details.get("full_name") != test_user_full_name:
                 print("ERROR: Specific user full_name mismatch.")
        else:
             print(f"ERROR: Failed to get user {created_user_id}. Are /api/users routes registered?")
             # Continue cautiously

        # 5. Update User (Admin Action) - Assuming PUT /api/users/{user_id} exists
        print("\n--- Test 5: Update User (Admin) ---")
        update_data = {"full_name": updated_full_name, "is_active": True} # Example update
        resp_update = requests.put(f"{USERS_URL}/{created_user_id}", headers=admin_headers, json=update_data)
        if print_response(f"PUT /users/{created_user_id}", resp_update):
             print(f"User {created_user_id} updated.")
             # Verify update
             resp_get_updated = requests.get(f"{USERS_URL}/{created_user_id}", headers=admin_headers)
             if print_response(f"GET /users/{created_user_id} (After Update)", resp_get_updated):
                  if resp_get_updated.json().get("full_name") != updated_full_name:
                       print("ERROR: User full_name was not updated correctly.")
        else:
             print(f"ERROR: Failed to update user {created_user_id}. Are /api/users routes registered?")

        # 6. Delete User (Admin Action) - Assuming DELETE /api/users/{user_id} exists
        print("\n--- Test 6: Delete User (Admin) ---")
        resp_delete = requests.delete(f"{USERS_URL}/{created_user_id}", headers=admin_headers)
        if print_response(f"DELETE /users/{created_user_id}", resp_delete):
            print(f"User {created_user_id} deleted.")
            # Verify deletion
            resp_get_deleted = requests.get(f"{USERS_URL}/{created_user_id}", headers=admin_headers)
            print_response(f"GET /users/{created_user_id} (After Delete)", resp_get_deleted)
            if resp_get_deleted.status_code != 404:
                 print(f"ERROR: User {created_user_id} still found after deletion attempt.")
            else:
                 print(f"User {created_user_id} confirmed deleted (404 received).")
            created_user_id = None # Mark as deleted for cleanup phase
        else:
             print(f"ERROR: Failed to delete user {created_user_id}. Are /api/users routes registered?")


        print("\n\n--- All Assumed User Tests Passed (Check for errors/warnings and 404s) ---")

    except Exception as e:
        print(f"\n\n--- TEST FAILED ---")
        print(f"Error during user testing: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # --- Cleanup ---
        # Attempt to delete the user again if it wasn't confirmed deleted
        print("\n--- Test Cleanup ---")
        if created_user_id and admin_token:
            print(f"Attempting final cleanup delete for user {created_user_id}...")
            # Re-create headers just in case token expired (unlikely in short script)
            final_admin_headers = {
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            }
            resp_final_delete = requests.delete(f"{USERS_URL}/{created_user_id}", headers=final_admin_headers)
            print_response(f"Final Cleanup DELETE /users/{created_user_id}", resp_final_delete)
        elif not created_user_id:
             print("Test user already confirmed deleted or failed creation.")
        else:
             print("Admin token not available for final cleanup.")

    print("\n=== Users API Tests Complete ===") 