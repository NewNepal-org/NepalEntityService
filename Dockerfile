FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml poetry.lock README.md ./
COPY nes2/ ./nes2/
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --extras api --only=main

COPY nes-db/ ./nes-db/
COPY docs/ ./docs/

EXPOSE 8195

CMD ["nes2-api"]