import os
from dotenv import load_dotenv
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig

load_dotenv()


async def send_email(email: str, body: str, attachments: list[str] | None = None):

    username = os.getenv("MAIL_USERNAME")
    password = os.getenv("MAIL_PASSWORD")
    mail_from = os.getenv("MAIL_FROM")

    if not username or not password or not mail_from:
        raise RuntimeError("Email configuration is not fully set.")

    conf = ConnectionConfig(
        MAIL_USERNAME=username,
        MAIL_PASSWORD=password,
        MAIL_FROM=mail_from,
        MAIL_PORT=int(os.getenv("MAIL_PORT", "587")),
        MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.gmail.com"),
        MAIL_STARTTLS=os.getenv("MAIL_STARTTLS", "True").lower() in ("true", "1", "yes"),
        MAIL_SSL_TLS=os.getenv("MAIL_SSL_TLS", "False").lower() in ("true", "1", "yes"),
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True,
    )

    message = MessageSchema(
        subject="Monthly Expense Report",
        recipients=[email],
        body=body,
        subtype="html",
        attachments=attachments or [],
    )

    # Debug prints
    print("USERNAME:", username)
    print("PASSWORD LENGTH:", len(password))
    print("MAIL_FROM:", mail_from)
    print("MAIL_SERVER:", os.getenv("MAIL_SERVER"))
    print("MAIL_PORT:", os.getenv("MAIL_PORT"))

    fm = FastMail(conf)

    try:
        print("About to send email...")
        await fm.send_message(message)
        print("Email sent successfully!")
    except Exception as e:
        print("EMAIL ERROR:", str(e))