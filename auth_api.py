import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from firebase_admin import auth

from api_schemas import (
    GoogleFletAuthRequest,
    ProfileUpsertRequest,
    RecoveryCheckRequest,
    RecoveryResetPasswordRequest,
    RecoveryStartRequest,
)
from firebase_admin_init import get_auth_client, get_firebase_app
from firestore_service import (
    get_user_by_email,
    get_user_by_phone,
    upsert_user_profile,
)
from otp_email_service import send_email_otp
from otp_sms_service import check_sms_verification, start_sms_verification
from recovery_store import (
    create_email_otp_record,
    create_recovery_token_record,
    get_recovery_token_record,
    get_valid_email_otp,
    mark_email_otp_used,
    mark_recovery_token_used,
)
from security import (
    generate_otp_code,
    is_expired,
    normalize_email,
    normalize_phone_pe,
)

load_dotenv()
get_firebase_app()

app = FastAPI(title="Avoruna Auth API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"ok": True, "message": "Backend funcionando"}


@app.post("/auth/google/flet")
def auth_google_flet(payload: GoogleFletAuthRequest):
    """
    Recibe perfil ya autenticado por Flet/Google OAuth y crea un custom token en Firebase.
    """
    auth_client = get_auth_client()
    email = normalize_email(payload.email)
    display_name = payload.name.strip() or email

    try:
        user = auth_client.get_user_by_email(email)
        auth_client.update_user(
            user.uid,
            email=email,
            display_name=display_name,
            photo_url=payload.picture or None,
        )
    except auth.UserNotFoundError:
        user = auth_client.create_user(
            email=email,
            email_verified=payload.email_verified,
            display_name=display_name,
            photo_url=payload.picture or None,
        )

    custom_token = auth_client.create_custom_token(user.uid).decode("utf-8")

    return {
        "uid": user.uid,
        "email": email,
        "name": display_name,
        "custom_token": custom_token,
    }


@app.post("/profile/upsert")
def profile_upsert(payload: ProfileUpsertRequest):
    auth_client = get_auth_client()

    try:
        firebase_user = auth_client.get_user(payload.uid)
    except Exception:
        raise HTTPException(status_code=404, detail="Usuario de Firebase no encontrado")

    if payload.firebase_id_token:
        try:
            decoded = auth_client.verify_id_token(payload.firebase_id_token)
            if decoded.get("uid") != payload.uid:
                raise HTTPException(status_code=403, detail="UID no coincide con el token")
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=401, detail="ID token inválido")

    if firebase_user.email and normalize_email(firebase_user.email) != normalize_email(payload.email):
        raise HTTPException(status_code=400, detail="El correo no coincide con Firebase Auth")

    saved_profile = upsert_user_profile(payload.model_dump())
    return {"ok": True, "profile": saved_profile}


@app.post("/recovery/start")
def recovery_start(payload: RecoveryStartRequest):
    identifier = (payload.identifier or "").strip()

    if payload.channel == "email":
        email = normalize_email(identifier)
        profile = get_user_by_email(email)
        if not profile:
            raise HTTPException(status_code=404, detail="No existe una cuenta asociada a ese correo")

        code = generate_otp_code(6)
        create_email_otp_record(
            uid=profile["uid"],
            identifier=email,
            code=code,
            channel="email",
        )
        send_email_otp(email, code)
        return {"ok": True, "message": "Código enviado al correo"}

    if payload.channel == "sms":
        phone_e164 = normalize_phone_pe(identifier)
        profile = get_user_by_phone(phone_e164)
        if not profile:
            raise HTTPException(status_code=404, detail="No existe una cuenta asociada a ese teléfono")

        verification = start_sms_verification(phone_e164)
        return {
            "ok": True,
            "message": "Código enviado por SMS",
            "status": verification.status,
        }

    raise HTTPException(status_code=400, detail="Canal no válido")


@app.post("/recovery/check")
def recovery_check(payload: RecoveryCheckRequest):
    identifier = (payload.identifier or "").strip()
    code = (payload.code or "").strip()

    if payload.channel == "email":
        email = normalize_email(identifier)
        doc_id, otp_data = get_valid_email_otp(email, "email")

        if not otp_data:
            raise HTTPException(status_code=400, detail="No hay un código pendiente para ese correo")

        if is_expired(otp_data["expires_at"]):
            raise HTTPException(status_code=400, detail="El código expiró")

        if otp_data["code"] != code:
            raise HTTPException(status_code=400, detail="Código inválido")

        mark_email_otp_used(doc_id)

        recovery_token = create_recovery_token_record(
            uid=otp_data["uid"],
            identifier=email,
            channel="email",
        )
        return {
            "ok": True,
            "message": "Código validado",
            "recovery_token": recovery_token,
        }

    if payload.channel == "sms":
        phone_e164 = normalize_phone_pe(identifier)
        check = check_sms_verification(phone_e164, code)

        if check.status != "approved":
            raise HTTPException(status_code=400, detail="Código inválido o expirado")

        profile = get_user_by_phone(phone_e164)
        if not profile:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        recovery_token = create_recovery_token_record(
            uid=profile["uid"],
            identifier=phone_e164,
            channel="sms",
        )
        return {
            "ok": True,
            "message": "Código validado",
            "recovery_token": recovery_token,
        }

    raise HTTPException(status_code=400, detail="Canal no válido")


@app.post("/recovery/reset-password")
def recovery_reset_password(payload: RecoveryResetPasswordRequest):
    token_data = get_recovery_token_record(payload.recovery_token)

    if not token_data:
        raise HTTPException(status_code=400, detail="Token de recuperación inválido")

    if token_data.get("used"):
        raise HTTPException(status_code=400, detail="El token ya fue utilizado")

    if is_expired(token_data["expires_at"]):
        raise HTTPException(status_code=400, detail="El token expiró")

    new_password = (payload.new_password or "").strip()
    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 8 caracteres")

    try:
        auth.update_user(token_data["uid"], password=new_password)
        auth.revoke_refresh_tokens(token_data["uid"])
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"No se pudo actualizar la contraseña: {ex}")

    mark_recovery_token_used(payload.recovery_token)
    return {"ok": True, "message": "Contraseña actualizada correctamente"}
