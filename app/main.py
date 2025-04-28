import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from datetime import datetime, timedelta

from app.routes.auth import router as auth_router
from app.routes.profiles import router as profiles_router
from app.routes.billing import router as billing_router
from app.routes.brands import router as brands_router
from app.routes.billing_connections import router as billing_connections_router
from app.models import Role
from app.database import users_collection
from app.auth import get_password_hash
from bson import ObjectId

# Create FastAPI app
app = FastAPI(
    title="Python Backend Portal API",
    description="API for managing profiles and user authentication",
    version="1.0.0"
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

# Include auth router
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(profiles_router, prefix="/api", tags=["profiles"])
app.include_router(billing_router, prefix="/api", tags=["billing"])
app.include_router(brands_router, prefix="/api", tags=["brands"])
app.include_router(billing_connections_router, prefix="/api", tags=["billing-connections"])

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Welcome to Python Backend Portal API"}

# Health check endpoint
@app.get("/healthcheck", tags=["health"])
def perform_healthcheck():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Startup event to create admin user if it doesn't exist
@app.on_event("startup")
async def startup_db_client():
    try:
        # Check if admin user exists
        admin_user = users_collection.find_one({"email": "admin@example.com"})
        
        if not admin_user:
            # Create admin user
            admin_user = {
                "email": "admin@example.com",
                "username": "admin",
                "hashed_password": get_password_hash("admin123"),
                "role": Role.ADMIN,
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            users_collection.insert_one(admin_user)
            print("Admin user created successfully!")
    except Exception as e:
        print(f"Error creating admin user: {e}")
        raise

# Run the application
# if __name__ == "__main__":
#     uvicorn.run("app.main:app", host="0.0.0.0", port=5001, reload=True) 
