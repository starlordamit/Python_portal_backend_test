# Python Backend Portal API

## Overview

This project provides a FastAPI-based backend API for managing influencer profiles, brands, and associated billing details within a portal. It features role-based access control (RBAC) to manage permissions for different user types (Admin, Manager, Finance, Data Operator, etc.) and uses JWT for authentication.

## Features

*   **User Authentication:** JWT-based login and registration.
*   **Role-Based Access Control (RBAC):** Different permissions for various user roles.
*   **Profile Management:** CRUD operations for influencer profiles (Instagram, YouTube, etc.).
*   **Brand Management:** CRUD operations for brands.
*   **Billing Details Management:** CRUD operations for billing details, including bank accounts.
*   **Linking:** Functionality to connect/disconnect billing details with profiles and brands.
*   **Filtering & Pagination:** Robust filtering and pagination for retrieving lists of profiles, brands, and billing details.
*   **Verification:** Endpoints for marking GST, PAN, and Bank Accounts as verified (implementation may vary).
*   **MongoDB Integration:** Uses MongoDB as the database via Pymongo.

## Tech Stack

*   **Backend Framework:** FastAPI
*   **Database:** MongoDB
*   **ODM:** Pymongo (implicitly via direct collection usage)
*   **Data Validation:** Pydantic
*   **Authentication:** python-jose (JWT), passlib (hashing)
*   **Environment Variables:** python-dotenv
*   **ASGI Server:** Uvicorn

## Prerequisites

*   Python 3.10+
*   Pip (Python package installer)
*   MongoDB instance (local or cloud-based like MongoDB Atlas)

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd PYTHON\ BACKEND\ PORTAL
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    # Using venv
    python3 -m venv venv
    source venv/bin/activate # On Windows use `venv\Scripts\activate`

    # Or using conda
    # conda create -n portalenv python=3.11
    # conda activate portalenv
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: If `requirements.txt` doesn't exist, you'll need to create one based on the project's imports or install packages manually: `pip install fastapi uvicorn pymongo pydantic python-dotenv python-jose passlib bcrypt email-validator`)*

4.  **Configure Environment Variables:**
    Create a `.env` file in the project root directory (`PYTHON BACKEND PORTAL/`) and add the following variables:
    ```dotenv
    MONGODB_URL=mongodb://localhost:27017/auth_db # Replace with your MongoDB connection string and DB name
    SECRET_KEY=your_strong_secret_key_here # Replace with a strong, random secret key
    ALGORITHM=HS256
    ACCESS_TOKEN_EXPIRE_MINUTES=30
    ```

## Running the Application

To run the FastAPI server:

```bash
python run.py
```

The API will be available at `http://localhost:5002`. Uvicorn will automatically reload the server when code changes are detected.

You can access the interactive API documentation (Swagger UI) at `http://localhost:5002/docs` and the alternative documentation (ReDoc) at `http://localhost:5002/redoc`.

## Running Tests

The project includes bash scripts for testing the API endpoints:

1.  **Make scripts executable:**
    ```bash
    chmod +x test_linking_api.sh
    chmod +x test_billing_api.sh
    # Add others if needed
    ```

2.  **Run the tests:**
    ```bash
    # Tests profile/brand/billing linking
    ./test_linking_api.sh

    # Tests original billing endpoints
    ./test_billing_api.sh

    # Run the Python test script (if preferred)
    # python test_profiles_endpoints.py
    ```
    *(Ensure the server is running before executing the test scripts)*

## API Endpoints

All endpoints require a valid JWT Bearer token in the `Authorization` header unless otherwise specified.

---

### Authentication (`/api/auth`)

*   **POST `/login`**
    *   **Description:** Authenticates a user with email and password.
    *   **Authentication:** None required.
    *   **Request Body:** `{ "email": "user@example.com", "password": "userpassword" }`
    *   **Response (200 OK):** `{ "access_token": "...", "token_type": "bearer" }`
    *   **Errors:** `401 Unauthorized` (Incorrect credentials)

*   **POST `/register`**
    *   **Description:** Registers a new user. By default, assigns the `DATA_OPERATOR` role.
    *   **Authentication:** Requires Admin privileges.
    *   **Permissions:** Admin only.
    *   **Request Body:** `{ "email": "...", "full_name": "...", "password": "...", "role": "data_operator" }` (Role is optional)
    *   **Response (201 Created):** `{ "id": "...", "email": "...", ... }` (New user details)
    *   **Errors:** `400 Bad Request` (User exists), `401`, `403`, `422`

