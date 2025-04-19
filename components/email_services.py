import os
import json
from django.http import JsonResponse, HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.management import call_command
from django.core.mail import EmailMessage

from .models import Endpoint  # adjust the import path as needed

TMP_DIR = "./tmp"
os.makedirs(TMP_DIR, exist_ok=True)


def send_email(
    model_type: str,
    subject: str,
    message: str,
    recipient: str,
    filename_suffix: str = None,
):
    """
    Dumps the given model_type to JSON, attaches it to an email, and sends it
    to `recipient`.
    """
    # build dump filename
    base = subject.replace(" ", "_")
    if filename_suffix:
        base += f"_{filename_suffix}"
    filename = f"{base}.json"
    filepath = os.path.join(TMP_DIR, filename)

    # dumpmodel data
    with open(filepath, "w") as f:
        call_command(
            "dumpdata",
            model_type,
            format="json",
            indent=2,
            stdout=f,
        )

    with open(filepath, "r") as f:
        file_content = f.read()

    # prepend endpoint info if available
    full_message = message

    email = EmailMessage(
        subject=subject,
        body=full_message,
        from_email=settings.EMAIL_HOST_USER,
        to=[recipient],
    )
    email.attach(filename, file_content, "application/json")
    email.send()


@csrf_exempt
def send_mail_page(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"], "Only POST allowed")

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    subject_key  = payload.get("subject", "")
    message      = payload.get("message", "")
    endpoint_id  = payload.get("endpoint_id")

    if not endpoint_id:
        return JsonResponse({"error": "Missing endpoint_id"}, status=400)

    # look up endpoint → user
    try:
        endpoint = Endpoint.objects.select_related("user_id").get(endpoint_id=endpoint_id)
    except Endpoint.DoesNotExist:
        return JsonResponse({"error": "Endpoint not found"}, status=404)

    user_email = endpoint.user_id.email

    # map incoming key → model & nice subject
    subject_map = {
        "CPU":      ("components.cpu_diagnostics", "CPU Usage Exceeded Limit"),
        "DISK":     ("components.disk_diagnostics", "Disk Usage Exceeded Limit"),
        "MEMORY":   ("components.memory_diagnostics", "Memory Usage Exceeded Limit"),
        "SSL":      ("components.endpoint_log",     "SSL Certificate Error"),
        "ENDPOINT": ("components.endpoint_log",     "Endpoint Response Error"),
        "HTTP":     ("components.endpoint_log",     "HTTP Error Encountered"),
    }

    if subject_key not in subject_map:
        return JsonResponse({"error": "Unknown subject"}, status=400)

    model_type, nice_subject = subject_map[subject_key]

    # include endpoint_id in message header
    prefixed_message = f"Endpoint ID: {endpoint_id}\n\n{message}"
    send_email(
            model_type=model_type,
            subject=nice_subject,
            message=prefixed_message,
            recipient=user_email,
            filename_suffix=endpoint_id
        )
    return JsonResponse({"result": "Email sent successfully to " + user_email}, status=201)