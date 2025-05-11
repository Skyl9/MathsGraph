from fastapi import HTTPException

from app.db.database import get_db_connection
from app.schemas import UpdateConceptDict

from app.schemas.concept import ConceptName

class ConceptService:
    @staticmethod
    def get_all_concepts_name()->list[ConceptName]:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id,nom FROM concepts")

        concepts = cur.fetchall()
        conceptList = []
        for i in concepts:
            categoryDict = {
                "id": i[0],
                "nom": i[1],
            }
            conceptList.append(categoryDict)
        return conceptList

    @staticmethod
    def updateConcept(concept_id: int, data: UpdateConceptDict):
        data = data.model_dump() if isinstance(data, UpdateConceptDict) else data
        conn = get_db_connection()
        cursor = conn.cursor()
        print(data)
        # Vérifier si l'ID existe
        cursor.execute("SELECT id FROM concepts WHERE id = %s;", (concept_id,))
        if cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="ID not found")

        if data["field"] in ["nom", "enonce", "demonstration", "verification", "date_ajout"]:
            set_clause = data["field"] + " = %s"  # Ex: "x = %s, y = %s"
            sql = f"UPDATE concepts SET {set_clause} WHERE id = %s;"
            cursor.execute(sql, (data["value"], concept_id))

        elif data["field"] == "type":
            cursor.execute("UPDATE concepts SET type_id = (SELECT id FROM type WHERE type = %s ) WHERE id = %s;",
                           (data["value"], concept_id))

        elif data["field"] == "categorie":
            print('hi')
            sql = f"UPDATE concepts SET categorie_id = (SELECT id FROM categories WHERE nom = %s ) WHERE id = %s;"
            print(sql)
            cursor.execute(sql, (data["value"], concept_id))


        elif data["field"] == "mathematicien":
            sql = f"UPDATE concepts SET mathematicien_id = (SELECT id FROM mathematiciens WHERE nom = %s ) WHERE id = %s;"
            cursor.execute(sql, (data["value"], concept_id))


        elif data["field"] == "relations":
            cursor.execute("DELETE FROM relations WHERE concept_source = %s OR concept_cible = %s;",
                           (concept_id, concept_id))
            for relation in data["value"]:
                cursor.execute("""
                    INSERT INTO relations (concept_source, concept_cible, type_relation, description)
                    VALUES (%s, %s, %s, %s);
                """, (
                    relation["concept_source"]["id"],
                    relation["concept_cible"]["id"],
                    relation["type_relation"],
                    relation.get("description"),
                ))

        elif data["field"] == "sources":
            for source in data["value"]:
                cursor.execute("UPDATE sources SET titre = %s,auteur = %s,annee = %s,url = %s,type = %s  WHERE id = %s ;", (source["titre"], source["auteur"], source["annee"], source["url"], source["type"],source["id"]))

        elif data["field"] == "aliases":
            cursor.execute("DELETE FROM aliases WHERE concept_id = %s;", (concept_id,))
            for alias in data["value"]:
                cursor.execute("INSERT INTO aliases (concept_id, alias) VALUES (%s, %s);", (concept_id, alias))
        conn.commit()

        cursor.close()
        conn.close()

        return {"message": "Mise à jour réussie", "status": 200, "data": data}


    @staticmethod
    def getEditableFieldsOptions():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT type FROM type")
        type_concept = [r[0] for r in cursor.fetchall()]
        cursor.execute("SELECT DISTINCT nom FROM categories")
        category = [r[0] for r in cursor.fetchall()]
        cursor.execute("SELECT DISTINCT nom FROM mathematiciens")
        mathematiciens = [r[0] for r in cursor.fetchall()]
        data = {"mathematicien": mathematiciens,
                "categorie": category,
                "type": type_concept}
        return data