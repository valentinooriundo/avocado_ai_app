import os
import requests


BACKEND_URL = os.getenv("BACKEND_AUTH_URL", "http://127.0.0.1:8000").strip()


def upsert_user_profile_backend(
    *,
    uid: str,
    full_name: str,
    email: str,
    phone_e164: str,
    farm_location: str,
    avocado_variety: str,
    auth_provider: str,
    firebase_id_token: str | None = None,
):
    payload = {
        "uid": uid,
        "full_name": full_name,
        "email": email,
        "phone_e164": phone_e164,
        "farm_location": farm_location,
        "avocado_variety": avocado_variety,
        "auth_provider": auth_provider,
        "firebase_id_token": firebase_id_token,
    }

    response = requests.post(
        f"{BACKEND_URL}/profile/upsert",
        json=payload,
        timeout=20,
    )

    data = response.json()
    if not response.ok:
        raise Exception(data.get("detail", "No se pudo guardar el perfil"))

    return data
