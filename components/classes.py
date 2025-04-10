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
    user_id:str
    email: str
    password: str