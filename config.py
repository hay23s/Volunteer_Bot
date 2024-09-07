from typing import Final
import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Load the .env file to access environment variables
load_dotenv()

# Retrieve MongoDB credentials and connection details
MONGO_USER: Final[str] = os.getenv('MONGODB_USER')
MONGO_PASSWORD: Final[str] = os.getenv('MONGODB_PASSWORD')
MONGO_DATABASE: Final[str] = os.getenv('MONGODB_DATABASE')
MONGO_HOST: Final[str] = os.getenv('MONGODB_HOST')

MONGO_URI = f"mongodb+srv://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}/{MONGO_DATABASE}?retryWrites=true&w=majority"

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client[MONGO_DATABASE]

def check_connection():
    try:
        # The ping command is cheap and does not require auth.
        client.admin.command('ping')
        print("MongoDB connection is successful.")
    except Exception as e:
        print(f"MongoDB connection error: {e}")