#!/bin/bash

# Configuration
MAIN_SERVICE="ai_leads"
WORKER_SERVICE="ai-leads-worker"
WORKER_COUNT=3  # Adjust this to the number of worker instances you have

# Function to restart the main service
restart_main_service() {
    local SERVICE_NAME=$1
    echo "Restarting $SERVICE_NAME..."

    if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
        echo "Service $SERVICE_NAME is active. Attempting to reload..."
        if sudo systemctl reload "$SERVICE_NAME"; then
            echo "Successfully reloaded $SERVICE_NAME."
        else
            echo "Reload failed for $SERVICE_NAME. Attempting restart..."
            sudo systemctl restart "$SERVICE_NAME"
        fi
    else
        echo "Service $SERVICE_NAME is not active. Starting..."
        sudo systemctl start "$SERVICE_NAME"
    fi

    if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
        echo "$SERVICE_NAME is now active."
    else
        echo "Failed to start $SERVICE_NAME. Please check the logs."
    fi
}

# Function to restart a worker service
restart_worker_service() {
    local SERVICE_NAME=$1
    echo "Restarting $SERVICE_NAME..."

    # For workers, we'll always do a full restart
    sudo systemctl restart "$SERVICE_NAME"

    # Wait a bit for the service to start up
    sleep 5

    if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
        echo "$SERVICE_NAME is now active."
    else
        echo "Failed to start $SERVICE_NAME. Please check the logs."
        # Output the last few lines of the journal for this service
        sudo journalctl -u "$SERVICE_NAME" -n 20 --no-pager
    fi
}

# Function to restart worker services
restart_workers() {
    for i in $(seq 1 $WORKER_COUNT); do
        restart_worker_service "${WORKER_SERVICE}@$i"
    done
}

# Main execution
echo "Starting graceful restart process..."

# Restart the main application service
restart_main_service "$MAIN_SERVICE"

# Restart the worker services
restart_workers

echo "Graceful restart process completed."
