#!/bin/bash
echo "Setting up Authentication API..."

# Create virtual environment
echo "Creating virtual environment..."
python -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install wheel
pip install -r requirements.txt

# Ensure bson is installed
echo "Ensuring bson module is installed..."
pip install pymongo[srv]

# Set up environment variables
echo "Setting up environment variables..."
if [ ! -f .env ]; then
  echo "Creating .env file..."
  cat > .env << EOL
MONGODB_URL=mongodb://root:ccx39U5GKAHryuzVRK8U28En9cDhxUXAmwFUBoNh4riGq1ySu0iKw4uqd2bOMW1s@147.93.103.9:6677/?directConnection=true
SECRET_KEY=09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=adminpassword
EOL
fi

echo "Setup completed successfully!"
echo "Run the API with: python run.py" 