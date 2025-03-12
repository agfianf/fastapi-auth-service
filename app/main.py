"""FastAPI authentication service main application module.

This module initializes the FastAPI application and defines the basic routes.
"""

from fastapi import FastAPI
from fastapi.responses import RedirectResponse


app = FastAPI()


@app.get("/up")
async def up() -> str:
    return "ok"


@app.get("/")
async def root() -> RedirectResponse:
    return RedirectResponse(url="/docs")
