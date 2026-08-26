from __future__ import annotations

from app.schemas.common import APIModel


class GoogleDriveAuthorizationResponse(APIModel):
    authorization_url: str
    nonce: str


class GoogleDriveFileResponse(APIModel):
    id: str
    name: str
    mime_type: str
    size: int | None = None
    modified_time: str | None = None
    can_download: bool = True


class GoogleDriveFileListResponse(APIModel):
    files: list[GoogleDriveFileResponse]
