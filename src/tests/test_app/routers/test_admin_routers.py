from unittest.mock import AsyncMock, patch

import pytest

from fastapi import status

from app.exceptions.admin import NoUsersFoundException
from app.helpers.generator import generate_uuid
from app.helpers.response_api import MetaResponse
from app.schemas.users import UserMembershipQueryReponse


@pytest.mark.asyncio
async def test_get_list_users_success(async_client, db_conn, override_role_admin):
    """Test the get_list_users endpoint when it returns data successfully."""
    user_profile, jwt_token = override_role_admin

    # Mock data
    mock_users = [
        {
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
        },
        {
            "uuid": str(generate_uuid()),
            "role": "user",
            "username": "testuser",
            "firstname": "Test",
            "lastname": "User",
            "email": "testuser@example.com",
            "phone": "+1234567891",
            "is_active": True,
            "mfa_enabled": False,
            "created_at": "2025-03-17T07:12:40.919356Z",
            "updated_at": "2025-03-17T07:12:40.919356Z",
            "services": [],
        },
    ]

    mock_meta = {
        "current_page": 1,
        "page_size": 2,
        "prev_page": False,
        "next_page": False,
        "total_pages": 1,
        "total_items": 2,
    }

    # Convert mock data to appropriate schema objects
    ls_users = [UserMembershipQueryReponse.model_validate(user) for user in mock_users]
    meta = MetaResponse.model_validate(mock_meta)

    # Mock the admin service
    mock_admin_service = AsyncMock()
    mock_admin_service.fetch_user_list.return_value = (ls_users, meta)

    with patch("starlette.datastructures.State.__getattr__", return_value=mock_admin_service):
        # Make the request with a query parameter
        response = await async_client.get(
            "/api/v1/admin/users",
            params={
                "page": 1,
                "limit": 5,
                "sort_by": "created_at",
                "sort_order": "desc",
            },
            headers={
                "Authorization": f"Bearer {jwt_token}",
                "accept": "application/json",
            },
        )

    response_json = response.json()
    print(f"{response_json=}")

    # Assertions
    assert response.status_code == status.HTTP_200_OK

    assert response_json["status_code"] == status.HTTP_200_OK
    assert response_json["message"] == "Successfully get list of users"

    # Check the returned data
    assert len(response_json["data"]) == 2
    assert response_json["data"][0]["username"] == "testadmin"
    assert response_json["data"][1]["username"] == "testuser"

    # Check the meta information
    assert response_json["meta"]["current_page"] == mock_meta["current_page"]
    assert response_json["meta"]["total_items"] == mock_meta["total_items"]

    # Verify mock was called with appropriate parameters
    mock_admin_service.fetch_user_list.assert_called_once()
    call_args = mock_admin_service.fetch_user_list.call_args
    # assert call_args is not None
    args, kwargs = call_args

    # Check the payload and current_user arguments
    assert kwargs["current_user"].uuid == user_profile.uuid
    assert kwargs["current_user"].role == user_profile.role
    assert kwargs["payload"].page == 1
    assert kwargs["payload"].limit == 5


@pytest.mark.asyncio
async def test_get_list_users_with_filters(async_client, db_conn, override_role_admin):
    """Test the get_list_users endpoint with query filters."""
    user_profile, jwt_token = override_role_admin

    # Mock data
    mock_user = {
        "uuid": "c47240a6-b1a6-7958-965c-39e89c975bb8",
        "role": "admin",
        "username": "testadmin",
        "firstname": "Test",
        "lastname": "User",
        "email": "testadmin@example.com",
        "is_active": True,
        "mfa_enabled": False,
        "created_at": "2025-03-17T07:12:39.919356Z",
        "updated_at": "2025-03-17T07:12:39.919356Z",
        "services": [],
    }

    mock_meta = {
        "current_page": 1,
        "page_size": 1,
        "prev_page": False,
        "next_page": False,
        "total_pages": 1,
        "total_items": 1,
    }

    # Convert mock data to appropriate schema objects
    users = [UserMembershipQueryReponse.model_validate(mock_user)]
    meta = MetaResponse.model_validate(mock_meta)

    # Mock the admin service
    mock_admin_service = AsyncMock()
    mock_admin_service.fetch_user_list.return_value = (users, meta)

    # Patch JWT permission and service
    with patch("starlette.datastructures.State.__getattr__", return_value=mock_admin_service):
        # Make the request with multiple query parameters
        response = await async_client.get(
            "/api/v1/admin/users",
            params={
                "page": 1,
                "limit": 10,
                "username": "testadmin",
                "is_active": True,
                "sort_by": "created_at",
                "sort_order": "desc",
            },
            headers={"Authorization": f"Bearer {jwt_token}"},
        )

    # Assertions
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert response_json["status_code"] == status.HTTP_200_OK

    # Check the returned data
    assert len(response_json["data"]) == 1
    assert response_json["data"][0]["username"] == "testadmin"

    # Verify mock was called with appropriate parameters
    mock_admin_service.fetch_user_list.assert_called_once()
    call_args = mock_admin_service.fetch_user_list.call_args
    assert call_args is not None
    args, kwargs = call_args

    # Check the payload arguments match the query parameters
    assert kwargs["payload"].username == "testadmin"
    assert kwargs["payload"].is_active is True
    assert kwargs["payload"].sort_by == "created_at"
    assert kwargs["payload"].sort_order.value == "desc"


