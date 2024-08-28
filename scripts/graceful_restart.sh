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

# Restart Gunicorn master process for Zakaya
restart_service "ai_leads" ".*run:app"

# Restart ai-leads-worker instances
for i in {1..3}; do
    INSTANCE_NAME="ai-leads-worker@$i.service"
    restart_service "$INSTANCE_NAME" ".*rq worker"
done
