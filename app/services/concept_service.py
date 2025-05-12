from fastapi import HTTPException

from app.db.database import get_db_connection
from app.schemas import UpdateConceptDict

from app.schemas.concept import ConceptName, ConceptResponse


class ConceptService:
    @staticmethod
    def get_concept_info(concept_id) -> ConceptResponse:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Récupérer les informations de base sur le concept
            cursor.execute("""
                           SELECT c.id,
                                  c.nom,
                                  t.type,
                                  c.enonce,
                                  c.demonstration,
                                  c.verification,
                                  c.date_modification,
                                  m.id,
                                  m.nom,
                                  cat.id,
                                  cat.nom
                           FROM concepts c
                                    LEFT JOIN mathematiciens m ON c.mathematicien_id = m.id
                                    LEFT JOIN categories cat ON c.categorie_id = cat.id
                                    LEFT JOIN type t ON c.type_id = t.id
                           WHERE c.id = %s
                           ORDER BY c.id ASC
                           """, (concept_id,))
            result = cursor.fetchone()

            if not result:
                return None  # Si le concept n'existe pas

            concept = {
                "id": result[0],
                "nom": result[1],
                "type": result[2],
                "enonce": result[3],
                "demonstration": result[4],
                "verification": result[5],
                "date_modification": result[6],
                "mathematicien": {"id": result[7], "mathematicien": result[8]}
                if result[7] else None,
                "categorie": {"id": result[9], "category": result[10]}
                if result[9] else None,
            }
            # Récupérer les alias du concept
            cursor.execute("SELECT alias FROM aliases WHERE concept_id = %s", (concept_id,))
            concept["aliases"] = [row[0] for row in cursor.fetchall()]

            # Récupérer les sources liées au concept
            cursor.execute("""
                           SELECT DISTINCT s.id, s.titre, s.auteur, s.annee, s.url, s."type"
                           FROM sources s
                                    JOIN concepts_sources cs ON s.id = cs.source_id
                           WHERE cs.concept_id = %s
                           """, (concept_id,))
            concept["sources"] = [
                {
                    "id": row[0],
                    "titre": row[1],
                    "auteur": row[2],
                    "annee": row[3],
                    "url": row[4],
                    "type": row[5],
                } for row in cursor.fetchall()
            ]

            # Récupérer les relations du concept (sources ou cibles)
            cursor.execute("""
                           SELECT r.id,
                                  r.concept_source,
                                  c_source.nom AS nom_source,
                                  r.concept_cible,
                                  c_cible.nom  AS nom_cible,
                                  r.type_relation,
                                  r.description,
                                  r.date_relation
                           FROM relations r
                                    JOIN concepts c_source ON r.concept_source = c_source.id
                                    JOIN concepts c_cible ON r.concept_cible = c_cible.id
                           WHERE concept_source = %s
                              OR concept_cible = %s
                           """, (concept_id, concept_id))
            concept["relations"] = [
                {
                    "id": row[0],
                    "concept_source": {"id": row[1], "nom": row[2]},
                    "concept_cible": {"id": row[3], "nom": row[4]},
                    "type_relation": row[5],
                    "description": row[6],
                } for row in cursor.fetchall()
            ]
            cursor.execute("""
                           SELECT id, "Nom_francais", "Nom_étranger", langue
                           FROM foreign_name
                           WHERE "Nom_francais" = (SELECT nom FROM concepts WHERE id = %s)

                           """, (concept_id,))
            concept["noms_etrangers"] = [
                {
                    "id": row[0],
                    "Nom_francais": row[1],
                    "Nom_étranger": row[2],
                    "langue": row[3],
                } for row in cursor.fetchall()
            ]
        if not concept:
            raise HTTPException(status_code=404, detail="Concept non trouvé")
        return concept

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