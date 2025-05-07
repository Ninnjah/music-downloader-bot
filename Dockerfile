# temp stage
FROM python:3.10-slim-bookworm AS builder

RUN apt-get update && apt-get install -y --no-install-recommends git
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Install dependencies
WORKDIR /app
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-editable

# Copy the project into the intermediate image
ADD . /app

# Sync the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable

# final stage
FROM python:3.10-slim-buster AS production

LABEL description="Music Downloader"
RUN apt-get update -q \
    && apt-get upgrade -y \
    && apt-get install --no-install-recommends -qy \
        ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder --chown=app:app /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

COPY . /app
CMD ["python", "bot.py"]