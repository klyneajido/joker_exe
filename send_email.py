import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Email Config
my_email = "andriqklyne.ajido@lorma.edu" 
receiver_email = "ajido.andriqklyne@gmail.com"
subject = "ACCESS LORMA"

# Plain text version (fallback)
plain_body = """
Dear Student,

Greetings with a LORMA smile!                                    

This is just a gentle reminder of the upcoming 4th installment due to your Tuition and Miscellaneous fees amounting to Php   6,824.72

Kindly pay on or before May 31, 2023 to avoid the 5% late payment charges and please note that you should pay your remaining balance to avoid restrictions in your Midterm Grades.

We have alternative payment channels other than our Business Office. Just visit this link https://www.lormacolleges.com/payment-options. Please send your validated deposit slip to accounts@lorma.edu. You can also use this link https://access.lorma.edu/index.php?g=601 to send us the notification of your payment.

Thank you very much and keep safe.

-Business Office

Emails:
    For Payment: accounts@lorma.edu
    Other concerns: businessoffice@lorma.edu

Telephone: (072) 700-2500 loc 359

Mobile:
     CHS – 0919-066-2972
     CLI – 0919-066-2971
"""

html_body = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f4f4f4; /* Light gray background for email client */
        }
        .container {
            width: 100%;
            max-width: 600px;
            margin: 20px auto;
            background-color: #ffffff; /* White background for content */
            border: 1px solid #ddd;
            border-radius: 5px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        .header {
            background-color: #2e6a50; /* Green header */
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
            background-color: #2e6a50; /* Green footer */
            color: #ffffff;
            padding: 10px;
            text-align: center;
            border-bottom-left-radius: 5px;
            border-bottom-right-radius: 5px;
        }
        a {
            color: #2e6a50; /* Green links */
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
            <h2>Greetings with a LORMA Smile!</h2>
        </div>
        <div class="content">
            <p>Dear Student,</p>
            <p>This is a gentle reminder of the upcoming <strong>4th installment</strong> due for your Tuition and Miscellaneous fees amounting to <strong>Php 6,824.72</strong>.</p>
            <p>Kindly pay on or before <strong>May 31, 2023</strong> to avoid the 5% late payment charges. Please ensure your remaining balance is settled to avoid restrictions on your Midterm Grades.</p>
            <p>We offer alternative payment channels beyond our Business Office. Visit <a href="https://www.lormacolleges.com/payment-options">this link</a> for details. Send your validated deposit slip to <a href="mailto:accounts@lorma.edu">accounts@lorma.edu</a>. You can also notify us of your payment via <a href="https://access.lorma.edu/index.php?g=601">this link</a>.</p>
            <p>Thank you very much and keep safe!</p>
            <p>- Business Office</p>
        </div>
        <div class="footer">
            <p><strong>Emails:</strong><br>
            For Payment: <a href="mailto:accounts@lorma.edu" style="color: #ffffff;">accounts@lorma.edu</a><br>
            Other concerns: <a href="mailto:businessoffice@lorma.edu" style="color: #ffffff;">businessoffice@lorma.edu</a></p>
            <p><strong>Telephone:</strong> (072) 700-2500 loc 359</p>
            <p><strong>Mobile:</strong><br>
            CHS – 0919-066-2972<br>
            CLI – 0919-066-2971</p>
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