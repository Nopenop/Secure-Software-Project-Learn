import json
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from components.models import User, Endpoint
from django.core.mail import DEFAULT_ATTACHMENT_MIME_TYPE, EmailMessage, send_mail
from django.core.management import call_command
import os

from Other_Classes.CompressStuff import zip_stuff


def send_email(subject: str, message: str):

    
    print("Emailing Service Called booo")
    model_types = [
        "components.cpu_diagnostics",
        "components.disk_diagnostics",
        "components.memory_diagnostics",
        "components.endpoint_log",
        "components.endpoint",
    ]
    folder = "./tmp"
    os.makedirs(folder, exist_ok=True)
    for model in model_types:
        file_path = os.path.join(folder, model)
        # Dump database info
        with open(file_path, "w") as f:
            call_command(
                "dumpdata",
                model,
                format="json",
                indent=3,
                stdout=f,
            )

    # Create Archive
    archive_path = ""
    aes_key = settings.AES_KEY.encode()
    compression_password = settings.COMPRESSION_PASSWORD.encode()
    archive_path = zip_stuff(folder, compression_password, aes_key)


    # Read contents of archive
    with open(archive_path, "rb") as f:
        file_content = f.read()

    # Remove files in tmp directory
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)

    # Remove Archive
    os.unlink(archive_path)

    # Send Email with Attached Container
    
    email = EmailMessage(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [settings.ADMIN_EMAIL],
    )
    email.attach("secure-archive.zip", file_content, DEFAULT_ATTACHMENT_MIME_TYPE)
    try:
        sent = email.send(fail_silently=False)
        print("Email send status:", sent)
    except Exception as e:
        print("Email failed to send:", str(e))
        import traceback
        traceback.print_exc()


@csrf_exempt
def send_mail_page(request):
    context = {}

    if request.method == "POST":
        json_data = json.loads(request.body)

        subject = json_data.get("subject")
        message = json_data.get("message")
        endpoint_id = json_data.get("endpoint_id")
        print(endpoint_id)
        print(subject)

        # Translate short subject codes
        if subject == "CPU":
            subject = "CPU Usage Exceeded Limit Over Tolerable Amount"
        elif subject == "DISK":
            subject = "Disk Usage Exceeded Limit Over Tolerable Amount"
        elif subject == "MEMORY":
            subject = "Memory Usage Exceeded Limit Over Tolerable Amount"
        elif subject == "SSL":
            subject = "SSL Error invalid SSL"
        elif subject == "ENDPOINT":
            subject = "Endpoint Invalid Responses Exceeded Limit Over Tolerable Amount"
        elif subject == "HTTP":
            subject = "HTTP Error of unknown type"

        # Call the correct function
        if endpoint_id:
            send_email_monitor(subject, message, endpoint_id)
       
        else:
            send_email(subject, message)

        context["result"] = "Email sent successfully"

    return HttpResponse(status=201)


def send_email_monitor(subject: str, message: str, endpoint_id:str):
    
    endpoint = Endpoint.objects.select_related("user_id").get(endpoint_id=endpoint_id)
    user_email = endpoint.user_id.email
    user_password = endpoint.user_id.password
    
    print("Emailing Service Called, but just Endpoint")
    model_types = [
        "components.cpu_diagnostics",
        "components.disk_diagnostics",
        "components.memory_diagnostics",
        "components.endpoint_log",
        "components.endpoint",
    ]
    folder = "./tmp"
    os.makedirs(folder, exist_ok=True)
    for model in model_types:
        file_path = os.path.join(folder, model)
        # Dump database info
        with open(file_path, "w") as f:
            call_command(
                "dumpdata",
                model,
                format="json",
                indent=3,
                stdout=f,
            )

    # Create Archive
    archive_path = ""
    aes_key = settings.AES_KEY.encode()
    compression_password = user_password.encode()
    archive_path = zip_stuff(folder, compression_password, aes_key)


    # Read contents of archive
    with open(archive_path, "rb") as f:
        file_content = f.read()

    # Remove files in tmp directory
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)

    # Remove Archive
    os.unlink(archive_path)

    # Send Email with Attached Container
    
    email = EmailMessage(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [user_email]
    )
    email.attach("secure-archive.zip", file_content, DEFAULT_ATTACHMENT_MIME_TYPE)
    try:
        sent = email.send(fail_silently=False)
        print("Email send status:", sent)
    except Exception as e:
        print("Email failed to send:", str(e))
        import traceback
        traceback.print_exc()

