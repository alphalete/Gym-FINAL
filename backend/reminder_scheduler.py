"""
Automatic Payment Reminder Scheduler Service
Handles scheduling and sending automatic payment reminders based on due dates.
"""
import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from motor.motor_asyncio import AsyncIOMotorClient
from email_service import EmailService
import os
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReminderScheduler:
    def __init__(self, mongo_client: AsyncIOMotorClient, email_service: EmailService):
        self.mongo_client = mongo_client
        self.email_service = email_service
        self.db = mongo_client[os.environ['DB_NAME']]
        self.scheduler = AsyncIOScheduler()
        
        # Configure scheduler to run daily at 9 AM
        self.scheduler.add_job(
            self.check_and_send_reminders,
            CronTrigger(hour=9, minute=0),  # 9:00 AM daily
            id="daily_reminder_check",
            replace_existing=True
        )
        
        logger.info("ReminderScheduler initialized with daily check at 9:00 AM")

    async def start(self):
        """Start the reminder scheduler"""
        try:
            self.scheduler.start()
            logger.info("✅ Reminder scheduler started successfully")
            
            # Run an initial check when service starts
            await self.check_and_send_reminders()
            
        except Exception as e:
            logger.error(f"❌ Failed to start reminder scheduler: {str(e)}")
            raise

    async def stop(self):
        """Stop the reminder scheduler"""
        try:
            self.scheduler.shutdown()
            logger.info("✅ Reminder scheduler stopped successfully")
        except Exception as e:
            logger.error(f"❌ Failed to stop reminder scheduler: {str(e)}")

    async def check_and_send_reminders(self):
        """
        Main function that checks all clients and sends reminders based on due dates
        """
        logger.info("🔍 Starting automatic reminder check...")
        
        try:
            # Get all active clients with reminders enabled
            clients = await self.get_clients_needing_reminders()
            
            if not clients:
                logger.info("📭 No clients need reminders today")
                return
            
            logger.info(f"📋 Found {len(clients)} clients to check for reminders")
            
            reminder_stats = {
                "three_day_reminders": 0,
                "due_date_reminders": 0,
                "skipped_reminders": 0,
                "failed_reminders": 0
            }
            
            for client in clients:
                await self.process_client_reminders(client, reminder_stats)
            
            # Log summary
            total_sent = reminder_stats["three_day_reminders"] + reminder_stats["due_date_reminders"]
            logger.info(f"📊 Reminder Summary: {total_sent} sent, {reminder_stats['skipped_reminders']} skipped, {reminder_stats['failed_reminders']} failed")
            
            # Store daily reminder summary
            await self.store_reminder_summary(reminder_stats)
            
        except Exception as e:
            logger.error(f"❌ Error in reminder check: {str(e)}")

    async def get_clients_needing_reminders(self) -> List[Dict]:
        """Get all active clients who have reminders enabled"""
        try:
            # Get all active clients
            clients = await self.db.clients.find({
                "status": "Active",
                "$or": [
                    {"auto_reminders_enabled": True},
                    {"auto_reminders_enabled": {"$exists": False}}  # Default to enabled for existing clients
                ]
            }).to_list(1000)
            
            # Process date fields
            processed_clients = []
            for client in clients:
                try:
                    # Handle date conversion
                    if 'next_payment_date' in client and isinstance(client['next_payment_date'], str):
                        client['next_payment_date'] = datetime.fromisoformat(client['next_payment_date']).date()
                    elif 'next_payment_date' not in client:
                        # Skip clients without payment dates
                        continue
                        
                    # Default to enabled if not specified
                    if 'auto_reminders_enabled' not in client:
                        client['auto_reminders_enabled'] = True
                    
                    processed_clients.append(client)
                    
                except Exception as e:
                    logger.warning(f"⚠️ Skipping client {client.get('name', 'Unknown')} due to date processing error: {str(e)}")
                    continue
            
            return processed_clients
            
        except Exception as e:
            logger.error(f"❌ Error fetching clients: {str(e)}")
            return []

    async def process_client_reminders(self, client: Dict, stats: Dict):
        """Process reminders for a single client"""
        try:
            client_name = client.get('name', 'Unknown')
            client_email = client.get('email', 'Unknown')
            next_payment_date = client.get('next_payment_date')
            
            if not next_payment_date:
                logger.warning(f"⚠️ Skipping {client_name} - no payment date")
                stats["skipped_reminders"] += 1
                return
            
            today = date.today()
            three_days_before = next_payment_date - timedelta(days=3)
            
            # Check if client needs 3-day reminder
            if today == three_days_before:
                sent = await self.send_reminder_if_not_sent(client, "3_day", stats)
                if sent:
                    logger.info(f"📧 Sent 3-day reminder to {client_name}")
            
            # Check if client needs due date reminder
            elif today == next_payment_date:
                sent = await self.send_reminder_if_not_sent(client, "due_date", stats)
                if sent:
                    logger.info(f"📧 Sent due date reminder to {client_name}")
            
            else:
                # No reminder needed today
                pass
                
        except Exception as e:
            logger.error(f"❌ Error processing client {client.get('name', 'Unknown')}: {str(e)}")
            stats["failed_reminders"] += 1

    async def send_reminder_if_not_sent(self, client: Dict, reminder_type: str, stats: Dict) -> bool:
        """Send reminder if not already sent for this payment cycle"""
        try:
            client_id = client.get('id')
            client_name = client.get('name', 'Unknown')
            client_email = client.get('email')
            next_payment_date = client.get('next_payment_date')
            
            if not client_email:
                logger.warning(f"⚠️ Skipping {client_name} - no email address")
                stats["skipped_reminders"] += 1
                return False
            
            # Check if reminder already sent for this payment cycle
            existing_reminder = await self.db.reminder_history.find_one({
                "client_id": client_id,
                "reminder_type": reminder_type,
                "payment_due_date": next_payment_date.isoformat(),
                "status": "sent"
            })
            
            if existing_reminder:
                logger.info(f"🔄 Skipping {client_name} - {reminder_type} reminder already sent")
                stats["skipped_reminders"] += 1
                return False
            
            # Send the reminder
            success = await self.send_automatic_reminder(client, reminder_type)
            
            if success:
                # Record the sent reminder
                await self.record_sent_reminder(client, reminder_type, "sent")
                
                if reminder_type == "3_day":
                    stats["three_day_reminders"] += 1
                else:
                    stats["due_date_reminders"] += 1
                
                return True
            else:
                # Record the failed reminder
                await self.record_sent_reminder(client, reminder_type, "failed")
                stats["failed_reminders"] += 1
                return False
                
        except Exception as e:
            logger.error(f"❌ Error sending reminder: {str(e)}")
            stats["failed_reminders"] += 1
            return False

    async def send_automatic_reminder(self, client: Dict, reminder_type: str) -> bool:
        """Send automatic reminder email"""
        try:
            client_name = client.get('name', 'Unknown')
            client_email = client.get('email')
            monthly_fee = client.get('monthly_fee', 0)
            next_payment_date = client.get('next_payment_date')
            
            # Format due date
            due_date_str = next_payment_date.strftime("%B %d, %Y")
            
            # Customize subject and message based on reminder type
            if reminder_type == "3_day":
                custom_subject = f"Payment Reminder - Due in 3 Days - Alphalete Athletics"
                custom_message = f"This is a friendly reminder that your payment of ${monthly_fee:.2f} is due in 3 days on {due_date_str}. Please ensure your payment is processed to avoid any interruption to your membership."
            else:  # due_date
                custom_subject = f"Payment Due Today - Alphalete Athletics"
                custom_message = f"Your payment of ${monthly_fee:.2f} is due today ({due_date_str}). Please complete your payment to continue enjoying our premium facilities and services."
            
            # Send email using existing email service
            success = self.email_service.send_payment_reminder(
                client_email=client_email,
                client_name=client_name,
                amount=monthly_fee,
                due_date=due_date_str,
                template_name="default",
                custom_subject=custom_subject,
                custom_message=custom_message
            )
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error sending automatic reminder: {str(e)}")
            return False

    async def record_sent_reminder(self, client: Dict, reminder_type: str, status: str):
        """Record reminder in history for duplicate prevention"""
        try:
            reminder_record = {
                "id": str(uuid.uuid4()),
                "client_id": client.get('id'),
                "client_name": client.get('name'),
                "client_email": client.get('email'),
                "reminder_type": reminder_type,
                "payment_due_date": client.get('next_payment_date').isoformat(),
                "sent_date": date.today().isoformat(),
                "status": status,
                "created_at": datetime.utcnow()
            }
            
            await self.db.reminder_history.insert_one(reminder_record)
            logger.info(f"📝 Recorded {reminder_type} reminder for {client.get('name')} - Status: {status}")
            
        except Exception as e:
            logger.error(f"❌ Error recording reminder: {str(e)}")

    async def store_reminder_summary(self, stats: Dict):
        """Store daily reminder summary for reporting"""
        try:
            summary = {
                "id": str(uuid.uuid4()),
                "date": date.today().isoformat(),
                "three_day_reminders_sent": stats["three_day_reminders"],
                "due_date_reminders_sent": stats["due_date_reminders"],
                "skipped_reminders": stats["skipped_reminders"],
                "failed_reminders": stats["failed_reminders"],
                "total_reminders_sent": stats["three_day_reminders"] + stats["due_date_reminders"],
                "created_at": datetime.utcnow()
            }
            
            await self.db.reminder_summaries.insert_one(summary)
            logger.info(f"📊 Stored daily reminder summary: {summary['total_reminders_sent']} sent")
            
        except Exception as e:
            logger.error(f"❌ Error storing reminder summary: {str(e)}")

    async def get_reminder_history(self, client_id: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Get reminder history for reporting"""
        try:
            query = {}
            if client_id:
                query["client_id"] = client_id
            
            reminders = await self.db.reminder_history.find(query).sort("created_at", -1).limit(limit).to_list(limit)
            
            # Convert ObjectId and datetime objects to JSON-serializable format
            for reminder in reminders:
                if '_id' in reminder:
                    del reminder['_id']  # Remove MongoDB ObjectId
                if 'created_at' in reminder and isinstance(reminder['created_at'], datetime):
                    reminder['created_at'] = reminder['created_at'].isoformat()
            
            return reminders
            
        except Exception as e:
            logger.error(f"❌ Error getting reminder history: {str(e)}")
            return []

    async def get_upcoming_reminders(self, days_ahead: int = 7) -> List[Dict]:
        """Get clients who will need reminders in the next N days"""
        try:
            today = date.today()
            end_date = today + timedelta(days=days_ahead)
            
            clients = await self.db.clients.find({
                "status": "Active",
                "$or": [
                    {"auto_reminders_enabled": True},
                    {"auto_reminders_enabled": {"$exists": False}}
                ]
            }).to_list(1000)
            
            upcoming = []
            for client in clients:
                try:
                    # Convert date if needed
                    if 'next_payment_date' in client and isinstance(client['next_payment_date'], str):
                        next_payment_date = datetime.fromisoformat(client['next_payment_date']).date()
                    else:
                        next_payment_date = client.get('next_payment_date')
                    
                    if not next_payment_date:
                        continue
                    
                    # Check if 3-day reminder is needed
                    three_day_reminder_date = next_payment_date - timedelta(days=3)
                    if today <= three_day_reminder_date <= end_date:
                        upcoming.append({
                            "client_id": client.get('id'),
                            "client_name": client.get('name'),
                            "client_email": client.get('email'),
                            "reminder_type": "3_day",
                            "reminder_date": three_day_reminder_date.isoformat(),
                            "payment_due_date": next_payment_date.isoformat(),
                            "amount": client.get('monthly_fee', 0)
                        })
                    
                    # Check if due date reminder is needed
                    if today <= next_payment_date <= end_date:
                        upcoming.append({
                            "client_id": client.get('id'),
                            "client_name": client.get('name'),
                            "client_email": client.get('email'),
                            "reminder_type": "due_date",
                            "reminder_date": next_payment_date.isoformat(),
                            "payment_due_date": next_payment_date.isoformat(),
                            "amount": client.get('monthly_fee', 0)
                        })
                        
                except Exception as e:
                    logger.warning(f"⚠️ Skipping client in upcoming reminders: {str(e)}")
                    continue
            
            return upcoming
            
        except Exception as e:
            logger.error(f"❌ Error getting upcoming reminders: {str(e)}")
            return []

# Global reminder scheduler instance
reminder_scheduler = None

async def initialize_reminder_scheduler(mongo_client: AsyncIOMotorClient, email_service: EmailService):
    """Initialize the global reminder scheduler"""
    global reminder_scheduler
    try:
        reminder_scheduler = ReminderScheduler(mongo_client, email_service)
        await reminder_scheduler.start()
        logger.info("✅ Global reminder scheduler initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize reminder scheduler: {str(e)}")
        raise

async def shutdown_reminder_scheduler():
    """Shutdown the global reminder scheduler"""
    global reminder_scheduler
    if reminder_scheduler:
        await reminder_scheduler.stop()
        logger.info("✅ Global reminder scheduler shutdown")