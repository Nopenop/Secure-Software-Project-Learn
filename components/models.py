from django.db import models

class User(models.Model):
    user_id = models.BigAutoField(primary_key=True)
    email = models.EmailField(max_length=60, unique=True)
    password = models.CharField(max_length=128)

class Endpoint(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    endpoint_name = models.CharField(max_length=60)
    endpoint_path = models.CharField(max_length=60)