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

# In-memory storage for demo purposes
status_checks_store = []
gym_members_store = [
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
    },
    {
        "id": "3",
        "name": "Mike Wilson",
        "email": "mike.wilson@email.com",
        "phone": "(555) 345-6789",
        "membership_type": "Custom",
        "join_date": "2024-06-20",
        "last_payment": "2025-01-10",
        "next_due": "2025-02-10",
        "status": "Active",
        "amount": 99.0,
        "overdue": 0
    }
]

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Alphalete Athletics Club API", "status": "running", "mode": "production"}

@api_router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "mode": "production",
        "timestamp": datetime.utcnow().isoformat()
    }

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    status_checks_store.append(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    return [StatusCheck(**check) for check in status_checks_store]

@api_router.get("/members", response_model=List[GymMember])
async def get_gym_members():
    return [GymMember(**member) for member in gym_members_store]

@api_router.post("/members", response_model=GymMember)
async def create_gym_member(member: GymMember):
    gym_members_store.append(member.dict())
    return member

@api_router.put("/members/{member_id}", response_model=GymMember)
async def update_gym_member(member_id: str, member: GymMember):
    for i, existing_member in enumerate(gym_members_store):
        if existing_member["id"] == member_id:
            gym_members_store[i] = member.dict()
            return member
    raise HTTPException(status_code=404, detail="Member not found")

@api_router.delete("/members/{member_id}")
async def delete_gym_member(member_id: str):
    for i, existing_member in enumerate(gym_members_store):
        if existing_member["id"] == member_id:
            gym_members_store.pop(i)
            return {"message": "Member deleted successfully"}
    raise HTTPException(status_code=404, detail="Member not found")

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

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Alphalete Athletics Club API starting up...")
    logger.info("Running in production mode with in-memory storage")

# No MongoDB dependency or cleanup needed
