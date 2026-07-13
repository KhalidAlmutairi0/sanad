FROM python:3.12-slim

# bubblewrap: the sanitizer worker executes extraction inside a bwrap sandbox.
# tesseract-ocr (+ Arabic data) and poppler-utils: offline OCR fallback for scanned PDFs.
# All run with no network, so the sandbox's containment guarantee is preserved.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bubblewrap tesseract-ocr tesseract-ocr-ara tesseract-ocr-eng poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY apps/api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY apps/api/ ./
# Seed scripts + data (run via `docker compose run --rm api python scripts/seed_regulations.py`).
COPY scripts/ /app/scripts/
# Sanitizer sources are also copied so the worker can run extract.py inside bwrap.
COPY sandboxes/sanitizer/ /sandboxes/sanitizer/

RUN chmod +x /app/entrypoint.sh

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000
# Role selected by $ROLE (api|worker). compose overrides this per service.
CMD ["/app/entrypoint.sh"]
