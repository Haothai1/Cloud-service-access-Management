from fastapi import APIRouter, HTTPException
from uuid import uuid4
from app.database import execute_query, fetch_all

router = APIRouter()

@router.post("/")
def add_permission(name: str, endpoint: str, description: str):
    permission_id = str(uuid4())
    execute_query('''INSERT INTO permissions (id, name, endpoint, description) VALUES (?, ?, ?, ?)''',
                  (permission_id, name, endpoint, description))
    return {"id": permission_id, "name": name, "endpoint": endpoint, "description": description}

@router.get("/")
def get_permissions():
    permissions = fetch_all('''SELECT id, name, endpoint, description FROM permissions''')
    return [{"id": p[0], "name": p[1], "endpoint": p[2], "description": p[3]} for p in permissions]

@router.delete("/{permission_id}")
def delete_permission(permission_id: str):
    execute_query('''DELETE FROM permissions WHERE id = ?''', (permission_id,))
    return {"message": "Permission deleted successfully"}