@pytest.mark.asyncio
async def test_get_list_users_no_data(async_client, db_conn, override_role_admin):
    """Test the get_list_users endpoint when no users are found."""
    user_profile, jwt_token = override_role_admin
    # Mock the admin service to raise NoUsersFoundException
    mock_admin_service = AsyncMock()
    mock_admin_service.fetch_user_list.side_effect = NoUsersFoundException()

    # Patch JWT permission and service
    with patch("starlette.datastructures.State.__getattr__", return_value=mock_admin_service):
        # Make the request
        response = await async_client.get(
            "/api/v1/admin/users",
            headers={
                "Authorization": f"Bearer {jwt_token}",
            },
        )

    # Assertions
    assert response.status_code == status.HTTP_404_NOT_FOUND

    response_json = response.json()
    #! Note: the current implementation still not standarize error response, so we using `detail`
    assert response_json["detail"] == "No users found."


@pytest.mark.asyncio
async def test_get_list_users_unauthorized(async_client, db_conn):
    """Test the get_list_users endpoint with missing authorization."""
    # Make the request without authorization header
    response = await async_client.get("/api/v1/admin/users")

    # Assertions
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_get_user_admin_details_as_admin(async_client, db_conn, override_role_admin):
    """Test the get_user_admin_details endpoint as an admin user."""
    user_profile, jwt_token = override_role_admin

    # Mock data
    uuid_user = str(generate_uuid())
    mock_user = {
        "uuid": uuid_user,
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

    user_detail = UserMembershipQueryReponse.model_validate(mock_user)

    mock_admin_service = AsyncMock()
    mock_admin_service.fetch_user_details.return_value = user_detail

    # Patch JWT permission and service
    with patch("starlette.datastructures.State.__getattr__", return_value=mock_admin_service):
        # Make the request with multiple query parameters
        response = await async_client.get(
            f"/api/v1/admin/users/{uuid_user}",
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
    response_json = response.json()
    response_data = response_json["data"]

    # Assertions
    assert response.status_code == status.HTTP_200_OK

    assert response_data["uuid"] == uuid_user
    assert response_data["username"] == "testadmin"
    assert response_data["role"] == "admin"


@pytest.mark.asyncio
async def test_get_user_superadmin_details_as_admin(async_client, db_conn, override_role_admin):
    """Test the get_user_superadmin_details endpoint as an admin user.

    This test should be raised because the admin user should not be able to access superadmin details.
    """
    user_profile, jwt_token = override_role_admin

    # Mock data
    uuid_user = str(generate_uuid())

    mock_admin_service = AsyncMock()
    mock_admin_service.fetch_user_details.side_effect = NoUsersFoundException()

    # Patch JWT permission and service
    with patch("starlette.datastructures.State.__getattr__", return_value=mock_admin_service):
        # Make the request with multiple query parameters
        response = await async_client.get(
            f"/api/v1/admin/users/{uuid_user}",
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
    response_json = response.json()

    # Assertions
    assert response.status_code == status.HTTP_404_NOT_FOUND
    #! Note: the current implementation still not standarize error response, so we using `detail`
    assert response_json["detail"] == "No users found."
