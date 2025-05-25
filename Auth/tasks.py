from ProjectCore import settings
from django.core.mail import send_mail
from firebase_admin import messaging
from celery import shared_task
import supabase
import os
from datetime import datetime
supabase_client = supabase.create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
def upload_to_supabase(file,name):
    file_content = file.read()
    file_extension = os.path.splitext(file.name)[1]
    file_path = f"uploads/{file.name}+{name}+{datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}+{file_extension}"  
    response = supabase_client.storage.from_("cp2").upload(
        path=file_path,
        file=file_content,
        file_options={"content-type": file.content_type}
    )
    return {
        'size':len(file_content),
        'name':file.name,
        'created_at':datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'link':supabase_client.storage.from_("cp2").get_public_url(file_path)}
def upload_to_supabase_pdf(file,name):
    file_content = file.read()
    file_extension = os.path.splitext(file.name)[1]  
    file_path = f"uploads/{file.name}+{name}+{datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}+{file_extension}"  
    response = supabase_client.storage.from_("cp2").upload(
        path=file_path,
        file=file_content,
        file_options={"content-type": file.content_type}
    )
    return {
        'size':len(file_content),
        'name':file.name,
        'created_at':datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'link':supabase_client.storage.from_("cp2").get_public_url(file_path)}
def send_fcm_notification(device_token, title, body):
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        token=device_token
    )
    try:
        response = messaging.send(message)
        print(f'Successfully sent message: {response}')
        return True
    except Exception as e:
        print(f'Error sending message: {e}')
        return False
@shared_task
def sendemail(message,subject,receipnt,title,user):
     subject = subject 
     html_message = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Email Template</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
            margin: 0;
            padding: 0;
        }}
        .email-container {{
            max-width: 600px;
            margin: 20px auto;
            background-color: #ffffff;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }}
        .email-header {{
            background-color: #92E3A9;
            color: #ffffff;
            text-align: center;
            padding: 20px;
        }}
        .email-header h1 {{
            margin: 0;
            font-size: 24px;
            font-weight: bold;
        }}
        .email-body {{
            padding: 20px;
            color: #333333;
            font-size: 16px;
            line-height: 1.6;
        }}
        .email-footer {{
            text-align: center;
            padding: 20px;
            background-color: #f9f9f9;
            color: #777777;
            font-size: 14px;
        }}
        .email-footer a {{
            color: #92E3A9;
            text-decoration: none;
        }}
        .email-footer a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="email-container">
        <div class="email-header">
            <h1>APP NAME</h1>
        </div>
        <div class="email-body">
            <p>{message}</p>
            <p>If you have any questions or need assistance, please feel free to reach out to our support team at <a href="mailto:bouroumanamoundher@gmail.com">support@gmail.com</a>.</p>
            <p>We look forward to serving you!</p>
        </div>
        <div class="email-footer">
            <p>Best regards,</p>
            <p><strong>The Team</strong></p>
            <p><a href="https://example.com">Visit our website</a></p>
        </div>
    </div>
</body>
</html>
"""
     from_email = settings.DEFAULT_FROM_EMAIL
     recipient_list = receipnt
     send_mail(subject, title, from_email, recipient_list, html_message=html_message)
