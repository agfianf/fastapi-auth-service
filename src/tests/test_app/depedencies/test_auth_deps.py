from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from fastapi import Request
from fastapi.security import HTTPAuthorizationCredentials
from uuid_utils.compat import uuid7

from app.depedencies.auth import AUTH_SCHEME, JWTBearer, RoleChecker
from app.exceptions.auth import (
    InactiveUserException,
    InsufficientPermissionsException,
    InvalidCredentialsHeaderException,
    InvalidCredentialsSchemeException,
    InvalidTokenException,
    TokenRevokedException,
)
from app.helpers.generator import generate_uuid
from app.schemas.roles.base import UserRole
from app.schemas.users import UserMembershipQueryReponse


@pytest.fixture
def mock_request():
    """Create a mock request with Redis helper attached to state."""
    request = MagicMock(spec=Request)
    request.state.redis_helper = MagicMock()
    request.state.redis_helper.is_token_revoked = MagicMock(return_value=False)
    return request


@pytest.fixture
def valid_user_data():
    """Return valid user profile data."""
    return {
        "uuid": uuid7(),
        "username": "agfian",
        "firstname": "Agfian",
        "midname": "Fadilah",
        "lastname": "Muhammad",
        "email": "agfian@email.com",
        "phone": None,
        "telegram": None,
        "is_active": True,
        "mfa_enabled": False,
        "services": [],
        "created_at": "2025-03-18 02:29:56.297139+00:00",
        "created_by": None,
        "updated_at": "2025-03-18 02:29:56.297139+00:00",
        "updated_by": None,
    }


@pytest.fixture
def inactive_user_data():
    """Inactive user profile data."""
    return {
        "uuid": uuid7(),
        "username": "agfian",
        "firstname": "Agfian",
        "midname": "Fadilah",
        "lastname": "Muhammad",
        "email": "agfian@email.com",
        "phone": None,
        "telegram": None,
        "is_active": False,
        "mfa_enabled": False,
        "services": [],
        "created_at": "2025-03-18 02:29:56.297139+00:00",
        "created_by": None,
        "updated_at": "2025-03-18 02:29:56.297139+00:00",
        "updated_by": None,
    }


