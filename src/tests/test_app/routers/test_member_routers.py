from unittest.mock import AsyncMock, patch

import pytest

from fastapi import status

from app.exceptions.member import (
    InvalidCurrentPasswordException,
    MemberNotFoundException,
    MFACodeInvalidException,
)
from app.helpers.generator import generate_uuid
from app.schemas.member import (
    MemberDetailsResponse,
    MFAQRCodeResponse,
    UpdateMemberMFAResponse,
    UpdateMemberResponse,
)


@pytest.mark.asyncio
async def test_get_member_details_success(async_client, db_conn, override_role_jwt_bearer):
    """Test the get_member_details endpoint when it returns data successfully."""
    user_profile, jwt_token = override_role_jwt_bearer

    # Mock data
    mock_member = {
        "uuid": str(user_profile.uuid),
        "role": "admin",
        "username": "testadmin",
        "firstname": "Test",
        "midname": "Admin",
        "lastname": "User",
        "email": "testadmin@example.com",
        "phone": "+1234567890",
        "telegram": "@testadmin",
        "is_active": True,
        "mfa_enabled": False,
        "created_at": "2025-03-17T07:12:39.919356Z",
        "updated_at": "2025-03-17T07:12:39.919356Z",
        "services": [
            {
                "uuid": str(generate_uuid()),
                "name": "Service 1",
                "description": "Test service",
                "role": "admin",
                "member_is_active": True,
                "service_is_active": True,
            }
        ],
    }

    # Mock the member service
    mock_member_service = AsyncMock()
    mock_member_service.fetch_member_details.return_value = MemberDetailsResponse.model_validate(mock_member)

    with patch("starlette.datastructures.State.__getattr__", return_value=mock_member_service):
        response = await async_client.get(
            "/api/v1/me",
            headers={"Authorization": f"Bearer {jwt_token}"},
        )

    response_json = response.json()

    # Assertions
    assert response.status_code == status.HTTP_200_OK
    assert response_json["status_code"] == status.HTTP_200_OK
    assert response_json["message"] == "Successfully retrieved member details"

    # Check returned data
    assert response_json["data"]["uuid"] == str(user_profile.uuid)
    assert response_json["data"]["username"] == "testadmin"
    assert response_json["data"]["role"] == "admin"

    # Verify mock was called with correct parameters
    mock_member_service.fetch_member_details.assert_called_once_with(
        user_uid=user_profile.uuid,
        connection=db_conn,
    )


@pytest.mark.asyncio
async def test_get_member_details_not_found(async_client, db_conn, override_role_jwt_bearer):
    """Test the get_member_details endpoint when the member is not found."""
    user_profile, jwt_token = override_role_jwt_bearer

    # Mock the member service to raise MemberNotFoundException
    mock_member_service = AsyncMock()
    mock_member_service.fetch_member_details.side_effect = MemberNotFoundException()

    with patch("starlette.datastructures.State.__getattr__", return_value=mock_member_service):
        response = await async_client.get(
            "/api/v1/me",
            headers={"Authorization": f"Bearer {jwt_token}"},
        )

    # Assertions
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["message"] == "Member not found"


