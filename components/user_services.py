import requests
import json
import secrets
import binascii

from django.http import HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


from components.classes import Endpoint_Data, User_Data
from components.id_creator import user_ID_Creator
from components.models import User, Endpoint

def ID_Creator():
    random_bytes = secrets.token_bytes(16)
    hex_string = binascii.hexlify(random_bytes).decode() 
    return hex_string
    
    
    
@csrf_exempt
def createUser(request:requests): 
        if request.method == "POST": 
        #if the request is a post request, map the data to the corresponding data 
	    #class and then write it into the database 
     
            request_body = json.loads(request.body)	 
    

            config_data = User_Data(
            user_id = user_ID_Creator(),
            email = request_body["email"],
            password = request_body["password"],
            )
            #Creates a new user and saves it to the DB
            new_user = User(user_id = config_data.user_id,
                            email = config_data.email,
                            password = config_data.password)
            

            
            new_user.save()
            
            
            
            return HttpResponse(status = 200)
