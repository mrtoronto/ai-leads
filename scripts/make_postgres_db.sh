#!/bin/bash

# Load environment variables from .env file
set -a
source .env
set +a

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Ensure psql is installed
if ! command_exists psql; then
    echo "psql command not found. Please install PostgreSQL."
    exit 1
fi

# Ensure flask is installed
if ! command_exists flask; then
    echo "flask command not found. Please ensure Flask is installed and your virtual environment is activated."
    exit 1
fi

# Create the PostgreSQL user and database
echo "Setting up PostgreSQL user and database..."
psql postgres -c "CREATE DATABASE $DB_NAME;"
psql postgres -c "CREATE USER $DB_USER WITH ENCRYPTED PASSWORD '$DB_PASS';"
psql postgres -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"

# Grant necessary privileges
echo "Granting privileges..."
psql -U postgres -d $DB_NAME -c "GRANT USAGE ON SCHEMA public TO $DB_USER;"
psql -U postgres -d $DB_NAME -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $DB_USER;"
psql -U postgres -d $DB_NAME -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $DB_USER;"
psql -U postgres -d $DB_NAME -c "GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO $DB_USER;"
psql -U postgres -d $DB_NAME -c "GRANT CREATE ON SCHEMA public TO $DB_USER;"

# Initialize migrations
echo "Initializing Flask-Migrate..."
flask db init

# Create initial migration script
echo "Creating initial migration script..."
flask db migrate -m "Initial migration."

# Apply migrations
echo "Applying migrations..."
flask db upgrade

echo "Database setup and migration complete."
