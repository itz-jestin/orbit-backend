import datetime
from typing import Optional

import email_validator
from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email_deliverability(cls, v: str) -> str:
        # EmailStr only checks the format (name@domain.tld). It happily
        # accepts things like "jestinmonachan55@gmail.scam" because
        # that's syntactically valid. This extra check confirms the
        # domain actually exists and has mail servers (MX records),
        # which rejects fake/typo'd domains at registration time.
        try:
            info = email_validator.validate_email(v, check_deliverability=True)
        except email_validator.EmailNotValidError as e:
            raise ValueError(f"Enter a valid, real email address ({e})")
        return info.normalized


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    name: str
    email: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class HistoryItemOut(BaseModel):
    id: str
    query: str
    final_report: Optional[str] = None
    state_json: Optional[str] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class HistoryListItemOut(BaseModel):
    id: str
    query: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class SaveHistoryRequest(BaseModel):
    query: str
    final_report: Optional[str] = None
    state_json: Optional[str] = None