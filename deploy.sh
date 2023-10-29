#!/bin/bash

# Check if the Openaibot directory exists
echo "$(tput setaf 6)Checking the Openaibot directory...$(tput sgr0)"
if [ -d "Openaibot" ]; then
  # shellcheck disable=SC2164
  pip uninstall llmkira
  cd Openaibot && git pull && echo "$(tput setaf 6)Update successfully...$(tput sgr0)"
  # Update the Openaibot project
  exit 0
else
  # Clone the project if not already cloned
  git clone https://github.com/LlmKira/Openaibot.git
fi

echo "$(tput setaf 2)Openaibot directory check complete.$(tput sgr0)"
echo "$(tput setaf 6)This script will install Docker and the Openaibot project. Do you want to proceed? (y/n):$(tput sgr0) "
read -r choice
if [[ $choice =~ ^([yY][eE][sS]|[yY])$ ]]; then
  sleep 1s
else
  echo "$(tput setaf 1)Installation cancelled.$(tput sgr0)"
  exit 0
fi

# Function to handle errors and exit
handle_error() {
  echo "$(tput setaf 1)Error occurred during installation. Exiting...$(tput sgr0)"
  exit 1
}

# Set error trap
trap 'handle_error' ERR

# Check if Docker is installed
if ! [ -x "$(command -v docker)" ]; then
  # Install Docker
  echo "$(tput setaf 6)Installing Docker...$(tput sgr0)"
  curl -fsSL https://get.docker.com | bash -s docker
else
  echo "$(tput setaf 2)Docker already installed.$(tput sgr0)"
fi

# Run Docker Compose
echo "$(tput setaf 6)Running Docker Compose...$(tput sgr0)"
# 检查是否安装docker-compose
if ! [ -x "$(command -v docker-compose)" ]; then
  # Install Docker
  echo "$(tput setaf 6)Installing docker-compose...$(tput sgr0)"
  curl -L https://github.com/docker/compose/releases/download/v2.14.0/docker-compose-linux-$(uname -m) >/usr/local/bin/docker-compose
  chmod +x /usr/local/bin/docker-compose
else
  echo "$(tput setaf 2)docker-compose already installed.$(tput sgr0)"
fi
# Change directory to the project
cd Openaibot || echo "DO NOT" && exit

# Install project dependencies
echo "$(tput setaf 6)Installing project dependencies...$(tput sgr0)"
pip install -r requirements.txt
echo "$(tput setaf 2)Project dependencies installation complete.$(tput sgr0)"

# Copy .env.exp to .env if .env doesn't exist
if [ ! -f ".env" ]; then
  echo "$(tput setaf 6)Copying .env.example to .env...$(tput sgr0)"
  cp .env.exp .env
  nano .env
  echo "$(tput setaf 2).env file copy complete.$(tput sgr0)"
fi

docker-compose -f docker-compose.yml up -d

echo "$(tput setaf 2)Docker Compose completed with:docker-compose -f docker-compose.yml up -d$(tput sgr0)"

# Remove the error trap
trap - ERR

echo "$(tput setaf 2)Installation completed successfully.$(tput sgr0)"
