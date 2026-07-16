# Pinned to Debian 12 (bookworm): Playwright 1.49 officially supports it, so
# `playwright install --with-deps chromium` resolves Chromium's OS libs cleanly. (Bare
# python:3.12-slim now tracks Debian 13/trixie, which Playwright's dep installer can't match.)
FROM python:3.12-slim-bookworm

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

# Headless Chromium for the monitoring browser-fetch (run-check). --with-deps pulls the OS
# libraries Chromium needs on the slim base. Single sequential page per fetch keeps RAM bounded.
# World-readable browser path so it resolves regardless of the runtime user.
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
# apt-get update first: the base image's earlier RUN cleared /var/lib/apt/lists, and
# `playwright install --with-deps` runs apt-get install (which needs a fresh package index).
RUN apt-get update \
    && python -m playwright install --with-deps chromium \
    && chmod -R a+rX /ms-playwright \
    && rm -rf /var/lib/apt/lists/*

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
