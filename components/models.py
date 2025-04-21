from django.db import models
import datetime


class User(models.Model):
    user_id = models.CharField(primary_key=True, max_length=32)
    email = models.EmailField(max_length=60, unique=True)
    password = models.CharField(max_length=128)


class Endpoint(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, default = -1) #Foreign Key, Users have a 1..* relationship with Endpoints
    endpoint_id = models.CharField(primary_key=True, max_length=32, default = -1) #Primary Key
    endpoint_name = models.CharField(max_length=60, default="")
    endpoint_path = models.CharField(max_length=60)
    endpoint_status = models.SmallIntegerField(default=1)
    


class Endpoint_Log(models.Model):
    endpoint_id = models.ForeignKey(Endpoint, on_delete=models.CASCADE, default=-1)
    endpoint_status = models.SmallIntegerField(null=True)
    event_time = models.TimeField(
        default=datetime.time(9, 0),  # Default to 9:00 AM
        null=True,  # Allow null in database
        blank=True,  # Allow blank in forms
    )


class CPU_Diagnostics(models.Model):
    cpu_percent_usage = models.FloatField(primary_key=False, blank=True)
    event_time = models.TimeField(
        default=datetime.time(9, 0),  # Default to 9:00 AM
        null=True,  # Allow null in database
        blank=True,  # Allow blank in forms
    )


class Memory_Diagnostics(models.Model):
    memory_percent_usage = models.FloatField()
    memory_GB_usage = models.FloatField(default=0.0, primary_key=False)
    memory_GB_total = models.FloatField(default=0.0, primary_key=False)
    event_time = models.TimeField(
        default=datetime.time(9, 0),  # Default to 9:00 AM
        null=True,  # Allow null in database
        blank=True,  # Allow blank in forms
    )


class Disk_Diagnostics(models.Model):
    disk_percent_usage = models.FloatField()
    disk_GB_usage = models.FloatField(default=0.0, primary_key=False)
    disk_GB_total = models.FloatField(default=0.0, primary_key=False)
    event_time = models.TimeField(
        default=datetime.time(9, 0),  # Default to 9:00 AM
        null=True,  # Allow null in database
        blank=True,  # Allow blank in forms
    )