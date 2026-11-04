#!/bin/sh
set -eu
psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" --set=reader_password="$ANALYTICS_READER_PASSWORD" --file=/bootstrap/analytics.sql
