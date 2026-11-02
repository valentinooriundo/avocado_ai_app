from firebase_admin_init import get_firestore_client
from security import generate_recovery_token, make_expiry, utc_now


def create_email_otp_record(uid: str, identifier: str, code: str, channel: str):
    db = get_firestore_client()
    doc_ref = db.collection("recovery_otps").document()

    data = {
        "uid": uid,
        "identifier": identifier,
        "channel": channel,
        "code": code,
        "status": "pending",
        "used": False,
        "created_at": utc_now().isoformat(),
        "expires_at": make_expiry(10).isoformat(),
    }

    doc_ref.set(data)
    return doc_ref.id, data


def get_valid_email_otp(identifier: str, channel: str):
    db = get_firestore_client()

    docs = list(
        db.collection("recovery_otps")
        .where("identifier", "==", identifier)
        .where("channel", "==", channel)
        .where("used", "==", False)
        .stream()
    )

    if not docs:
        return None, None

    docs_sorted = sorted(
        docs,
        key=lambda d: d.to_dict().get("created_at", ""),
        reverse=True,
    )

    doc = docs_sorted[0]
    return doc.id, doc.to_dict()


def mark_email_otp_used(doc_id: str):
    db = get_firestore_client()
    db.collection("recovery_otps").document(doc_id).set(
        {"used": True, "status": "approved"},
        merge=True,
    )


def create_recovery_token_record(uid: str, identifier: str, channel: str):
    db = get_firestore_client()
    token = generate_recovery_token()

    db.collection("recovery_tokens").document(token).set(
        {
            "uid": uid,
            "identifier": identifier,
            "channel": channel,
            "used": False,
            "created_at": utc_now().isoformat(),
            "expires_at": make_expiry(10).isoformat(),
        }
    )
    return token


def get_recovery_token_record(token: str):
    db = get_firestore_client()
    doc = db.collection("recovery_tokens").document(token).get()
    return doc.to_dict() if doc.exists else None


def mark_recovery_token_used(token: str):
    db = get_firestore_client()
    db.collection("recovery_tokens").document(token).set(
        {"used": True},
        merge=True,
    )