*   **GET `/me`**
    *   **Description:** Retrieves the details of the currently authenticated user.
    *   **Authentication:** Required.
    *   **Response (200 OK):** `{ "id": "...", "email": "...", "role": "...", ... }`

---

### Profiles (`/api/profiles`)

*   **POST `/`**
    *   **Description:** Creates a new influencer profile.
    *   **Authentication:** Required.
    *   **Permissions:** Admin, Manager, Operations Manager, Intern, Data Operator.
    *   **Request Body:** `ProfileCreate` model (platform, username, profile_url, optional fields like followers, region, costing, contact_details, billing_details_id, etc.)
    *   **Response (201 Created):** `{ "message": "Profile created successfully", "id": "..." }`
    *   **Errors:** `400` (Invalid billing ID), `401`, `403`, `404` (Billing details not found), `422`

*   **GET `/`**
    *   **Description:** Retrieves a list of profiles with filtering and pagination. Field visibility depends on user role.
    *   **Authentication:** Required.
    *   **Query Parameters:** `platform`, `content_orientation`, `region`, `language`, `min_followers`, `max_followers`, `search`, `is_betting_allowed`, `skip` (int, default 0), `limit` (int, default 10).
    *   **Response (200 OK):** `List[Union[Profile, ProfilePublic]]`
    *   **Errors:** `401`, `422`

*   **GET `/{profile_id}`**
    *   **Description:** Retrieves a specific profile by its ID. Field visibility depends on user role.
    *   **Authentication:** Required.
    *   **Response (200 OK):** `Union[Profile, ProfilePublic]`
    *   **Errors:** `401`, `404` (Not found or invalid ID), `422`

*   **PUT `/{profile_id}`**
    *   **Description:** Updates an existing profile.
    *   **Authentication:** Required.
    *   **Permissions:** Admin, Manager. Data Operator can update only their own profiles.
    *   **Request Body:** `ProfileUpdate` model (subset of profile fields to update).
    *   **Response (200 OK):** `{ "message": "Profile updated successfully" }`
    *   **Errors:** `401`, `403`, `404` (Not found), `422`

*   **DELETE `/{profile_id}`**
    *   **Description:** Deletes a profile.
    *   **Authentication:** Required.
    *   **Permissions:** Admin only.
    *   **Response (200 OK):** `{ "message": "Profile deleted successfully" }`
    *   **Errors:** `401`, `403`, `404` (Not found), `422`

---

### Billing (`/api/billing`)

*   **POST `/`**
    *   **Description:** Creates new billing details.
    *   **Authentication:** Required.
    *   **Permissions:** Admin, Finance, Manager.
    *   **Request Body:** `BillingDetailsCreate` model (party_legal_name, gst/pan info, address, bank_accounts, etc.)
    *   **Response (201 Created):** `{ "message": "Billing details created successfully", "id": "..." }`
    *   **Errors:** `400` (Invalid GST/PAN logic), `401`, `403`, `422`

*   **GET `/`**
    *   **Description:** Retrieves a list of billing details.
    *   **Authentication:** Required.
    *   **Permissions:** Admin, Finance, Manager.
    *   **Query Parameters:** `skip` (int, default 0), `limit` (int, default 10).
    *   **Response (200 OK):** `List[BillingDetails]`
    *   **Errors:** `401`, `403`, `422`

*   **GET `/{billing_id}`**
    *   **Description:** Retrieves specific billing details by ID.
    *   **Authentication:** Required.
    *   **Permissions:** Admin, Finance, Manager.
    *   **Response (200 OK):** `BillingDetails`
    *   **Errors:** `401`, `403`, `404` (Not found), `422`

*   **PUT `/{billing_id}`**
    *   **Description:** Updates existing billing details.
    *   **Authentication:** Required.
    *   **Permissions:** Admin, Finance.
    *   **Request Body:** `BillingDetailsUpdate` model (subset of fields).
    *   **Response (200 OK):** `{ "message": "Billing details updated successfully" }`
    *   **Errors:** `400` (Invalid GST/PAN logic), `401`, `403`, `404` (Not found), `422`

