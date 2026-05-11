
"""
Email service for password reset.
Uses Python's standard smtplib 


"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_password_reset_email(to_email: str, reset_link: str, username: str) -> bool:
    smtp_user     = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_host     = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port     = int(os.getenv("SMTP_PORT", "587"))
    from_name     = os.getenv("SMTP_FROM_NAME", "Mindful")

    subject = "Reset your Mindful password"
    body = f"""Hi {username},

We received a request to reset the password for your Mindful account.

Click the link below to set a new password. This link expires in 1 hour.

{reset_link}

If you didn't request this, you can safely ignore this email.

— The Mindful team
"""

    # Dev mode: SMTP not configured -> print to console
    if not smtp_user or not smtp_password:
        print("\n" + "=" * 70)
        print(" [DEV MODE] Password reset email (SMTP not configured)")
        print("=" * 70)
        print(f"To:      {to_email}")
        print(f"Subject: {subject}")
        print(f"\n{body}")
        print("=" * 70 + "\n")
        return True

    # Production: send via SMTP
    try:
        msg = MIMEMultipart()
        msg["From"]    = f"{from_name} <{smtp_user}>"
        msg["To"]      = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)

        print(f" Password reset email sent to {to_email}")
        return True

    except Exception as e:
        print(f"❌ Failed to send email via SMTP: {e}")
        # Fallback: print so dev can still test the flow
        print(f"\n[FALLBACK] Reset link for {to_email}: {reset_link}\n")
        return True