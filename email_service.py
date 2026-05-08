import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ── Your Gmail credentials ─────────────────────────────────────────────────────
GMAIL_ADDRESS  = "jsobrevinas6@gmail.com"   # <-- your Gmail address
GMAIL_APP_PWD  = "hvsdkumyiouqzzzx"    # <-- your 16-char App Password

# In-memory OTP store  {email: {"code": "123456", "used": False}}
_otp_store: dict = {}


def generate_otp(length: int = 6) -> str:
    """Generate a numeric OTP."""
    return "".join(random.choices(string.digits, k=length))


def send_otp(recipient_email: str) -> str:
    """
    Generate an OTP, send it to recipient_email, store it, and return the code.
    Raises RuntimeError if sending fails.
    """
    code = generate_otp()
    _otp_store[recipient_email.lower()] = {"code": code, "used": False}

    subject = "Majayjay Scholars – Email Verification Code"
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background: #F7FAFC; padding: 32px;">
        <div style="max-width:480px; margin:auto; background:#fff;
                    border-radius:12px; padding:32px;
                    border:1px solid #E2E8F0;">
            <h2 style="color:#667EEA; margin-bottom:8px;">
                🎓 Majayjay Scholars
            </h2>
            <p style="color:#4A5568; font-size:15px;">
                Hi there! Here is your email verification code:
            </p>
            <div style="text-align:center; margin:24px 0;">
                <span style="font-size:40px; font-weight:bold;
                             letter-spacing:12px; color:#667EEA;
                             background:#EBF4FF; padding:16px 28px;
                             border-radius:8px;">
                    {code}
                </span>
            </div>
            <p style="color:#718096; font-size:13px;">
                This code is valid for <strong>10 minutes</strong>.
                Do not share it with anyone.
            </p>
            <hr style="border:none; border-top:1px solid #E2E8F0; margin:20px 0;">
            <p style="color:#A0AEC0; font-size:12px;">
                If you did not request this, please ignore this email.
            </p>
        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = GMAIL_ADDRESS
    msg["To"]      = recipient_email
    msg.attach(MIMEText(body, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PWD)
            server.sendmail(GMAIL_ADDRESS, recipient_email, msg.as_string())
    except smtplib.SMTPAuthenticationError:
        raise RuntimeError(
            "Gmail authentication failed.\n"
            "Make sure you are using an App Password, not your regular password."
        )
    except Exception as e:
        raise RuntimeError(f"Failed to send email: {e}")

    return code


def verify_otp(email: str, code: str) -> bool:
    """
    Returns True if the code matches and has not been used yet.
    Marks the code as used on success.
    """
    record = _otp_store.get(email.lower())
    if not record:
        return False
    if record["used"]:
        return False
    if record["code"] == code.strip():
        record["used"] = True
        return True
    return False


def clear_otp(email: str):
    """Remove OTP record after successful registration."""
    _otp_store.pop(email.lower(), None)


# ── Quick test ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    test_email = input("Enter your email to test OTP sending: ").strip()
    try:
        code = send_otp(test_email)
        print(f"✅ OTP sent! Code (for testing): {code}")
        entered = input("Enter the code you received: ").strip()
        if verify_otp(test_email, entered):
            print("✅ OTP verified successfully!")
        else:
            print("❌ Wrong code.")
    except RuntimeError as e:
        print(f"❌ Error: {e}")