class TestJWTBearer:
    @pytest.mark.asyncio
    @patch("app.depedencies.auth.decode_access_jwt")
    async def test_valid_token(self, mock_decode_jwt, mock_request, valid_user_data):
        """Test successful authentication with valid token."""
        # Setup
        bearer = JWTBearer()
        mock_credentials = HTTPAuthorizationCredentials(scheme=AUTH_SCHEME, credentials="valid_token")

        # Mock __call__ parent class untuk return credentials
        with patch("fastapi.security.http.HTTPBearer.__call__", new_callable=AsyncMock, return_value=mock_credentials):
            # Configure mocks
            mock_decode_jwt.return_value = valid_user_data

            # Call the method
            user_profile, token = await bearer.__call__(mock_request)

            # Assertions
            assert user_profile.uuid == valid_user_data["uuid"]
            assert user_profile.email == valid_user_data["email"]
            assert user_profile.is_active == valid_user_data["is_active"]
            assert token == "valid_token"
            mock_request.state.redis_helper.is_token_revoked.assert_called_once_with("valid_token")

    @pytest.mark.asyncio
    async def test_missing_credentials(self, mock_request):
        """Test exception raised when credentials are missing."""
        # Setup
        bearer = JWTBearer()

        with (
            patch("fastapi.security.http.HTTPBearer.__call__", new_callable=AsyncMock, return_value=None),
            pytest.raises(InvalidCredentialsHeaderException),
        ):
            await bearer.__call__(mock_request)

    @pytest.mark.asyncio
    async def test_invalid_scheme(self, mock_request):
        """Test exception raised when auth scheme is invalid."""
        # Setup
        bearer = JWTBearer()
        mock_credentials = HTTPAuthorizationCredentials(scheme="Basic", credentials="token")

        # Mock super().__call__
        with (
            patch("fastapi.security.http.HTTPBearer.__call__", new_callable=AsyncMock, return_value=mock_credentials),
            pytest.raises(InvalidCredentialsSchemeException),
        ):
            await bearer.__call__(mock_request)

    @pytest.mark.asyncio
    @patch("app.depedencies.auth.decode_access_jwt")
    async def test_invalid_token(self, mock_decode_jwt, mock_request):
        # Setup
        bearer = JWTBearer()
        mock_credentials = HTTPAuthorizationCredentials(scheme=AUTH_SCHEME, credentials="invalid_token")
        mock_decode_jwt.return_value = None

        with (
            patch("fastapi.security.http.HTTPBearer.__call__", new_callable=AsyncMock, return_value=mock_credentials),
            pytest.raises(InvalidTokenException),
        ):
            await bearer(mock_request)

    @pytest.mark.asyncio
    @patch("app.depedencies.auth.decode_access_jwt")
    async def test_revoked_token(self, mock_decode_jwt, mock_request, valid_user_data):
        """Test exception raised when token is revoked."""
        # Setup
        bearer = JWTBearer()
        mock_credentials = HTTPAuthorizationCredentials(scheme=AUTH_SCHEME, credentials="revoked_token")

        # Configure mocks before assertion block
        mock_decode_jwt.return_value = valid_user_data
        mock_request.state.redis_helper.is_token_revoked.return_value = True

        with (
            patch("fastapi.security.http.HTTPBearer.__call__", new_callable=AsyncMock, return_value=mock_credentials),
            pytest.raises(TokenRevokedException),
        ):
            await bearer.__call__(mock_request)

    @pytest.mark.asyncio
    @patch("app.depedencies.auth.decode_access_jwt")
    async def test_inactive_user(self, mock_decode_jwt, mock_request, inactive_user_data):
        """Test exception raised when user is inactive."""
        # Setup
        bearer = JWTBearer()
        mock_credentials = HTTPAuthorizationCredentials(scheme=AUTH_SCHEME, credentials="valid_token")
        mock_decode_jwt.return_value = inactive_user_data

        with (
            patch("fastapi.security.http.HTTPBearer.__call__", new_callable=AsyncMock, return_value=mock_credentials),
            pytest.raises(InactiveUserException),
        ):
            await bearer.__call__(mock_request)


class TestRoleChecker:
    @pytest.fixture
    def mock_user_profile(self):
        return UserMembershipQueryReponse(
            uuid=generate_uuid(),
            email="test@example.com",
            username="testuser",
            firstname="Test",
            is_active=True,
            role=UserRole.member,
            services=[],
        )

    @pytest.fixture
    def mock_jwt(self):
        return "mock.jwt.token"

    @pytest.mark.asyncio
    async def test_call_with_valid_role(self, mock_user_profile, mock_jwt):
        # Setup
        role_checker = RoleChecker([UserRole.member, UserRole.admin])
        jwt_data = (mock_user_profile, mock_jwt)

        # Execute
        result_profile, result_jwt = await role_checker(jwt_data)

        # Assert
        assert result_profile == mock_user_profile
        assert result_jwt == mock_jwt

    @pytest.mark.asyncio
    async def test_call_with_invalid_role_raises_exception(self, mock_user_profile, mock_jwt):
        # Setup
        role_checker = RoleChecker([UserRole.admin, UserRole.superadmin])
        jwt_data = (mock_user_profile, mock_jwt)

        # Execute and Assert
        with pytest.raises(InsufficientPermissionsException):
            await role_checker(jwt_data)

    @pytest.mark.asyncio
    async def test_call_with_multiple_allowed_roles(self, mock_user_profile, mock_jwt):
        # Setup
        mock_user_profile.role = UserRole.admin
        role_checker = RoleChecker([UserRole.member, UserRole.admin, UserRole.superadmin])
        jwt_data = (mock_user_profile, mock_jwt)

        # Execute
        result_profile, result_jwt = await role_checker(jwt_data)

        # Assert
        assert result_profile == mock_user_profile
        assert result_jwt == mock_jwt
