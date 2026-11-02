import re
import secrets
from datetime import datetime, timedelta, timezone


def utc_now():
    return datetime.now(timezone.utc)


def make_expiry(minutes: int):
    return utc_now() + timedelta(minutes=minutes)


def is_expired(expiry_iso: str) -> bool:
    expiry = datetime.fromisoformat(expiry_iso)
    return utc_now() > expiry


def generate_otp_code(length: int = 6) -> str:
    digits = "0123456789"
    return "".join(secrets.choice(digits) for _ in range(length))


def generate_recovery_token() -> str:
    return secrets.token_urlsafe(32)


def normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def normalize_phone_pe(phone: str) -> str:
    """
    Convierte a E.164 para Perú.
    Ejemplos:
    922196988 -> +51922196988
    +51922196988 -> +51922196988
    51 922 196 988 -> +51922196988
    """
    raw = re.sub(r"[^\d+]", "", (phone or "").strip())

    if raw.startswith("+"):
        digits = "+" + re.sub(r"\D", "", raw)
        return digits

    digits = re.sub(r"\D", "", raw)

    if digits.startswith("51") and len(digits) >= 11:
        return f"+{digits}"

    if len(digits) == 9:
        return f"+51{digits}"

    if len(digits) == 11 and digits.startswith("51"):
        return f"+{digits}"

    return f"+{digits}" if digits else ""
