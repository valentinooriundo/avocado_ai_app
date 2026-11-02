import os

from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
TWILIO_VERIFY_SERVICE_SID = os.getenv("TWILIO_VERIFY_SERVICE_SID", "").strip()


def _get_client():
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_VERIFY_SERVICE_SID]):
        raise RuntimeError("Faltan variables de Twilio en el .env")
    return Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


def start_sms_verification(phone_e164: str):
    client = _get_client()
    verification = client.verify.v2.services(
        TWILIO_VERIFY_SERVICE_SID
    ).verifications.create(
        to=phone_e164,
        channel="sms",
    )
    return verification


def check_sms_verification(phone_e164: str, code: str):
    client = _get_client()
    check = client.verify.v2.services(
        TWILIO_VERIFY_SERVICE_SID
    ).verification_checks.create(
        to=phone_e164,
        code=code,
    )
    return check
