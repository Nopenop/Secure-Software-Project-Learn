#!/bin/bash

read -p "What is the Admin's Email: " ADMIN_EMAIL
read -p "What is the Host Email: " HOST_EMAIL
read -p "What is the Host Email's Password: " HOST_EMAIL_PASSWORD
read -p "What is the compression password: " COMPRESSION_PASSWORD

export ADMIN_EMAIL
export HOST_EMAIL
export HOST_EMAIL_PASSWORD
export COMPRESSION_PASSWORD

echo $HOST_EMAIL

python manage.py runserver
