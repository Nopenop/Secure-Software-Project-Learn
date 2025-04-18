import json
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.conf import settings

from django.core.mail import EmailMessage
from django.core.management import call_command
import os


def send_email(model_type: str, subject: str, message: str):
    # dump database info
    with open(f"./tmp/{subject}-file.txt", "w") as f:
        call_command(
            "dumpdata",
            model_type,
            format="json",
            indent=3,
            stdout=f,
        )

    with open(f"./tmp/{subject}-file.txt", "r") as f:
        file_content = f.read()

    email = EmailMessage(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [f"{os.environ['ADMIN_EMAIL']}"],
    )
    email.attach("logs.txt", file_content)

    email.send()


@csrf_exempt
def send_mail_page(request):
    context = {}

    if request.method == "POST":
        json_data = json.loads(request.body)

        subject = json_data["subject"]
        message = json_data["message"]
        model_type = ""

        if subject == "CPU":
            model_type = "components.cpu_diagnostics"
            subject = "CPU Usage Exceeded Limit Over Tolerable Amount"
        elif subject == "DISK":
            model_type = "components.disk_diagnostics"
            subject = "Disk Usage Exceeded Limit Over Tolerable Amount"
        elif subject == "MEMORY":
            model_type = "components.memory_diagnostics"
            subject = "Memory Usage Exceeded Limit Over Tolerable Amount"
        elif subject == "SSL":
            model_type = "components.endpoint_log"
            subject = "SSL Error invalid SSL"
        elif subject == "ENDPOINT":
            model_type = "components.endpoint_log"
            subject = "Endpoint Invalid Responses Exceeded Limit Over Tolerable Amount"
        elif subject == "HTTP":
            model_type = "components.endpoint_log"
            subject = "HTTP Error of unknown type"
        try:
            send_email(
                model_type,
                subject,
                message,
            )
            context["result"] = "Email sent successfully"
        except Exception as e:
            context["result"] = f"Error sending email: {e}"

    return HttpResponse(status=201)
