FROM python:3.12-slim AS builder

WORKDIR /app
COPY pyproject.toml .
COPY src/ ./src/
RUN pip install --no-cache-dir .

FROM python:3.12-slim

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/uvicorn /usr/local/bin/uvicorn
COPY src/ ./src/

ENV PORT=8080
EXPOSE 8080
CMD uvicorn grounded_qa.main:app --host 0.0.0.0 --port $PORT
