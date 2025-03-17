import datetime as dt

from datetime import datetime

import pytest

from fastapi import HTTPException
from pydantic import SecretStr, ValidationError
from uuid_utils.compat import UUID

from app.schemas.users import (
    CreateUserPayload,
    CreateUserQuery,
    CreateUserQueryResponse,
    SignInPayload,
    UserBase,
    UserMembershipQueryReponse,
)
from app.schemas.users.response import SignInResponse


class TestUserBase:
    def test_user_base_initialization(self):
        """Test that UserBase can be properly initialized with valid data."""
        user_data = {
            "uuid": "c47240a6-b1a6-7958-965c-39e89c975bb8",
            "role_id": 1,
            "username": "testuser",
            "firstname": "Test",
            "midname": "Middle",
            "lastname": "User",
            "email": "testuser@example.com",
            "phone": "+1234567890",
            "telegram": "@testuser",
            "password_hash": "hashedpassword",
            "is_active": True,
            "mfa_enabled": True,
            "mfa_secret": "TESTSECRET",
            "created_at": datetime.now(dt.UTC),
            "created_by": "admin",
            "updated_at": datetime.now(dt.UTC),
            "updated_by": "admin",
        }

        user_base = UserBase.model_validate(user_data)

        assert str(user_base.uuid) == user_data["uuid"]
        assert user_base.username == "testuser"
        assert user_base.email == "testuser@example.com"
        assert user_base.password_hash == "hashedpassword"
        assert user_base.is_active is True
        assert user_base.mfa_enabled is True
        assert user_base.mfa_secret == "TESTSECRET"

    def test_jwt_data_method(self):
        """Test the jwt_data method of UserBase."""
        user_data = {
            "uuid": "c47240a6-b1a6-7958-965c-39e89c975bb8",
            "role_id": 1,
            "username": "testuser",
            "firstname": "Test",
            "midname": "Middle",
            "lastname": "User",
            "email": "testuser@example.com",
            "phone": "+1234567890",
            "telegram": "@testuser",
            "password_hash": "hashedpassword",
            "is_active": True,
            "mfa_enabled": True,
            "mfa_secret": "TESTSECRET",
            "created_at": datetime.now(dt.UTC),
            "created_by": "admin",
            "updated_at": datetime.now(dt.UTC),
            "updated_by": "admin",
        }

        user_base = UserBase.model_validate(user_data)
        jwt_data = user_base.jwt_data(role="admin")

        assert jwt_data["uuid"] == user_data["uuid"]
        assert jwt_data["role"] == "admin"
        assert jwt_data["username"] == "testuser"
        assert jwt_data["email"] == "testuser@example.com"
        assert jwt_data["is_active"] is True
        assert jwt_data["mfa_enabled"] is True
        assert "password_hash" not in jwt_data
        assert "mfa_secret" not in jwt_data


