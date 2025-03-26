import requests
import json
import secrets
import binascii

from django.http import HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from dataclasses import dataclass, asdict
from customDataClasses import Endpoint_Data, User_Data

def passwordCreator():
    random_bytes = secrets.token_bytes(16)
    hex_string = binascii.hexlify(random_bytes).decode() 
    return hex_string


@csrf_exempt
def ceateEndpoint(request:requests): 
    try: 
        if request.method == "POST": 
        #if the request is a post request, map the data to the corresponding data 
	    #class and then write it into the database 
            request_body = json.loads(request.body)	 
    
            config_data = Endpoint_Data(
            user_id = request_body["user_id"], 
            endpoint_id = request_body["endpoint_id"], 
            endpoint_name = request_body["endpoint_name"], 
            endpoint_path = request_body["endpoint_path"],
            endpoint_status = request_body["endpoint_status"]
            )

        #write the data from the config into the Database 
        #add code here
 
        #Create the monitoring Daemon using the config data 
        #add code here
        
        return HttpResponse.status_code(200)
    except: #error handling 
        return JsonResponse({"Invalid Request or Bad Data" : 405})
    
    
    
@csrf_exempt
def createUser(request:requests): 
    try: 
        if request.method == "POST": 
        #if the request is a post request, map the data to the corresponding data 
	    #class and then write it into the database 
            request_body = json.loads(request.body)	 
    
            config_data = User_Data(
            user_id = passwordCreator(),
            email = request_body["email"],
            email = request_body["password"]
            )

        #write the user data into the Database 
        #add code here
        
        return HttpResponse.status_code(200)
    except: #error handling 
        return JsonResponse({"Invalid Request or Bad Data" : 405})