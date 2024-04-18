#!/bin/bash
echo "Beginning the setup process..."

# Install Voice dependencies
echo "Installing Voice dependencies..."
apt install ffmpeg

# Pull RabbitMQ
echo "Pulling RabbitMQ..."
docker pull rabbitmq:3.10-management

# Check if RabbitMQ container exists
if [ "$(docker ps -a -f name=rabbitmq | grep rabbitmq | wc -l)" -eq 0 ]; then
  # Run the RabbitMQ if not exist
  echo "Running RabbitMQ..."
  docker run -d -p 5672:5672 -p 15672:15672 \
    -e RABBITMQ_DEFAULT_USER=admin \
    -e RABBITMQ_DEFAULT_PASS=8a8a8a \
    --hostname myRabbit \
    --name rabbitmq \
    rabbitmq:3.10-management
else
  echo "RabbitMQ already exists. Using it..."
fi

docker ps -l

# Clone or update the project
if [ ! -d "Openaibot" ] ; then
  echo "Cloning Openaibot..."
  git clone https://github.com/LlmKira/Openaibot/
  cd Openaibot || exit
else
  echo "Updating Openaibot..."
  cd Openaibot || exit
  git pull
fi

echo "Setting up Python dependencies..."
pip install pdm
pdm install -G bot
cp .env.exp .env && nano .env

# Install or update pm2
if ! [ -x "$(command -v pm2)" ]; then
  echo "Installing npm and pm2..."
  apt install npm
  npm install pm2 -g
fi

echo "Starting application with pm2..."
pm2 start pm2.json

echo "Setup complete!"