@pytest.mark.asyncio
async def test_get_member_details_unauthorized(async_client, db_conn):
    """Test the get_member_details endpoint with missing authorization."""
    response = await async_client.get("/api/v1/me")

    # Assertions
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_update_password_success(async_client, db_conn_trans, override_role_jwt_bearer):
    """Test the update_password endpoint when it successfully updates a password."""
    user_profile, jwt_token = override_role_jwt_bearer

    # Setup client with cookies
    async_client.cookies.set("refresh_token_app", "mock_refresh_token")

    # Password update payload
    password_payload = {
        "current_password": "OldPassword123!",
        "new_password": "NewPassword123!",
        "new_password_confirm": "NewPassword123!",
    }

    # Mock the member service
    mock_member_service = AsyncMock()
    mock_member_service.update_password.return_value = (
        UpdateMemberResponse(
            access_token="new_access_token",
            user=user_profile,
        ),
        {"key": "refresh_token_app", "value": "new_refresh_token", "httponly": True, "path": "/", "samesite": "lax"},
    )

    with patch("starlette.datastructures.State.__getattr__", return_value=mock_member_service):
        response = await async_client.put(
            "/api/v1/me/password",
            data=password_payload,
            headers={"Authorization": f"Bearer {jwt_token}"},
        )

    response_json = response.json()

    # Assertions
    assert response.status_code == status.HTTP_200_OK
    assert response_json["status_code"] == status.HTTP_200_OK
    assert response_json["message"] == "Password updated successfully"
    assert response_json["success"] is True

    # Verify cookie was set
    assert "set-cookie" in response.headers
    assert "refresh_token_app=new_refresh_token" in response.headers["set-cookie"]

    # Verify mock was called with correct parameters
    mock_member_service.update_password.assert_called_once()
    call_args = mock_member_service.update_password.call_args
    args, kwargs = call_args

    assert kwargs["current_user"].uuid == user_profile.uuid
    assert kwargs["payload"].current_password.get_secret_value() == password_payload["current_password"]
    assert kwargs["payload"].new_password.get_secret_value() == password_payload["new_password"]
    assert kwargs["payload"].new_password_confirm.get_secret_value() == password_payload["new_password_confirm"]
    assert kwargs["access_token"] == jwt_token
    assert kwargs["refresh_token"] == "mock_refresh_token"


@pytest.mark.asyncio
async def test_update_password_current_mismatch(async_client, db_conn_trans, override_role_jwt_bearer):
    """Test the update_password endpoint when the current password is incorrect."""
    user_profile, jwt_token = override_role_jwt_bearer

    # Setup client with cookies
    async_client.cookies.set("refresh_token_app", "mock_refresh_token")

    # Password update payload
    password_payload = {
        "current_password": "WrongPassword123!",
        "new_password": "NewPassword123!",
        "new_password_confirm": "NewPassword123!",
    }

    # Mock the member service to raise CurrentPasswordMismatchException
    mock_member_service = AsyncMock()
    mock_member_service.update_password.side_effect = InvalidCurrentPasswordException()

    with patch("starlette.datastructures.State.__getattr__", return_value=mock_member_service):
        response = await async_client.put(
            "/api/v1/me/password",
            data=password_payload,
            headers={"Authorization": f"Bearer {jwt_token}"},
        )

    # Assertions

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["message"] == "Current password is incorrect"


@pytest.mark.asyncio
async def test_update_mfa_enable_success(async_client, db_conn_trans, override_role_jwt_bearer):
    """Test the update_mfa endpoint when it successfully enables MFA."""
    user_profile, jwt_token = override_role_jwt_bearer

    # Setup client with cookies
    async_client.cookies.set("refresh_token_app", "mock_refresh_token")

    # MFA update payload
    mfa_payload = {
        "mfa_enabled": True,
        "mfa_code": "123456",
    }

    # Mock the member service response
    user_profile.mfa_enabled = True
    mock_member_service = AsyncMock()
    mock_member_service.update_mfa.return_value = (
        UpdateMemberMFAResponse(
            access_token="new_access_token",
            user=user_profile,
            qr_code_bs64="base64_qr_code_data",
        ),
        {"key": "refresh_token_app", "value": "new_refresh_token", "httponly": True, "path": "/", "samesite": "lax"},
    )

    with patch("starlette.datastructures.State.__getattr__", return_value=mock_member_service):
        response = await async_client.put(
            "/api/v1/me/mfa",
            data=mfa_payload,
            headers={"Authorization": f"Bearer {jwt_token}"},
        )

    response_json = response.json()

    # Assertions
    assert response.status_code == status.HTTP_200_OK
    assert response_json["status_code"] == status.HTTP_200_OK
    assert response_json["message"] == "MFA enabled successfully"
    assert response_json["data"]["user"]["mfa_enabled"] is True
    assert response_json["data"]["access_token"] == "new_access_token"

    # Verify cookie was set
    assert "set-cookie" in response.headers
    assert "refresh_token_app=new_refresh_token" in response.headers["set-cookie"]

    # Verify mock was called with correct parameters
    mock_member_service.update_mfa.assert_called_once()
    call_args = mock_member_service.update_mfa.call_args
    args, kwargs = call_args

    assert kwargs["current_user"].uuid == user_profile.uuid
    assert kwargs["payload"].mfa_enabled is True
    assert kwargs["payload"].mfa_code == "123456"
    assert kwargs["access_token"] == jwt_token
    assert kwargs["refresh_token"] == "mock_refresh_token"


