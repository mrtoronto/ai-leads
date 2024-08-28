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

# Function to stop all worker services
stop_worker_services() {
    echo "Stopping all worker services..."
    for i in $(seq 1 $WORKER_COUNT); do
        sudo systemctl stop "${WORKER_SERVICE}@$i"
    done
}

# Function to kill all RQ worker processes
kill_all_workers() {
    echo "Killing all RQ worker processes..."
    sudo pkill -f "rq worker"
}

# Function to start worker services
start_worker_services() {
    echo "Starting all worker services..."
    for i in $(seq 1 $WORKER_COUNT); do
        sudo systemctl start "${WORKER_SERVICE}@$i"

        # Allow some time for each worker to start
        sleep 5

        if sudo systemctl is-active --quiet "${WORKER_SERVICE}@$i"; then
            echo "${WORKER_SERVICE}@$i is now active."
        else
            echo "Failed to start ${WORKER_SERVICE}@$i. Please check the logs."
            sudo journalctl -u "${WORKER_SERVICE}@$i" -n 20 --no-pager
        fi
    done
}

# Main execution
echo "Starting graceful restart process..."

# Restart the main application service
restart_main_service "$MAIN_SERVICE"

# Stop all worker services
stop_worker_services

# Ensure all worker processes are terminated
kill_all_workers

# Allow a brief pause to ensure all processes are killed
sleep 5

# Start all worker services
start_worker_services

echo "Graceful restart process completed."
