import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.environ.get('SMTP_PORT', 587))
        self.email = os.environ.get('GMAIL_EMAIL')
        self.password = os.environ.get('GMAIL_APP_PASSWORD')
        
        if not self.email or not self.password:
            raise ValueError("Gmail credentials not configured properly")
        
        # Remove spaces from app password if present
        self.password = self.password.replace(' ', '')
    
    def send_payment_reminder(self, client_email: str, client_name: str, amount: float, due_date: str):
        """Send payment reminder email to client"""
        try:
            # Create email content
            subject = "Payment Reminder - Alphalete Athletics Club"
            
            # HTML email template
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #2c3e50; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 30px 20px; }}
                    .amount {{ font-size: 24px; font-weight: bold; color: #e74c3c; }}
                    .due-date {{ font-size: 18px; color: #f39c12; }}
                    .footer {{ background-color: #f8f9fa; padding: 15px; text-align: center; font-size: 12px; }}
                    .btn {{ background-color: #3498db; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; display: inline-block; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🏋️‍♂️ ALPHALETE ATHLETICS CLUB</h1>
                        <p>Elite Fitness Training & Membership</p>
                    </div>
                    <div class="content">
                        <h2>Payment Reminder</h2>
                        <p>Dear {client_name},</p>
                        
                        <p>We hope you're crushing your fitness goals! This is a friendly reminder about your upcoming payment:</p>
                        
                        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                            <p><strong>Amount Due:</strong> <span class="amount">${amount:.2f}</span></p>
                            <p><strong>Due Date:</strong> <span class="due-date">{due_date}</span></p>
                        </div>
                        
                        <p>To continue enjoying our premium facilities and training programs, please ensure your payment is completed by the due date.</p>
                        
                        <p>If you have any questions about your membership or payment, please don't hesitate to contact us.</p>
                        
                        <p>Keep grinding!</p>
                        
                        <p><strong>The Alphalete Athletics Team</strong></p>
                    </div>
                    <div class="footer">
                        <p>Alphalete Athletics Club | Elite Fitness Training</p>
                        <p>This is an automated payment reminder. Please do not reply to this email.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"Alphalete Athletics Club <{self.email}>"
            msg['To'] = client_email
            
            # Add HTML content
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
            
            # Send email
            logger.info(f"Connecting to SMTP server: {self.smtp_server}:{self.smtp_port}")
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                logger.info("Starting TLS...")
                server.starttls()
                logger.info(f"Logging in with email: {self.email}")
                server.login(self.email, self.password)
                logger.info(f"Sending email to: {client_email}")
                server.send_message(msg)
                
            logger.info(f"Payment reminder sent successfully to {client_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send payment reminder to {client_email}: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            return False
    
    def test_email_connection(self):
        """Test if email configuration is working"""
        try:
            logger.info(f"Testing SMTP connection to {self.smtp_server}:{self.smtp_port}")
            logger.info(f"Using email: {self.email}")
            logger.info(f"Password length: {len(self.password)}")
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.set_debuglevel(1)  # Enable debug output
                logger.info("Starting TLS...")
                server.starttls()
                logger.info("Attempting login...")
                server.login(self.email, self.password)
                logger.info("Login successful!")
            
            logger.info("Email connection test passed!")
            return True
            
        except Exception as e:
            logger.error(f"Email connection test failed: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            # Try to get more specific error information
            if hasattr(e, 'smtp_code'):
                logger.error(f"SMTP code: {e.smtp_code}")
            if hasattr(e, 'smtp_error'):
                logger.error(f"SMTP error: {e.smtp_error}")
            return False