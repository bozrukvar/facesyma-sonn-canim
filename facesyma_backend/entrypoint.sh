#!/bin/sh
set -e

# Wait for MongoDB to be ready
echo "Waiting for MongoDB..."
until python -c "from pymongo import MongoClient; MongoClient(\"${MONGO_URI:-mongodb://mongodb:27017/}\").admin.command('ping')" 2>/dev/null; do
    sleep 2
done
echo "MongoDB ready."

# Seed attribute databases (idempotent — uses upsert)
echo "Seeding attribute databases..."
python /app/seed_attribute_databases.py || echo "Seed warning (non-fatal)"

# Seed communities (47 predefined: ASTRO, INTEREST, LIFESTYLE, FACE, COLORTYPE, GOAL)
echo "Seeding communities..."
python manage.py seed_communities || echo "Community seed warning (non-fatal)"

# Start the server
exec daphne -b 0.0.0.0 -p 8000 facesyma_project.asgi:application
