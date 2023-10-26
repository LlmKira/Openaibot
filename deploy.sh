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
echo "$(tput setaf 6)This script will install Docker, Redis, RabbitMQ, Node.js, NPM, PM2, and the Openaibot project. THAT ACTION MAY BREAK YOUR SYSTEM. Do you want to proceed? (y/n):$(tput sgr0) "
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

# Pull Redis image
if [[ $(docker images -q redis:latest) == "" ]]; then
  echo "$(tput setaf 6)Pulling Redis image...$(tput sgr0)"
  docker pull redis:latest
  echo "$(tput setaf 2)Redis image pull complete.$(tput sgr0)"
fi
# Run Redis container if not already running
if ! docker inspect -f '{{.State.Running}}' redis &>/dev/null; then
  echo "$(tput setaf 6)Starting Redis container...$(tput sgr0)"
  docker run -d -p 6379:6379 \
    --name redis \
    redis:latest
fi
if ! docker inspect -f '{{.State.Running}}' redis &>/dev/null; then
  echo "$(tput setaf 1)Redis container started failed.$(tput sgr0)"
else
  echo "$(tput setaf 2)Redis container started successfully.$(tput sgr0)"
fi

# Pull RabbitMQ image
if [[ $(docker images -q rabbitmq:3-management) == "" ]]; then
  echo "$(tput setaf 6)Pulling RabbitMQ image...$(tput sgr0)"
  docker pull rabbitmq:3-management
  echo "$(tput setaf 2)RabbitMQ image pull complete.$(tput sgr0)"
fi
# Run RabbitMQ container if not already running
if ! docker inspect -f '{{.State.Running}}' rabbitmq &>/dev/null; then
  echo "$(tput setaf 6)Starting RabbitMQ container...$(tput sgr0)"
  docker run -d -p 5672:5672 -p 15672:15672 \
    -e RABBITMQ_DEFAULT_USER=admin \
    -e RABBITMQ_DEFAULT_PASS=admin \
    --hostname myRabbit \
    --name rabbitmq \
    rabbitmq:3-management
fi
if ! docker inspect -f '{{.State.Running}}' rabbitmq &>/dev/null; then
  echo "$(tput setaf 1)RabbitMQ container started failed.$(tput sgr0)"
else
  echo "$(tput setaf 2)RabbitMQ container started successfully.$(tput sgr0)"
fi

# Pull MongoDB image
if [[ $(docker images -q mongo:latest) == "" ]]; then
  echo "$(tput setaf 6)Pulling MongoDB image...$(tput sgr0)"
  docker pull mongo:latest
  echo "$(tput setaf 2)MongoDB image pull complete.$(tput sgr0)"
fi
# Run MongoDB container if not already running
if ! docker inspect -f '{{.State.Running}}' mongo &>/dev/null; then
  echo "$(tput setaf 6)Starting MongoDB container...$(tput sgr0)"
  docker run -d -p 27017:27017 \
    --name mongo \
    mongo:latest
fi


# Check if Node.js and NPM are installed, otherwise exit
echo "$(tput setaf 6)Checking Node.js and NPM...$(tput sgr0)"
if ! [ -x "$(command -v node)" ] || ! [ -x "$(command -v npm)" ]; then
  echo "$(tput setaf 1)Node.js and/or NPM are not installed. Please install them and run the script again.$(tput sgr0)"
  exit 1
fi
echo "$(tput setaf 2)Node.js and NPM installation check complete.$(tput sgr0)"

# Install PM2 globally if not already installed
if ! [ -x "$(command -v pm2)" ]; then
  echo "$(tput setaf 6)Installing PM2...$(tput sgr0)"
  npm install pm2 -g
else
  echo "$(tput setaf 2)PM2 already installed.$(tput sgr0)"
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

# Start the project using PM2
echo "$(tput setaf 6)Starting project using PM2...$(tput sgr0)"
pm2 start pm2.json
echo "$(tput setaf 2)Project started using PM2.$(tput sgr0)"

sleep 3s

# Check if the project is already running
if pm2 status | grep -E "^(llm_receiver|llm_sender).*(\b|^)online(\b|$)" >/dev/null; then
  echo "$(tput setaf 2)Project is already running.$(tput sgr0)"
else
  echo "$(tput setaf 1)Project failed to start.$(tput sgr0)"
fi

# Remove the error trap
trap - ERR

echo "$(tput setaf 2)Installation completed successfully.$(tput sgr0)"
