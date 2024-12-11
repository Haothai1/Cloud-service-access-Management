from fastapi import APIRouter, HTTPException
from uuid import uuid4
from app.database import execute_query, fetch_all

router = APIRouter()

@router.post("/")
def create_plan(name: str, description: str, api_permissions: list, api_limits: dict):
    plan_id = str(uuid4())
    execute_query('''INSERT INTO plans (id, name, description, api_permissions, api_limits) VALUES (?, ?, ?, ?, ?)''',
                  (plan_id, name, description, ",".join(api_permissions), str(api_limits)))
    return {"id": plan_id, "name": name, "description": description, "api_permissions": api_permissions, "api_limits": api_limits}

@router.get("/")
def get_plans():
    plans = fetch_all('''SELECT id, name, description, api_permissions, api_limits FROM plans''')
    return [{"id": p[0], "name": p[1], "description": p[2], "api_permissions": p[3].split(","), "api_limits": eval(p[4])} for p in plans]
