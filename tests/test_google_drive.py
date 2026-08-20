from __future__ import annotations

from urllib.parse import parse_qs, urlparse
from uuid import uuid4

import httpx
import pytest

from app.api.routes.google_drive import _selected_file_ids
from app.core.security import decode_token
from app.services.google_drive import GoogleDriveConfigurationError, GoogleDriveConnectionError, GoogleDriveService


class DummySession:
    pass


def test_authorization_url_uses_signed_brand_scoped_one_pick_state(monkeypatch: pytest.MonkeyPatch) -> None:
    service = GoogleDriveService(DummySession())
    monkeypatch.setattr(
        service,
        "_configuration",
        lambda: ("client-id", "client-secret", "https://api.example.com/api/v1/google-drive/oauth/callback"),
    )
    tenant_id = uuid4()
    user_id = uuid4()
    brand_id = uuid4()

    authorization_url, nonce = service.create_authorization(
        tenant_id,
        user_id,
        brand_id,
        "https://app.example.com",
        allow_multiple=True,
    )

    assert authorization_url.startswith("https://accounts.google.com/o/oauth2/v2/auth?")
    params = parse_qs(urlparse(authorization_url).query)
    assert params["client_id"] == ["client-id"]
    assert params["scope"] == ["https://www.googleapis.com/auth/drive.file"]
    assert params["include_granted_scopes"] == ["false"]
    assert params["trigger_onepick"] == ["true"]
    assert params["allow_multiple"] == ["true"]
    assert params["allow_folder_selection"] == ["false"]
    state = params["state"][0]
    payload = decode_token(state)
    assert payload["typ"] == "google_drive_oauth"
    assert payload["tenant_id"] == str(tenant_id)
    assert payload["brand_id"] == str(brand_id)
    assert payload["nonce"] == nonce
    assert GoogleDriveService.callback_origin(state) == "https://app.example.com"


def test_selected_file_ids_discards_invalid_or_duplicate_values() -> None:
    assert _selected_file_ids("valid-file_1,invalid/file,valid-file_1,second") == ["valid-file_1", "second"]


@pytest.mark.asyncio
async def test_token_exchange_transport_error_is_reported_as_connection_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class FailingAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return False

        async def post(self, *_args, **_kwargs):
            raise httpx.RemoteProtocolError("Disconnected")

    service = GoogleDriveService(DummySession())
    monkeypatch.setattr(service, "_configuration", lambda: ("client-id", "client-secret", "https://api.example.com/callback"))
    authorization_url, _ = service.create_authorization(uuid4(), uuid4(), uuid4(), "https://app.example.com")
    state = parse_qs(urlparse(authorization_url).query)["state"][0]
    monkeypatch.setattr("app.services.google_drive.httpx.AsyncClient", lambda **_kwargs: FailingAsyncClient())

    with pytest.raises(GoogleDriveConnectionError, match="could not complete"):
        await service.complete_authorization("authorization-code", state)

def test_authorization_requires_server_side_google_drive_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    service = GoogleDriveService(DummySession())
    monkeypatch.setattr(service.settings, "google_drive_client_id", None)
    monkeypatch.setattr(service.settings, "google_drive_client_secret", None)
    monkeypatch.setattr(service.settings, "google_drive_redirect_uri", None)

    with pytest.raises(GoogleDriveConfigurationError):
        service.create_authorization(uuid4(), uuid4(), uuid4(), "https://app.example.com")