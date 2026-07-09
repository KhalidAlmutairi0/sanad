#!/bin/sh
# One image, two roles. On a PaaS set ROLE=api or ROLE=worker per application.
# (docker-compose overrides the command explicitly, so this is only the default path.)
set -e
case "${ROLE:-api}" in
  api)    exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" ;;
  worker) exec arq app.workers.main.WorkerSettings ;;
  *)      echo "unknown ROLE=$ROLE (expected api|worker)" >&2; exit 1 ;;
esac
