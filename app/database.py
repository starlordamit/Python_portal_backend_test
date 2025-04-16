import os
from dotenv import load_dotenv
from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure

# Load environment variables
load_dotenv()

# MongoDB connection string
MONGODB_URL = os.getenv("MONGODB_URL")

# Create MongoDB client
try:
    client = MongoClient(MONGODB_URL)
    # Check connection by pinging the server
    client.admin.command('ping')
    print("Connected to MongoDB successfully!")
except ConnectionFailure:
    print("Failed to connect to MongoDB")
    raise

# Get database and collections
db = client.get_database("auth_db")
users_collection = db.users
profiles_collection = db.profiles
billing_details_collection = db.billing_details
brands_collection = db.brands

# Create indexes for better performance
try:
    # Create an index on email field for faster lookups
    users_collection.create_index([("email", ASCENDING)], unique=True)
    print("Created index on email field")
    
    # Create indexes for profiles collection
    profiles_collection.create_index([("created_by", ASCENDING)])
    profiles_collection.create_index([("platform", ASCENDING)])
    profiles_collection.create_index([("username", ASCENDING)])
    profiles_collection.create_index([("region", ASCENDING)])
    profiles_collection.create_index([("language", ASCENDING)])
    profiles_collection.create_index([("followers", ASCENDING)])
    profiles_collection.create_index([("content_orientation", ASCENDING)])
    profiles_collection.create_index([("billing_details_id", ASCENDING)])
    print("Created indexes for profiles collection")
    
    # Create indexes for billing details collection
    billing_details_collection.create_index([("created_by", ASCENDING)])
    billing_details_collection.create_index([("party_legal_name", ASCENDING)])
    billing_details_collection.create_index([("gstin", ASCENDING)])
    billing_details_collection.create_index([("pan_card", ASCENDING)])
    print("Created indexes for billing details collection")
    
    # Create indexes for brands collection
    brands_collection.create_index([("created_by", ASCENDING)])
    brands_collection.create_index([("name", ASCENDING)])
    brands_collection.create_index([("billing_details_id", ASCENDING)])
    print("Created indexes for brands collection")
except Exception as e:
    print(f"Index creation error: {e}") 