from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.exceptions.auth import InvalidMFATokenException, SignInFailureException, UserIsUnactiveException
from app.helpers.generator import generate_uuid
from app.helpers.user_validator import verify_mfa_credentials, verify_user_password, verify_user_status
from app.schemas.users import CreateUserQueryResponse, UserMembershipQueryReponse


@pytest.mark.parametrize(
    "user, expected_exception",
    [
        # Test cases for user verification
        (None, SignInFailureException),
        # User is inactive
        (
            CreateUserQueryResponse(
                uuid=generate_uuid(),
                username="test",
                email="test@example.com",
                firstname="Test",
                lastname="User",
                is_active=False,
                created_at=datetime.now(),
                updated_at=None,
                deleted_at=None,
            ),
            UserIsUnactiveException,
        ),
        # User is deleted
        (
            CreateUserQueryResponse(
                uuid=generate_uuid(),
                username="test2",
                email="test2@example.com",
                firstname="Test",
                is_active=True,
                created_at=datetime.now(),
                updated_at=None,
                deleted_at=datetime.now(),
            ),
            SignInFailureException,
        ),
        # User is active and not deleted
        (
            CreateUserQueryResponse(
                uuid=generate_uuid(),
                username="test3",
                email="test3@example.com",
                firstname="Test",
                is_active=True,
                created_at=datetime.now(),
                updated_at=None,
                deleted_at=None,
            ),
            None,
        ),
    ],
)
def test_verify_user_status(user, expected_exception):
    if expected_exception:
        with pytest.raises(expected_exception):
            verify_user_status(user)
    else:
        verify_user_status(user)


@pytest.mark.parametrize(
    "password_input, password_hash, is_verified, expected_exception",
    [
        ("password123", "hashed_password", True, None),
        ("wrong_password", "hashed_password", False, SignInFailureException),
    ],
)
def test_verify_user_password(password_input, password_hash, is_verified, expected_exception):
    with patch("app.helpers.user_validator.verify_password", return_value=is_verified):
        if expected_exception:
            with pytest.raises(expected_exception):
                verify_user_password(password_input, password_hash)
        else:
            verify_user_password(password_input, password_hash)


@pytest.mark.parametrize(
    "mfa_token, mfa_code, redis_token, decode_result, is_verified_token, expected_exception",
    [
        # Valid case
        ("valid_token", "123456", "valid_token", {"username": "testuser"}, True, None),
        # Invalid MFA token
        ("invalid_token", "123456", "valid_token", None, True, InvalidMFATokenException),
        # Invalid MFA code
        ("valid_token", "wrong_code", "valid_token", {"username": "testuser"}, False, InvalidMFATokenException),
        # Token not matching DB
        ("valid_token", "123456", "different_token", {"username": "testuser"}, True, InvalidMFATokenException),
    ],
)
def test_verify_mfa_credentials(mfa_token, mfa_code, redis_token, decode_result, is_verified_token, expected_exception):
    # Mock Redis helper
    mock_redis = MagicMock()
    mock_redis.get_data.return_value = redis_token
    mock_redis.delete_data.return_value = None

    # Mock user data
    user = UserMembershipQueryReponse(
        uuid=generate_uuid(),
        firstname="Test",
        username="testuser",
        email="test@example.com",
        is_active=True,
        created_at=datetime.now(),
        updated_at=None,
        deleted_at=None,
        mfa_enabled=True,
        services=[],
    )

    with (
        patch("app.helpers.user_validator.decode_access_jwt", return_value=decode_result),
        patch("app.helpers.user_validator.TwoFactorAuth.verify_token", return_value=is_verified_token),
    ):
        if expected_exception:
            with pytest.raises(expected_exception):
                verify_mfa_credentials(mock_redis, mfa_token, mfa_code, user)
        else:
            verify_mfa_credentials(mock_redis, mfa_token, mfa_code, user)
