from fastapi import FastAPI, APIRouter, HTTPException
from starlette.middleware.cors import CORSMiddleware
import logging
from pydantic import BaseModel, Field
from typing import List
import uuid
from datetime import datetime

# Create the main app
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

# In-memory storage
status_checks_store = []
gym_members_store = []

# Initial system setup with empty database
# Use the frontend interface to add your first gym members

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Alphalete Athletics Club API", "status": "running", "mode": "production"}

@api_router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "mode": "production",
        "timestamp": datetime.utcnow().isoformat(),
        "members_count": len(gym_members_store)
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
    member_dict = member.dict()
    member_dict["id"] = str(uuid.uuid4())
    gym_members_store.append(member_dict)
    return GymMember(**member_dict)

@api_router.put("/members/{member_id}", response_model=GymMember)
async def update_gym_member(member_id: str, member: GymMember):
    for i, existing_member in enumerate(gym_members_store):
        if existing_member["id"] == member_id:
            member_dict = member.dict()
            member_dict["id"] = member_id
            gym_members_store[i] = member_dict
            return GymMember(**member_dict)
    raise HTTPException(status_code=404, detail="Member not found")

@api_router.delete("/members/{member_id}")
async def delete_gym_member(member_id: str):
    for i, existing_member in enumerate(gym_members_store):
        if existing_member["id"] == member_id:
            gym_members_store.pop(i)
            return {"message": "Member deleted successfully"}
    raise HTTPException(status_code=404, detail="Member not found")

@api_router.get("/dashboard-stats")
async def get_dashboard_stats():
    total_members = len(gym_members_store)
    active_members = len([m for m in gym_members_store if m["status"] == "Active"])
    overdue_members = len([m for m in gym_members_store if m["status"] == "Overdue"])
    total_revenue = sum(m["amount"] for m in gym_members_store)
    
    return {
        "total_members": total_members,
        "active_members": active_members,
        "overdue_members": overdue_members,
        "total_revenue": total_revenue
    }

# Include the router in the main app
app.include_router(api_router)

# Add CORS middleware
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
    logger.info("🏋️ Alphalete Athletics Club API starting up...")
    logger.info(f"📊 Loaded {len(gym_members_store)} gym members")
    logger.info("🚀 Running in production mode with in-memory storage")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
