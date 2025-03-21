"""FastAPI authentication service main application module.

This module initializes the FastAPI application and defines the basic routes.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.config import settings
from app.integrations.redis import RedisHelper
from app.middleware.error_response import handle_error_response
from app.repositories.admin import AdminAsyncRepositories
from app.repositories.auth import AuthAsyncRepositories
from app.repositories.member import MemberAsyncRepositories
from app.repositories.roles import RoleAsyncRepositories
from app.repositories.services import ServiceAsyncRepositories
from app.routers.admin import router as admin_router
from app.routers.auth import router as auth_router
from app.routers.member import router as member_router
from app.routers.roles import router as roles_router
from app.routers.services import router as services_router
from app.services.admin import AdminService
from app.services.auth import AuthService
from app.services.member import MemberService
from app.services.roles import RoleService
from app.services.services import ServiceService


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa
    print("Initializing resources...")
    # integration
    redis = RedisHelper()

    auth_service = AuthService(
        repo_auth=AuthAsyncRepositories,
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

    member_repo = MemberAsyncRepositories()
    member_service = MemberService(
        repo_member=member_repo,
        redis=redis,
    )

    yield {
        "redis_helper": redis,
        "auth_service": auth_service,
        "admin_service": admin_service,
        "role_service": role_service,
        "service_service": service_service,
        "member_service": member_service,
    }

    print("Cleaning up resources...")


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


@app.get("/", include_in_schema=False)
async def root():  # noqa: ANN201
    return RedirectResponse("/docs")


# These two handlers can't be combined because they handle different exception types
# HTTPException handles explicit raised exceptions
app.add_exception_handler(HTTPException, handle_error_response)
# RequestValidationError handles request validation failures
app.add_exception_handler(RequestValidationError, handle_error_response)

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(member_router)
app.include_router(roles_router)
app.include_router(services_router)
