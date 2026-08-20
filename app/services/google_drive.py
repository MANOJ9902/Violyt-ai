from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
import secrets
from typing import Any
from urllib.parse import urlencode
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.crypto import decrypt_secret, encrypt_secret
from app.core.security import create_token, decode_token
from app.models.collaboration import GoogleDriveConnection


GOOGLE_DRIVE_PLATFORM = "google_drive"
GOOGLE_DRIVE_SCOPE = "https://www.googleapis.com/auth/drive.file"
GOOGLE_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_DRIVE_FILES_URL = "https://www.googleapis.com/drive/v3/files"

GOOGLE_WORKSPACE_EXPORTS = {
    "application/vnd.google-apps.document": (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".docx",
    ),
    "application/vnd.google-apps.presentation": (
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".pptx",
    ),
    "application/vnd.google-apps.drawing": ("image/png", ".png"),
}


class GoogleDriveConfigurationError(ValueError):
    pass


class GoogleDriveConnectionError(ValueError):
    pass


@dataclass(frozen=True)
class GoogleDriveFile:
    id: str
    name: str
    mime_type: str
    size: int | None
    modified_time: str | None
    can_download: bool


@dataclass(frozen=True)
class GoogleDriveDownloadedFile:
    name: str
    mime_type: str
    content: bytes


