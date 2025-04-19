import requests
import json


from django.http import HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


from components.classes import Endpoint_Data, User_Data
from components.id_creator import endpoint_ID_Creator
from components.models import User, Endpoint
from components.monitor import Endpoint_Monitor

@csrf_exempt
def createEndpoint(request:requests): 
    if request.method == "POST": 
        try:
        #if the request is a post request, map the data to the corresponding data 
	    #class and then write it into the database 

            userID = request.GET.get('userID')
            request_body = json.loads(request.body)	 

            
            config_data = Endpoint_Data(
            user_id = userID,
            endpoint_id = endpoint_ID_Creator(),
            endpoint_name = request_body["endpoint_name"], 
            endpoint_path = request_body["endpoint_path"],
            )
            
            #Creates a new Endpoint object linked to the user via user_id
            new_endpoint = Endpoint(user_id=User.objects.get(user_id = config_data.user_id), 
                                    endpoint_id = config_data.endpoint_id,
                                    endpoint_name = config_data.endpoint_name,
                                    endpoint_path = config_data.endpoint_path,
                              )
            
            new_endpoint.save()

            Endpoint_Monitor(
                5,
                1,
                endpoint_id=config_data.endpoint_id,
                url=config_data.endpoint_path,
                expected_code=200,
                database_path='./db.sqlite3',
                certificate_path="",
            ).start()
        
            return JsonResponse({"message":"Successful Post for New Endpoint"}, status = 200)
        except:
            return JsonResponse({"message":"Failed Post for New Endpoint"}, status = 405)

@csrf_exempt 
def editEndpoint(request):
    try:
        if request.method == "POST":
            request_body = json.loads(request.body)
            
            endpoint_id = request_body["endpoint_id"]
            user_endpoint = Endpoint.objects.get(endpoint_id=endpoint_id)

            user_endpoint.endpoint_name = request_body['endpoint_name']
            user_endpoint.endpoint_path = request_body['endpoint_path']
            user_endpoint.save()
            
            
            Endpoint_Monitor(
                5,
                1,
                endpoint_id=endpoint_id,
                url=request_body['endpoint_path'],
                expected_code=200,
                database_path='./db.sqlite3',
                certificate_path="",
            ).start()

            return JsonResponse({"message": "Endpoint Successfully Edited"}, status=200)

    except:
            return JsonResponse({"message":"Endpoint Failed to be Edited"}, status = 400)
@csrf_exempt
def deleteEndpoint(request:requests):
        if request.method == "POST":
            
            request_body = json.loads(request.body)
            endpoint_id = request_body['endpoint_id']
            user_endpoint = Endpoint.objects.get(endpoint_id=endpoint_id)
            user_endpoint.delete()
            print("hello")
            
         
            
            return JsonResponse({"message":"Endpoint Successfully Deleted"}, status = 200)