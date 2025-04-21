#!/bin/bash

# Input variables for environment variables
echo "Admin Information"
read -p "What is the Admin's Email: " ADMIN_EMAIL
read -p "What is the Host Email: " EMAIL_HOST_USER
read -sp "What is the Host Email's Password: " EMAIL_HOST_PASSWORD
echo ""
read -sp "What is the compression password: " COMPRESSION_PASSWORD
echo ""

echo "Server Diagnostics Information"
read -p "Maximum Tolerable CPU Usage Percentage: " CPU_USAGE
read -p "Maximum Tolerable Memory Usage Percentage: " MEMORY_USAGE
read -p "Maximum Tolerable Disk Usage Percentage: " DISK_USAGE

# default tolerable values
CPU_USAGE=${CPU_USAGE:-"80"}
MEMORY_USAGE=${MEMORY_USAGE:-"80"}
DISK_USAGE=${DISK_USAGE:-"80"}

# Create and print out generated AES_KEY
AES_KEY=$(python ./Other_Classes/create_aes_key.py)
echo $AES_KEY

# ensure that cpu, memory, and disk monitors are created
CREATE_OS_MONITORS="true"

# Export variables to environment variables for server to use
export CREATE_OS_MONITORS
export ADMIN_EMAIL
export EMAIL_HOST_USER
export EMAIL_HOST_PASSWORD
export AES_KEY
export COMPRESSION_PASSWORD
export CPU_USAGE
export MEMORY_USAGE
export DISK_USAGE

# Start the server with environment variables
python manage.py runserver