@pytest.mark.asyncio
async def test_update_mfa_disable_success(async_client, db_conn_trans, override_role_jwt_bearer):
    """Test the update_mfa endpoint when it successfully disables MFA."""
    user_profile, jwt_token = override_role_jwt_bearer

    # Setup client with cookies
    async_client.cookies.set("refresh_token_app", "mock_refresh_token")

    # MFA update payload
    mfa_payload = {
        "mfa_enabled": False,
        "mfa_code": "123456",
    }

    # Mock the member service
    user_profile.mfa_enabled = False
    mock_member_service = AsyncMock()
    mock_member_service.update_mfa.return_value = (
        UpdateMemberMFAResponse(
            access_token="new_access_token",
            user=user_profile,
            qr_code_bs64="base64_qr_code_data",
        ),
        {"key": "refresh_token_app", "value": "new_refresh_token", "httponly": True, "path": "/", "samesite": "lax"},
    )

    with patch("starlette.datastructures.State.__getattr__", return_value=mock_member_service):
        response = await async_client.put(
            "/api/v1/me/mfa",
            data=mfa_payload,
            headers={"Authorization": f"Bearer {jwt_token}"},
        )

    response_json = response.json()

    # Verify cookie was set
    assert "set-cookie" in response.headers
    assert "refresh_token_app=new_refresh_token" in response.headers["set-cookie"]

    # Assertions
    assert response.status_code == status.HTTP_200_OK
    assert response_json["status_code"] == status.HTTP_200_OK
    assert response_json["message"] == "MFA disabled successfully"
    assert response_json["success"] is True
    assert response_json["data"]["user"]["mfa_enabled"] is False
    assert response_json["data"]["access_token"] == "new_access_token"


@pytest.mark.asyncio
async def test_update_mfa_invalid_code(async_client, db_conn_trans, override_role_jwt_bearer):
    """Test the update_mfa endpoint with an invalid MFA code."""
    user_profile, jwt_token = override_role_jwt_bearer

    # Setup client with cookies
    async_client.cookies.set("refresh_token_app", "mock_refresh_token")

    # MFA update payload
    mfa_payload = {
        "mfa_enabled": True,
        "mfa_code": "999999",  # Invalid code
    }

    # Mock the member service to raise InvalidMFACodeException
    mock_member_service = AsyncMock()
    mock_member_service.update_mfa.side_effect = MFACodeInvalidException()

    with patch("starlette.datastructures.State.__getattr__", return_value=mock_member_service):
        response = await async_client.put(
            "/api/v1/me/mfa",
            data=mfa_payload,
            headers={"Authorization": f"Bearer {jwt_token}"},
        )

    # Assertions
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["message"] == "Invalid MFA code provided"


