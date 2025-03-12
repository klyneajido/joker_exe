import smtplib
import os
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Email Config
my_email = "ysoserious135@gmail.com"
my_password = os.getenv("MY_PASSWORD")
receiver_email = "andriqklyne.ajido@lorma.edu"
subject = "This is ad"
body = "This is a sample text"

# Print credentials for debugging
print(f"Email: {my_email}")
print(f"Password: {my_password}")

# Create the email
msg = MIMEText(body)
msg['Subject'] = subject
msg['To'] = receiver_email
msg['From'] = my_email

server = None
try:
    server = smtplib.SMTP('smtp.gmail.com', 587)
    print("Connecting...")
    server.starttls()
    print("TLS running")
    server.login(my_email, my_password)
    print("Logged in successfully")
    server.send_message(msg)
    print("Email sent successfully")
except Exception as e:
    print(f"Failed to send email: {e}")
finally:
    if server:
        server.quit()
        print("Server connection closed")
    else:
        print("Server was never initialized")