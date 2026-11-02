from firebase_admin import auth

from firebase_admin_init import get_firestore_client
from security import normalize_email, normalize_phone_pe, utc_now


def upsert_user_profile(payload: dict):
    db = get_firestore_client()

    uid = payload["uid"]
    email = normalize_email(payload["email"])
    phone_e164 = normalize_phone_pe(payload["phone_e164"])

    doc_ref = db.collection("users").document(uid)
    existing = doc_ref.get()
    now = utc_now().isoformat()

    data = {
        "uid": uid,
        "full_name": payload["full_name"].strip(),
        "email": email,
        "phone_e164": phone_e164,
        "farm_location": payload.get("farm_location", "").strip(),
        "avocado_variety": payload.get("avocado_variety", "").strip(),
        "auth_provider": payload["auth_provider"],
        "email_verified": False,
        "phone_verified": False,
        "status": "active",
        "updated_at": now,
    }

    try:
        firebase_user = auth.get_user(uid)
        data["email_verified"] = bool(getattr(firebase_user, "email_verified", False))
        data["display_name"] = getattr(firebase_user, "display_name", "") or payload["full_name"].strip()
        data["photo_url"] = getattr(firebase_user, "photo_url", "") or ""
    except Exception:
        data["display_name"] = payload["full_name"].strip()
        data["photo_url"] = ""

    if not existing.exists:
        data["created_at"] = now

    doc_ref.set(data, merge=True)
    return doc_ref.get().to_dict()


def get_user_by_uid(uid: str):
    db = get_firestore_client()
    doc = db.collection("users").document(uid).get()
    return doc.to_dict() if doc.exists else None


def get_user_by_email(email: str):
    db = get_firestore_client()
    email = normalize_email(email)

    docs = db.collection("users").where("email", "==", email).limit(1).stream()
    for doc in docs:
        return doc.to_dict()
    return None


def get_user_by_phone(phone_e164: str):
    db = get_firestore_client()
    phone_e164 = normalize_phone_pe(phone_e164)

    docs = db.collection("users").where("phone_e164", "==", phone_e164).limit(1).stream()
    for doc in docs:
        return doc.to_dict()
    return None
