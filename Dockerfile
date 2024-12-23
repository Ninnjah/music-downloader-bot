# temp stage
FROM python:3.10-slim-buster AS builder

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

RUN apt-get update -q \
    && apt-get upgrade -y \
    && apt-get install --no-install-recommends -qy \
        ffmpeg \
    && rm -rf /var/lib/apt/lists/*
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies
COPY pyproject.toml .
RUN pip install -U pip && pip install --no-cache-dir -e .

# final stage
FROM python:3.10-slim-buster AS production

LABEL description="Music Downloader"
WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

COPY . .
CMD ["python", "bot.py"]