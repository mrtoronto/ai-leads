#!/bin/bash

# Configuration
MAIN_SERVICE="ai_leads"
WORKER_SERVICE="ai-leads-worker"
WORKER_COUNT=3  # Adjust this to the number of worker instances you have

# Function to restart a single service
restart_single_service() {
    local SERVICE_NAME=$1
    echo "Restarting $SERVICE_NAME..."

    # Check if the service is active
    if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
        # Service is running, attempt to reload
        echo "Service $SERVICE_NAME is active. Attempting to reload..."
        if sudo systemctl reload "$SERVICE_NAME"; then
            echo "Successfully reloaded $SERVICE_NAME."
        else
            echo "Reload failed for $SERVICE_NAME. Attempting restart..."
            sudo systemctl restart "$SERVICE_NAME"
        fi
    else
        # Service is not running, start it
        echo "Service $SERVICE_NAME is not active. Starting..."
        sudo systemctl start "$SERVICE_NAME"
    fi

    # Verify the service status after restart/reload
    if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
        echo "$SERVICE_NAME is now active."
    else
        echo "Failed to start $SERVICE_NAME. Please check the logs."
    fi
}

# Function to restart worker services
restart_workers() {
    for i in $(seq 1 $WORKER_COUNT); do
        restart_single_service "${WORKER_SERVICE}@$i"
    done
}

# Main execution
echo "Starting graceful restart process..."

# Restart the main application service
restart_single_service "$MAIN_SERVICE"

# Restart the worker services
restart_workers

echo "Graceful restart process completed."
