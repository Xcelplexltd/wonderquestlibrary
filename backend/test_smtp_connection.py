
import os
import smtplib
import ssl
import certifi
import truststore

host = os.environ.get("WQ_SMTP_HOST")
port = int(os.environ.get("WQ_SMTP_PORT", "465"))
username = os.environ.get("WQ_SMTP_USER")
password = os.environ.get("WQ_SMTP_PASSWORD")

if not all((host, username, password)):
    raise RuntimeError("SMTP configuration is incomplete")

try:
    with smtplib.SMTP_SSL(
        host,
        port,
        context=truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT),
        timeout=15,
    ) as smtp:
        smtp.login(username, password)

    print("Resend SMTP authentication successful")

except smtplib.SMTPAuthenticationError:
    print("SMTP authentication failed. Check Resend API key.")

except (OSError, smtplib.SMTPException) as exc:
    print(f"SMTP connection failed: {type(exc).__name__}")
