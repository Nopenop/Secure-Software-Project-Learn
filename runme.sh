#!/bin/bash

# Input variables for environment variables
read -p "What is the Admin's Email: " ADMIN_EMAIL
read -p "What is the Host Email: " EMAIL_HOST_USER
read -p "What is the Host Email's Password: " EMAIL_HOST_PASSWORD
read -p "What is the compression password: " COMPRESSION_PASSWORD

# Create and print out generated AES_KEY
AES_KEY=$(python ./Other_Classes/create_aes_key.py)
echo $AES_KEY

# Export variables to environment variables for server to use
export ADMIN_EMAIL
export EMAIL_HOST_USER
export EMAIL_HOST_PASSWORD
export AES_KEY
export COMPRESSION_PASSWORD

# Start the server with environment variables
python manage.py runserver
