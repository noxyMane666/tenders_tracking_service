#!/bin/sh
set -e

alembic upgrade head
exec uvicorn run:application --host 0.0.0.0 --port 8000
