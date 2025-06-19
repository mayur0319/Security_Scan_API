#!/bin/bash

# This script automates Docker build, run, and cleanup operations for the 'mayur:latest' image.

# Function to display usage information
usage() {
  echo "Usage: $0 [command]"
  echo "Commands:"
  echo "  build_and_run   - Builds the 'mayur:latest' image and runs it, cleaning up any existing container first."
  echo "  cleanup         - Stops and removes any running 'mayur:latest' container and deletes the 'mayur:latest' image."
  echo "  help            - Displays this help message."
  exit 1
}

# Function to clean up existing running containers and images
cleanup_existing() {
  echo "--- Cleaning up existing containers and images for 'mayur:latest' ---"

  # Get the container ID of any running container based on 'mayur:latest'
  CONTAINER_ID=$(sudo docker ps -q --filter ancestor=mayur:latest)

  if [ -n "$CONTAINER_ID" ]; then
    echo "Found running container ID: $CONTAINER_ID"
    echo "Stopping container $CONTAINER_ID..."
    sudo docker stop "$CONTAINER_ID"
    echo "Removing container $CONTAINER_ID..."
    sudo docker rm "$CONTAINER_ID"
  else
    echo "No running container for 'mayur:latest' found."
  fi

  # Check if the 'mayur:latest' image exists
  if sudo docker images -q mayur:latest | grep -q .; then
    echo "Removing Docker image 'mayur:latest'..."
    sudo docker rmi mayur:latest
  else
    echo "Docker image 'mayur:latest' not found."
  fi

  echo "Cleaning up unused containers and images..."
  sudo docker container prune -f
  sudo docker image prune -f

  echo "Cleanup complete."
}

# Function to build and run the Docker image
build_and_run() {
  echo "--- Starting build and run process for 'mayur:latest' ---"
  cleanup_existing

  echo "--- Building Docker image 'mayur:latest' ---"
  if sudo docker build -t mayur:latest .; then
    echo "Docker image 'mayur:latest' built successfully."
    echo "Running Docker container 'mayur:latest' on port 8888..."
    sudo docker run -it -p 8888:8888 mayur:latest
  else
    echo "Error: Docker image build failed."
    exit 1
  fi
}

# Main script logic
case "$1" in
  build_and_run)
    build_and_run
    ;;
  cleanup)
    cleanup_existing
    ;;
  help | --help | -h)
    usage
    ;;
  *)
    echo "Invalid command: $1"
    usage
    ;;
esac
