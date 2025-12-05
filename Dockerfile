FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml poetry.lock README.md ./
COPY nes/ ./nes/
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --extras api --only=main

# Copy database directory and ensure v2 subdirectory exists
COPY nes-db/ ./nes-db/
RUN mkdir -p ./nes-db/v2

COPY docs/ ./docs/
COPY .kiro/ ./.kiro/

# Set default NES_DB_URL for container
ENV NES_DB_URL=file+memcached:///app/nes-db/v2

EXPOSE 8080

CMD ["nes-api"]