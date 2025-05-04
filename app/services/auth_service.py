from app.db.database import get_db_connection


class AuthService:
    @staticmethod
    def register_user(user_data):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # [Code existant de register_user]
            pass
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def login_user(form_data):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # [Code existant de login_for_access_token]
            pass
        finally:
            cursor.close()
            conn.close()