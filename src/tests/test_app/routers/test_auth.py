from unittest.mock import AsyncMock, patch

import pytest

from fastapi import status

from app.schemas.users import SignInResponse


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "user_payload, mock_return, expected_status, expected_message",
    [
        # Successful sign-up without MFA
        (
            # user payload
            {
                "email": "johndoe@gmail.com",
                "username": "johndoe",
                "password": "Password123!",
                "password_confirm": "Password123!",
                "firstname": "John",
                "midname": "M.",
                "lastname": "Doe",
                "phone": "+1234567890",
                "mfa_enabled": False,
            },
            # mock return value
            (
                {
                    "uuid": "0195a2f1-8267-744f-8e76-2d2b211910b2",
                    "username": "johndoe",
                    "firstname": "John",
                    "midname": "M.",
                    "lastname": "Doe",
                    "email": "johndoe@gmail.com",
                    "phone": "+1234567890",
                    "telegram": None,
                    "is_active": False,
                    "mfa_enabled": False,
                    "created_at": "2025-03-17T07:12:39.919356Z",
                    "created_by": "johndoe@gmail.com",
                    "updated_at": "2025-03-17T07:12:39.919356Z",
                    "updated_by": None,
                    "deleted_at": None,
                    "deleted_by": None,
                },
                None,  # qr_code_bs64 is None for non-MFA
            ),
            # expected status code
            status.HTTP_201_CREATED,
            # expected message
            "Success register user",
        ),
        # Sign-up with MFA enabled
        (
            {
                "email": "janedoe@gmail.com",
                "username": "janedoe",
                "password": "Password123!",
                "password_confirm": "Password123!",
                "firstname": "Jane",
                "midname": "N.",
                "lastname": "Doe",
                "phone": "+1234567891",
                "mfa_enabled": True,
            },
            (
                {
                    "uuid": "0195a2f1-8267-744f-8e76-2d2b211910b3",
                    "username": "janedoe",
                    "firstname": "Jane",
                    "midname": "N.",
                    "lastname": "Doe",
                    "email": "janedoe@gmail.com",
                    "phone": "+1234567891",
                    "telegram": None,
                    "is_active": False,
                    "mfa_enabled": True,
                    "created_at": "2025-03-17T07:12:39.919356Z",
                    "created_by": "janedoe@gmail.com",
                    "updated_at": "2025-03-17T07:12:39.919356Z",
                    "updated_by": None,
                    "deleted_at": None,
                    "deleted_by": None,
                },
                "base64_qr_code_data",
            ),
            status.HTTP_201_CREATED,
            "Success register user",
        ),
        # Special characters in username
        (
            {
                "email": "john.doe123@gmail.com",
                "username": "john_doe-123",
                "password": "Password123!",
                "password_confirm": "Password123!",
                "firstname": "John",
                "lastname": "Doe",
                "phone": "+1234567892",
                "mfa_enabled": False,
            },
            (
                {
                    "uuid": "0195a2f1-8267-744f-8e76-2d2b211910b4",
                    "username": "john_doe-123",
                    "firstname": "John",
                    "midname": None,
                    "lastname": "Doe",
                    "email": "john.doe123@gmail.com",
                    "phone": "+1234567892",
                    "telegram": None,
                    "is_active": False,
                    "mfa_enabled": False,
                    "created_at": "2025-03-17T07:12:39.919356Z",
                    "created_by": "john.doe123@gmail.com",
                    "updated_at": "2025-03-17T07:12:39.919356Z",
                    "updated_by": None,
                    "deleted_at": None,
                    "deleted_by": None,
                },
                None,
            ),
            status.HTTP_201_CREATED,
            "Success register user",
        ),
    ],
)
async def test_sign_up(async_client, user_payload, expected_status, mock_return, expected_message):
    # Creating a mock for auth_service function from app state
    mock_auth_service = AsyncMock()
    mock_auth_service.sign_up.return_value = mock_return

    # Patch request.state.__getattr__ to return auth_service
    with patch("starlette.datastructures.State.__getattr__", return_value=mock_auth_service):
        response = await async_client.post("/api/v1/auth/sign-up", data=user_payload)

    response_json = response.json()

    # Assertions
    assert response.status_code == expected_status
    assert response_json["message"] == expected_message

    # Verify mock was called with correct parameters
    mock_auth_service.sign_up.assert_called_once()

    # Check the response data structure
    assert "data" in response_json
    assert "user" in response_json["data"]

    # If MFA is enabled, check for qr_code in response
    if user_payload.get("mfa_enabled", False):
        assert response_json["data"]["qr_code_bs64"] is not None
    else:
        assert response_json["data"].get("qr_code_bs64") is None


# skip
# @pytest.mark.skip(reason="no way of currently testing this")
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "signin_payload, mock_return, expected_status, expected_message",
    [
        # Successful sign-in without MFA
        (
            # signin_payload
            {
                "username": "johndoe",
                "password": "Password123!",
            },
            # mock return value
            (
                SignInResponse(
                    access_token="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                    mfa_token=None,
                    mfa_required=False,
                ),
                {"key": "refresh_token", "value": "some_refresh_token", "httponly": True},
            ),
            status.HTTP_200_OK,
            "Sign in successful",
        ),
        # Sign-in with MFA required
        (
            {
                "username": "janedoe",
                "password": "Password123!",
            },
            (
                SignInResponse(
                    access_token=None,
                    mfa_token="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                    mfa_required=True,
                ),
                None,
            ),
            status.HTTP_202_ACCEPTED,
            "MFA verification required - temporary token issued",
        ),
    ],
)
async def test_sign_in(async_client, signin_payload, mock_return, expected_status, expected_message):
    # Creating a mock for auth_service function from app state
    mock_auth_service = AsyncMock()
    mock_auth_service.sign_in.return_value = mock_return

    # Patch request.state.__getattr__ to return auth_service
    with patch("starlette.datastructures.State.__getattr__", return_value=mock_auth_service):
        response = await async_client.post("/api/v1/auth/sign-in", data=signin_payload)

    response_json = response.json()

    # Assertions
    print(f"TEST >> {response_json=}")
    print(f"TEST >> {response.status_code=} == {expected_status=}")
    assert response.status_code == expected_status
    assert response_json["status_code"] == expected_status
    assert response_json["message"] == expected_message

    # Verify mock was called with correct parameters
    mock_auth_service.sign_in.assert_called_once()

    # Check the response data structure
    assert "data" in response_json

    # Verify the correct response type based on MFA requirement
    if mock_return[0].mfa_required:
        assert response_json["data"]["mfa_token"] is not None
        assert "mfa_token" in response_json["data"]
        assert response_json["data"].get("access_token") is None
        assert response_json["data"]["mfa_required"] is True
    else:
        assert response_json["data"]["access_token"] is not None
        assert "access_token" in response_json["data"]
        assert response_json["data"].get("mfa_token") is None
        assert response_json["data"]["mfa_required"] is False

    # Verify mock was called with correct payload
    call_args = mock_auth_service.sign_in.call_args
    assert call_args is not None
    args, kwargs = call_args

    # Check that the payload was passed correctly to the service
    assert "payload" in kwargs
    assert kwargs["payload"].username == signin_payload["username"]
    assert "connection" in kwargs
