from unittest.mock import AsyncMock, patch

import pytest

from fastapi import status

from app.exceptions.roles import RoleNotFoundException
from app.helpers.response_api import MetaResponse
from app.schemas.roles.base import RoleBase
from app.schemas.roles.response import CreateRoleResponse, UpdateRoleResponse


@pytest.mark.asyncio
async def test_get_all_roles_success(async_client, db_conn, override_role_superadmin):
    """Test the get_all_roles endpoint when it returns data successfully."""
    user_profile, jwt_token = override_role_superadmin

    # Mock data
    mock_roles = [
        {"id": 1, "name": "superadmin", "description": "Super Administrator"},
        {"id": 2, "name": "admin", "description": "Administrator"},
        {"id": 3, "name": "staff", "description": "Staff Member"},
        {"id": 4, "name": "user", "description": "Regular User"},
    ]

    mock_meta = {
        "current_page": 1,
        "page_size": 4,
        "prev_page": False,
        "next_page": False,
        "total_pages": 1,
        "total_items": 4,
    }

    # Convert mock data to appropriate schema objects
    ls_roles = [RoleBase.model_validate(role) for role in mock_roles]
    meta = MetaResponse.model_validate(mock_meta)

    # Mock the role service
    mock_role_service = AsyncMock()
    mock_role_service.fetch_all_roles.return_value = (ls_roles, meta)

    with patch("starlette.datastructures.State.__getattr__", return_value=mock_role_service):
        # Make the request with query parameters
        response = await async_client.get(
            "/api/v1/roles",
            params={
                "page": 1,
                "limit": 10,
                "sort_by": "created_at",
                "sort_order": "desc",
            },
            headers={"Authorization": f"Bearer {jwt_token}"},
        )

    response_json = response.json()

    # Assertions
    assert response.status_code == status.HTTP_200_OK
    assert response_json["status_code"] == status.HTTP_200_OK
    assert response_json["message"] == "Successfully retrieved roles"

    # Check returned data
    assert len(response_json["data"]) == 4
    assert response_json["data"][0]["name"] == "superadmin"
    assert response_json["data"][1]["name"] == "admin"

    # Check meta information
    assert response_json["meta"]["current_page"] == mock_meta["current_page"]
    assert response_json["meta"]["total_items"] == mock_meta["total_items"]

    # Verify mock was called with appropriate parameters
    mock_role_service.fetch_all_roles.assert_called_once()
    call_args = mock_role_service.fetch_all_roles.call_args
    args, kwargs = call_args

    # Check the parameters
    assert kwargs["page"] == 1
    assert kwargs["limit"] == 10
    assert kwargs["sort_by"] == "created_at"
    assert kwargs["sort_order"].value == "desc"


@pytest.mark.asyncio
async def test_get_all_roles_unauthorized(async_client, db_conn):
    """Test the get_all_roles endpoint with missing authorization."""
    # Make the request without authorization header
    response = await async_client.get("/api/v1/roles")

    # Assertions
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_get_role_by_id_success(async_client, db_conn, override_role_superadmin):
    """Test the get_role_by_id endpoint when it returns data successfully."""
    user_profile, jwt_token = override_role_superadmin

    # Mock data
    mock_role = {"id": 2, "name": "admin", "description": "Administrator"}
    role_id = 2

    # Mock the role service
    mock_role_service = AsyncMock()
    mock_role_service.fetch_role_by_id.return_value = RoleBase.model_validate(mock_role)

    with patch("starlette.datastructures.State.__getattr__", return_value=mock_role_service):
        # Make the request
        response = await async_client.get(
            f"/api/v1/roles/{role_id}",
            headers={"Authorization": f"Bearer {jwt_token}"},
        )

    response_json = response.json()

    # Assertions
    assert response.status_code == status.HTTP_200_OK
    assert response_json["status_code"] == status.HTTP_200_OK
    assert response_json["message"] == "Successfully retrieved role"

    # Check returned data
    assert response_json["data"]["id"] == role_id
    assert response_json["data"]["name"] == "admin"
    assert response_json["data"]["description"] == "Administrator"

    # Verify mock was called with appropriate parameters
    mock_role_service.fetch_role_by_id.assert_called_once_with(
        role_id=role_id,
        connection=pytest.approx(db_conn, abs=1e-9),
    )


@pytest.mark.asyncio
async def test_get_role_by_id_not_found(async_client, db_conn, override_role_superadmin):
    """Test the get_role_by_id endpoint when the role is not found."""
    user_profile, jwt_token = override_role_superadmin
    role_id = 99

    # Mock the role service to raise an exception
    mock_role_service = AsyncMock()
    mock_role_service.fetch_role_by_id.side_effect = RoleNotFoundException()

    with patch("starlette.datastructures.State.__getattr__", return_value=mock_role_service):
        # Make the request
        response = await async_client.get(
            f"/api/v1/roles/{role_id}",
            headers={"Authorization": f"Bearer {jwt_token}"},
        )

    # Assertions
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_create_role_success(async_client, db_conn_trans, override_role_superadmin):
    """Test the create_role endpoint when it successfully creates a role."""
    user_profile, jwt_token = override_role_superadmin

    # Mock data
    payload = {
        "name": "manager",
        "description": "Department Manager",
    }
    mock_response = {
        "id": 5,
        "name": "manager",
        "description": "Department Manager",
    }

    # Mock the role service
    mock_role_service = AsyncMock()
    mock_role_service.create_role.return_value = CreateRoleResponse.model_validate(mock_response)

    with patch("starlette.datastructures.State.__getattr__", return_value=mock_role_service):
        # Make the request
        response = await async_client.post(
            "/api/v1/roles",
            data=payload,
            headers={"Authorization": f"Bearer {jwt_token}"},
        )

    response_json = response.json()

    # Assertions
    assert response.status_code == status.HTTP_201_CREATED
    assert response_json["status_code"] == status.HTTP_201_CREATED
    assert response_json["message"] == "Successfully created role"

    # Check returned data
    assert response_json["data"]["id"] == 5
    assert response_json["data"]["name"] == "manager"
    assert response_json["data"]["description"] == "Department Manager"

    # Verify mock was called with appropriate parameters
    mock_role_service.create_role.assert_called_once()
    call_args = mock_role_service.create_role.call_args
    args, kwargs = call_args

    # Check that the current_user and payload were passed correctly
    assert kwargs["current_user"].uuid == user_profile.uuid
    assert kwargs["current_user"].role == user_profile.role
    assert kwargs["payload"].name == payload["name"]
    assert kwargs["payload"].description == payload["description"]


