from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime

class Permission(BaseModel):
    id: str
    name: str
    endpoint: str
    description: str

class Plan(BaseModel):
    id: str
    name: str
    description: str
    api_permissions: List[str]
    api_limits: Dict[str, int]

class Subscription(BaseModel):
    id: str
    user_id: str
    plan_id: str
    start_date: datetime
    end_date: Optional[datetime] = None

class Usage(BaseModel):
    user_id: str
    api_calls: Dict[str, int]
