#!/bin/bash

# Confirmation prompt
read -r -p "This script will install Docker, Redis, RabbitMQ, Node.js, NPM, PM2, and the Openaibot project.THAT ACTION MAY BREAK YOUR SYSTEM.Do you want to proceed? (y/n): " choice
if [[ ! $choice =~ ^[Yy]$ ]]; then
  echo "Installation cancelled."
  exit 0
fi

# Function to handle errors and exit
handle_error() {
  echo "Error occurred during installation. Exiting..."
  exit 1
}

# Set error trap
trap 'handle_error' ERR

# Check if Docker is installed
if ! command -v docker &>/dev/null; then
  # Install Docker
  curl -fsSL https://get.docker.com | bash -s docker
fi

# Check if Redis is installed, otherwise exit
if ! command -v redis-server &>/dev/null; then
  echo "Redis is not installed. Please install Redis and run the script again."
  exit 1
fi

# Pull RabbitMQ image
if [[ $(docker images -q rabbitmq:3.10-management) == "" ]]; then
  docker pull rabbitmq:3.10-management
fi

# Run RabbitMQ container if not already running
if ! docker inspect -f '{{.State.Running}}' rabbitmq &>/dev/null; then
  docker run -d -p 5672:5672 -p 15672:15672 \
    -e RABBITMQ_DEFAULT_USER=admin \
    -e RABBITMQ_DEFAULT_PASS=admin \
    --hostname myRabbit \
    --name rabbitmq \
    rabbitmq:3.10-management
fi

# Check if Node.js and NPM are installed, otherwise exit
if ! command -v node &>/dev/null || ! command -v npm &>/dev/null; then
  echo "Node.js and/or NPM are not installed. Please install them and run the script again."
  exit 1
fi

# Install PM2 globally if not already installed
if ! command -v pm2 &>/dev/null; then
  npm install pm2 -g
fi

# Check if the Openaibot directory exists
if [ -d "Openaibot" ]; then
  # Menu prompt for Openaibot directory options
  select option in "Update Openaibot" "Skip Openaibot Update"; do
    case $option in
    "Update Openaibot")
      # Change directory to the project
      cd Openaibot || exit

      # Update the Openaibot project
      git pull

      # Exit the menu
      break
      ;;
    "Skip Openaibot Update")
      # Exit the menu and continue with installation
      break
      ;;
    *)
      echo "Invalid option. Please select a valid option."
      ;;
    esac
  done
else
  # Clone the project if not already cloned
  git clone https://github.com/LlmKira/Openaibot.git
fi

# Change directory to the project
cd Openaibot || exit

# Install project dependencies
pip install -r requirements.txt

# Copy .env.example to .env if .env doesn't exist
if [ ! -f ".env" ]; then
  cp .env.example .env
  nano .env
fi

# Start the project using PM2
pm2 start pm2.json

# Check if the project is already running
if pm2 describe all | grep -q "status: online"; then
  echo "Project is already running."
else
  echo "Project started successfully."
fi

# Remove the error trap
trap - ERR

echo "Installation completed successfully."
