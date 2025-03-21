import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Email Config
my_email = "andriqklyne.ajido@lorma.edu"
receiver_email = "ajido.andriqklyne@gmail.com"
subject = "ACCESS Lormo"

# Plain text version (fallback)
plain_body = """
Dear Student,

We would like to meet with you at the Dean’s Office to discuss a matter that requires your attention.

We have received information that may need clarification on your part. We kindly request that you visit the office as soon as possible to ensure everything is properly addressed.

If you have any information related to this matter, please submit it through [this link](https://access.lormo.edu/index.php?g=601).

Your cooperation is highly appreciated.

Thank you and we look forward to hearing from you.

- SAO Office

Email:
    For inquiries: SAO@lormo.edu

Telephone: (072) 700-2340 loc 351

Mobile:
     CHS – 0919-236-2192
     CLI – 0949-066-3978

"""

# HTML version with updated message
html_body = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f4f4f4;
        }
        .container {
            width: 100%;
            max-width: 600px;
            margin: 20px auto;
            background-color: #ffffff;
            border: 1px solid #ddd;
            border-radius: 5px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        .header {
            background-color: #2e6a50;
            color: #ffffff;
            padding: 20px;
            text-align: center;
            border-top-left-radius: 5px;
            border-top-right-radius: 5px;
        }
        .content {
            padding: 20px;
            color: #333;
        }
        .footer {
            background-color: #2e6a50;
            color: #ffffff;
            padding: 10px;
            text-align: center;
            border-bottom-left-radius: 5px;
            border-bottom-right-radius: 5px;
        }
        a {
            color: #2e6a50;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>Follow-up from the Dean’s Office</h2>
        </div>
        <div class="content">
            <p>Dear Student,</p>
            <p>We would like to meet with you at the Dean’s Office to discuss a matter that requires your attention.</p>
            <p>We have received information that may need clarification on your part. We kindly request that you visit the office as soon as possible to ensure everything is properly addressed.</p>
            <p>If you have any information related to this matter, please submit it through <a href="https://access.lormo.edu/index.php?g=601">this link</a>.</p>
            <p>Your cooperation is highly appreciated.</p>
            <p>Thank you and we look forward to hearing from you.</p>
            <p>- SAO Office</p>
        </div>
        <div class="footer">
            <p><strong>Email:</strong><br>
            For inquiries: <a href="mailto:SAO@lormo.edu" style="color: #ffffff;">SAO@lormo.edu</a></p>
            <p><strong>Telephone:</strong> (072) 700-2340 loc 351</p>
            <p><strong>Mobile:</strong><br>
            CHS – 0919-236-2192<br>
            CLI – 0949-066-3978</p>
        </div>
    </div>
</body>
</html>
"""

# SendGrid API Key
api_key = os.getenv("SENDGRID_API_KEY")

# Create the email with both plain text and HTML content
message = Mail(
    from_email=my_email,
    to_emails=receiver_email,
    subject=subject,
    plain_text_content=plain_body,
    html_content=html_body
)

try:
    sg = SendGridAPIClient(api_key)
    response = sg.send(message)
    print(f"Email sent successfully! Status code: {response.status_code}")
except Exception as e:
    print(f"Failed to send email: {e}")
