"""FastAPI authentication service main application module.

This module initializes the FastAPI application and defines the basic routes.
"""

from contextlib import asynccontextmanager

import structlog

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse

from app.config import settings
from app.helpers.logger import setup_logging
from app.helpers.response_api import JsonResponse
from app.integrations.redis import RedisHelper
from app.middleware.error_response import handle_error_response
from app.middleware.logger import logging_middleware
from app.repositories.admin import AdminAsyncRepositories
from app.repositories.auth import AuthAsyncRepositories
from app.repositories.business_roles import BusinessRoleAsyncRepositories
from app.repositories.member import MemberAsyncRepositories
from app.repositories.roles import RoleAsyncRepositories
from app.repositories.services import ServiceAsyncRepositories
from app.routers.admin import router as admin_router
from app.routers.auth import router as auth_router
from app.routers.business_roles import router as business_roles_router
from app.routers.member import router as member_router
from app.routers.roles import router as roles_router
from app.routers.services import router as services_router
from app.services.admin import AdminService
from app.services.auth import AuthService
from app.services.business_roles import BusinessRoleService
from app.services.member import MemberService
from app.services.roles import RoleService
from app.services.services import ServiceService


logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa
    setup_logging(log_level="DEBUG", enable_json_logs=True, enable_file_logs=True, is_async=False)
    logger.info("Initializing resources...")
    # integration
    redis = RedisHelper()
    member_repo = MemberAsyncRepositories()
    auth_repo = AuthAsyncRepositories()

    auth_service = AuthService(
        repo_auth=auth_repo,
        repo_member=member_repo,
        redis=redis,
    )

    admin_service = AdminService(
        repo_admin=AdminAsyncRepositories,
        redis=redis,
    )

    role_repo = RoleAsyncRepositories()
    role_service = RoleService(
        repo_roles=role_repo,
        redis=redis,
    )

    service_repo = ServiceAsyncRepositories()
    service_service = ServiceService(
        repo_services=service_repo,
        redis=redis,
    )

    member_service = MemberService(
        repo_member=member_repo,
        redis=redis,
    )

    # Business Role Service
    business_role_repo = BusinessRoleAsyncRepositories()
    business_role_service = BusinessRoleService(
        repo_business_roles=business_role_repo,
        redis=redis,
    )

    yield {
        "redis_helper": redis,
        "auth_service": auth_service,
        "admin_service": admin_service,
        "role_service": role_service,
        "service_service": service_service,
        "member_service": member_service,
        "business_role_service": business_role_service,
    }

    logger.info("Application is shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version=f"{settings.APP_VERSION}-{settings.APP_ENV}",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(logging_middleware)


# Custom Exception handler
@app.exception_handler(Exception)
async def handle_generic_exception(request: Request, exc: Exception):  # noqa
    message = str(exc)
    response = JsonResponse(
        data=None,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message=f"Failed to process your request due to: {message}",
        success=False,
        meta=None,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response.model_dump(mode="json"),
    )


@app.get("/", include_in_schema=False)
async def root():  # noqa: ANN201
    return RedirectResponse("/docs")


app.add_exception_handler(HTTPException, handle_error_response)
app.add_exception_handler(RequestValidationError, handle_error_response)

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(member_router)
app.include_router(roles_router)
app.include_router(business_roles_router)
app.include_router(services_router)