class TestCreateUserPayload:
    @pytest.mark.parametrize(
        "input_data, expected_result",
        [
            # Valid case - all required fields
            (
                {
                    "email": "test@example.com",
                    "username": "testuser",
                    "password": "Password123!",
                    "password_confirm": "Password123!",
                    "firstname": "Test",
                    "lastname": "User",
                    "phone": "+1234567890",
                    "mfa_enabled": False,
                },
                True,
            ),
            # Valid case - with midname
            (
                {
                    "email": "test@example.com",
                    "username": "testuser",
                    "password": "Password123!",
                    "password_confirm": "Password123!",
                    "firstname": "Test",
                    "midname": "Middle",
                    "lastname": "User",
                    "mfa_enabled": True,
                },
                True,
            ),
            # Valid case - with all fields
            (
                {
                    "email": "test@example.com",
                    "username": "testuser",
                    "password": "Password123!",
                    "password_confirm": "Password123!",
                    "firstname": "Test",
                    "midname": "Middle",
                    "lastname": "User",
                    "role_id": 1,
                    "phone": "+1234567890",
                    "telegram": "@testuser",
                    "mfa_enabled": True,
                },
                True,
            ),
        ],
    )
    def test_valid_payloads(self, input_data, expected_result):
        """Test that valid payloads are accepted."""
        # Convert password fields to SecretStr
        if "password" in input_data:
            input_data["password"] = SecretStr(input_data["password"])
        if "password_confirm" in input_data:
            input_data["password_confirm"] = SecretStr(input_data["password_confirm"])

        # Create payload
        payload = CreateUserPayload.model_validate(input_data)

        # Basic assertions
        assert isinstance(payload, CreateUserPayload) == expected_result
        assert payload.email == input_data["email"]
        assert payload.username == input_data["username"]
        assert payload.firstname == input_data["firstname"]
        if "midname" in input_data:
            assert payload.midname == input_data["midname"]
        if "lastname" in input_data:
            assert payload.lastname == input_data["lastname"]

    @pytest.mark.parametrize(
        "input_data, expected_error",
        [
            # Empty username
            (
                {
                    "email": "test@example.com",
                    "username": "",
                    "password": "Password123!",
                    "password_confirm": "Password123!",
                    "firstname": "Test",
                },
                # because of empty username, this will preprocess "" to None
                "argument of type 'NoneType' is not iterable",
            ),
            # Invalid email
            (
                {
                    "email": "invalid-email",
                    "username": "testuser",
                    "password": "Password123!",
                    "password_confirm": "Password123!",
                    "firstname": "Test",
                },
                "value is not a valid email address",
            ),
            # Username with space
            (
                {
                    "email": "test@example.com",
                    "username": "test user",
                    "password": "Password123!",
                    "password_confirm": "Password123!",
                    "firstname": "Test",
                },
                "Username cannot contain space",
            ),
            # Too short username
            (
                {
                    "email": "test@example.com",
                    "username": "test",
                    "password": "Password123!",
                    "password_confirm": "Password123!",
                    "firstname": "Test",
                },
                "String should have at least 5 characters",
            ),
            # Missing required field (firstname)
            (
                {
                    "email": "test@example.com",
                    "username": "testuser",
                    "password": "Password123!",
                    "password_confirm": "Password123!",
                },
                "Field required",
            ),
        ],
    )
    def test_invalid_payloads(self, input_data, expected_error):
        """Test that invalid payloads raise appropriate validation errors."""
        # Convert password fields to SecretStr if present
        if "password" in input_data and isinstance(input_data["password"], str):
            input_data["password"] = SecretStr(input_data["password"])
        if "password_confirm" in input_data and isinstance(input_data["password_confirm"], str):
            input_data["password_confirm"] = SecretStr(input_data["password_confirm"])

        # Test validation
        with pytest.raises((ValidationError, TypeError, ValueError, HTTPException), match=f".*{expected_error}.*"):
            CreateUserPayload.model_validate(input_data)

    @pytest.mark.parametrize(
        "password,confirm_password,username",
        [
            ("Password123!", "Password123!", "testuser"),  # Valid
            ("Password123!", "DifferentPass123!", "testuser"),  # Non-matching passwords
            ("testuser123!", "testuser123!", "testuser"),  # Similar to username
            ("short", "short", "testuser"),  # Too short
            ("lowercase123!", "lowercase123!", "testuser"),  # No uppercase
            ("UPPERCASE123!", "UPPERCASE123!", "testuser"),  # No lowercase
            ("Passwordabc!", "Passwordabc!", "testuser"),  # No numbers
            ("Password123", "Password123", "testuser"),  # No special chars
        ],
    )
    def test_password_validation(self, password, confirm_password, username):
        """Test password validation logic in the model validator."""
        data = {
            "email": "test@example.com",
            "username": username,
            "password": SecretStr(password),
            "password_confirm": SecretStr(confirm_password),
            "firstname": "Test",
        }

        # Create expected validation status
        is_valid_pw = (
            password == confirm_password
            and password != username
            and len(password) >= 8
            and any(c.isupper() for c in password)
            and any(c.islower() for c in password)
            and any(c.isdigit() for c in password)
            and any(not c.isalnum() for c in password)
            and username not in password.lower()
        )

        if is_valid_pw:
            # Should validate without error
            payload = CreateUserPayload.model_validate(data)
            assert payload.username == username
        else:
            with pytest.raises((ValidationError, Exception)):
                CreateUserPayload.model_validate(data)

    def test_transform_method(self):
        """Test that the transform method correctly prepares data for storage."""
        payload = CreateUserPayload(
            email="test@example.com",
            username="testuser",
            password=SecretStr("Password123!"),
            password_confirm=SecretStr("Password123!"),
            firstname="Test",
            lastname="User",
            mfa_enabled=True,
        )

        transformed_data = payload.transform()

        # Check that UUIDv7 was generated
        assert "uuid" in transformed_data
        assert isinstance(transformed_data["uuid"], UUID)

        # Check that password was hashed
        assert "password_hash" in transformed_data
        assert transformed_data["password_hash"] != "Password123!"

        # Check that password is not in the result
        assert "password" not in transformed_data
        assert "password_confirm" not in transformed_data

        # Check that created_by is set to the email
        assert transformed_data["created_by"] == "test@example.com"

        # Check that is_active is set to False by default
        assert transformed_data["is_active"] is False


