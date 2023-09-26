read -r -p "$(tput setaf 6)This script will install Docker, Redis, RabbitMQ, Node.js, NPM, PM2, and the Openaibot project. THAT ACTION MAY BREAK YOUR SYSTEM. Do you want to proceed? (y/n):$(tput sgr0) " rrchoice
if [[ ! $rrchoice =~ ^[Yy]$ ]]; then
  echo "$(tput setaf 1)Installation cancelled.$(tput sgr0)"
  exit 0
fi