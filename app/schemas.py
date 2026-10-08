from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional


class RecipientCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr


class GenerationJobCreate(BaseModel):
    event_name: str = Field(..., min_length=2, max_length=255)
    certificate_title: str = Field(
        default="Certificate of Completion",
        min_length=2,
        max_length=255
    )
    recipients: List[RecipientCreate] = Field(
        ...,
        min_length=1
    )


class CertificateResponse(BaseModel):
    id: int
    recipient_name: str
    recipient_email: str
    status: str
    file_path: Optional[str] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class JobResponse(BaseModel):
    id: int
    event_name: str
    certificate_title: str
    status: str

    total: int
    successful: int
    failed: int

    certificates: List[CertificateResponse] = []

    class Config:
        from_attributes = True