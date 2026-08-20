from __future__ import annotations

import html
import json
from urllib.parse import urlparse
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.dependencies import CurrentPrincipal, assert_brand_access, assert_brand_manage_access, forbid_super_admin_brand_access, get_current_principal
from app.db.session import AsyncSessionLocal, get_db_session
from app.schemas.google_drive import (
    GoogleDriveAuthorizationResponse,
    GoogleDriveFileListResponse,
    GoogleDriveFileResponse,
)
from app.services.google_drive import GoogleDriveConfigurationError, GoogleDriveConnectionError, GoogleDriveService


router = APIRouter()


def _normalize_origin(value: str) -> str | None:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.path not in {"", "/"}:
        return None
    return f"{parsed.scheme}://{parsed.netloc}"


def _allowed_frontend_origins() -> set[str]:
    settings = get_settings()
    configured = [settings.frontend_base_url, *settings.cors_origins]
    return {origin for value in configured if (origin := _normalize_origin(value))}


def _request_frontend_origin(request: Request) -> str:
    configured_origin = _normalize_origin(get_settings().frontend_base_url)
    request_origin = _normalize_origin(request.headers.get("origin", ""))
    if request.headers.get("origin"):
        if request_origin and request_origin in _allowed_frontend_origins():
            return request_origin
        raise HTTPException(status_code=403, detail="Google Drive sign-in must start from an allowed frontend origin.")
    if configured_origin:
        return configured_origin
    raise HTTPException(status_code=503, detail="A valid frontend origin is required for Google Drive sign-in.")


def _popup_response(payload: dict[str, object], target_origin: str | None = None) -> HTMLResponse:
    frontend_origin = target_origin or _normalize_origin(get_settings().frontend_base_url)
    if not frontend_origin:
        raise HTTPException(status_code=503, detail="A valid frontend origin is required for Google Drive sign-in.")
    serialized_payload = json.dumps(payload).replace("<", "\\u003c")
    return HTMLResponse(
        "<!doctype html><html><head><title>Google Drive</title></head><body>"
        "<script>if(window.opener){window.opener.postMessage("
        + serialized_payload
        + ","
        + json.dumps(frontend_origin)
        + ");}window.setTimeout(function(){window.close();}, 150);</script>"
        "<p>Google Drive selection is complete. You can close this window.</p></body></html>"
    )


def _selected_file_ids(value: str | None) -> list[str]:
    if not value:
        return []
    selected: list[str] = []
    for file_id in value.split(","):
        normalized = file_id.strip()
        if (
            normalized
            and len(normalized) <= 255
            and normalized.replace("-", "").replace("_", "").isalnum()
            and normalized not in selected
        ):
            selected.append(normalized)
    return selected[:50]


@router.post("/brands/{brand_id}/google-drive/authorize", response_model=GoogleDriveAuthorizationResponse)
async def authorize_google_drive(
    brand_id: UUID,
    request: Request,
    allow_multiple: bool = Query(default=True),
    principal: CurrentPrincipal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> GoogleDriveAuthorizationResponse:
    forbid_super_admin_brand_access(principal)
    assert_brand_access(principal, brand_id)
    assert_brand_manage_access(principal)
    try:
        authorization_url, nonce = GoogleDriveService(session).create_authorization(
            principal.tenant_id,
            principal.user_id,
            brand_id,
            _request_frontend_origin(request),
            allow_multiple,
        )
    except GoogleDriveConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return GoogleDriveAuthorizationResponse(authorization_url=authorization_url, nonce=nonce)


@router.get("/google-drive/oauth/callback", include_in_schema=False)
async def google_drive_oauth_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    picked_file_ids: str | None = None,
) -> HTMLResponse:
    callback_origin: str | None = None
    if state:
        try:
            candidate = GoogleDriveService.callback_origin(state)
            callback_origin = candidate if candidate in _allowed_frontend_origins() else None
        except GoogleDriveConnectionError:
            pass
    if not state:
        return _popup_response({"type": "violyt:google-drive-oauth", "status": "error", "message": "Missing OAuth state."})
    if error:
        return _popup_response(
            {
                "type": "violyt:google-drive-oauth",
                "status": "cancelled" if error == "access_denied" else "error",
                "message": "Google Drive selection was cancelled." if error == "access_denied" else "Google Drive sign-in failed.",
            },
            callback_origin,
        )
    if not code:
        return _popup_response(
            {"type": "violyt:google-drive-oauth", "status": "error", "message": "Missing authorization code."},
            callback_origin,
        )
    try:
        async with AsyncSessionLocal() as session:
            nonce, brand_id = await GoogleDriveService(session).complete_authorization(code, state)
        selected_ids = _selected_file_ids(picked_file_ids)
        if not selected_ids:
            return _popup_response(
                {
                    "type": "violyt:google-drive-oauth",
                    "status": "cancelled",
                    "nonce": nonce,
                    "brandId": brand_id,
                    "message": "No Google Drive files were selected.",
                },
                callback_origin,
            )
        return _popup_response(
            {
                "type": "violyt:google-drive-oauth",
                "status": "picked",
                "nonce": nonce,
                "brandId": brand_id,
                "fileIds": selected_ids,
            },
            callback_origin,
        )
    except (GoogleDriveConfigurationError, GoogleDriveConnectionError) as exc:
        return _popup_response(
            {"type": "violyt:google-drive-oauth", "status": "error", "message": str(exc)},
            callback_origin,
        )


@router.get("/brands/{brand_id}/google-drive/files", response_model=GoogleDriveFileListResponse)
async def list_google_drive_files(
    brand_id: UUID,
    query: str = Query(default="", max_length=120),
    principal: CurrentPrincipal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> GoogleDriveFileListResponse:
    forbid_super_admin_brand_access(principal)
    assert_brand_access(principal, brand_id)
    assert_brand_manage_access(principal)
    try:
        files = await GoogleDriveService(session).list_files(principal.tenant_id, brand_id, principal.user_id, query)
    except (GoogleDriveConfigurationError, GoogleDriveConnectionError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return GoogleDriveFileListResponse(
        files=[
            GoogleDriveFileResponse(
                id=file.id,
                name=file.name,
                mime_type=file.mime_type,
                size=file.size,
                modified_time=file.modified_time,
                can_download=file.can_download,
            )
            for file in files
        ]
    )


@router.get("/brands/{brand_id}/google-drive/files/{file_id}/download")
async def download_google_drive_file(
    brand_id: UUID,
    file_id: str,
    principal: CurrentPrincipal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    forbid_super_admin_brand_access(principal)
    assert_brand_access(principal, brand_id)
    assert_brand_manage_access(principal)
    try:
        downloaded = await GoogleDriveService(session).download_file(principal.tenant_id, brand_id, principal.user_id, file_id)
    except (GoogleDriveConfigurationError, GoogleDriveConnectionError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    safe_filename = html.escape(downloaded.name, quote=True).replace("\r", "").replace("\n", "")
    return Response(
        content=downloaded.content,
        media_type=downloaded.mime_type,
        headers={"Content-Disposition": f'attachment; filename="{safe_filename}"', "X-Drive-File-Name": safe_filename},
    )