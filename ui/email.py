try:
    print("About to send email...")
    await fm.send_message(message)
    print("Email sent successfully!")
except Exception as e:
    print("EMAIL ERROR:", str(e))