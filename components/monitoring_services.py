import requests
import json


from django.http import HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


from components.classes import Endpoint_Data, User_Data
from components.id_creator import endpoint_ID_Creator
from components.models import User, Endpoint


@csrf_exempt
def createEndpoint(request: requests):
    try:
        if request.method == "POST":
            # if the request is a post request, map the data to the corresponding data
            # class and then write it into the database
            request_body = json.loads(request.body)

            config_data = Endpoint_Data(
                user_id=request_body["user_id"],
                endpoint_id=endpoint_ID_Creator(),
                endpoint_name=request_body["endpoint_name"],
                endpoint_path=request_body["endpoint_path"],
                endpoint_status=-1,  # indicates it hasn't been monitored yet
            )

            # Creates a new Endpoint object linked to the user via user_id
            new_endpoint = Endpoint(
                user_id=User.objects.get(user_id=config_data.user_id),
                endpoint_id=config_data.endpoint_id,
                endpoint_name=config_data.endpoint_name,
                endpoint_path=config_data.endpoint_path,
                endpoint_status=config_data.endpoint_status,
            )

            print(new_endpoint.endpoint_name)

            new_endpoint.save()

            # Create the monitoring Daemon using the config data
            # add code here

            return JsonResponse(
                {"message": "Successful Post for New Endpoint"}, status=200
            )
    except:  # error handling
        return JsonResponse({"message": "Failed Post for New Endpoint"}, status=405)
