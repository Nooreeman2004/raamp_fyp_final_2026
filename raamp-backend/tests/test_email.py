import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Mailtrap SMTP Sandbox credentials
SMTP_HOST = "sandbox.smtp.mailtrap.io"
SMTP_PORT = 2525
SMTP_USERNAME = "41576076e86242"
SMTP_PASSWORD = "e9e14836df233c"

# Email details
sender_email = "hello@demomailtrap.com"
sender_name = "RAAMP Test"
recipient_email = "test@example.com"  # Any email - it goes to Mailtrap inbox
subject = "Test Email from RAAMP"

# Create message
msg = MIMEMultipart('alternative')
msg['Subject'] = subject
msg['From'] = f"{sender_name} <{sender_email}>"
msg['To'] = recipient_email

# Plain text and HTML versions
text_content = """
Hi there,

This is a test email from RAAMP to verify SMTP configuration.

Your verification code is: 123456

This code expires in 24 hours.

---
RAAMP Team
"""

html_content = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .code { font-size: 32px; font-weight: bold; color: #667eea; letter-spacing: 8px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Test Email from RAAMP</h1>
        <p>This is a test email to verify SMTP configuration.</p>
        <p>Your verification code is:</p>
        <p class="code">123456</p>
        <p>This code expires in 24 hours.</p>
        <hr>
        <p><strong>RAAMP Team</strong></p>
    </div>
</body>
</html>
"""

# Attach both versions
part1 = MIMEText(text_content, 'plain')
part2 = MIMEText(html_content, 'html')
msg.attach(part1)
msg.attach(part2)

print("Sending test email via SMTP...")
print(f"Host: {SMTP_HOST}:{SMTP_PORT}")
print(f"Username: {SMTP_USERNAME}")
print(f"From: {sender_email}")
print(f"To: {recipient_email}")
print()

try:
    # Send via SMTP
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.set_debuglevel(1)  # Show SMTP conversation
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(sender_email, recipient_email, msg.as_string())
    
    print("\n✅ Email sent successfully!")
    print("Check your Mailtrap inbox at: https://mailtrap.io/inboxes")
    
except Exception as e:
    print(f"\n❌ Error sending email: {e}")