*   **DELETE `/{billing_id}`**
    *   **Description:** Deletes billing details.
    *   **Authentication:** Required.
    *   **Permissions:** Admin, Finance.
    *   **Response (200 OK):** `{ "message": "Billing details deleted successfully" }`
    *   **Errors:** `401`, `403`, `404` (Not found), `422`

*   **POST `/{billing_id}/bank-accounts`**
    *   **Description:** Adds a bank account to existing billing details.
    *   **Authentication:** Required.
    *   **Permissions:** Admin, Finance.
    *   **Request Body:** `BankAccountCreate` model.
    *   **Response (200 OK):** `{ "message": "Bank account added successfully", "account_id": "..." }`
    *   **Errors:** `401`, `403`, `404` (Billing not found), `422`

*   **PUT `/{billing_id}/bank-accounts/{account_id}`**
    *   **Description:** Updates a specific bank account.
    *   **Authentication:** Required.
    *   **Permissions:** Admin, Finance.
    *   **Request Body:** `BankAccountUpdate` model.
    *   **Response (200 OK):** `{ "message": "Bank account updated successfully" }`
    *   **Errors:** `401`, `403`, `404` (Billing or Account not found), `422`

*   **DELETE `/{billing_id}/bank-accounts/{account_id}`**
    *   **Description:** Deletes a bank account.
    *   **Authentication:** Required.
    *   **Permissions:** Admin, Finance.
    *   **Response (200 OK):** `{ "message": "Bank account deleted successfully" }`
    *   **Errors:** `401`, `403`, `404` (Billing or Account not found), `422`

*   **PATCH `/{billing_id}/bank-accounts/{account_id}/set-default`**
    *   **Description:** Sets a specific bank account as the default for the billing details.
    *   **Authentication:** Required.
    *   **Permissions:** Admin, Finance.
    *   **Response (200 OK):** `{ "message": "Bank account set as default successfully" }`
    *   **Errors:** `401`, `403`, `404` (Billing or Account not found), `422`

*   **(Other PATCH endpoints for verification - GST, PAN, Bank Account - follow similar patterns with Admin/Finance permissions)**

---

### Brands (`/api/brands`)

*   **POST `/`**
    *   **Description:** Creates a new brand.
    *   **Authentication:** Required.
    *   **Permissions:** Admin, Manager.
    *   **Request Body:** `BrandCreate` model (name, company_name, pocs, optional billing_details_id, etc.)
    *   **Response (201 Created):** `{ "message": "Brand created successfully", "id": "..." }`
    *   **Errors:** `400` (Invalid billing ID), `401`, `403`, `404` (Billing details not found), `422`

*   **GET `/`**
    *   **Description:** Retrieves a list of brands with filtering and pagination. Field visibility depends on role.
    *   **Authentication:** Required.
    *   **Query Parameters:** `search`, `skip` (int, default 0), `limit` (int, default 10).
    *   **Response (200 OK):** `List[Union[Brand, BrandPublic]]`
    *   **Errors:** `401`, `422`

*   **GET `/{brand_id}`**
    *   **Description:** Retrieves a specific brand by ID. Field visibility depends on role.
    *   **Authentication:** Required.
    *   **Response (200 OK):** `Union[Brand, BrandPublic]`
    *   **Errors:** `401`, `404` (Not found or invalid ID), `422`

*   **PUT `/{brand_id}`**
    *   **Description:** Updates an existing brand.
    *   **Authentication:** Required.
    *   **Permissions:** Admin, Manager.
    *   **Request Body:** `BrandUpdate` model (subset of fields).
    *   **Response (200 OK):** `{ "message": "Brand updated successfully" }`
    *   **Errors:** `401`, `403`, `404` (Not found), `422`

*   **DELETE `/{brand_id}`**
    *   **Description:** Deletes a brand.
    *   **Authentication:** Required.
    *   **Permissions:** Admin, Manager.
    *   **Response (200 OK):** `{ "message": "Brand deleted successfully" }`
    *   **Errors:** `401`, `403`, `404` (Not found), `422`

*   **(Endpoints for adding/updating/deleting POCs exist within the brand routes and typically require Admin/Manager permissions)**

---

