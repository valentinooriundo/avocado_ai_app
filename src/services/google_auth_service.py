import os
from dotenv import load_dotenv
from flet.auth.providers import GoogleOAuthProvider

load_dotenv()


def get_google_provider() -> GoogleOAuthProvider:
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    redirect_url = os.getenv("GOOGLE_REDIRECT_URL", "http://localhost:8550/oauth_callback")

    if not client_id:
        raise ValueError("Falta GOOGLE_CLIENT_ID en .env")
    if not client_secret:
        raise ValueError("Falta GOOGLE_CLIENT_SECRET en .env")

    return GoogleOAuthProvider(
        client_id=client_id,
        client_secret=client_secret,
        redirect_url=redirect_url,
    )
