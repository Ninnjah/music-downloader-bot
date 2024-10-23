FROM python:3.10-alpine as production
LABEL description="Aiogram 3 Template"

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir .

COPY . .

ARG config=config.yaml

COPY $config ./config.yaml

ENTRYPOINT ["python", "./start.py"]
