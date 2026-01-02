"""
Admin request/response schemas.
"""

from pydantic import BaseModel


class UserUpdateRequest(BaseModel):
    is_active: bool | None = None
    role: str | None = None
    subscription_plan: str | None = None
    subscription_status: str | None = None


class EmailTemplateRequest(BaseModel):
    trigger: str
    subject: str
    body_html: str
    body_text: str
    variables: list[str] | None = None
    is_active: bool = True


class EmailTemplateUpdateRequest(BaseModel):
    subject: str | None = None
    body_html: str | None = None
    body_text: str | None = None
    variables: list[str] | None = None
    is_active: bool | None = None


class WebhookEndpointRequest(BaseModel):
    name: str
    url: str
    events: list[str]
    is_active: bool = True


class WebhookEndpointUpdateRequest(BaseModel):
    name: str | None = None
    url: str | None = None
    events: list[str] | None = None
    is_active: bool | None = None


class AdminNoteRequest(BaseModel):
    content: str
    is_pinned: bool = False


class ErrorResolveRequest(BaseModel):
    resolution_notes: str | None = None
