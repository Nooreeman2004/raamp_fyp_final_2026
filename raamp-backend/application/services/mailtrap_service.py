# Application Layer - Mailtrap Email Service
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from datetime import datetime
from config import config


# HTML Email Templates with placeholders
VERIFICATION_EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6; 
            color: #333;
            background-color: #f5f5f5;
            margin: 0;
            padding: 0;
        }
        .email-container { 
            max-width: 600px; 
            margin: 40px auto; 
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .header { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; 
            padding: 40px 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 28px;
            font-weight: 600;
        }
        .content { 
            padding: 40px 30px;
        }
        .greeting {
            font-size: 18px;
            color: #333;
            margin-bottom: 20px;
        }
        .message {
            color: #666;
            margin-bottom: 30px;
            font-size: 15px;
        }
        .otp-box {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            border-radius: 10px;
            padding: 30px;
            text-align: center;
            margin: 30px 0;
        }
        .otp-label {
            font-size: 14px;
            color: #666;
            margin-bottom: 15px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .otp-code { 
            font-size: 42px;
            font-weight: 700;
            letter-spacing: 12px;
            color: #667eea;
            font-family: 'Courier New', monospace;
            margin: 15px 0;
        }
        .expiry-info {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px 20px;
            margin: 25px 0;
            border-radius: 4px;
        }
        .expiry-info strong {
            color: #856404;
        }
        .timer {
            font-size: 16px;
            color: #666;
            margin-top: 15px;
        }
        .resend-info {
            background: #e3f2fd;
            border-left: 4px solid #2196f3;
            padding: 15px 20px;
            margin: 25px 0;
            border-radius: 4px;
            font-size: 14px;
            color: #0d47a1;
        }
        .footer { 
            background: #f8f9fa;
            text-align: center;
            padding: 25px;
            color: #6c757d;
            font-size: 13px;
            border-top: 1px solid #e9ecef;
        }
        .security-note {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin-top: 25px;
            font-size: 13px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header">
            <h1>✨ Verify Your Email</h1>
        </div>
        <div class="content">
            <div class="greeting">
                Hi <strong>{name}</strong>,
            </div>
            <div class="message">
                Welcome to RAAMP! We're excited to have you on board. 
                To complete your registration, please verify your email address using the code below:
            </div>
            
            <div class="otp-box">
                <div class="otp-label">Your Verification Code</div>
                <div class="otp-code">{verificationCode}</div>
                <div class="timer">⏱️ Code expires in: <strong>24 hours</strong></div>
            </div>
            
            <div class="expiry-info">
                <strong>⚠️ Important:</strong> This code is valid for 24 hours. 
                After that, you'll need to request a new one.
            </div>
            
            <div class="resend-info">
                <strong>Didn't receive the code?</strong><br>
                You can request a new verification code after 60 seconds.
            </div>
            
            <div class="security-note">
                🔒 <strong>Security Note:</strong> If you didn't create a RAAMP account, 
                please ignore this email. Your email address will not be used without verification.
            </div>
        </div>
        <div class="footer">
            <p><strong>RAAMP</strong> - Revolutionary AI-Powered Autonomous Marketing Platform</p>
            <p>© 2025 RAAMP. All rights reserved.</p>
            <p style="margin-top: 15px; font-size: 12px;">
                This is an automated email. Please do not reply to this message.
            </p>
        </div>
    </div>
</body>
</html>
"""

WELCOME_EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6; 
            color: #333;
            background-color: #f5f5f5;
            margin: 0;
            padding: 0;
        }
        .email-container { 
            max-width: 600px; 
            margin: 40px auto; 
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .header { 
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            color: white; 
            padding: 40px 30px;
            text-align: center;
        }
        .content { 
            padding: 40px 30px;
        }
        .welcome-message {
            font-size: 18px;
            color: #333;
            margin-bottom: 20px;
        }
        .feature-list {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 25px;
            margin: 25px 0;
        }
        .feature-list h3 {
            color: #667eea;
            margin-top: 0;
        }
        .feature-list ul {
            list-style: none;
            padding: 0;
        }
        .feature-list li {
            padding: 10px 0;
            border-bottom: 1px solid #e9ecef;
        }
        .feature-list li:last-child {
            border-bottom: none;
        }
        .cta-button {
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 35px;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 600;
            margin: 20px 0;
        }
        .footer { 
            background: #f8f9fa;
            text-align: center;
            padding: 25px;
            color: #6c757d;
            font-size: 13px;
            border-top: 1px solid #e9ecef;
        }
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header">
            <h1>🎉 Welcome to RAAMP!</h1>
        </div>
        <div class="content">
            <div class="welcome-message">
                <p>Hi <strong>{name}</strong>,</p>
                <p>Your email has been successfully verified! You're now ready to explore RAAMP.</p>
            </div>
            
            <div class="feature-list">
                <h3>🚀 What you can do with RAAMP:</h3>
                <ul>
                    <li>🌍 <strong>Geo-Intent:</strong> Access your geo-intent tools and insights</li>
                    <li>🎨 <strong>Creative Studio:</strong> Access your creative studio tools and insights</li>
                    <li>📈 <strong>Trend Arbitrage:</strong> Access your trend arbitrage tools and insights</li>
                    <li>🔬 <strong>A/B Testing:</strong> Access your a/b testing tools and insights</li>
                    <li>📊 <strong>Performance:</strong> Access your performance tools and insights</li>
                    <li>🤖 <strong>RAAMP Assistant:</strong> Access your raamp assistant tools and insights</li>
                </ul>
            </div>
            
            <div style="text-align: center;">
                <a href="http://localhost:8081/login" class="cta-button">Sign In Now</a>
            </div>
        </div>
        <div class="footer">
            <p><strong>RAAMP</strong> - Revolutionary AI-Powered Autonomous Marketing Platform</p>
            <p>© 2025 RAAMP. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""

PASSWORD_RESET_EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6; 
            color: #333;
            background-color: #f5f5f5;
            margin: 0;
            padding: 0;
        }
        .email-container { 
            max-width: 600px; 
            margin: 40px auto; 
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .header { 
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white; 
            padding: 40px 30px;
            text-align: center;
        }
        .content { 
            padding: 40px 30px;
        }
        .reset-button {
            display: inline-block;
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 15px 35px;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 600;
            margin: 20px 0;
        }
        .security-warning {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px 20px;
            margin: 25px 0;
            border-radius: 4px;
        }
        .footer { 
            background: #f8f9fa;
            text-align: center;
            padding: 25px;
            color: #6c757d;
            font-size: 13px;
            border-top: 1px solid #e9ecef;
        }
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header">
            <h1>🔐 Password Reset Request</h1>
        </div>
        <div class="content">
            <p>Hi <strong>{name}</strong>,</p>
            <p>We received a request to reset your password. Click the button below to create a new password:</p>
            
            <div style="text-align: center;">
                <a href="{resetUrl}" class="reset-button">Reset Password</a>
            </div>
            
            <p style="color: #666; font-size: 14px; margin-top: 20px;">
                Or copy and paste this link into your browser:<br>
                <a href="{resetUrl}" style="color: #667eea; word-break: break-all;">{resetUrl}</a>
            </p>
            
            <div class="security-warning">
                <strong>⚠️ Security Notice:</strong><br>
                This link will expire in 1 hour. If you didn't request a password reset, please ignore this email.
            </div>
        </div>
        <div class="footer">
            <p><strong>RAAMP</strong> - Revolutionary AI-Powered Autonomous Marketing Platform</p>
            <p>© 2025 RAAMP. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""

RESET_SUCCESS_EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6; 
            color: #333;
            background-color: #f5f5f5;
            margin: 0;
            padding: 0;
        }
        .email-container { 
            max-width: 600px; 
            margin: 40px auto; 
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .header { 
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            color: white; 
            padding: 40px 30px;
            text-align: center;
        }
        .content { 
            padding: 40px 30px;
        }
        .success-message {
            background: #d4edda;
            border-left: 4px solid #28a745;
            padding: 15px 20px;
            margin: 25px 0;
            border-radius: 4px;
            color: #155724;
        }
        .footer { 
            background: #f8f9fa;
            text-align: center;
            padding: 25px;
            color: #6c757d;
            font-size: 13px;
            border-top: 1px solid #e9ecef;
        }
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header">
            <h1>✅ Password Changed Successfully</h1>
        </div>
        <div class="content">
            <p>Hi <strong>{name}</strong>,</p>
            
            <div class="success-message">
                Your password has been successfully changed at <strong>{timestamp}</strong>.
            </div>
            
            <p>If you did not make this change, please contact our support team immediately.</p>
        </div>
        <div class="footer">
            <p><strong>RAAMP</strong> - Revolutionary AI-Powered Autonomous Marketing Platform</p>
            <p>© 2025 RAAMP. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""


class MailtrapService:
    """
    Email service using Mailtrap (SMTP or API)
    Handles OTP verification emails, welcome emails, password reset emails
    """
    
    def __init__(self):
        # Mailtrap Configuration from centralized config
        self.email_method = config.EMAIL_METHOD
        
        # SMTP Configuration
        self.smtp_host = config.MAILTRAP_SMTP_HOST
        self.smtp_port = config.MAILTRAP_SMTP_PORT
        self.smtp_username = config.MAILTRAP_SMTP_USERNAME
        self.smtp_password = config.MAILTRAP_SMTP_PASSWORD
        
        # API Configuration
        self.api_token = config.MAILTRAP_API_TOKEN
        self.api_endpoint = config.MAILTRAP_ENDPOINT
        
        # Sender info
        self.sender_email = config.SENDER_EMAIL
        self.sender_name = config.SENDER_NAME
        
        # Fallback to console printing if no credentials
        self.use_console = (self.email_method == "smtp" and not self.smtp_username) or \
                          (self.email_method == "api" and not self.api_token)
    
    def _send_email_smtp(self, to_email: str, subject: str, html_content: str, text_content: str) -> bool:
        """Send email via SMTP with retry logic"""
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                print(f"📧 SMTP attempt {attempt + 1}/{max_retries} to {to_email}")
                
                # Create message
                msg = MIMEMultipart('alternative')
                msg['Subject'] = subject
                msg['From'] = f"{self.sender_name} <{self.sender_email}>"
                msg['To'] = to_email
                
                # Attach plain text and HTML versions
                part1 = MIMEText(text_content, 'plain')
                part2 = MIMEText(html_content, 'html')
                msg.attach(part1)
                msg.attach(part2)
                
                # Send via SMTP with timeout
                import ssl
                context = ssl.create_default_context()

                # Choose secure connection method based on port
                import traceback

                if self.smtp_port == 465:
                    # SMTPS (implicit TLS)
                    with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, timeout=10, context=context) as server:
                        # Enable verbose SMTP debug to stdout for diagnosis
                        server.set_debuglevel(1)
                        server.login(self.smtp_username, self.smtp_password)
                        server.sendmail(self.sender_email, to_email, msg.as_string())
                else:
                    # Plain SMTP with STARTTLS
                    with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                        # Enable verbose SMTP debug to stdout for diagnosis
                        server.set_debuglevel(1)
                        # Ensure EHLO/HELO
                        try:
                            server.ehlo()
                        except Exception:
                            pass
                        server.starttls(context=context)
                        try:
                            server.ehlo()
                        except Exception:
                            pass
                        server.login(self.smtp_username, self.smtp_password)
                        server.sendmail(self.sender_email, to_email, msg.as_string())
                
                print(f"✅ Email sent via SMTP to {to_email}: {subject}")
                return True
                
            except Exception as e:
                print(f"❌ SMTP error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    print(f"⏳ Retrying in {retry_delay} seconds...")
                    import time
                    time.sleep(retry_delay)
                else:
                    print(f"❌ All SMTP attempts failed for {to_email}")
                    # Print OTP to console as fallback
                    if "Verification code" in text_content or "OTP" in subject:
                        print("\n" + "="*70)
                        print(f"⚠️  EMAIL FAILED - OTP FALLBACK")
                        print(f"📧 To: {to_email}")
                        print(f"📝 Subject: {subject}")
                        print("="*70 + "\n")
                    return False
        
        return False
    
    def _send_email(self, to_email: str, subject: str, html_content: str, text_content: str) -> bool:
        """
        Internal method to send email via Mailtrap (SMTP or API)
        
        Args:
            to_email: Recipient email
            subject: Email subject
            html_content: HTML email body
            text_content: Plain text fallback
            
        Returns:
            True if sent successfully
        """
        try:
            if self.use_console:
                # Development mode - print to console
                print(f"\n{'='*60}")
                print(f"📧 EMAIL (Console Mode)")
                print(f"{'='*60}")
                print(f"To: {to_email}")
                print(f"From: {self.sender_email}")
                print(f"Subject: {subject}")
                print(f"\n{text_content}")
                print(f"{'='*60}\n")
                return True
            
            # Use SMTP or API based on configuration
            if self.email_method == "smtp":
                return self._send_email_smtp(to_email, subject, html_content, text_content)
            
            # Send via Mailtrap API
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "from": {
                    "email": self.sender_email,
                    "name": self.sender_name
                },
                "to": [
                    {
                        "email": to_email
                    }
                ],
                "subject": subject,
                "text": text_content,
                "html": html_content,
                "category": "Email Verification"
            }
            
            response = requests.post(
                self.api_endpoint,
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.ok:
                print(f"✅ Email sent to {to_email}: {subject} (API)")
                return True
            else:
                print(f"❌ Mailtrap API error {response.status_code}: {response.text}")
                # Fallback to console
                print(f"\n📧 EMAIL CONTENT:\nTo: {to_email}\nSubject: {subject}\n{text_content}\n")
                return False
            
        except Exception as e:
            import traceback
            print(f"❌ Failed to send email: {e}")
            print(traceback.format_exc())
            # Fallback to console in case of error
            print(f"\n📧 EMAIL CONTENT:\nTo: {to_email}\nSubject: {subject}\n{text_content}\n")
            return False
    
    async def send_verification_email(self, to_email: str, name: str, otp_code: str) -> bool:
        """
        Send OTP verification email using HTML template (Non-blocking)
        
        Args:
            to_email: User's email address
            name: User's name/username
            otp_code: 6-digit OTP code
            
        Returns:
            True if sent successfully
        """
        print(f"🔔 send_verification_email called: to={to_email}, name={name}, otp={otp_code}")
        
        subject = "Verify Your Email - RAAMP"
        
        # Use template with placeholder replacement
        html_content = VERIFICATION_EMAIL_TEMPLATE.replace("{verificationCode}", otp_code).replace("{name}", name)
        
        text_content = f"""
        Hi {name},

        Welcome to RAAMP! Please verify your email address using the code below:

        VERIFICATION CODE: {otp_code}

        This code expires in 24 hours.

        If you didn't create a RAAMP account, please ignore this email.

        ---
        RAAMP Team
        """
        
        print(f"📧 Attempting to send email to {to_email} via {self.email_method}")
        
        # Run email sending in executor to prevent blocking
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        try:
            loop = asyncio.get_event_loop()
            executor = ThreadPoolExecutor(max_workers=1)
            # Set 10 second timeout for email sending
            result = await asyncio.wait_for(
                loop.run_in_executor(executor, self._send_email, to_email, subject, html_content, text_content),
                timeout=10.0
            )
            print(f"📬 Email send result: {result}")
            return result
        except asyncio.TimeoutError:
            print(f"⚠️ Email sending timed out for {to_email}, but continuing...")
            # Don't fail signup if email times out - user can resend
            return True
        except Exception as e:
            print(f"⚠️ Email sending failed for {to_email}: {e}, but continuing...")
            # Don't fail signup if email fails - user can resend
            return True
    
    async def send_welcome_email(self, to_email: str, name: str) -> bool:
        """
        Send welcome email after successful verification
        
        Args:
            to_email: User's email address
            name: User's name/username
            
        Returns:
            True if sent successfully
        """
        subject = "Welcome to RAAMP! 🎉"
        
        # Use template with placeholder replacement
        html_content = WELCOME_EMAIL_TEMPLATE.replace("{name}", name)
        
        text_content = f"""
        Hi {name},

        Your email has been successfully verified! You're now ready to explore RAAMP.

        What you can do with RAAMP:
        - Geo-Intent: Access your geo-intent tools and insights
        - Creative Studio: Access your creative studio tools and insights
        - Trend Arbitrage: Access your trend arbitrage tools and insights
        - A/B Testing: Access your a/b testing tools and insights
        - Performance: Access your performance tools and insights
        - RAAMP Assistant: Access your raamp assistant tools and insights

        Sign in now: http://localhost:8081/login

        ---
        RAAMP Team
        """
        
        return self._send_email(to_email, subject, html_content, text_content)
    
    async def send_password_reset_email(self, to_email: str, name: str, reset_token: str) -> bool:
        """
        Send password reset email with reset link
        
        Args:
            to_email: User's email address
            name: User's name/username
            reset_token: Password reset token
            
        Returns:
            True if sent successfully
        """
        subject = "Reset Your Password - RAAMP"
        
        reset_url = f"http://localhost:8081/reset-password?token={reset_token}"
        
        # Use template with placeholder replacement
        html_content = PASSWORD_RESET_EMAIL_TEMPLATE.replace("{name}", name).replace("{resetUrl}", reset_url)
        
        text_content = f"""
        Hi {name},

        We received a request to reset your password.

        Reset your password using this link:
        {reset_url}

        This link will expire in 1 hour.

        If you didn't request a password reset, please ignore this email.

        ---
        RAAMP Team
        """
        
        return self._send_email(to_email, subject, html_content, text_content)
    
    async def send_reset_success_email(self, to_email: str, name: str) -> bool:
        """
        Send confirmation email after successful password reset
        
        Args:
            to_email: User's email address
            name: User's name/username
            
        Returns:
            True if sent successfully
        """
        subject = "Password Changed Successfully - RAAMP"
        
        timestamp = datetime.utcnow().strftime("%B %d, %Y at %I:%M %p UTC")
        
        # Use template with placeholder replacement
        html_content = RESET_SUCCESS_EMAIL_TEMPLATE.replace("{name}", name).replace("{timestamp}", timestamp)
        
        text_content = f"""
        Hi {name},

        Your password has been successfully changed at {timestamp}.

        If you did not make this change, please contact our support team immediately.

        ---
        RAAMP Team
        """
        
        return self._send_email(to_email, subject, html_content, text_content)
    
    async def send_custom_email(self, to_email: str, to_name: str, subject: str, html_content: str, text_content: str) -> bool:
        """
        Send a custom email with provided subject and content
        
        Args:
            to_email: Recipient's email address
            to_name: Recipient's name
            subject: Email subject line
            html_content: HTML email body
            text_content: Plain text email body
            
        Returns:
            True if sent successfully
        """
        return self._send_email(to_email, subject, html_content, text_content)






