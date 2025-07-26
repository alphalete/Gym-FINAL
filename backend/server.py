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
from datetime import datetime, date, timedelta
from email_service import EmailService
from reminder_scheduler import initialize_reminder_scheduler, shutdown_reminder_scheduler

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Initialize email service
email_service = EmailService()

# Global reminder scheduler instance
reminder_scheduler = None

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

class MembershipType(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    monthly_fee: float
    description: str
    features: List[str] = []
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class MembershipTypeCreate(BaseModel):
    name: str
    monthly_fee: float
    description: str
    features: List[str] = []
    is_active: bool = True

class MembershipTypeUpdate(BaseModel):
    name: Optional[str] = None
    monthly_fee: Optional[float] = None
    description: Optional[str] = None
    features: Optional[List[str]] = None
    is_active: Optional[bool] = None

class Client(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: EmailStr
    phone: Optional[str] = None
    membership_type: str = "Standard"
    monthly_fee: float
    start_date: date
    next_payment_date: date
    status: str = "Active"
    auto_reminders_enabled: bool = True  # New field for automatic reminders
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ClientCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    membership_type: str = "Standard"
    monthly_fee: float
    start_date: date
    auto_reminders_enabled: bool = True  # New field for automatic reminders

class ClientUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    membership_type: Optional[str] = None
    monthly_fee: Optional[float] = None
    start_date: Optional[date] = None
    status: Optional[str] = None
    auto_reminders_enabled: Optional[bool] = None  # New field for automatic reminders

class EmailTemplateRequest(BaseModel):
    template_name: str
    subject: str
    html_body: str
    is_active: bool = True

class CustomEmailRequest(BaseModel):
    client_id: str
    custom_subject: Optional[str] = None
    custom_message: Optional[str] = None
    template_name: Optional[str] = "default"
    custom_amount: Optional[float] = None
    custom_due_date: Optional[str] = None

class EmailResponse(BaseModel):
    success: bool
    message: str
    client_email: str

class PaymentRecordRequest(BaseModel):
    client_id: str
    amount_paid: float
    payment_date: date
    payment_method: Optional[str] = "Cash"
    notes: Optional[str] = None

# Helper function to calculate next payment date
def calculate_next_payment_date(start_date: date) -> date:
    return start_date + timedelta(days=30)

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

# Membership Types Management Routes
@api_router.post("/membership-types", response_model=MembershipType)
async def create_membership_type(membership_data: MembershipTypeCreate):
    """Create a new membership type"""
    membership_dict = membership_data.dict()
    membership_obj = MembershipType(**membership_dict)
    
    # Check if membership type with this name already exists
    existing_membership = await db.membership_types.find_one({"name": membership_obj.name})
    if existing_membership:
        raise HTTPException(status_code=400, detail="Membership type with this name already exists")
    
    await db.membership_types.insert_one(membership_obj.dict())
    return membership_obj

@api_router.get("/membership-types", response_model=List[MembershipType])
async def get_membership_types():
    """Get all membership types"""
    membership_types = await db.membership_types.find({"is_active": True}).to_list(1000)
    return [MembershipType(**membership_type) for membership_type in membership_types]

@api_router.get("/membership-types/{membership_id}", response_model=MembershipType)
async def get_membership_type(membership_id: str):
    """Get a specific membership type"""
    membership_type = await db.membership_types.find_one({"id": membership_id})
    if not membership_type:
        raise HTTPException(status_code=404, detail="Membership type not found")
    return MembershipType(**membership_type)

@api_router.put("/membership-types/{membership_id}", response_model=MembershipType)
async def update_membership_type(membership_id: str, membership_update: MembershipTypeUpdate):
    """Update membership type information"""
    membership_type = await db.membership_types.find_one({"id": membership_id})
    if not membership_type:
        raise HTTPException(status_code=404, detail="Membership type not found")
    
    # Update fields
    update_data = {k: v for k, v in membership_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    await db.membership_types.update_one({"id": membership_id}, {"$set": update_data})
    
    # Return updated membership type
    updated_membership_type = await db.membership_types.find_one({"id": membership_id})
    return MembershipType(**updated_membership_type)

@api_router.delete("/membership-types/{membership_id}")
async def delete_membership_type(membership_id: str):
    """Soft delete a membership type (set is_active to False)"""
    membership_type = await db.membership_types.find_one({"id": membership_id})
    if not membership_type:
        raise HTTPException(status_code=404, detail="Membership type not found")
    
    # Soft delete by setting is_active to False
    await db.membership_types.update_one({"id": membership_id}, {"$set": {"is_active": False, "updated_at": datetime.utcnow()}})
    return {"message": "Membership type deactivated successfully"}

@api_router.post("/membership-types/seed")
async def seed_default_membership_types():
    """Seed default membership types"""
    default_types = [
        {
            "name": "Standard",
            "monthly_fee": 50.00,
            "description": "Basic gym access with equipment usage",
            "features": ["Equipment Access", "Locker Room", "Basic Support"]
        },
        {
            "name": "Premium", 
            "monthly_fee": 75.00,
            "description": "Gym access plus group fitness classes",
            "features": ["All Standard Features", "Group Classes", "Extended Hours", "Guest Passes"]
        },
        {
            "name": "Elite",
            "monthly_fee": 100.00,
            "description": "Premium features plus personal training sessions",
            "features": ["All Premium Features", "Personal Training Sessions", "Nutrition Consultation", "Priority Booking"]
        },
        {
            "name": "VIP",
            "monthly_fee": 150.00,
            "description": "All-inclusive membership with premium amenities",
            "features": ["All Elite Features", "VIP Lounge Access", "Massage Therapy", "Meal Planning", "24/7 Support"]
        }
    ]
    
    created_types = []
    for type_data in default_types:
        # Check if membership type already exists
        existing = await db.membership_types.find_one({"name": type_data["name"]})
        if not existing:
            membership_obj = MembershipType(**type_data)
            await db.membership_types.insert_one(membership_obj.dict())
            created_types.append(type_data["name"])
    
    return {"message": f"Seeded {len(created_types)} membership types", "created_types": created_types}

# Client Management Routes (Updated)
@api_router.post("/clients", response_model=Client)
async def create_client(client_data: ClientCreate):
    """Create a new client"""
    client_dict = client_data.dict()
    
    # Calculate next payment date (30 days after start date)
    next_payment_date = calculate_next_payment_date(client_data.start_date)
    client_dict['next_payment_date'] = next_payment_date
    
    client_obj = Client(**client_dict)
    
    # Check if client with this email already exists
    existing_client = await db.clients.find_one({"email": client_obj.email})
    if existing_client:
        raise HTTPException(status_code=400, detail="Client with this email already exists")
    
    # Convert dates to strings for MongoDB storage
    client_dict_for_db = client_obj.dict()
    client_dict_for_db['start_date'] = client_obj.start_date.isoformat()
    client_dict_for_db['next_payment_date'] = client_obj.next_payment_date.isoformat()
    
    await db.clients.insert_one(client_dict_for_db)
    return client_obj

@api_router.get("/clients", response_model=List[Client])
async def get_clients():
    """Get all clients"""
    clients = await db.clients.find().to_list(1000)
    
    # Convert date strings back to date objects
    for client in clients:
        if 'start_date' in client and isinstance(client['start_date'], str):
            try:
                client['start_date'] = datetime.fromisoformat(client['start_date']).date()
            except ValueError:
                # Handle legacy date format or invalid dates
                client['start_date'] = date.today()
        elif 'start_date' not in client:
            # Handle clients without start_date (legacy)
            client['start_date'] = date.today()
            
        if 'next_payment_date' in client and isinstance(client['next_payment_date'], str):
            try:
                client['next_payment_date'] = datetime.fromisoformat(client['next_payment_date']).date()
            except ValueError:
                # Handle legacy date format or calculate from start_date
                start_date = client.get('start_date', date.today())
                if isinstance(start_date, str):
                    start_date = datetime.fromisoformat(start_date).date()
                client['next_payment_date'] = calculate_next_payment_date(start_date)
        elif 'next_payment_date' not in client:
            # Handle clients without next_payment_date (legacy)
            start_date = client.get('start_date', date.today())
            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date).date()
            client['next_payment_date'] = calculate_next_payment_date(start_date)
    
    return [Client(**client) for client in clients]

@api_router.get("/clients/{client_id}", response_model=Client)
async def get_client(client_id: str):
    """Get a specific client"""
    client = await db.clients.find_one({"id": client_id})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Convert date strings back to date objects
    if 'start_date' in client and isinstance(client['start_date'], str):
        client['start_date'] = datetime.fromisoformat(client['start_date']).date()
    if 'next_payment_date' in client and isinstance(client['next_payment_date'], str):
        client['next_payment_date'] = datetime.fromisoformat(client['next_payment_date']).date()
    
    return Client(**client)

@api_router.put("/clients/{client_id}", response_model=Client)
async def update_client(client_id: str, client_update: ClientUpdate):
    """Update client information"""
    client = await db.clients.find_one({"id": client_id})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Update fields
    update_data = {k: v for k, v in client_update.dict().items() if v is not None}
    
    # If start_date is updated, recalculate next_payment_date
    if 'start_date' in update_data:
        update_data['next_payment_date'] = calculate_next_payment_date(update_data['start_date']).isoformat()
        update_data['start_date'] = update_data['start_date'].isoformat()
    
    update_data["updated_at"] = datetime.utcnow()
    
    await db.clients.update_one({"id": client_id}, {"$set": update_data})
    
    # Return updated client
    updated_client = await db.clients.find_one({"id": client_id})
    
    # Convert date strings back to date objects for response
    if 'start_date' in updated_client and isinstance(updated_client['start_date'], str):
        updated_client['start_date'] = datetime.fromisoformat(updated_client['start_date']).date()
    if 'next_payment_date' in updated_client and isinstance(updated_client['next_payment_date'], str):
        updated_client['next_payment_date'] = datetime.fromisoformat(updated_client['next_payment_date']).date()
    
    return Client(**updated_client)

@api_router.delete("/clients/{client_id}")
async def delete_client(client_id: str):
    """Delete a client"""
    result = await db.clients.delete_one({"id": client_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Client not found")
    return {"message": "Client deleted successfully"}

# Email Routes (Updated to handle new client structure)
@api_router.post("/email/test")
async def test_email():
    """Test email configuration"""
    success = email_service.test_email_connection()
    return {
        "success": success,
        "message": "Email configuration is working!" if success else "Email configuration failed!"
    }

@api_router.get("/email/templates")
async def get_email_templates():
    """Get available email templates"""
    templates = {
        "default": {
            "name": "Default",
            "description": "Professional standard template with gym branding"
        },
        "professional": {
            "name": "Professional",
            "description": "Clean, business-style template for formal communications"
        },
        "friendly": {
            "name": "Friendly",
            "description": "Casual, fun template with emojis and vibrant colors"
        }
    }
    return {"templates": templates}

@api_router.post("/email/custom-reminder", response_model=EmailResponse)
async def send_custom_payment_reminder(reminder_request: CustomEmailRequest):
    """Send customized payment reminder to a specific client"""
    # Get client details
    client = await db.clients.find_one({"id": reminder_request.client_id})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Convert date strings back to date objects if needed
    if 'start_date' in client and isinstance(client['start_date'], str):
        client['start_date'] = datetime.fromisoformat(client['start_date']).date()
    if 'next_payment_date' in client and isinstance(client['next_payment_date'], str):
        client['next_payment_date'] = datetime.fromisoformat(client['next_payment_date']).date()
    
    client_obj = Client(**client)
    
    # Use custom amount or client's monthly fee
    amount = reminder_request.custom_amount or client_obj.monthly_fee
    
    # Use custom due date or client's next payment date
    due_date = reminder_request.custom_due_date or client_obj.next_payment_date.strftime("%B %d, %Y")
    
    # Send email with customization
    success = email_service.send_payment_reminder(
        client_email=client_obj.email,
        client_name=client_obj.name,
        amount=amount,
        due_date=due_date,
        template_name=reminder_request.template_name or "default",
        custom_subject=reminder_request.custom_subject,
        custom_message=reminder_request.custom_message
    )
    
    return EmailResponse(
        success=success,
        message="Custom payment reminder sent successfully!" if success else "Failed to send custom payment reminder",
        client_email=client_obj.email
    )

@api_router.post("/email/payment-reminder", response_model=EmailResponse)
async def send_payment_reminder(reminder_request: CustomEmailRequest):
    """Send payment reminder to a specific client"""
    # Get client details
    client = await db.clients.find_one({"id": reminder_request.client_id})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Convert date strings back to date objects if needed
    if 'start_date' in client and isinstance(client['start_date'], str):
        client['start_date'] = datetime.fromisoformat(client['start_date']).date()
    if 'next_payment_date' in client and isinstance(client['next_payment_date'], str):
        client['next_payment_date'] = datetime.fromisoformat(client['next_payment_date']).date()
    
    client_obj = Client(**client)
    
    # Use custom amount or client's monthly fee
    amount = reminder_request.custom_amount or client_obj.monthly_fee
    
    # Use custom due date or client's next payment date
    due_date = reminder_request.custom_due_date or client_obj.next_payment_date.strftime("%B %d, %Y")
    
    # Send email with customization
    success = email_service.send_payment_reminder(
        client_email=client_obj.email,
        client_name=client_obj.name,
        amount=amount,
        due_date=due_date,
        template_name=reminder_request.template_name or "default",
        custom_subject=reminder_request.custom_subject,
        custom_message=reminder_request.custom_message
    )
    
    return EmailResponse(
        success=success,
        message="Payment reminder sent successfully!" if success else "Failed to send payment reminder",
        client_email=client_obj.email
    )

@api_router.post("/payments/record")
async def record_client_payment(payment_request: PaymentRecordRequest):
    """Record a payment and update client's next payment date"""
    # Get client details
    client = await db.clients.find_one({"id": payment_request.client_id})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Convert date strings back to date objects if needed
    if 'start_date' in client and isinstance(client['start_date'], str):
        client['start_date'] = datetime.fromisoformat(client['start_date']).date()
    if 'next_payment_date' in client and isinstance(client['next_payment_date'], str):
        client['next_payment_date'] = datetime.fromisoformat(client['next_payment_date']).date()
    
    client_obj = Client(**client)
    
    # Calculate new next payment date (30 days from payment date)
    new_next_payment_date = payment_request.payment_date + timedelta(days=30)
    
    # Update client's next payment date
    await db.clients.update_one(
        {"id": payment_request.client_id}, 
        {
            "$set": {
                "next_payment_date": new_next_payment_date.isoformat(),
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    # Record the payment (you could store this in a separate payments collection if needed)
    payment_record = {
        "id": str(uuid.uuid4()),
        "client_id": payment_request.client_id,
        "client_name": client_obj.name,
        "client_email": client_obj.email,
        "amount_paid": payment_request.amount_paid,
        "payment_date": payment_request.payment_date.isoformat(),
        "payment_method": payment_request.payment_method,
        "notes": payment_request.notes,
        "previous_due_date": client_obj.next_payment_date.isoformat(),
        "new_due_date": new_next_payment_date.isoformat(),
        "recorded_at": datetime.utcnow()
    }
    
    # You could optionally store payment records in a separate collection
    # await db.payment_records.insert_one(payment_record)
    
    # Send automatic invoice email
    invoice_success = email_service.send_payment_invoice(
        client_email=client_obj.email,
        client_name=client_obj.name,
        amount_paid=payment_request.amount_paid,
        payment_date=payment_request.payment_date.strftime("%B %d, %Y"),
        payment_method=payment_request.payment_method,
        notes=payment_request.notes
    )
    
    return {
        "success": True,
        "message": f"Payment recorded successfully for {client_obj.name}",
        "client_name": client_obj.name,
        "amount_paid": payment_request.amount_paid,
        "new_next_payment_date": new_next_payment_date.strftime("%B %d, %Y"),
        "payment_record": payment_record,
        "invoice_sent": invoice_success,
        "invoice_message": "Invoice email sent successfully!" if invoice_success else "Invoice email failed to send"
    }

@api_router.post("/email/payment-reminder/bulk")
async def send_bulk_payment_reminders():
    """Send payment reminders to all active clients with upcoming payments"""
    clients = await db.clients.find({"status": "Active"}).to_list(1000)
    
    sent_count = 0
    failed_count = 0
    results = []
    
    for client_data in clients:
        try:
            # Convert date strings back to date objects if needed and handle missing fields
            if 'start_date' in client_data and isinstance(client_data['start_date'], str):
                try:
                    client_data['start_date'] = datetime.fromisoformat(client_data['start_date']).date()
                except ValueError:
                    # Handle legacy date format or invalid dates
                    client_data['start_date'] = date.today()
            elif 'start_date' not in client_data:
                # Handle clients without start_date (legacy)
                client_data['start_date'] = date.today()
                
            if 'next_payment_date' in client_data and isinstance(client_data['next_payment_date'], str):
                try:
                    client_data['next_payment_date'] = datetime.fromisoformat(client_data['next_payment_date']).date()
                except ValueError:
                    # Handle legacy date format or calculate from start_date
                    start_date = client_data.get('start_date', date.today())
                    if isinstance(start_date, str):
                        start_date = datetime.fromisoformat(start_date).date()
                    client_data['next_payment_date'] = calculate_next_payment_date(start_date)
            elif 'next_payment_date' not in client_data:
                # Handle clients without next_payment_date (legacy)
                start_date = client_data.get('start_date', date.today())
                if isinstance(start_date, str):
                    start_date = datetime.fromisoformat(start_date).date()
                client_data['next_payment_date'] = calculate_next_payment_date(start_date)
            
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
            
        except Exception as e:
            # Handle any other validation errors gracefully
            logger.error(f"Error processing client {client_data.get('name', 'Unknown')}: {str(e)}")
            failed_count += 1
            results.append({
                "client_name": client_data.get('name', 'Unknown'),
                "client_email": client_data.get('email', 'Unknown'),
                "success": False,
                "error": str(e)
            })
    
    return {
        "total_clients": len(clients),
        "sent_successfully": sent_count,
        "failed": failed_count,
        "results": results
    }

# Automatic Reminders API Routes
@api_router.get("/reminders/upcoming")
async def get_upcoming_reminders(days_ahead: int = 7):
    """Get upcoming automatic reminders for the next N days"""
    if not reminder_scheduler:
        raise HTTPException(status_code=503, detail="Reminder scheduler not initialized")
    
    try:
        upcoming = await reminder_scheduler.get_upcoming_reminders(days_ahead)
        return {
            "upcoming_reminders": upcoming,
            "days_ahead": days_ahead,
            "total_reminders": len(upcoming)
        }
    except Exception as e:
        logger.error(f"Error getting upcoming reminders: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get upcoming reminders")

@api_router.get("/reminders/history")
async def get_reminder_history(client_id: Optional[str] = None, limit: int = 100):
    """Get reminder history for all clients or specific client"""
    if not reminder_scheduler:
        raise HTTPException(status_code=503, detail="Reminder scheduler not initialized")
    
    try:
        history = await reminder_scheduler.get_reminder_history(client_id, limit)
        return {
            "reminder_history": history,
            "total_records": len(history),
            "client_id": client_id
        }
    except Exception as e:
        logger.error(f"Error getting reminder history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get reminder history")

@api_router.post("/reminders/test-run")
async def test_reminder_run():
    """Manually trigger a reminder check (for testing purposes)"""
    if not reminder_scheduler:
        raise HTTPException(status_code=503, detail="Reminder scheduler not initialized")
    
    try:
        await reminder_scheduler.check_and_send_reminders()
        return {
            "success": True,
            "message": "Test reminder run completed successfully"
        }
    except Exception as e:
        logger.error(f"Error in test reminder run: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to run reminder test")

@api_router.get("/reminders/stats")
async def get_reminder_stats():
    """Get reminder statistics and summary"""
    try:
        # Get recent summaries
        summaries = await db.reminder_summaries.find().sort("created_at", -1).limit(30).to_list(30)
        
        # Convert datetime objects to JSON-serializable format
        for summary in summaries:
            if '_id' in summary:
                del summary['_id']  # Remove MongoDB ObjectId
            if 'created_at' in summary and isinstance(summary['created_at'], datetime):
                summary['created_at'] = summary['created_at'].isoformat()
        
        # Calculate totals
        total_sent = sum(summary.get("total_reminders_sent", 0) for summary in summaries)
        total_failed = sum(summary.get("failed_reminders", 0) for summary in summaries)
        
        # Get today's stats
        today_summary = await db.reminder_summaries.find_one({"date": date.today().isoformat()})
        
        return {
            "total_reminders_sent": total_sent,
            "total_failed_reminders": total_failed,
            "success_rate": (total_sent / (total_sent + total_failed) * 100) if (total_sent + total_failed) > 0 else 0,
            "todays_reminders": today_summary.get("total_reminders_sent", 0) if today_summary else 0,
            "recent_summaries": summaries[:7],  # Last 7 days
            "scheduler_active": reminder_scheduler is not None and reminder_scheduler.scheduler.running
        }
    except Exception as e:
        logger.error(f"Error getting reminder stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get reminder statistics")

@api_router.put("/clients/{client_id}/reminders")
async def update_client_reminder_settings(client_id: str, request: dict):
    """Update automatic reminder settings for a specific client"""
    try:
        enabled = request.get("enabled", True)
        
        # Check if client exists
        client = await db.clients.find_one({"id": client_id})
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Update reminder settings
        await db.clients.update_one(
            {"id": client_id},
            {
                "$set": {
                    "auto_reminders_enabled": enabled,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return {
            "success": True,
            "message": f"Automatic reminders {'enabled' if enabled else 'disabled'} for client",
            "client_id": client_id,
            "auto_reminders_enabled": enabled
        }
    except Exception as e:
        logger.error(f"Error updating client reminder settings: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update reminder settings")

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

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global reminder_scheduler
    try:
        # Initialize reminder scheduler
        await initialize_reminder_scheduler(client, email_service)
        # Import the module and get the scheduler instance
        import reminder_scheduler as rs_module
        reminder_scheduler = rs_module.reminder_scheduler
        logger.info("✅ Application startup completed")
    except Exception as e:
        logger.error(f"❌ Application startup failed: {str(e)}")
        # Don't raise here to allow app to start even if scheduler fails
        # This allows manual functionality to still work

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up services on shutdown"""
    try:
        # Shutdown reminder scheduler
        await shutdown_reminder_scheduler()
        # Close database connection
        client.close()
        logger.info("✅ Application shutdown completed")
    except Exception as e:
        logger.error(f"❌ Application shutdown failed: {str(e)}")