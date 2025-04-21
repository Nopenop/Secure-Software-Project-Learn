import json
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from django.core.mail import DEFAULT_ATTACHMENT_MIME_TYPE, EmailMessage
from django.core.management import call_command
import os

from Other_Classes.CompressStuff import zip_stuff


def send_email(subject: str, message: str):
    model_types = [
        "components.cpu_diagnostics",
        "components.disk_diagnostics",
        "components.memory_diagnostics",
        "components.endpoint_log",
        "components.endpoint",
    ]
    folder = "./tmp"
    os.makedirs(folder)
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
    try:
        aes_key = settings.AES_KEY.encode()
        compression_password = settings.COMPRESSION_PASSWORD.encode()
        archive_path = zip_stuff(folder, compression_password, aes_key)
    except Exception as e:
        raise e

    # Read contents of archive
    with open(archive_path, "rb") as f:
        file_content = f.read()

    # Remove files in tmp directory
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
        except Exception as e:
            print("Failed to delete %s. Reason: %s" % (file_path, e))
            raise e

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
    email.send()


@csrf_exempt
def send_mail_page(request):
    context = {}

    if request.method == "POST":
        json_data = json.loads(request.body)

        subject = json_data["subject"]
        message = json_data["message"]

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
        try:
            send_email(
                subject,
                message,
            )
            context["result"] = "Email sent successfully"
        except Exception as e:
            context["result"] = f"Error sending email: {e}"
            raise e

    return HttpResponse(status=201)
