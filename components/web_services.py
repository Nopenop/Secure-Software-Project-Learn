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
    



#Get endpoints for user home page Function

#Edit an endpoint function

#Delete an endpoint function