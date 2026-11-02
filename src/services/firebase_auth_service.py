import os
import requests
from dotenv import load_dotenv

load_dotenv()


def sign_in_with_firebase_custom_token(custom_token: str) -> dict:
    api_key = os.getenv("FIREBASE_WEB_API_KEY")
    if not api_key:
        raise ValueError("Falta FIREBASE_WEB_API_KEY en .env")

    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key={api_key}"
    payload = {
        "token": custom_token,
        "returnSecureToken": True,
    }

    response = requests.post(url, json=payload, timeout=20)
    response.raise_for_status()
    return response.json()


def get_backend_auth_url() -> str:
    base_url = os.getenv("BACKEND_AUTH_URL")
    if not base_url:
        raise ValueError("Falta BACKEND_AUTH_URL en .env")
    return base_url.rstrip("/")
