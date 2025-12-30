"""
Admin request/response schemas.
"""

from typing import Optional, List
from pydantic import BaseModel


class UserUpdateRequest(BaseModel):
    is_active: Optional[bool] = None
    role: Optional[str] = None
    subscription_plan: Optional[str] = None
    subscription_status: Optional[str] = None


class EmailTemplateRequest(BaseModel):
    trigger: str
    subject: str
    body_html: str
    body_text: str
    variables: Optional[List[str]] = None
    is_active: bool = True


class EmailTemplateUpdateRequest(BaseModel):
    subject: Optional[str] = None
    body_html: Optional[str] = None
    body_text: Optional[str] = None
    variables: Optional[List[str]] = None
    is_active: Optional[bool] = None


class WebhookEndpointRequest(BaseModel):
    name: str
    url: str
    events: List[str]
    is_active: bool = True


class WebhookEndpointUpdateRequest(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    events: Optional[List[str]] = None
    is_active: Optional[bool] = None


class AdminNoteRequest(BaseModel):
    content: str
    is_pinned: bool = False


class ErrorResolveRequest(BaseModel):
    resolution_notes: Optional[str] = None
