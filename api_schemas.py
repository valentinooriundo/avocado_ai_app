from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field


class GoogleFletAuthRequest(BaseModel):
    sub: str = Field(min_length=1)
    email: EmailStr
    name: str = ""
    given_name: str = ""
    family_name: str = ""
    picture: str = ""
    email_verified: bool = False


class ProfileUpsertRequest(BaseModel):
    uid: str = Field(min_length=1)
    full_name: str = Field(min_length=3)
    email: EmailStr
    phone_e164: str = Field(min_length=8)
    farm_location: str = ""
    avocado_variety: str = ""
    auth_provider: Literal["password", "google"]
    firebase_id_token: Optional[str] = None


class RecoveryStartRequest(BaseModel):
    channel: Literal["email", "sms"]
    identifier: str = Field(min_length=3)


class RecoveryCheckRequest(BaseModel):
    channel: Literal["email", "sms"]
    identifier: str = Field(min_length=3)
    code: str = Field(min_length=4, max_length=10)


class RecoveryResetPasswordRequest(BaseModel):
    recovery_token: str = Field(min_length=12)
    new_password: str = Field(min_length=8, max_length=128)
