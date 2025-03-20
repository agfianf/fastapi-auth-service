# conftest.py
import time

import pytest_asyncio

from app.depedencies.auth import role_admin
from app.helpers.generator import generate_uuid
from app.helpers.generator_jwt import create_access_token
from app.main import app
from app.schemas.users.query import UserMembershipQueryReponse


def get_base_info_user() -> UserMembershipQueryReponse:
    return {
        "uuid": str(generate_uuid()),
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


def get_data_user_admin_valid_wo_mfa() -> tuple[UserMembershipQueryReponse, str]:
    timenow = time.time()
    expire_minutes_access = 3

    data = get_base_info_user()
    data["role"] = "admin"

    data_jwt = {
        **data,
        "expire_time": timenow + (60 * expire_minutes_access),
    }
    user_valid_jwt = create_access_token(data=data_jwt)

    return UserMembershipQueryReponse(**data), user_valid_jwt


def get_data_user_superadmin_valid() -> tuple[UserMembershipQueryReponse, str]:
    timenow = time.time()
    expire_minutes_access = 3

    data = get_base_info_user()
    data["role"] = "superadmin"
    data["is_active"] = True
    data["mfa_enabled"] = True

    data_jwt = {
        **data,
        "expire_time": timenow + (60 * expire_minutes_access),
    }
    user_valid_jwt = create_access_token(data=data_jwt)

    return UserMembershipQueryReponse(**data), user_valid_jwt


# ---override authenticator----
@pytest_asyncio.fixture
async def override_role_superadmin_in_admin():
    """Override role checker for admin role wo mfa."""
    data = get_data_user_superadmin_valid()
    app.dependency_overrides[role_admin] = lambda: data

    yield data
    # Cleanup after test
    app.dependency_overrides.pop(role_admin, None)


@pytest_asyncio.fixture
async def override_role_admin():
    """Override role checker for admin role wo mfa."""
    data = get_data_user_admin_valid_wo_mfa()
    app.dependency_overrides[role_admin] = lambda: data

    yield data
    # Cleanup after test
    app.dependency_overrides.pop(role_admin, None)
