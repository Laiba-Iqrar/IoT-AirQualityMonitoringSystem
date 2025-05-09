import smtplib
from email.message import EmailMessage
from datetime import datetime

EMAIL_ADDRESS = 'laibaiqrarahmedkhan@gmail.com'
EMAIL_PASSWORD = 'nggo xaaj prhx kvav'

def send_email_alert(subject, body):
    msg = EmailMessage()
    msg['Subject'] = f"[Sensor Alert] {subject}"
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = 'laibaiqrarahmedkhan@gmail.com'

    formatted_body = f"""
    Hello,

    This is an automated alert from your environmental monitoring system.

    📢 Alert: {subject}
    🕒 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

    Details:
    {body}

    Regards,
    MQ-135 Monitoring System
    """

    msg.set_content(formatted_body)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
        print(f"Email sent: {subject}")
    except Exception as e:
        print(f"Failed to send email: {e}")
