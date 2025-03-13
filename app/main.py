"""FastAPI authentication service main application module.

This module initializes the FastAPI application and defines the basic routes.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from src.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa
    print("Initializing resources...")
    yield
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