@pytest.mark.asyncio
async def test_update_role_success(async_client, db_conn_trans, override_role_superadmin):
    """Test the update_role endpoint when it successfully updates a role."""
    user_profile, jwt_token = override_role_superadmin

    # Mock data
    role_id = 3
    payload = {
        "name": "supervisor",
        "description": "Team Supervisor",
    }
    mock_response = {
        "id": role_id,
        "name": "supervisor",
        "description": "Team Supervisor",
    }

    # Mock the role service
    mock_role_service = AsyncMock()
    mock_role_service.update_role.return_value = UpdateRoleResponse.model_validate(mock_response)

    with patch("starlette.datastructures.State.__getattr__", return_value=mock_role_service):
        # Make the request
        response = await async_client.put(
            f"/api/v1/roles/{role_id}",
            data=payload,
            headers={"Authorization": f"Bearer {jwt_token}"},
        )

    response_json = response.json()

    # Assertions
    assert response.status_code == status.HTTP_200_OK
    assert response_json["status_code"] == status.HTTP_200_OK
    assert response_json["message"] == "Successfully updated role"

    # Check returned data
    assert response_json["data"]["id"] == role_id
    assert response_json["data"]["name"] == "supervisor"
    assert response_json["data"]["description"] == "Team Supervisor"

    # Verify mock was called with appropriate parameters
    mock_role_service.update_role.assert_called_once()
    call_args = mock_role_service.update_role.call_args
    args, kwargs = call_args

    # Check that the parameters were passed correctly
    assert kwargs["current_user"].uuid == user_profile.uuid
    assert kwargs["current_user"].role == user_profile.role
    assert kwargs["role_id"] == role_id
    assert kwargs["payload"].name == payload["name"]
    assert kwargs["payload"].description == payload["description"]


@pytest.mark.asyncio
async def test_delete_role_success(async_client, db_conn_trans, override_role_superadmin):
    """Test the delete_role endpoint when it successfully deletes a role."""
    user_profile, jwt_token = override_role_superadmin

    role_id = 4

    # Mock the role service
    mock_role_service = AsyncMock()
    mock_role_service.delete_role.return_value = True

    with patch("starlette.datastructures.State.__getattr__", return_value=mock_role_service):
        # Make the request
        response = await async_client.delete(
            f"/api/v1/roles/{role_id}",
            headers={"Authorization": f"Bearer {jwt_token}"},
        )

    response_json = response.json()

    # Assertions
    assert response.status_code == status.HTTP_200_OK
    assert response_json["status_code"] == status.HTTP_200_OK
    assert response_json["message"] == "Successfully deleted role"
    assert response_json["data"] is None
    assert response_json["success"] is True

    # Verify mock was called with appropriate parameters
    mock_role_service.delete_role.assert_called_once()
    call_args = mock_role_service.delete_role.call_args
    args, kwargs = call_args

    # Check that the parameters were passed correctly
    assert kwargs["current_user"].uuid == user_profile.uuid
    assert kwargs["current_user"].role == user_profile.role
    assert kwargs["role_id"] == role_id


@pytest.mark.asyncio
async def test_delete_role_unauthorized(async_client, db_conn_trans):
    """Test the delete_role endpoint with missing authorization."""
    role_id = 4

    # Make the request without authorization header
    response = await async_client.delete(f"/api/v1/roles/{role_id}")

    # Assertions
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_delete_role_failed(async_client, db_conn_trans, override_role_superadmin):
    """Test the delete_role endpoint when the delete operation fails."""
    user_profile, jwt_token = override_role_superadmin

    role_id = 1  # Assuming role ID 1 is a protected role that cannot be deleted

    # Mock the role service to return False (delete failed)
    mock_role_service = AsyncMock()
    mock_role_service.delete_role.return_value = False

    with patch("starlette.datastructures.State.__getattr__", return_value=mock_role_service):
        # Make the request
        response = await async_client.delete(
            f"/api/v1/roles/{role_id}",
            headers={"Authorization": f"Bearer {jwt_token}"},
        )

    response_json = response.json()

    # Assertions
    assert response.status_code == status.HTTP_200_OK
    assert response_json["status_code"] == status.HTTP_200_OK
    assert response_json["message"] == "Successfully deleted role"
    assert response_json["data"] is None
    assert response_json["success"] is False  # Operation failed
