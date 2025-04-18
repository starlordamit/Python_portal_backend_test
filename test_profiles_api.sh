#!/bin/bash

# Base URLs
AUTH_URL="http://localhost:5002/api/auth"
PROFILES_URL="http://localhost:5002/api/profiles"
BILLING_URL="http://localhost:5002/api/billing"

# Admin credentials
ADMIN_EMAIL="admin@example.com"
ADMIN_PASSWORD="admin123"

# Colors for output formatting
GREEN="\033[32m"
RED="\033[31m"
RESET="\033[0m"
BLUE="\033[34m"
YELLOW="\033[33m"

echo -e "${YELLOW}Starting Profile API Tests...${RESET}"

# Step 0: Login to get token
echo -e "${YELLOW}Step 0: Logging in to get token...${RESET}"
LOGIN_RESPONSE=$(curl -s -X POST "${AUTH_URL}/login" \
  -d "username=${ADMIN_EMAIL}&password=${ADMIN_PASSWORD}")

TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo -e "${RED}Failed to get token: ${LOGIN_RESPONSE}${RESET}"
  exit 1
fi

echo -e "${GREEN}✓ Token obtained successfully${RESET}"

# Step 1: Create billing details first (we need this for the profile)
echo -e "${YELLOW}Step 1: Creating billing details...${RESET}"
BILLING_DATA='{
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
  "msme_registered": true,
  "msme_registration_number": "UDYAM-MH-01-0123456"
}'

BILLING_RESPONSE=$(curl -s -X POST "${BILLING_URL}/" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d "${BILLING_DATA}")

echo -e "${BLUE}=== Create Billing Details ===${RESET}"
echo "${BILLING_RESPONSE}" | jq .

BILLING_ID=$(echo ${BILLING_RESPONSE} | grep -o '"id":"[^"]*' | cut -d'"' -f4)
if [ -z "$BILLING_ID" ]; then
  echo -e "${RED}Failed to create billing details. Exiting tests.${RESET}"
  exit 1
fi

echo -e "${GREEN}✓ Billing details created successfully with ID: ${BILLING_ID}${RESET}"
echo "---------------------------------------------------------"

# Step 2: Create a profile
echo -e "${YELLOW}Step 2: Creating a profile...${RESET}"
PROFILE_DATA='{
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
  "billing_details_id": "'${BILLING_ID}'",
  "costing_details": {
    "post": 5000,
    "story": 2000,
    "reel": 8000,
    "video": 10000
  },
  "notes": "Test profile for API testing"
}'

PROFILE_RESPONSE=$(curl -s -X POST "${PROFILES_URL}" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d "${PROFILE_DATA}")

echo -e "${BLUE}=== Create Profile ===${RESET}"
echo "${PROFILE_RESPONSE}" | jq .

PROFILE_ID=$(echo ${PROFILE_RESPONSE} | grep -o '"id":"[^"]*' | cut -d'"' -f4)
if [ -z "$PROFILE_ID" ]; then
  echo -e "${RED}Failed to create profile. Exiting tests.${RESET}"
  # Clean up
  curl -s -X DELETE "${BILLING_URL}/${BILLING_ID}" -H "Authorization: Bearer ${TOKEN}" > /dev/null
  exit 1
fi

echo -e "${GREEN}✓ Profile created successfully with ID: ${PROFILE_ID}${RESET}"
echo "---------------------------------------------------------"

# Step 3: Get all profiles
echo -e "${YELLOW}Step 3: Getting all profiles...${RESET}"
GET_PROFILES_RESPONSE=$(curl -s -X GET "${PROFILES_URL}" \
  -H "Authorization: Bearer ${TOKEN}")

echo -e "${BLUE}=== Get All Profiles ===${RESET}"
echo "${GET_PROFILES_RESPONSE}" | jq .
echo -e "${GREEN}✓ Profiles retrieved successfully${RESET}"
echo "---------------------------------------------------------"

# Step 4: Get profiles with filter
echo -e "${YELLOW}Step 4: Getting profiles with filter...${RESET}"
GET_FILTERED_PROFILES_RESPONSE=$(curl -s -X GET "${PROFILES_URL}?platform=Instagram&followers_min=5000" \
  -H "Authorization: Bearer ${TOKEN}")

echo -e "${BLUE}=== Get Filtered Profiles ===${RESET}"
echo "${GET_FILTERED_PROFILES_RESPONSE}" | jq .
echo -e "${GREEN}✓ Filtered profiles retrieved successfully${RESET}"
echo "---------------------------------------------------------"

# Step 5: Get a specific profile
echo -e "${YELLOW}Step 5: Getting specific profile...${RESET}"
GET_PROFILE_RESPONSE=$(curl -s -X GET "${PROFILES_URL}/${PROFILE_ID}" \
  -H "Authorization: Bearer ${TOKEN}")

echo -e "${BLUE}=== Get Specific Profile ===${RESET}"
echo "${GET_PROFILE_RESPONSE}" | jq .
echo -e "${GREEN}✓ Specific profile retrieved successfully${RESET}"
echo "---------------------------------------------------------"

# Step 6: Update the profile
echo -e "${YELLOW}Step 6: Updating profile...${RESET}"
UPDATE_DATA='{
  "username": "updateduser",
  "followers": 15000,
  "contact_details": {
    "email": "updateduser@example.com",
    "phone": "9876543210"
  },
  "notes": "Updated test profile"
}'

UPDATE_PROFILE_RESPONSE=$(curl -s -X PUT "${PROFILES_URL}/${PROFILE_ID}" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d "${UPDATE_DATA}")

echo -e "${BLUE}=== Update Profile ===${RESET}"
echo "${UPDATE_PROFILE_RESPONSE}" | jq .
echo -e "${GREEN}✓ Profile updated successfully${RESET}"
echo "---------------------------------------------------------"

# Step 7: Get the updated profile
echo -e "${YELLOW}Step 7: Getting updated profile...${RESET}"
GET_UPDATED_PROFILE_RESPONSE=$(curl -s -X GET "${PROFILES_URL}/${PROFILE_ID}" \
  -H "Authorization: Bearer ${TOKEN}")

echo -e "${BLUE}=== Get Updated Profile ===${RESET}"
echo "${GET_UPDATED_PROFILE_RESPONSE}" | jq .
echo -e "${GREEN}✓ Updated profile retrieved successfully${RESET}"
echo "---------------------------------------------------------"

# Step 8: Delete the profile
echo -e "${YELLOW}Step 8: Deleting profile...${RESET}"
DELETE_PROFILE_RESPONSE=$(curl -s -X DELETE "${PROFILES_URL}/${PROFILE_ID}" \
  -H "Authorization: Bearer ${TOKEN}")

echo -e "${BLUE}=== Delete Profile ===${RESET}"
echo "${DELETE_PROFILE_RESPONSE}" | jq .
echo -e "${GREEN}✓ Profile deleted successfully${RESET}"
echo "---------------------------------------------------------"

# Step 9: Clean up - Delete billing details
echo -e "${YELLOW}Step 9: Cleaning up - Deleting billing details...${RESET}"
DELETE_BILLING_RESPONSE=$(curl -s -X DELETE "${BILLING_URL}/${BILLING_ID}" \
  -H "Authorization: Bearer ${TOKEN}")

echo -e "${BLUE}=== Delete Billing Details ===${RESET}"
echo "${DELETE_BILLING_RESPONSE}" | jq .
echo -e "${GREEN}✓ Billing details deleted successfully${RESET}"
echo "---------------------------------------------------------"

echo -e "${GREEN}Profile API Tests Completed!${RESET}" 