class GoogleDriveService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.settings = get_settings()

    def _configuration(self) -> tuple[str, str, str]:
        client_id = (self.settings.google_drive_client_id or "").strip()
        client_secret = (self.settings.google_drive_client_secret or "").strip()
        redirect_uri = (self.settings.google_drive_redirect_uri or "").strip()
        if not client_id or not client_secret or not redirect_uri:
            raise GoogleDriveConfigurationError(
                "Google Drive upload is not configured. Set the Google Drive OAuth client ID, secret, and redirect URI."
            )
        return client_id, client_secret, redirect_uri

    def create_authorization(
        self,
        tenant_id: UUID,
        user_id: UUID,
        brand_id: UUID,
        return_origin: str,
        allow_multiple: bool = True,
    ) -> tuple[str, str]:
        client_id, _, redirect_uri = self._configuration()
        nonce = secrets.token_urlsafe(24)
        state = create_token(
            str(user_id),
            expires_delta=timedelta(minutes=10),
            extra={
                "typ": "google_drive_oauth",
                "tenant_id": str(tenant_id),
                "brand_id": str(brand_id),
                "nonce": nonce,
                "return_origin": return_origin,
            },
        )
        query = urlencode(
            {
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": GOOGLE_DRIVE_SCOPE,
                "access_type": "offline",
                # Google One Pick accepts only drive.file. Do not merge an older
                # Drive grant (for example drive.readonly) into this request.
                "include_granted_scopes": "false",
                "prompt": "consent select_account",
                "trigger_onepick": "true",
                "allow_multiple": "true" if allow_multiple else "false",
                "allow_folder_selection": "false",
                "state": state,
            }
        )
        return f"{GOOGLE_AUTHORIZE_URL}?{query}", nonce

    @staticmethod
    def callback_origin(state: str) -> str:
        try:
            payload = decode_token(state)
            if payload.get("typ") != "google_drive_oauth":
                raise ValueError("Unexpected OAuth state")
            return str(payload.get("return_origin") or "")
        except Exception as exc:
            raise GoogleDriveConnectionError("The Google Drive sign-in session is invalid or has expired.") from exc


    async def complete_authorization(self, code: str, state: str) -> tuple[str, str]:
        try:
            payload = decode_token(state)
            if payload.get("typ") != "google_drive_oauth":
                raise ValueError("Unexpected OAuth state")
            tenant_id = UUID(str(payload["tenant_id"]))
            brand_id = UUID(str(payload["brand_id"]))
            user_id = UUID(str(payload["sub"]))
        except Exception as exc:
            raise GoogleDriveConnectionError("The Google Drive sign-in session is invalid or has expired.") from exc

        _, client_secret, redirect_uri = self._configuration()
        client_id = self.settings.google_drive_client_id or ""
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(
                    GOOGLE_TOKEN_URL,
                    data={
                        "code": code,
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "redirect_uri": redirect_uri,
                        "grant_type": "authorization_code",
                    },
                )
        except httpx.HTTPError as exc:
            raise GoogleDriveConnectionError("Google Drive could not complete the sign-in request. Please try again.") from exc
        if response.is_error:
            raise GoogleDriveConnectionError("Google Drive sign-in could not be completed.")
        try:
            token_payload = response.json()
        except ValueError as exc:
            raise GoogleDriveConnectionError("Google Drive returned an invalid sign-in response. Please try again.") from exc
        access_token = str(token_payload.get("access_token") or "")
        if not access_token:
            raise GoogleDriveConnectionError("Google Drive did not return an access token.")

        connection = await self._find_connection(tenant_id, brand_id, user_id)
        if not connection:
            connection = GoogleDriveConnection(
                tenant_id=tenant_id,
                brand_space_id=brand_id,
                user_id=user_id,
                access_token_encrypted=encrypt_secret(access_token),
                refresh_token_encrypted=encrypt_secret(token_payload.get("refresh_token")),
                scopes=str(token_payload.get("scope") or GOOGLE_DRIVE_SCOPE).split(),
                is_connected=True,
            )
            self.session.add(connection)
        else:
            connection.access_token_encrypted = encrypt_secret(access_token)
            refresh_token = token_payload.get("refresh_token")
            if refresh_token:
                connection.refresh_token_encrypted = encrypt_secret(str(refresh_token))
            connection.scopes = str(token_payload.get("scope") or GOOGLE_DRIVE_SCOPE).split()
            connection.is_connected = True
        await self.session.commit()
        return str(payload.get("nonce") or ""), str(brand_id)

    async def _find_connection(
        self,
        tenant_id: UUID,
        brand_id: UUID,
        user_id: UUID,
    ) -> GoogleDriveConnection | None:
        result = await self.session.execute(
            select(GoogleDriveConnection).where(
                GoogleDriveConnection.tenant_id == tenant_id,
                GoogleDriveConnection.brand_space_id == brand_id,
                GoogleDriveConnection.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def _connection(self, tenant_id: UUID, brand_id: UUID, user_id: UUID) -> GoogleDriveConnection:
        connection = await self._find_connection(tenant_id, brand_id, user_id)
        if not connection or not connection.is_connected:
            raise GoogleDriveConnectionError("Connect Google Drive before selecting files.")
        return connection

    async def _access_token(self, connection: GoogleDriveConnection) -> str:
        token = decrypt_secret(connection.access_token_encrypted)
        if not token:
            raise GoogleDriveConnectionError("Reconnect Google Drive to continue.")
        return token

    async def _refresh_access_token(self, connection: GoogleDriveConnection) -> str:
        client_id, client_secret, _ = self._configuration()
        refresh_token = decrypt_secret(connection.refresh_token_encrypted)
        if not refresh_token:
            raise GoogleDriveConnectionError("Reconnect Google Drive to continue.")
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                },
            )
        if response.is_error:
            connection.is_connected = False
            await self.session.commit()
            raise GoogleDriveConnectionError("Google Drive access expired. Connect it again to continue.")
        token = str(response.json().get("access_token") or "")
        if not token:
            raise GoogleDriveConnectionError("Google Drive access could not be refreshed.")
        connection.access_token_encrypted = encrypt_secret(token)
        await self.session.commit()
        return token

    async def _request(self, connection: GoogleDriveConnection, method: str, url: str, **kwargs: Any) -> httpx.Response:
        token = await self._access_token(connection)
        headers = {**kwargs.pop("headers", {}), "Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.request(method, url, headers=headers, **kwargs)
            if response.status_code != 401:
                return response
        refreshed_token = await self._refresh_access_token(connection)
        headers["Authorization"] = f"Bearer {refreshed_token}"
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            return await client.request(method, url, headers=headers, **kwargs)

    async def list_files(self, tenant_id: UUID, brand_id: UUID, user_id: UUID, query: str = "") -> list[GoogleDriveFile]:
        connection = await self._connection(tenant_id, brand_id, user_id)
        filters = ["trashed = false"]
        if query.strip():
            escaped_query = query.strip().replace("'", "\\'")
            filters.append(f"name contains '{escaped_query}'")
        response = await self._request(
            connection,
            "GET",
            GOOGLE_DRIVE_FILES_URL,
            params={
                "q": " and ".join(filters),
                "pageSize": 100,
                "orderBy": "modifiedTime desc",
                "fields": "files(id,name,mimeType,size,modifiedTime,capabilities/canDownload)",
                "supportsAllDrives": "true",
                "includeItemsFromAllDrives": "true",
            },
        )
        if response.is_error:
            raise GoogleDriveConnectionError("Google Drive files could not be loaded.")
        files = []
        for item in response.json().get("files", []):
            files.append(
                GoogleDriveFile(
                    id=str(item.get("id") or ""),
                    name=str(item.get("name") or "Untitled"),
                    mime_type=str(item.get("mimeType") or "application/octet-stream"),
                    size=int(item["size"]) if str(item.get("size") or "").isdigit() else None,
                    modified_time=str(item.get("modifiedTime")) if item.get("modifiedTime") else None,
                    can_download=bool((item.get("capabilities") or {}).get("canDownload", False)),
                )
            )
        return files

    async def download_file(self, tenant_id: UUID, brand_id: UUID, user_id: UUID, file_id: str) -> GoogleDriveDownloadedFile:
        connection = await self._connection(tenant_id, brand_id, user_id)
        metadata_response = await self._request(
            connection,
            "GET",
            f"{GOOGLE_DRIVE_FILES_URL}/{file_id}",
            params={"fields": "id,name,mimeType,size,capabilities/canDownload", "supportsAllDrives": "true"},
        )
        if metadata_response.status_code == 404:
            raise GoogleDriveConnectionError("The selected Google Drive file is no longer available.")
        if metadata_response.is_error:
            raise GoogleDriveConnectionError("Google Drive file details could not be loaded.")
        metadata = metadata_response.json()
        if not bool((metadata.get("capabilities") or {}).get("canDownload", False)):
            raise GoogleDriveConnectionError("You do not have permission to download this Google Drive file.")

        declared_size = metadata.get("size")
        if str(declared_size or "").isdigit() and int(declared_size) > self.settings.upload_max_file_bytes:
            raise GoogleDriveConnectionError("The selected Google Drive file exceeds the configured upload size limit.")

        source_mime_type = str(metadata.get("mimeType") or "application/octet-stream")
        filename = str(metadata.get("name") or "download")
        export = GOOGLE_WORKSPACE_EXPORTS.get(source_mime_type)
        if export:
            mime_type, suffix = export
            filename = f"{Path(filename).stem}{suffix}"
            response = await self._request(
                connection,
                "GET",
                f"{GOOGLE_DRIVE_FILES_URL}/{file_id}/export",
                params={"mimeType": mime_type},
            )
        elif source_mime_type.startswith("application/vnd.google-apps"):
            raise GoogleDriveConnectionError("This Google Workspace file type is not supported for upload.")
        else:
            mime_type = source_mime_type
            response = await self._request(
                connection,
                "GET",
                f"{GOOGLE_DRIVE_FILES_URL}/{file_id}",
                params={"alt": "media", "acknowledgeAbuse": "false", "supportsAllDrives": "true"},
            )
        if response.is_error:
            raise GoogleDriveConnectionError("Google Drive could not download the selected file.")
        content = response.content
        if len(content) > self.settings.upload_max_file_bytes:
            raise GoogleDriveConnectionError("The selected Google Drive file exceeds the configured upload size limit.")
        return GoogleDriveDownloadedFile(name=filename, mime_type=mime_type, content=content)
