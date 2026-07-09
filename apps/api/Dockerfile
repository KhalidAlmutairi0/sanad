FROM python:3.12-slim

# bubblewrap: the sanitizer worker executes extraction inside a bwrap sandbox.
RUN apt-get update \
    && apt-get install -y --no-install-recommends bubblewrap \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY apps/api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY apps/api/ ./
# Seed scripts + data (run via `docker compose run --rm api python scripts/seed_regulations.py`).
COPY scripts/ /app/scripts/
# Sanitizer sources are also copied so the worker can run extract.py inside bwrap.
COPY sandboxes/sanitizer/ /sandboxes/sanitizer/

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
