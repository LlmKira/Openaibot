# Confirmation prompt
read -r -p "$(tput setaf 6)This script will install Docker, Redis, RabbitMQ, Node.js, NPM, PM2, and the Openaibot project. THAT ACTION MAY BREAK YOUR SYSTEM. Do you want to proceed? (y/n):$(tput sgr0) " choice
if [[ ! $choice =~ ^[Yy]$ ]]; then
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
echo "$(tput setaf 6)Installing Docker...$(tput sgr0)"
if ! [ -x "$(command -v docker)" ]; then
  # Install Docker
  curl -fsSL https://get.docker.com | bash -s docker
fi
echo "$(tput setaf 2)Docker installation complete.$(tput sgr0)"

# Check if Redis is installed, otherwise exit
echo "$(tput setaf 6)Installing Redis...$(tput sgr0)"
if ! [ -x "$(command -v redis-server)" ]; then
  apt-get install redis
  systemctl enable redis.service --now
  exit 1
fi
echo "$(tput setaf 2)Redis installation complete.$(tput sgr0)"

# Pull RabbitMQ image
echo "$(tput setaf 6)Pulling RabbitMQ image...$(tput sgr0)"
if [[ $(docker images -q rabbitmq:3.10-management) == "" ]]; then
  docker pull rabbitmq:3.10-management
fi
echo "$(tput setaf 2)RabbitMQ image pull complete.$(tput sgr0)"

# Run RabbitMQ container if not already running
echo "$(tput setaf 6)Starting RabbitMQ container...$(tput sgr0)"
if ! docker inspect -f '{{.State.Running}}' rabbitmq &>/dev/null; then
  docker run -d -p 5672:5672 -p 15672:15672 \
    -e RABBITMQ_DEFAULT_USER=admin \
    -e RABBITMQ_DEFAULT_PASS=admin \
    --hostname myRabbit \
    --name rabbitmq \
    rabbitmq:3.10-management
fi
echo "$(tput setaf 2)RabbitMQ container started successfully.$(tput sgr0)"

# Check if Node.js and NPM are installed, otherwise exit
echo "$(tput setaf 6)Checking Node.js and NPM...$(tput sgr0)"
if ! [ -x "$(command -v node)" ] || ! [ -x "$(command -v npm)" ]; then
  echo "$(tput setaf 1)Node.js and/or NPM are not installed. Please install them and run the script again.$(tput sgr0)"
  exit 1
fi
echo "$(tput setaf 2)Node.js and NPM installation check complete.$(tput sgr0)"

# Install PM2 globally if not already installed
echo "$(tput setaf 6)Installing PM2...$(tput sgr0)"
if ! [ -x "$(command -v pm2)" ]; then
  npm install pm2 -g
fi
echo "$(tput setaf 2)PM2 installation complete.$(tput sgr0)"

# Check if the Openaibot directory exists
echo "$(tput setaf 6)Checking the Openaibot directory...$(tput sgr0)"
if [ -d "Openaibot" ]; then
  # Menu prompt for Openaibot directory options
  select option in "Update Openaibot" "Skip Openaibot Update"; do
    case $option in
    "Update Openaibot")
      # Change directory to the project
      cd Openaibot  exit

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
      echo "$(tput setaf 1)Invalid option. Please select a valid option.$(tput sgr0)"
      ;;
    esac
  done
else
  # Clone the project if not already cloned
  git clone https://github.com/LlmKira/Openaibot.git
fi
echo "$(tput setaf 2)Openaibot directory check complete.$(tput sgr0)"

# Change directory to the project
cd Openaibot || exit

# Install project dependencies
echo "$(tput setaf 6)Installing project dependencies...$(tput sgr0)"
pip install -r requirements.txt
echo "$(tput setaf 2)Project dependencies installation complete.$(tput sgr0)"

# Copy .env.example to .env if .env doesn't exist
if [ ! -f ".env" ]; then
  echo "$(tput setaf 6)Copying .env.example to .env...$(tput sgr0)"
  cp .env.example .env
  nano .env
  echo "$(tput setaf 2).env file copy complete.$(tput sgr0)"
fi

# Start the project using PM2
echo "$(tput setaf 6)Starting project using PM2...$(tput sgr0)"
pm2 start pm2.json
echo "$(tput setaf 2)Project started using PM2.$(tput sgr0)"

# Check if the project is already running
if pm2 describe all | grep -q "status: online"; then
  echo "$(tput setaf 2)Project is already running.$(tput sgr0)"
else
  echo "$(tput setaf 1)Project failed to start.$(tput sgr0)"
fi

# Remove the error trap
trap - ERR

echo "$(tput setaf 2)Installation completed successfully.$(tput sgr0)"