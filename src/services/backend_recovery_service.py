import os
import requests


BACKEND_URL = os.getenv("BACKEND_AUTH_URL", "http://127.0.0.1:8000").strip()

def normalize_channel(channel: str) -> str:
    value = (channel or "").strip().lower()

    aliases = {
        "phone": "sms",
        "telefono": "sms",
        "teléfono": "sms",
        "correo": "email",
        "correo electrónico": "email",
    }

    value = aliases.get(value, value)

    if value not in {"email", "sms"}:
        raise ValueError("El canal debe ser 'email' o 'sms'")

    return value

def recovery_start(channel: str, identifier: str):
    channel = normalize_channel(channel)

    response = requests.post(
        f"{BACKEND_URL}/recovery/start",
        json={
            "channel": channel,
            "identifier": identifier,
        },
        timeout=20,
    )

    data = response.json()

    if not response.ok:
        detail = data.get("detail", "No se pudo enviar el código")
        raise Exception(str(detail))

    return data

def recovery_check(channel: str, identifier: str, code: str):
    channel = normalize_channel(channel)

    response = requests.post(
        f"{BACKEND_URL}/recovery/check",
        json={
            "channel": channel,
            "identifier": identifier,
            "code": code,
        },
        timeout=20,
    )

    data = response.json()

    if not response.ok:
        detail = data.get("detail", "No se pudo validar el código")
        raise Exception(str(detail))

    return data


def recovery_reset_password(recovery_token: str, new_password: str):
    response = requests.post(
        f"{BACKEND_URL}/recovery/reset-password",
        json={
            "recovery_token": recovery_token,
            "new_password": new_password,
        },
        timeout=20,
    )
    data = response.json()
    if not response.ok:
        raise Exception(data.get("detail", "No se pudo actualizar la contraseña"))
    return data
