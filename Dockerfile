# temp stage
FROM python:3.10-slim-bookworm AS builder

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates git
ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh

ENV PATH="/root/.local/bin/:$PATH"
ENV UV_COMPILE_BYTECODE=1

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Install dependencies
WORKDIR /app
COPY pyproject.toml .
RUN uv sync --no-cache --no-install-project

# final stage
FROM python:3.10-slim-buster AS production

LABEL description="Music Downloader"
RUN apt-get update -q \
    && apt-get upgrade -y \
    && apt-get install --no-install-recommends -qy \
        ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

COPY . .
CMD ["python", "bot.py"]