import requests
import json
import secrets
import binascii

from django.http import HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


from components.classes import Endpoint_Data, User_Data

from components.models import User, Endpoint

@csrf_exempt
def accountLogin(request:requests):
    try:
        if request.method == "POST": 
            
            
            request_body = json.loads(request.body)
            
            email = request_body["email"]
            password = request_body["password"]
            
            user = User.objects.filter(email=email).first()
            
            if user and user.password == password:
                return JsonResponse({"user_id": user.user_id}, status=200)
            else:
                return HttpResponse("Invalid credentials", status=401)
                
    except:
        return HttpResponse(status=405)
    

@csrf_exempt
def getUserEndpoints(request): 
        try:
            if request.method == "GET":
                user_id = request.GET.get('userID')
                user = User.objects.get(user_id=user_id)

                endpoints = Endpoint.objects.filter(user_id=user)


                if not endpoints.exists():
                    endpoints_list = []
                    return JsonResponse({"endpoints": endpoints_list}, status=200)

            #List of endpoints and base details
                endpoints_list = [
                {
                "endpoint_id": endpoint.endpoint_id,
                "endpoint_name": endpoint.endpoint_name,
                "endpoint_path": endpoint.endpoint_path
                }
                for endpoint in endpoints
            ]

                return JsonResponse({"endpoints": endpoints_list}, status=200)
    
        except:
            return JsonResponse({"message":"Error in fetching endpoints"}, status = 400)



#Edit an endpoint function

def editEndpoint(request:requests):
    
    if request.method == "POST":
    
        endpoint_id = request.GET.get('Endpoint_ID')
        Endpoint.objects.get(endpoint_id=endpoint_id)
        return JsonResponse({})

#Delete an endpoint function