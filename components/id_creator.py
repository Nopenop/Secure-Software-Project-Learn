import secrets
import binascii
from components.classes import Endpoint_Data, User_Data
from components.models import User, Endpoint


def user_ID_Creator():
    while True:  # if the user ID already exists, make a new ID
        random_bytes = secrets.token_bytes(16)
        hex_string = binascii.hexlify(random_bytes).decode()

        # if the user ID is unique, allow create new ID
        if not User.objects.filter(user_id=hex_string).exists():
            return hex_string


def endpoint_ID_Creator():
    while True:  # if the endpoint ID already exists, make a new ID
        random_bytes = secrets.token_bytes(16)
        hex_string = binascii.hexlify(random_bytes).decode()

        # if the endpoint ID is unique, allow create new ID
        if not Endpoint.objects.filter(endpoint_id=hex_string).exists():
            return hex_string

