import os

import firebase_admin
from firebase_admin import auth, credentials, firestore
from dotenv import load_dotenv

load_dotenv()

_firebase_app = None


def get_firebase_app():
    global _firebase_app

    if _firebase_app is not None:
        return _firebase_app

    service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "serviceAccountKey.json").strip()

    if not os.path.isabs(service_account_path):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        service_account_path = os.path.join(base_dir, service_account_path)

    cred = credentials.Certificate(service_account_path)
    _firebase_app = firebase_admin.initialize_app(cred)
    return _firebase_app


def get_firestore_client():
    app = get_firebase_app()
    return firestore.client(app=app)


def get_auth_client():
    get_firebase_app()
    return auth
