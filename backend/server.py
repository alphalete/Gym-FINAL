from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Create the main app without a prefix
app = FastAPI(title="Alphalete Athletics API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Initialize MongoDB connection as optional
mongo_client = None
db = None

# Try to connect to MongoDB, but don't fail if it's not available
try:
    from motor.motor_asyncio import AsyncIOMotorClient
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'alphalete_athletics')
    
    if mongo_url and mongo_url != 'mongodb://localhost:27017':
        mongo_client = AsyncIOMotorClient(mongo_url)
        db = mongo_client[db_name]
        logging.info("Connected to MongoDB successfully")
    else:
        logging.info("MongoDB connection skipped - using mock data mode")
except Exception as e:
    logging.warning(f"MongoDB connection failed: {e}. Running in mock mode.")
    mongo_client = None
    db = None

# Define Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

class GymMember(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    phone: str
    membership_type: str
    join_date: str
    last_payment: str
    next_due: str
    status: str
    amount: float
    overdue: int = 0

# Mock data for when database is not available
mock_status_checks = []
mock_gym_members = [
    {
        "id": "1",
        "name": "John Smith",
        "email": "john.smith@email.com",
        "phone": "(555) 123-4567",
        "membership_type": "Monthly",
        "join_date": "2024-01-15",
        "last_payment": "2025-01-01",
        "next_due": "2025-02-01",
        "status": "Active",
        "amount": 59.0,
        "overdue": 0
    },
    {
        "id": "2",
        "name": "Sarah Johnson",
        "email": "sarah.j@email.com",
        "phone": "(555) 234-5678",
        "membership_type": "Student",
        "join_date": "2024-03-10",
        "last_payment": "2024-12-15",
        "next_due": "2025-01-15",
        "status": "Overdue",
        "amount": 29.0,
        "overdue": 5
    }
]

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Alphalete Athletics Club API", "status": "running", "database": "connected" if db else "mock_mode"}

@api_router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database_connected": db is not None,
        "timestamp": datetime.utcnow().isoformat()
    }

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    
    if db:
        try:
            await db.status_checks.insert_one(status_obj.dict())
        except Exception as e:
            logging.error(f"Database insert failed: {e}")
            # Fall back to mock storage
            mock_status_checks.append(status_obj.dict())
    else:
        # Use mock storage
        mock_status_checks.append(status_obj.dict())
    
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    if db:
        try:
            status_checks = await db.status_checks.find().to_list(1000)
            return [StatusCheck(**status_check) for status_check in status_checks]
        except Exception as e:
            logging.error(f"Database query failed: {e}")
            # Fall back to mock data
            return [StatusCheck(**check) for check in mock_status_checks]
    else:
        # Use mock data
        return [StatusCheck(**check) for check in mock_status_checks]

@api_router.get("/members", response_model=List[GymMember])
async def get_gym_members():
    if db:
        try:
            members = await db.gym_members.find().to_list(1000)
            return [GymMember(**member) for member in members]
        except Exception as e:
            logging.error(f"Database query failed: {e}")
            # Fall back to mock data
            return [GymMember(**member) for member in mock_gym_members]
    else:
        # Use mock data
        return [GymMember(**member) for member in mock_gym_members]

@api_router.post("/members", response_model=GymMember)
async def create_gym_member(member: GymMember):
    if db:
        try:
            await db.gym_members.insert_one(member.dict())
        except Exception as e:
            logging.error(f"Database insert failed: {e}")
            # Fall back to mock storage
            mock_gym_members.append(member.dict())
    else:
        # Use mock storage
        mock_gym_members.append(member.dict())
    
    return member

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    if mongo_client:
        mongo_client.close()
