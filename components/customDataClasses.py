from dataclasses import dataclass

@dataclass
class Endpoint_Data: 
    user_id: str 
    endpoint_id: str 
    endpoint_name: str 
    endpoint_path: str 
    endpoint_status: int
    
    
@dataclass
class User_Data: 
    
    email: str,
    password: str,


class User(models.Model):
    user_id = models.BigAutoField(primary_key=True)
    email = models.EmailField(max_length=60, unique=True)
    password = models.CharField(max_length=128)