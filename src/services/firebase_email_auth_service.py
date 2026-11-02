import os
import requests


class FirebaseEmailAuthError(Exception):
    pass


def _get_api_key() -> str:
    api_key = os.getenv("FIREBASE_WEB_API_KEY", "").strip()
    if not api_key:
        raise FirebaseEmailAuthError(
            "Falta FIREBASE_WEB_API_KEY en las variables de entorno."
        )
    return api_key


def _handle_response(response: requests.Response) -> dict:
    try:
        data = response.json()
    except Exception:
        raise FirebaseEmailAuthError("Respuesta inválida de Firebase.")

    if response.ok:
        return data

    error_code = data.get("error", {}).get("message", "AUTH_ERROR")
    raise FirebaseEmailAuthError(error_code)


def map_firebase_auth_error(error_code: str) -> str:
    mapping = {
        "EMAIL_EXISTS": "Ese correo ya está registrado.",
        "OPERATION_NOT_ALLOWED": "El acceso con correo y contraseña no está habilitado en Firebase.",
        "TOO_MANY_ATTEMPTS_TRY_LATER": "Demasiados intentos. Intenta más tarde.",
        "EMAIL_NOT_FOUND": "No existe una cuenta con ese correo.",
        "INVALID_PASSWORD": "La contraseña es incorrecta.",
        "INVALID_LOGIN_CREDENTIALS": "Correo o contraseña incorrectos.",
        "USER_DISABLED": "La cuenta fue deshabilitada.",
        "WEAK_PASSWORD": "La contraseña debe tener al menos 6 caracteres.",
        "INVALID_EMAIL": "El correo no es válido.",
        "MISSING_PASSWORD": "Ingresa una contraseña.",
        "MISSING_EMAIL": "Ingresa un correo electrónico.",
    }
    return mapping.get(error_code, f"Error de autenticación: {error_code}")


def register_with_email_password(email: str, password: str) -> dict:
    api_key = _get_api_key()
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={api_key}"

    payload = {
        "email": email.strip(),
        "password": password,
        "returnSecureToken": True,
    }

    response = requests.post(url, json=payload, timeout=20)
    return _handle_response(response)


def login_with_email_password(email: str, password: str) -> dict:
    api_key = _get_api_key()
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"

    payload = {
        "email": email.strip(),
        "password": password,
        "returnSecureToken": True,
    }

    response = requests.post(url, json=payload, timeout=20)
    return _handle_response(response)