class TestSignInPayload:
    @pytest.mark.parametrize(
        "input_data",
        [
            # Valid case - minimal fields
            {
                "username": "testuser",
                "password": "Password123!",
            },
            # Valid case - longer username
            {
                "username": "test_user_name_longer",
                "password": "Password123!",
            },
        ],
    )
    def test_valid_sign_in_payloads(self, input_data):
        """Test that valid sign-in payloads are accepted."""
        # Convert password to SecretStr
        input_data["password"] = SecretStr(input_data["password"])

        # Create payload
        payload = SignInPayload.model_validate(input_data)

        # Assertions
        assert payload.username == input_data["username"]
        assert payload.password.get_secret_value() == input_data["password"].get_secret_value()

    @pytest.mark.parametrize(
        "input_data, expected_error",
        [
            # Too short username
            (
                {"username": "test", "password": "Password123!"},
                "String should have at least 5 characters",
            ),
            # Too short password
            (
                {"username": "testuser", "password": "Pass1!"},
                "1 validation error for SignInPayload",
            ),
            # Missing username
            (
                {"password": "Password123!"},
                "Field required",
            ),
            # Missing password
            (
                {"username": "testuser"},
                "Field required",
            ),
        ],
    )
    def test_invalid_sign_in_payloads(self, input_data, expected_error):
        """Test that invalid sign-in payloads raise appropriate validation errors."""
        # Convert password to SecretStr if present
        if "password" in input_data:
            input_data["password"] = SecretStr(input_data["password"])

        # Test validation
        with pytest.raises(ValidationError, match=f".*{expected_error}.*"):
            SignInPayload.model_validate(input_data)

    @pytest.mark.parametrize(
        "input_data, expected_mfa_required",
        [
            # Regular sign-in (no MFA)
            (
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "mfa_token": None,
                    "mfa_required": False,
                },
                False,
            ),
            # MFA required
            (
                {
                    "access_token": None,
                    "mfa_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "mfa_required": True,
                },
                True,
            ),
            # Default values
            (
                {},
                False,
            ),
        ],
    )
    def test_sign_in_response(self, input_data, expected_mfa_required):
        """Test SignInResponse initialization and validation."""
        response = SignInResponse.model_validate(input_data)

        # Check fields
        if "access_token" in input_data:
            assert response.access_token == input_data["access_token"]
        if "mfa_token" in input_data:
            assert response.mfa_token == input_data["mfa_token"]

        assert response.mfa_required == expected_mfa_required


