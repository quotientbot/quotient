#!/bin/bash

# To update, run this script from the root directory of the project.


# Get the name of the directory
directory_name=$(basename "$(pwd)")

echo "Updating ${directory_name}..."

# Pull the latest changes from git
git pull

# Remove the existing Docker image
docker rmi "${directory_name}_img"

# Rebuild the Docker image
docker build -t "${directory_name}_img" .

# Stop the existing container
docker stop "${directory_name}"

# Remove the stopped container
docker rm "${directory_name}"

# Start a new container with the updated image
docker run -d -p 8888:8888 --name "${directory_name}" "${directory_name}_img"