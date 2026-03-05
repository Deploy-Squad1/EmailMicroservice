import logging
import os
import smtplib
from email.message import EmailMessage

import jwt
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from jwt import PyJWTError
from pydantic import BaseModel, EmailStr, HttpUrl

load_dotenv(override=False)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("email-service")

app = FastAPI(title="EmailMicroservice")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["Authorization", "Content-type"],
)

JWT_SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
JWT_ALGORITHM = "HS256"

if not JWT_SECRET_KEY:
    logger.critical("DJANGO_SECRET_KEY environment variable isn't set")
    raise RuntimeError("DJANGO_SECRET_KEY environment isn't set")


def verify_jwt_from_cookie(request: Request):
    token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Missing access token",
        )

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["exp"]},
        )
    except PyJWTError as e:
        logger.error("JWT decode failed: %s", e)
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
        ) from e

    role = payload.get("role")

    if role != "Gold":
        raise HTTPException(status_code=403, detail="Forbidden")

    return payload


class EmailSendError(Exception):
    """Raised when sending an email fails."""


class InviteEmailRequest(BaseModel):
    """Request payload for sending invitation emails."""

    to_email: EmailStr
    invite_link: HttpUrl


class DailyPasswordRequest(BaseModel):
    """Request payload for sending daily password emails."""

    to_email: EmailStr
    # included by rotate-daily-password scheduler/cron from Core service
    daily_password: str
    # optional value provided by Core rotate-daily-password scheduler
    valid_until: str | None = None


@app.get("/health")
def health():
    return {"status": "ok"}


def send_email(to_email: str, subject: str, body: str):
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "25"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASS", "")
    from_email = os.getenv("FROM_EMAIL", "noreply@local")
    if not smtp_host:
        logger.critical("SMTP_HOST environment variable is not set")
        raise RuntimeError("SMTP_HOST environment variable is not set")
    msg = EmailMessage()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)
    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=5) as server:
            # Mailhog/local: SMTP_USER empty - no TLS/login
            # For real SMPT server TLS and port 587
            if smtp_user:
                server.starttls()
                server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        logger.info("Email successfully sent to %s", to_email)
    except (smtplib.SMTPException, OSError) as exc:
        logger.error("SMTP delivery failed: %s", exc)
        raise EmailSendError("Email delivery failed") from exc


def safe_send(to_email: str, subject: str, body: str):
    try:
        send_email(to_email, subject, body)
    except EmailSendError as exc:
        raise HTTPException(
            status_code=502,
            detail="Email delivery failed",
        ) from exc


@app.post("/send-invite")
def send_invite(
    payload: InviteEmailRequest,
    _=Depends(verify_jwt_from_cookie),
):
    body = "You've been invited.\n"
    body += f"Invitation link: {payload.invite_link}\n"
    safe_send(str(payload.to_email), "Your invitation", body)
    return {"sent": True}


@app.post("/send-daily-password")
def send_daily_password(
    payload: DailyPasswordRequest,
    _=Depends(verify_jwt_from_cookie),
):
    body = "Here is your daily password:\n"
    body += f"{payload.daily_password}\n"
    if payload.valid_until:
        body += f"\nValid until: {payload.valid_until}\n"
    safe_send(str(payload.to_email), "Daily password", body)
    return {"sent": True}