### Billing Connections (`/api/billing-connections`)

*   **GET `/profile-billing/{profile_id}`**
    *   **Description:** Gets the full billing details associated with a specific profile.
    *   **Authentication:** Required.
    *   **Permissions:** Admin, Manager, Intern. Data Operator (only for owned profiles).
    *   **Response (200 OK):** `{ "profile_id": "...", "profile_username": "...", "billing_details": { ... } }`
    *   **Errors:** `401`, `403`, `404` (Profile or Billing not found / not linked)

*   **PATCH `/connect-profile-billing/{profile_id}/{billing_id}`**
    *   **Description:** Links existing billing details to a profile.
    *   **Authentication:** Required.
    *   **Permissions:** Admin, Manager.
    *   **Response (200 OK):** `{ "message": "Successfully connected profile ... with billing details ..." }`
    *   **Errors:** `401`, `403`, `404` (Profile or Billing not found)

*   **PATCH `/disconnect-profile-billing/{profile_id}`**
    *   **Description:** Removes the billing details link from a profile.
    *   **Authentication:** Required.
    *   **Permissions:** Admin, Manager.
    *   **Response (200 OK):** `{ "message": "Successfully disconnected billing details from profile ..." }` or `{ "message": "Profile has no billing details to disconnect" }`
    *   **Errors:** `401`, `403`, `404` (Profile not found)

*   **GET `/brand-billing/{brand_id}`**
    *   **Description:** Gets the full billing details associated with a specific brand.
    *   **Authentication:** Required.
    *   **Permissions:** Admin, Manager, Intern. Data Operator (only for owned brands).
    *   **Response (200 OK):** `{ "brand_id": "...", "brand_name": "...", "billing_details": { ... } }`
    *   **Errors:** `401`, `403`, `404` (Brand or Billing not found / not linked)

*   **PATCH `/connect-brand-billing/{brand_id}/{billing_id}`**
    *   **Description:** Links existing billing details to a brand.
    *   **Authentication:** Required.
    *   **Permissions:** Admin, Manager.
    *   **Response (200 OK):** `{ "message": "Successfully connected brand ... with billing details ..." }`
    *   **Errors:** `401`, `403`, `404` (Brand or Billing not found)

*   **PATCH `/disconnect-brand-billing/{brand_id}`**
    *   **Description:** Removes the billing details link from a brand.
    *   **Authentication:** Required.
    *   **Permissions:** Admin, Manager.
    *   **Response (200 OK):** `{ "message": "Successfully disconnected billing details from brand ..." }` or `{ "message": "Brand has no billing details to disconnect" }`
    *   **Errors:** `401`, `403`, `404` (Brand not found)

*   **GET `/billing-users/{billing_id}`**
    *   **Description:** Finds all profiles and brands currently linked to the specified billing details ID.
    *   **Authentication:** Required.
    *   **Permissions:** Admin, Manager.
    *   **Response (200 OK):** `{ "billing_id": "...", "profiles": [ { "id": "...", "username": "..." }, ... ], "brands": [ { "id": "...", "name": "..." }, ... ], "total_profiles": count, "total_brands": count }`
    *   **Errors:** `401`, `403`, `404` (Billing details not found)

---

## Project Structure (Simplified)

```
PYTHON BACKEND PORTAL/
├── app/
│   ├── __init__.py
│   ├── auth.py         # Authentication logic, helpers
│   ├── database.py     # MongoDB connection, collections, indexes
│   ├── main.py         # FastAPI app creation, middleware, includes routers
│   ├── models/         # Pydantic models (User, Profile, Billing, Brand, Role, etc.)
│   │   ├── __init__.py
│   │   ├── billing.py
│   │   ├── brand.py
│   │   ├── profile.py
│   │   └── user.py
│   ├── routes/         # API route definitions
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── billing.py
│   │   ├── billing_connections.py
│   │   ├── brands.py
│   │   └── profiles.py
│   └── utils/          # Utility functions (e.g., PyObjectId)
│       └── object_id.py
├── .env                # Environment variables (create this file)
├── requirements.txt    # Project dependencies (create if needed)
├── run.py              # Script to run the Uvicorn server
├── test_billing_api.sh # Test script for billing endpoints
└── test_linking_api.sh # Test script for profile/brand/billing linking
```

--- 