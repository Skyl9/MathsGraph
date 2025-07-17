from typing import List

from app.core.exceptions import NotFoundException
from app.db.database import get_db_connection
from app.schemas.tags import TagsModel


class TagsService:
    @staticmethod
    def get_tags_id_by_concept_id(concept_id:int,warning = True )->List[int]|None:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:

            cursor.execute(
                "SELECT tag_id FROM concept_tags WHERE concept_id = %s;", (concept_id,)
            )
            tags = cursor.fetchall()
            if not tags :
                if warning:
                    raise NotFoundException(f"No tags found for this concept id: {concept_id}")
                else:
                    return None
            return [tag[0] for tag in tags]
        finally:
            conn.close()
    @staticmethod
    def get_tags_name_and_id_by_concept_id(concept_id:int,warning = True)->List[TagsModel]|None:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT concept_tags.tag_id, tags.name FROM concept_tags JOIN tags ON concept_tags.tag_id = tags.id WHERE concept_id = %s;", (concept_id,)
            )
            tags = cursor.fetchall()
            if not tags:
                if warning:
                    raise NotFoundException(f"No tags found for this concept id: {concept_id}")
                else:
                    return None
            return [{"id":tag[0],"tag":tag[1]} for tag in tags]
        finally:
            conn.close()

    @staticmethod
    def get_all_tags()->List[TagsModel]|None:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT id, name FROM tags;"
            )
            tags = cursor.fetchall()
            tags = [{"id":tag[0],"tag":tag[1]} for tag in tags]
            return tags
        except Exception as e:
            print(e)
            return None
        finally:
            conn.close()

    @staticmethod
    def create_new_tag(tag_name:str)->None:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT name FROM tags WHERE name = %s;", (tag_name,))
            if cursor.fetchone():
                return None
            cursor.execute(
                "INSERT INTO tags (name) VALUES (%s);", (tag_name,)
            )
            conn.commit()
        except Exception as e:
            print(e)
            return None
        finally:
            conn.close()

    @staticmethod
    def add_tag_to_concept(concept_id:int,tag_id:int)->None:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id FROM tags WHERE id = %s;", (tag_id,))
            if not cursor.fetchone():
                return None
            cursor.execute("SELECT concept_id FROM concept_tags WHERE concept_id = %s AND tag_id = %s;", (concept_id,tag_id))
            if cursor.fetchone():
                return None
            cursor.execute(
                "INSERT INTO concept_tags (concept_id, tag_id) VALUES (%s, %s);", (concept_id, tag_id)
            )
            conn.commit()
        except Exception as e:
            print(e)
            return None
        finally:
            conn.close()

    @staticmethod
    def remove_tag_from_concept(concept_id:int,tag_id:int)->None:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id FROM tags WHERE id = %s;", (tag_id,))
            if not cursor.fetchone():
                return None
            cursor.execute("SELECT concept_id FROM concept_tags WHERE concept_id = %s AND tag_id = %s;", (concept_id,tag_id))
            if not cursor.fetchone():
                return None
            cursor.execute(
                "DELETE FROM concept_tags WHERE concept_id = %s AND tag_id = %s;", (concept_id, tag_id)
            )
            conn.commit()

        except Exception as e:
            print(e)
            return None
        finally:
            conn.close()