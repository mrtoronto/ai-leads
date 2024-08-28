#!/bin/bash

# Function to send HUP signal or restart service
restart_service() {
    SERVICE_NAME=$1
    CMD_GREP=$2

    PIDs=$(ps aux | grep "$CMD_GREP" | grep -v grep | awk '{ print $2 }')

    if [ -z "$PIDs" ]; then
        echo "$SERVICE_NAME service not found. Starting it up."
        sudo systemctl start "$SERVICE_NAME"
    else
        echo "Sending HUP signal to $SERVICE_NAME service processes (PIDs: $PIDs) to gracefully reload."
        for PID in $PIDs; do
            sudo kill -HUP $PID
            echo "Sent HUP signal to $PID"
        done

        # Verify the processes are still running, a simple sleep can help
        sleep 2
        NEW_PIDs=$(ps aux | grep "$CMD_GREP" | grep -v grep | awk '{ print $2 }')

        if [ -z "$NEW_PIDs" ]; then
            echo "$SERVICE_NAME processes did not remain active. Restarting service."
            sudo systemctl restart "$SERVICE_NAME"
        else
            echo "$SERVICE_NAME processes are still active."
        fi
    fi
}

# Configuration
MAIN_SERVICE="ai_leads"
WORKER_SERVICE="ai-leads-worker"
WORKER_COUNT=3  # Adjust this to the number of worker instances you have

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

# Function to start all worker services
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
restart_service "$MAIN_SERVICE" ".*run:app"

# Stop all worker services
stop_worker_services

# Ensure all worker processes are terminated
kill_all_workers

# Allow a brief pause to ensure all processes are killed
sleep 5

# Start all worker services
start_worker_services

echo "Graceful restart process completed."
