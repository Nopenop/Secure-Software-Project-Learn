from django.db import models

class User(models.Model):
    user_id = models.CharField(primary_key=True, max_length=32)
    email = models.EmailField(max_length=60, unique=True)
    password = models.CharField(max_length=128)

class Endpoint(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, default = -1)
    endpoint_id = models.CharField(primary_key=True, max_length=32, default = -1)
    endpoint_name = models.CharField(max_length=60)
    endpoint_path = models.CharField(max_length=60)
    endpoint_status = models.SmallIntegerField(null=True)
    
class CPU_Diagnostics(models.Model):
    endpoint_id = models.ForeignKey(Endpoint, on_delete=models.CASCADE, default=-1)
    cpu_percent_usage = models.FloatField()
    cpu_GB_usage = models.IntegerField()
    
class Disk_Diagnostics(models.Model):
    endpoint_id = models.ForeignKey(Endpoint, on_delete=models.CASCADE, default=-1)
    disk_percent_usage = models.FloatField()
    disk_GB_usage = models.IntegerField()
    
class Memory_Diagnostics(models.Model):
    endpoint_id = models.ForeignKey(Endpoint, on_delete=models.CASCADE, default=-1)
    mem_percent_usage = models.FloatField()
    mem_GB_usage = models.IntegerField()