#!/bin/bash

echo "Are you sure you want to proceed? (y/n)"
read -r response
if [[ $response =~ ^([yY][eE][sS]|[yY])$ ]]; then
  # Do something
  echo "Aborting."
else
  echo "Aborting."
fi
