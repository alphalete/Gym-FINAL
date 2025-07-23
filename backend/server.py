from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, date
from email_service import EmailService

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Initialize email service
email_service = EmailService()

# Create the main app without a prefix
app = FastAPI(title="Alphalete Athletics Club API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Define Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

class Client(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: EmailStr
    phone: Optional[str] = None
    membership_type: str = "Standard"
    monthly_fee: float
    next_payment_date: date
    status: str = "Active"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ClientCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    membership_type: str = "Standard"
    monthly_fee: float
    next_payment_date: date

class ClientUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    membership_type: Optional[str] = None
    monthly_fee: Optional[float] = None
    next_payment_date: Optional[date] = None
    status: Optional[str] = None

class PaymentReminderRequest(BaseModel):
    client_id: str
    custom_amount: Optional[float] = None
    custom_due_date: Optional[str] = None

class EmailResponse(BaseModel):
    success: bool
    message: str
    client_email: str

# Existing routes
@api_router.get("/")
async def root():
    return {"message": "Alphalete Athletics Club API - Ready to Rock!"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# Client Management Routes
@api_router.post("/clients", response_model=Client)
async def create_client(client_data: ClientCreate):
    """Create a new client"""
    client_dict = client_data.dict()
    client_obj = Client(**client_dict)
    
    # Check if client with this email already exists
    existing_client = await db.clients.find_one({"email": client_obj.email})
    if existing_client:
        raise HTTPException(status_code=400, detail="Client with this email already exists")
    
    await db.clients.insert_one(client_obj.dict())
    return client_obj

@api_router.get("/clients", response_model=List[Client])
async def get_clients():
    """Get all clients"""
    clients = await db.clients.find().to_list(1000)
    return [Client(**client) for client in clients]

@api_router.get("/clients/{client_id}", response_model=Client)
async def get_client(client_id: str):
    """Get a specific client"""
    client = await db.clients.find_one({"id": client_id})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return Client(**client)

@api_router.put("/clients/{client_id}", response_model=Client)
async def update_client(client_id: str, client_update: ClientUpdate):
    """Update client information"""
    client = await db.clients.find_one({"id": client_id})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Update fields
    update_data = {k: v for k, v in client_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    await db.clients.update_one({"id": client_id}, {"$set": update_data})
    
    # Return updated client
    updated_client = await db.clients.find_one({"id": client_id})
    return Client(**updated_client)

@api_router.delete("/clients/{client_id}")
async def delete_client(client_id: str):
    """Delete a client"""
    result = await db.clients.delete_one({"id": client_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Client not found")
    return {"message": "Client deleted successfully"}

# Email Routes
@api_router.post("/email/test")
async def test_email():
    """Test email configuration"""
    success = email_service.test_email_connection()
    return {
        "success": success,
        "message": "Email configuration is working!" if success else "Email configuration failed!"
    }

@api_router.post("/email/payment-reminder", response_model=EmailResponse)
async def send_payment_reminder(reminder_request: PaymentReminderRequest):
    """Send payment reminder to a specific client"""
    # Get client details
    client = await db.clients.find_one({"id": reminder_request.client_id})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    client_obj = Client(**client)
    
    # Use custom amount or client's monthly fee
    amount = reminder_request.custom_amount or client_obj.monthly_fee
    
    # Use custom due date or client's next payment date
    due_date = reminder_request.custom_due_date or client_obj.next_payment_date.strftime("%B %d, %Y")
    
    # Send email
    success = email_service.send_payment_reminder(
        client_email=client_obj.email,
        client_name=client_obj.name,
        amount=amount,
        due_date=due_date
    )
    
    return EmailResponse(
        success=success,
        message="Payment reminder sent successfully!" if success else "Failed to send payment reminder",
        client_email=client_obj.email
    )

@api_router.post("/email/payment-reminder/bulk")
async def send_bulk_payment_reminders():
    """Send payment reminders to all active clients with upcoming payments"""
    clients = await db.clients.find({"status": "Active"}).to_list(1000)
    
    sent_count = 0
    failed_count = 0
    results = []
    
    for client_data in clients:
        client_obj = Client(**client_data)
        
        success = email_service.send_payment_reminder(
            client_email=client_obj.email,
            client_name=client_obj.name,
            amount=client_obj.monthly_fee,
            due_date=client_obj.next_payment_date.strftime("%B %d, %Y")
        )
        
        if success:
            sent_count += 1
        else:
            failed_count += 1
            
        results.append({
            "client_name": client_obj.name,
            "client_email": client_obj.email,
            "success": success
        })
    
    return {
        "total_clients": len(clients),
        "sent_successfully": sent_count,
        "failed": failed_count,
        "results": results
    }

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
    client.close()