@pytest.mark.asyncio
async def test_update_profile_success(async_client, db_conn_trans, override_role_jwt_bearer):
    """Test the update_profile endpoint when it successfully updates a profile."""
    user_profile, jwt_token = override_role_jwt_bearer

    # Setup client with cookies
    async_client.cookies.set("refresh_token_app", "mock_refresh_token")

    # Profile update payload
    profile_payload = {
        "firstname": "Updated",
        "midname": "New",
        "lastname": "Name",
        "phone": "+1987654321",
        "telegram": "@updateduser",
    }

    # Mock the member service
    mock_member_service = AsyncMock()
    user_profile.firstname = profile_payload["firstname"]
    user_profile.midname = profile_payload["midname"]
    user_profile.lastname = profile_payload["lastname"]
    user_profile.phone = profile_payload["phone"]
    user_profile.telegram = profile_payload["telegram"]
    mock_member_service.update_profile.return_value = (
        UpdateMemberResponse(
            access_token="new_access_token",
            user=user_profile,
        ),
        {"key": "refresh_token_app", "value": "new_refresh_token", "httponly": True, "path": "/", "samesite": "lax"},
    )

    with patch("starlette.datastructures.State.__getattr__", return_value=mock_member_service):
        response = await async_client.put(
            "/api/v1/me",
            data=profile_payload,
            headers={"Authorization": f"Bearer {jwt_token}"},
        )

    response_json = response.json()

    # Assertions
    assert response.status_code == status.HTTP_200_OK
    assert response_json["status_code"] == status.HTTP_200_OK
    assert response_json["message"] == "Profile updated successfully"
    assert response_json["data"]["user"]["firstname"] == profile_payload["firstname"]
    assert response_json["data"]["user"]["midname"] == profile_payload["midname"]
    assert response_json["data"]["user"]["lastname"] == profile_payload["lastname"]
    assert response_json["data"]["user"]["phone"] == profile_payload["phone"]
    assert response_json["data"]["user"]["telegram"] == profile_payload["telegram"]
    assert response_json["data"]["access_token"] == "new_access_token"

    # Verify cookie was set
    assert "set-cookie" in response.headers
    assert "refresh_token_app=new_refresh_token" in response.headers["set-cookie"]

    # Verify mock was called with correct parameters
    mock_member_service.update_profile.assert_called_once()
    call_args = mock_member_service.update_profile.call_args
    args, kwargs = call_args

    assert kwargs["current_user"].uuid == user_profile.uuid
    assert kwargs["payload"].firstname == profile_payload["firstname"]
    assert kwargs["payload"].midname == profile_payload["midname"]
    assert kwargs["payload"].lastname == profile_payload["lastname"]
    assert kwargs["payload"].phone == profile_payload["phone"]
    assert kwargs["payload"].telegram == profile_payload["telegram"]
    assert kwargs["access_token"] == jwt_token
    assert kwargs["refresh_token"] == "mock_refresh_token"


@pytest.mark.asyncio
async def test_update_profile_failure(async_client, db_conn_trans, override_role_jwt_bearer):
    """Test the update_profile endpoint when the update fails."""
    user_profile, jwt_token = override_role_jwt_bearer

    # Setup client with cookies
    async_client.cookies.set("refresh_token_app", "mock_refresh_token")

    # Profile update payload
    profile_payload = {
        "firstname": "Updated",
        "lastname": "Name",
    }

    # Mock the member service to raise MemberUpdateFailedException
    mock_member_service = AsyncMock()
    mock_member_service.update_profile.side_effect = MemberNotFoundException()

    with patch("starlette.datastructures.State.__getattr__", return_value=mock_member_service):
        response = await async_client.put(
            "/api/v1/me",
            data=profile_payload,
            headers={"Authorization": f"Bearer {jwt_token}"},
        )

    # Assertions
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["message"] == "Member not found"


@pytest.mark.asyncio
async def test_get_mfa_qrcode_success(async_client, db_conn, override_role_jwt_bearer):
    """Test the get_mfa_qrcode endpoint when it successfully returns a QR code."""
    user_profile, jwt_token = override_role_jwt_bearer

    # Mock data
    mock_qrcode = {
        "qr_code_bs64": "base64_qr_code_data",
    }

    # Mock the member service
    mock_member_service = AsyncMock()
    mock_member_service.get_mfa_qrcode.return_value = MFAQRCodeResponse(qr_code_bs64=mock_qrcode["qr_code_bs64"])

    with patch("starlette.datastructures.State.__getattr__", return_value=mock_member_service):
        response = await async_client.get(
            "/api/v1/me/mfa/qrcode",
            headers={"Authorization": f"Bearer {jwt_token}"},
        )

    response_json = response.json()

    # Assertions
    assert response.status_code == status.HTTP_200_OK
    assert response_json["status_code"] == status.HTTP_200_OK
    assert response_json["message"] == "MFA QR code generated successfully"
    assert response_json["data"]["qr_code_bs64"] == "base64_qr_code_data"

    # Verify mock was called with correct parameters
    mock_member_service.get_mfa_qrcode.assert_called_once_with(
        current_user=user_profile,
        connection=db_conn,
    )


@pytest.mark.asyncio
async def test_get_mfa_qrcode_unauthorized(async_client, db_conn):
    """Test the get_mfa_qrcode endpoint with missing authorization."""
    response = await async_client.get("/api/v1/me/mfa/qrcode")

    # Assertions
    assert response.status_code == status.HTTP_403_FORBIDDEN
