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
    
    def get_email_template(self, template_name: str = "default", custom_subject: str = None, custom_message: str = None):
        """Get email template with customization support"""
        
        # Default template
        if template_name == "default" or not template_name:
            subject = custom_subject or "Payment Reminder - Alphalete Athletics Club"
            
            custom_message_section = f"<p><em>{custom_message}</em></p>" if custom_message else "<p>We hope you're crushing your fitness goals! This is a friendly reminder about your upcoming payment:</p>"
            
            html_template = """
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                    .header { background-color: #2c3e50; color: white; padding: 20px; text-align: center; }
                    .content { padding: 30px 20px; }
                    .amount { font-size: 24px; font-weight: bold; color: #e74c3c; }
                    .due-date { font-size: 18px; color: #f39c12; }
                    .footer { background-color: #f8f9fa; padding: 15px; text-align: center; font-size: 12px; }
                    .btn { background-color: #3498db; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; display: inline-block; }
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
                        
                        """ + custom_message_section + """
                        
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
            
            return subject, html_template
        
        # Professional template
        elif template_name == "professional":
            subject = custom_subject or "Payment Due Notice - Alphalete Athletics Club"
            
            custom_message_section = f"<p><em>{custom_message}</em></p>" if custom_message else "<p>This is a reminder regarding your upcoming membership payment:</p>"
            
            html_template = """
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #2c3e50; }
                    .container { max-width: 600px; margin: 0 auto; padding: 0; background: white; }
                    .header { background: linear-gradient(135deg, #2c3e50, #34495e); color: white; padding: 30px 20px; text-align: center; }
                    .content { padding: 40px 30px; }
                    .amount-box { background: #f8f9fa; border-left: 4px solid #e74c3c; padding: 20px; margin: 20px 0; }
                    .amount { font-size: 28px; font-weight: bold; color: #e74c3c; }
                    .due-date { font-size: 16px; color: #7f8c8d; }
                    .footer { background: #ecf0f1; padding: 20px; text-align: center; font-size: 12px; color: #7f8c8d; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>ALPHALETE ATHLETICS CLUB</h1>
                        <p>Professional Fitness Management</p>
                    </div>
                    <div class="content">
                        <h2 style="color: #2c3e50;">Payment Notice</h2>
                        <p>Dear {client_name},</p>
                        
                        """ + custom_message_section + """
                        
                        <div class="amount-box">
                            <p><strong>Payment Amount:</strong> <span class="amount">${amount:.2f}</span></p>
                            <p><strong>Payment Due:</strong> <span class="due-date">{due_date}</span></p>
                        </div>
                        
                        <p>Please ensure your payment is processed by the due date to maintain uninterrupted access to our facilities.</p>
                        
                        <p>For payment options or inquiries, please contact our membership services team.</p>
                        
                        <p>Best regards,<br><strong>Alphalete Athletics Club Management</strong></p>
                    </div>
                    <div class="footer">
                        <p>Alphalete Athletics Club | Professional Fitness Services</p>
                        <p>Automated notification - Please do not reply to this email</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            return subject, html_template
        
        # Friendly template
        elif template_name == "friendly":
            subject = custom_subject or "Hey! Your Payment is Coming Up 💪 - Alphalete Athletics"
            
            custom_message_section = f"<p><em>Special message: {custom_message}</em></p>" if custom_message else "<p>Hope you're smashing those fitness goals! 🎯 Just a friendly heads up about your upcoming payment:</p>"
            
            html_template = """
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body { font-family: 'Comic Sans MS', cursive, Arial, sans-serif; line-height: 1.6; color: #444; }
                    .container { max-width: 600px; margin: 0 auto; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
                    .inner { background: white; border-radius: 15px; padding: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
                    .header { text-align: center; margin-bottom: 30px; }
                    .emoji { font-size: 48px; }
                    .content { }
                    .amount { font-size: 24px; font-weight: bold; color: #e74c3c; }
                    .due-date { font-size: 18px; color: #f39c12; }
                    .footer { text-align: center; margin-top: 30px; font-size: 12px; color: #888; }
                    .highlight { background: linear-gradient(135deg, #ff9a56, #ff6b6b); color: white; padding: 20px; border-radius: 10px; margin: 20px 0; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="inner">
                        <div class="header">
                            <div class="emoji">🏋️‍♂️💪</div>
                            <h1 style="color: #667eea;">ALPHALETE ATHLETICS CLUB</h1>
                            <p>Your Fitness Journey Partner!</p>
                        </div>
                        <div class="content">
                            <h2>Hey {client_name}! 👋</h2>
                            
                            """ + custom_message_section + """
                            
                            <div class="highlight">
                                <p><strong>Payment Amount:</strong> <span class="amount">${amount:.2f}</span></p>
                                <p><strong>Due Date:</strong> <span class="due-date">{due_date}</span></p>
                            </div>
                            
                            <p>We love having you as part of our fitness family! 🌟 Let's keep those gains coming by keeping your membership active.</p>
                            
                            <p>Questions? We're here to help! Just reach out anytime. 📞</p>
                            
                            <p>Stay strong! 💪<br><strong>Your Alphalete Team</strong></p>
                        </div>
                        <div class="footer">
                            <p>Alphalete Athletics Club | Making Fitness Fun! 🎉</p>
                            <p>This is a friendly automated reminder 🤖</p>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            
            return subject, html_template
        
        # Default fallback
        return self.get_email_template("default", custom_subject, custom_message)
    
    def send_payment_reminder(self, client_email: str, client_name: str, amount: float, due_date: str, 
                            template_name: str = "default", custom_subject: str = None, custom_message: str = None):
        """Send payment reminder email to client with customizable templates"""
        try:
            # Get email template
            subject, html_template = self.get_email_template(template_name, custom_subject, custom_message)
            
            # Format the template with client data using safe string replacement
            html_body = html_template.replace('{client_name}', client_name)
            html_body = html_body.replace('{amount:.2f}', f"{amount:.2f}")
            html_body = html_body.replace('{due_date}', due_date)
            
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
                logger.info(f"Sending email to: {client_email} with template: {template_name}")
                server.send_message(msg)
                
            logger.info(f"Payment reminder sent successfully to {client_email} using {template_name} template")
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