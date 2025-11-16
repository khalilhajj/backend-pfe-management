#!/bin/sh

echo "Waiting for Postgres..."
while ! nc -z $DATABASE_HOST $DATABASE_PORT; do
  sleep 0.5
done

echo "Postgres is up!"

echo "Running Django makemigrations..."
python manage.py makemigrations

echo "running migrations for auth app..."
python manage.py makemigrations authentication

echo "running migrations for student app..."
python manage.py makemigrations student

echo "running migrations for internship app..."
python manage.py makemigrations internship

echo "Running Django migrate..."
python manage.py migrate

echo "Starting Django server..."
python manage.py runserver 0.0.0.0:8000