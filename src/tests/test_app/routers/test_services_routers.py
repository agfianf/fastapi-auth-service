from unittest.mock import AsyncMock, patch

import pytest

from fastapi import status
from uuid_utils.compat import UUID

from app.exceptions.services import (
    ServiceCreationFailedException,
    ServiceDeletionFailedException,
    ServiceNameAlreadyExistsException,
    ServiceNotFoundException,
    ServiceUpdateFailedException,
)
from app.helpers.generator import generate_uuid
from app.helpers.response_api import MetaResponse
from app.schemas.services.base import ServiceBase


@pytest.mark.asyncio
async def test_get_all_services_success(async_client, db_conn, override_role_admin):
    """Test the get_all_services endpoint when it returns services successfully."""
    user_profile, jwt_token = override_role_admin

    # Mock data
    mock_services = [
        {
            "uuid": str(generate_uuid()),
            "name": "Service 1",
            "location": "Location 1",
            "description": "Description for Service 1",
            "is_active": True,
            "created_at": "2025-03-17T07:12:39.919356Z",
            "created_by": "admin@example.com",
            "updated_at": "2025-03-17T07:12:39.919356Z",
            "updated_by": "admin@example.com",
            "deleted_at": None,
            "deleted_by": None,
        },
        {
            "uuid": str(generate_uuid()),
            "name": "Service 2",
            "location": "Location 2",
            "description": "Description for Service 2",
            "is_active": False,
            "created_at": "2025-03-17T08:12:39.919356Z",
            "created_by": "admin@example.com",
            "updated_at": "2025-03-17T08:12:39.919356Z",
            "updated_by": "admin@example.com",
            "deleted_at": None,
            "deleted_by": None,
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
    services = [ServiceBase.model_validate(service) for service in mock_services]
    meta = MetaResponse.model_validate(mock_meta)

    # Mock the service service
    mock_service_service = AsyncMock()
    mock_service_service.fetch_all_services.return_value = (services, meta)

    with patch("starlette.datastructures.State.__getattr__", return_value=mock_service_service):
        # Make the request with query parameters
        response = await async_client.get(
            "/api/v1/services",
            params={
                "page": 1,
                "limit": 10,
                "name": None,
                "is_active": None,
                "sort_by": "created_at",
                "sort_order": "desc",
            },
            headers={
                "Authorization": f"Bearer {jwt_token}",
                "accept": "application/json",
            },
        )

    response_json = response.json()

    # Assertions
    assert response.status_code == status.HTTP_200_OK
    assert response_json["status_code"] == status.HTTP_200_OK
    assert response_json["message"] == "Successfully retrieved services"

    # Check the returned data
    assert len(response_json["data"]) == 2
    assert response_json["data"][0]["name"] == "Service 1"
    assert response_json["data"][1]["name"] == "Service 2"

    # Check the meta information
    assert response_json["meta"]["current_page"] == mock_meta["current_page"]
    assert response_json["meta"]["total_items"] == mock_meta["total_items"]

    # Verify mock was called with correct parameters
    mock_service_service.fetch_all_services.assert_called_once()
    call_args = mock_service_service.fetch_all_services.call_args
    args, kwargs = call_args

    # Check the payload was passed correctly
    assert kwargs["payload"].page == 1
    assert kwargs["payload"].limit == 10
    assert kwargs["payload"].sort_by == "created_at"
    assert kwargs["payload"].sort_order == "desc"


@pytest.mark.asyncio
async def test_get_all_services_with_filters(async_client, db_conn, override_role_admin):
    """Test the get_all_services endpoint with filters."""
    user_profile, jwt_token = override_role_admin

    # Mock data
    mock_service = {
        "uuid": str(generate_uuid()),
        "name": "Active Service",
        "location": "Location",
        "description": "An active service",
        "is_active": True,
        "created_at": "2025-03-17T07:12:39.919356Z",
        "created_by": "admin@example.com",
        "updated_at": "2025-03-17T07:12:39.919356Z",
        "updated_by": "admin@example.com",
        "deleted_at": None,
        "deleted_by": None,
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
    services = [ServiceBase.model_validate(mock_service)]
    meta = MetaResponse.model_validate(mock_meta)

    # Mock the service service
    mock_service_service = AsyncMock()
    mock_service_service.fetch_all_services.return_value = (services, meta)

    with patch("starlette.datastructures.State.__getattr__", return_value=mock_service_service):
        # Make the request with filters
        response = await async_client.get(
            "/api/v1/services",
            params={
                "page": 1,
                "limit": 10,
                "name": "Active",
                "is_active": True,
                "sort_by": "name",
                "sort_order": "asc",
            },
            headers={"Authorization": f"Bearer {jwt_token}"},
        )

    response_json = response.json()

    # Assertions
    assert response.status_code == status.HTTP_200_OK
    assert response_json["status_code"] == status.HTTP_200_OK
    assert len(response_json["data"]) == 1
    assert response_json["data"][0]["name"] == "Active Service"
    assert response_json["data"][0]["is_active"] is True

    # Verify mock was called with correct parameters
    mock_service_service.fetch_all_services.assert_called_once()
    call_args = mock_service_service.fetch_all_services.call_args
    args, kwargs = call_args

    # Check that the filters were passed correctly
    assert kwargs["payload"].name == "Active"
    assert kwargs["payload"].is_active is True
    assert kwargs["payload"].sort_by == "name"
    assert kwargs["payload"].sort_order == "asc"


@pytest.mark.asyncio
async def test_get_all_services_no_data(async_client, db_conn, override_role_admin):
    """Test the get_all_services endpoint when no services are found."""
    user_profile, jwt_token = override_role_admin

    # Mock empty data
    mock_meta = {
        "current_page": 1,
        "page_size": 0,
        "prev_page": False,
        "next_page": False,
        "total_pages": 0,
        "total_items": 0,
    }

    # Convert mock data to appropriate schema objects
    services = []
    meta = MetaResponse.model_validate(mock_meta)

    # Mock the service service
    mock_service_service = AsyncMock()
    mock_service_service.fetch_all_services.return_value = (services, meta)

    with patch("starlette.datastructures.State.__getattr__", return_value=mock_service_service):
        response = await async_client.get(
            "/api/v1/services",
            headers={"Authorization": f"Bearer {jwt_token}"},
        )

    response_json = response.json()

    # Assertions
    assert response.status_code == status.HTTP_200_OK
    assert response_json["status_code"] == status.HTTP_200_OK
    assert response_json["message"] == "Successfully retrieved services"
    assert len(response_json["data"]) == 0
    assert response_json["meta"]["total_items"] == 0


@pytest.mark.asyncio
async def test_get_all_services_unauthorized(async_client, db_conn):
    """Test the get_all_services endpoint with missing authorization."""
    # Make the request without authorization header
    response = await async_client.get("/api/v1/services")

    # Assertions
    assert response.status_code == status.HTTP_403_FORBIDDEN


# --------------------------------
# Tests for get_service_by_uuid
# --------------------------------


@pytest.mark.asyncio
async def test_get_service_by_uuid_success(async_client, db_conn, override_role_admin):
    """Test the get_service_by_uuid endpoint when it returns a service successfully."""
    user_profile, jwt_token = override_role_admin

    # Mock data
    service_uuid = str(generate_uuid())
    mock_service = {
        "uuid": service_uuid,
        "name": "Test Service",
        "location": "Test Location",
        "description": "Test Description",
        "is_active": True,
        "created_at": "2025-03-17T07:12:39.919356Z",
        "created_by": "admin@example.com",
        "updated_at": "2025-03-17T07:12:39.919356Z",
        "updated_by": "admin@example.com",
        "deleted_at": None,
        "deleted_by": None,
    }

    # Mock the service service
    mock_service_service = AsyncMock()
    mock_service_service.fetch_service_by_uuid.return_value = ServiceBase.model_validate(mock_service)

    with patch("starlette.datastructures.State.__getattr__", return_value=mock_service_service):
        response = await async_client.get(
            f"/api/v1/services/{service_uuid}",
            headers={"Authorization": f"Bearer {jwt_token}"},
        )

    response_json = response.json()

    # Assertions
    assert response.status_code == status.HTTP_200_OK
    assert response_json["status_code"] == status.HTTP_200_OK
    assert response_json["message"] == "Successfully retrieved service"

    # Check that the correct service was returned
    assert response_json["data"]["uuid"] == service_uuid
    assert response_json["data"]["name"] == "Test Service"
    assert response_json["data"]["description"] == "Test Description"
    assert response_json["data"]["is_active"] is True

    # Verify mock was called with correct parameters
    mock_service_service.fetch_service_by_uuid.assert_called_once_with(
        service_uuid=UUID(service_uuid),
        connection=db_conn,
    )


@pytest.mark.asyncio
async def test_get_service_by_uuid_not_found(async_client, db_conn, override_role_admin):
    """Test the get_service_by_uuid endpoint when the service is not found."""
    user_profile, jwt_token = override_role_admin

    service_uuid = str(generate_uuid())

    # Mock the service service to raise ServiceNotFoundException
    mock_service_service = AsyncMock()
    mock_service_service.fetch_service_by_uuid.side_effect = ServiceNotFoundException()

    with patch("starlette.datastructures.State.__getattr__", return_value=mock_service_service):
        response = await async_client.get(
            f"/api/v1/services/{service_uuid}",
            headers={"Authorization": f"Bearer {jwt_token}"},
        )

    # Assertions
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["message"] == "Service not found"


@pytest.mark.asyncio
async def test_get_service_by_uuid_unauthorized(async_client, db_conn):
    """Test the get_service_by_uuid endpoint with missing authorization."""
    service_uuid = str(generate_uuid())

    # Make the request without authorization header
    response = await async_client.get(f"/api/v1/services/{service_uuid}")

    # Assertions
    assert response.status_code == status.HTTP_403_FORBIDDEN


# --------------------------------
# Tests for create_service
# --------------------------------


@pytest.mark.asyncio
async def test_create_service_success(async_client, db_conn_trans, override_role_admin):
    """Test the create_service endpoint when it successfully creates a service."""
    user_profile, jwt_token = override_role_admin

    # Service data to create
    service_data = {
        "name": "New Service",
        "location": "New Location",
        "description": "New service description",
        "is_active": True,
    }

    # Mock the created service
    service_uuid = str(generate_uuid())
    mock_created_service = {
        "uuid": service_uuid,
        **service_data,
        "created_at": "2025-03-17T07:12:39.919356Z",
        "created_by": user_profile.email,
        "updated_at": "2025-03-17T07:12:39.919356Z",
        "updated_by": user_profile.email,
        "deleted_at": None,
        "deleted_by": None,
    }

    # Mock the service service
    mock_service_service = AsyncMock()
    mock_service_service.create_service.return_value = ServiceBase.model_validate(mock_created_service)

    with patch("starlette.datastructures.State.__getattr__", return_value=mock_service_service):
        response = await async_client.post(
            "/api/v1/services",
            data=service_data,
            headers={"Authorization": f"Bearer {jwt_token}"},
        )

    response_json = response.json()

    # Assertions
    assert response.status_code == status.HTTP_201_CREATED
    assert response_json["status_code"] == status.HTTP_201_CREATED
    assert response_json["message"] == "Successfully created service"

    # Check the created service data
    assert response_json["data"]["uuid"] == service_uuid
    assert response_json["data"]["name"] == "New Service"
    assert response_json["data"]["location"] == "New Location"
    assert response_json["data"]["description"] == "New service description"
    assert response_json["data"]["is_active"] is True

    # Verify mock was called with correct parameters
    mock_service_service.create_service.assert_called_once()
    call_args = mock_service_service.create_service.call_args
    args, kwargs = call_args

    assert kwargs["current_user"].uuid == user_profile.uuid
    assert kwargs["payload"].name == service_data["name"]
    assert kwargs["payload"].location == service_data["location"]
    assert kwargs["payload"].description == service_data["description"]
    assert kwargs["payload"].is_active == service_data["is_active"]


@pytest.mark.asyncio
async def test_create_service_name_exists(async_client, db_conn_trans, override_role_admin):
    """Test the create_service endpoint when the service name already exists."""
    user_profile, jwt_token = override_role_admin

    # Service data to create
    service_data = {
        "name": "Existing Service",
        "location": "Some Location",
        "description": "Service description",
        "is_active": True,
    }

    # Mock the service service to raise ServiceNameAlreadyExistsException
    mock_service_service = AsyncMock()
    mock_service_service.create_service.side_effect = ServiceNameAlreadyExistsException()

    with patch("starlette.datastructures.State.__getattr__", return_value=mock_service_service):
        response = await async_client.post(
            "/api/v1/services",
            data=service_data,
            headers={"Authorization": f"Bearer {jwt_token}"},
        )

    # Assertions
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["message"] == "Service with this name already exists"


@pytest.mark.asyncio
async def test_create_service_failure(async_client, db_conn_trans, override_role_admin):
    """Test the create_service endpoint when service creation fails."""
    user_profile, jwt_token = override_role_admin

    # Service data to create
    service_data = {
        "name": "Failed Service",
        "location": "Some Location",
        "description": "Service description",
        "is_active": True,
    }

    # Mock the service service to raise ServiceCreationFailedException
    mock_service_service = AsyncMock()
    mock_service_service.create_service.side_effect = ServiceCreationFailedException()

    with patch("starlette.datastructures.State.__getattr__", return_value=mock_service_service):
        response = await async_client.post(
            "/api/v1/services",
            data=service_data,
            headers={"Authorization": f"Bearer {jwt_token}"},
        )

    # Assertions
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json()["message"] == "Failed to create service"


@pytest.mark.asyncio
async def test_create_service_unauthorized(async_client, db_conn_trans):
    """Test the create_service endpoint with missing authorization."""
    service_data = {
        "name": "Unauthorized Service",
        "location": "Some Location",
        "description": "Service description",
        "is_active": True,
    }

    # Make the request without authorization header
    response = await async_client.post("/api/v1/services", data=service_data)

    # Assertions
    assert response.status_code == status.HTTP_403_FORBIDDEN


# --------------------------------
# Tests for update_service
# --------------------------------


@pytest.mark.asyncio
async def test_update_service_success(async_client, db_conn_trans, override_role_admin):
    """Test the update_service endpoint when it successfully updates a service."""
    user_profile, jwt_token = override_role_admin

    # Service UUID and update data
    service_uuid = str(generate_uuid())
    update_data = {
        "name": "Updated Service",
        "description": "Updated description",
        "is_active": False,
    }

    # Mock the updated service
    mock_updated_service = {
        "uuid": service_uuid,
        "name": "Updated Service",
        "location": "Original Location",  # Unchanged
        "description": "Updated description",
        "is_active": False,
        "created_at": "2025-03-17T07:12:39.919356Z",
        "created_by": "admin@example.com",
        "updated_at": "2025-03-18T07:12:39.919356Z",  # Note this changed
        "updated_by": user_profile.email,  # Changed to current user
        "deleted_at": None,
        "deleted_by": None,
    }

    # Mock the service service
    mock_service_service = AsyncMock()
    mock_service_service.update_service.return_value = ServiceBase.model_validate(mock_updated_service)

    with patch("starlette.datastructures.State.__getattr__", return_value=mock_service_service):
        response = await async_client.put(
            f"/api/v1/services/{service_uuid}",
            data=update_data,
            headers={"Authorization": f"Bearer {jwt_token}"},
        )

    response_json = response.json()

    # Assertions
    assert response.status_code == status.HTTP_200_OK
    assert response_json["status_code"] == status.HTTP_200_OK
    assert response_json["message"] == "Successfully updated service"

    # Check the updated service data
    assert response_json["data"]["uuid"] == service_uuid
    assert response_json["data"]["name"] == "Updated Service"
    assert response_json["data"]["description"] == "Updated description"
    assert response_json["data"]["is_active"] is False

    # Verify mock was called with correct parameters
    mock_service_service.update_service.assert_called_once()
    call_args = mock_service_service.update_service.call_args
    args, kwargs = call_args

    assert kwargs["current_user"].uuid == user_profile.uuid
    assert str(kwargs["service_uuid"]) == service_uuid
    assert kwargs["payload"].name == update_data["name"]
    assert kwargs["payload"].description == update_data["description"]
    assert kwargs["payload"].is_active == update_data["is_active"]


@pytest.mark.asyncio
async def test_update_service_not_found(async_client, db_conn_trans, override_role_admin):
    """Test the update_service endpoint when the service is not found."""
    user_profile, jwt_token = override_role_admin

    service_uuid = str(generate_uuid())
    update_data = {
        "name": "Non-existent Service",
        "description": "This service doesn't exist",
        "is_active": True,
    }

    # Mock the service service to raise ServiceNotFoundException
    mock_service_service = AsyncMock()
    mock_service_service.update_service.side_effect = ServiceNotFoundException()

    with patch("starlette.datastructures.State.__getattr__", return_value=mock_service_service):
        response = await async_client.put(
            f"/api/v1/services/{service_uuid}",
            data=update_data,
            headers={"Authorization": f"Bearer {jwt_token}"},
        )

    # Assertions
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["message"] == "Service not found"


@pytest.mark.asyncio
async def test_update_service_name_exists(async_client, db_conn_trans, override_role_admin):
    """Test the update_service endpoint when the new name already exists."""
    user_profile, jwt_token = override_role_admin

    service_uuid = str(generate_uuid())
    update_data = {
        "name": "Existing Service Name",
    }

    # Mock the service service to raise ServiceNameAlreadyExistsException
    mock_service_service = AsyncMock()
    mock_service_service.update_service.side_effect = ServiceNameAlreadyExistsException()

    with patch("starlette.datastructures.State.__getattr__", return_value=mock_service_service):
        response = await async_client.put(
            f"/api/v1/services/{service_uuid}",
            data=update_data,
            headers={"Authorization": f"Bearer {jwt_token}"},
        )

    # Assertions
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["message"] == "Service with this name already exists"


@pytest.mark.asyncio
async def test_update_service_failure(async_client, db_conn_trans, override_role_admin):
    """Test the update_service endpoint when service update fails."""
    user_profile, jwt_token = override_role_admin

    service_uuid = str(generate_uuid())
    update_data = {
        "name": "Failed Update Service",
    }

    # Mock the service service to raise ServiceUpdateFailedException
    mock_service_service = AsyncMock()
    mock_service_service.update_service.side_effect = ServiceUpdateFailedException()

    with patch("starlette.datastructures.State.__getattr__", return_value=mock_service_service):
        response = await async_client.put(
            f"/api/v1/services/{service_uuid}",
            data=update_data,
            headers={"Authorization": f"Bearer {jwt_token}"},
        )

    # Assertions
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json()["message"] == "Failed to update service"


@pytest.mark.asyncio
async def test_update_service_unauthorized(async_client, db_conn_trans):
    """Test the update_service endpoint with missing authorization."""
    service_uuid = str(generate_uuid())
    update_data = {
        "name": "Unauthorized Update",
    }

    # Make the request without authorization header
    response = await async_client.put(
        f"/api/v1/services/{service_uuid}",
        data=update_data,
    )

    # Assertions
    assert response.status_code == status.HTTP_403_FORBIDDEN


# --------------------------------
# Tests for delete_service
# --------------------------------


@pytest.mark.asyncio
async def test_delete_service_success(async_client, db_conn_trans, override_role_admin):
    """Test the delete_service endpoint when it successfully deletes a service."""
    user_profile, jwt_token = override_role_admin

    service_uuid = str(generate_uuid())

    # Mock the service service
    mock_service_service = AsyncMock()
    mock_service_service.delete_service.return_value = True

    with patch("starlette.datastructures.State.__getattr__", return_value=mock_service_service):
        response = await async_client.delete(
            f"/api/v1/services/{service_uuid}",
            headers={"Authorization": f"Bearer {jwt_token}"},
        )

    response_json = response.json()

    # Assertions
    assert response.status_code == status.HTTP_200_OK
    assert response_json["status_code"] == status.HTTP_200_OK
    assert response_json["message"] == "Successfully deleted service"
    assert response_json["success"] is True
    assert response_json["data"] is None

    # Verify mock was called with correct parameters
    mock_service_service.delete_service.assert_called_once_with(
        current_user=user_profile,
        service_uuid=UUID(service_uuid),
        connection=db_conn_trans,
    )


@pytest.mark.asyncio
async def test_delete_service_not_found(async_client, db_conn_trans, override_role_admin):
    """Test the delete_service endpoint when the service is not found."""
    user_profile, jwt_token = override_role_admin

    service_uuid = str(generate_uuid())

    # Mock the service service to raise ServiceNotFoundException
    mock_service_service = AsyncMock()
    mock_service_service.delete_service.side_effect = ServiceNotFoundException()

    with patch("starlette.datastructures.State.__getattr__", return_value=mock_service_service):
        response = await async_client.delete(
            f"/api/v1/services/{service_uuid}",
            headers={"Authorization": f"Bearer {jwt_token}"},
        )

    # Assertions
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["message"] == "Service not found"


@pytest.mark.asyncio
async def test_delete_service_failure(async_client, db_conn_trans, override_role_admin):
    """Test the delete_service endpoint when service deletion fails."""
    user_profile, jwt_token = override_role_admin

    service_uuid = str(generate_uuid())

    # Mock the service service to raise ServiceDeletionFailedException
    mock_service_service = AsyncMock()
    mock_service_service.delete_service.side_effect = ServiceDeletionFailedException()

    with patch("starlette.datastructures.State.__getattr__", return_value=mock_service_service):
        response = await async_client.delete(
            f"/api/v1/services/{service_uuid}",
            headers={"Authorization": f"Bearer {jwt_token}"},
        )

    # Assertions
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json()["message"] == "Failed to delete service"


@pytest.mark.asyncio
async def test_delete_service_unauthorized(async_client, db_conn_trans):
    """Test the delete_service endpoint with missing authorization."""
    service_uuid = str(generate_uuid())

    # Make the request without authorization header
    response = await async_client.delete(f"/api/v1/services/{service_uuid}")

    # Assertions
    assert response.status_code == status.HTTP_403_FORBIDDEN
