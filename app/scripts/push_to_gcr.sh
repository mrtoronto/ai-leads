#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Check if PROJECT_ID is provided
if [ -z "$1" ]; then
    echo "Please provide your Google Cloud project ID as an argument."
    echo "Usage: ./push_to_gcr.sh [PROJECT_ID]"
    exit 1
fi

PROJECT_ID=$1
IMAGE_NAME="bizdevbot"
GCR_HOSTNAME="gcr.io"

# Ensure we're authenticated
gcloud auth login

# Build the Docker image (if not already built)
docker-compose build

# Tag the image for GCR
docker tag ${IMAGE_NAME} ${GCR_HOSTNAME}/${PROJECT_ID}/${IMAGE_NAME}:latest

# Push the image to GCR
docker push ${GCR_HOSTNAME}/${PROJECT_ID}/${IMAGE_NAME}:latest

echo "Image successfully pushed to GCR: ${GCR_HOSTNAME}/${PROJECT_ID}/${IMAGE_NAME}:latest"
