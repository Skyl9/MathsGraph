from datetime import datetime
from typing import Dict
from unittest import case

from fastapi import HTTPException
from sympy.strategies.core import switch

from app.db.database import get_db_connection
from app.schemas.user import UserId, UpdateUser


class UserService:
    @staticmethod
    def get_user_by_id(id_user: int):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id,username,email,is_active,created_at,role,preferred_language,avatar_url,bio FROM users WHERE id = %s;", (id_user,))
        user = cursor.fetchone()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        # Sérialisation du champ created_at
        created_at = user[4]
        if isinstance(created_at, datetime):
            created_at = created_at.isoformat()  # Convertit datetime au format ISO 8601

        return {
            "id": user[0],
            "username": user[1],
            "email": user[2],
            "is_active": user[3],
            "created_at":created_at,
            "role": user[5],
            "preferred_language": user[6],
            "avatar_url":user[7],
            "bio": user[8],
        }
    @staticmethod
    def get_id_by_username(username: str) -> UserId :
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = %s;", (username,))
        user = cursor.fetchone()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return {"id":user[0]}

    @staticmethod
    def patch_user(id:str, data: UpdateUser):
        conn = get_db_connection()
        cursor = conn.cursor()
        data = data.model_dump() if isinstance(data, UpdateUser) else data
        cursor.execute(f"UPDATE users SET {data["field"]} = %s WHERE id = %s;", (data["value"], id))
        conn.commit()