#!/bin/sh
set -e

until nc -z -v -w30 db 5432
do
  echo "Waiting for database..."
  sleep 1
done

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collect static..."
python manage.py collectstatic --noinput
echo "Starting service..."
exec "$@"
