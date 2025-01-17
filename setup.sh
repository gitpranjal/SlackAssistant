#!/bin/bash

# Remove the existing environment
conda env remove -n slackenv

# Create the new environment
conda env create -f environment.yml

# Initialize conda (if not already initialized)
conda init

# Reload the shell to apply changes made by conda init
exec "$SHELL"

# Activate the environment
conda activate slackenv

echo "Environment setup complete. Activate it using: conda activate slackenv"