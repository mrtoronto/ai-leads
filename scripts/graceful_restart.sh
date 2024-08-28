#!/bin/bash

# Function to send HUP signal or restart service
restart_service() {
    SERVICE_NAME=$1
    CMD_GREP=$2
    IS_WORKER=$3

    if [ "$IS_WORKER" = true ]; then
        # For workers, we'll handle multiple instances
        for i in {1..3}; do  # Adjust the range based on how many worker instances you have
            WORKER_SERVICE="${SERVICE_NAME}@$i.service"
            PIDs=$(ps aux | grep "$CMD_GREP" | grep "worker-$i" | grep -v grep | awk '{ print $2 }')

            if [ -z "$PIDs" ]; then
                echo "$WORKER_SERVICE not found. Starting it up."
                sudo systemctl start "$WORKER_SERVICE"
            else
                echo "Sending HUP signal to $WORKER_SERVICE processes (PIDs: $PIDs) to gracefully reload."
                for PID in $PIDs; do
                    sudo kill -HUP $PID
                    echo "Sent HUP signal to $PID"
                done

                # Verify the processes are still running, a simple sleep can help
                sleep 2
                NEW_PIDs=$(ps aux | grep "$CMD_GREP" | grep "worker-$i" | grep -v grep | awk '{ print $2 }')

                if [ -z "$NEW_PIDs" ]; then
                    echo "$WORKER_SERVICE processes did not remain active. Restarting service."
                    sudo systemctl restart "$WORKER_SERVICE"
                else
                    echo "$WORKER_SERVICE processes are still active."
                fi
            fi
        done
    else
        # For non-worker services, use the original logic
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
    fi
}

# Restart Gunicorn master process for AI Leads
restart_service "ai_leads" ".*run:app" false

# Restart RQ worker processes for AI Leads
restart_service "ai-leads-worker" ".*rq worker" true