class TestTransformJwtMethods:
    def test_user_membership_query_response_transform_jwt(self):
        """Test the transform_jwt method of UserMembershipQueryReponse."""
        # Create test data with services
        now = datetime.now(dt.UTC)
        user_data = {
            "uuid": "c47240a6-b1a6-7958-965c-39e89c975bb8",
            "role_id": 1,
            "username": "testuser",
            "firstname": "Test",
            "midname": "Middle",
            "lastname": "User",
            "email": "testuser@example.com",
            "phone": "+1234567890",
            "telegram": "@testuser",
            "password_hash": "hashedpassword",
            "is_active": True,
            "mfa_enabled": True,
            "mfa_secret": "TESTSECRET",
            "created_at": now,
            "created_by": "admin",
            "updated_at": now,
            "updated_by": "admin",
            "services": [
                {
                    "uuid": "d47240a6-b1a6-7958-965c-39e89c975bb9",
                    "name": "Service 1",
                    "description": "Test service",
                    "role": "admin",
                    "member_is_active": True,
                    "service_is_active": True,
                }
            ],
        }

        # Create object and transform
        user = UserMembershipQueryReponse.model_validate(user_data)
        jwt_data = user.transform_jwt()

        # JWT data should have strings instead of UUID objects
        assert jwt_data["uuid"] == str(user_data["uuid"])
        assert jwt_data["created_at"] == str(user_data["created_at"])
        assert jwt_data["updated_at"] == str(user_data["updated_at"])

        # Service UUID should be converted to string
        assert jwt_data["services"][0]["uuid"] == str(user_data["services"][0]["uuid"])

        # Sensitive fields should be excluded
        assert "password_hash" not in jwt_data
        assert "mfa_secret" not in jwt_data
        assert "deleted_at" not in jwt_data
        assert "deleted_by" not in jwt_data
        assert "role_id" not in jwt_data


class TestCreateUserQueryResponse:
    def test_transform_jwt_with_role(self):
        """Test that transform_jwt correctly formats user data with role for JWT."""
        user_data = {
            "uuid": "c47240a6-b1a6-7958-965c-39e89c975bb8",
            "role_id": 1,
            "username": "testuser",
            "firstname": "Test",
            "midname": "Middle",
            "lastname": "User",
            "email": "testuser@example.com",
            "phone": "+1234567890",
            "telegram": "@testuser",
            "password_hash": "hashedpassword",
            "is_active": True,
            "mfa_enabled": True,
            "mfa_secret": "TESTSECRET",
            "created_at": datetime.now(dt.UTC),
            "created_by": "admin",
            "updated_at": datetime.now(dt.UTC),
            "updated_by": "admin",
        }

        user = CreateUserQueryResponse.model_validate(user_data)
        jwt_data = user.transform_jwt(role="admin")

        # Check basic fields
        assert jwt_data["uuid"] == str(user_data["uuid"])
        assert jwt_data["username"] == user_data["username"]
        assert jwt_data["email"] == user_data["email"]
        assert jwt_data["role"] == "admin"

        # Sensitive data should be excluded
        assert "password_hash" not in jwt_data
        assert "mfa_secret" not in jwt_data


class TestCreateUserQuery:
    def test_create_user_query_with_mfa_secret(self):
        """Test that CreateUserQuery properly handles MFA secret."""
        data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "Password123!",
            "password_confirm": "Password123!",
            "firstname": "Test",
            "lastname": "User",
            "mfa_enabled": True,
            "mfa_secret": "TESTSECRET123",
        }

        # Convert password fields to SecretStr
        data["password"] = SecretStr(data["password"])
        data["password_confirm"] = SecretStr(data["password_confirm"])

        # Create query object
        query = CreateUserQuery.model_validate(data)

        # Check that MFA secret was properly set
        assert query.mfa_secret == "TESTSECRET123"
        assert query.mfa_enabled is True
