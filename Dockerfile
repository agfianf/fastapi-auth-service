FROM python:3.12-slim

WORKDIR /code

# Install dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Install the application dependencies.
RUN --mount=from=ghcr.io/astral-sh/uv:0.6.6,source=/uv,target=/bin/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-dev --no-cache

# Copy the application into the container.
COPY ./src/app /code/src/app
COPY ./src/migrations /code/src/migrations
COPY ./src/alembic.ini /code/src/alembic.ini

# Create nonroot user and set permissions
RUN groupadd -r nonroot && useradd -r -g nonroot nonroot
USER nonroot

CMD ["/code/.venv/bin/uvicorn", "app.main:app", "--host",  "0.0.0.0", "--port", "8000"]
