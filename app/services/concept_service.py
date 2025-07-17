import copy
import json
from typing import List
import datetime

from fastapi import HTTPException
from psycopg2.extras import RealDictCursor

from app.db.database import get_db_connection
from app.schemas import UpdateConceptDict

from app.schemas.concept import ConceptName, ConceptResponse
from app.schemas.history import History
from app.services.tags_service import TagsService

def format_alias(alias):
    string_alias = ""
    for i in alias:
        string = i[2] + ", "
        string_alias += string
    return alias


def format_relation(relation):
    string_relation = ""
    for i in relation:
        string = i["concept_source"]["nom"] + " -> " + i["concept_cible"]["nom"] + " : " + i["type_relation"] + " - " + \
                 i["description"] + "\n"
        string_relation += string
    return string_relation


def format_source(source):
    string_source = ""
    for i in source:
        string = i[1] + " - " + i[2] + " - " + str(i[3]) + " - " + i[4] + " - " + i[5] + "\n"
        string_source += string
    return string_source


def format_foreign_name(foreign_name):
    string_foreign_name = ""
    for i in foreign_name:
        string = i + "\n"
        string_foreign_name += string
    return string_foreign_name


def format_tags(tags):
    string_tags = ""
    for i in tags:
        string = i["tag"] + " - " + i["tag_id"] + "\n"
        string_tags += string
    return string_tags


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
                           SELECT id, "Nom_étranger", langue
                           FROM foreign_name
                           WHERE concept_id= %s

                           """, (concept_id,))

            concept["noms_etrangers"] = [
                {
                    "id": row[0],
                    "Nom_francais": result[1], # Reprise du nom car il est toujours identique
                    "Nom_étranger": row[1],
                    "langue": row[2],
                } for row in cursor.fetchall()
            ]
            tags = TagsService.get_tags_name_and_id_by_concept_id(concept_id, False)
            if tags:
                concept["tags"] = tags
            else:
                concept["tags"] = None
        if not concept:
            raise HTTPException(status_code=404, detail="Concept non trouvé")
        return concept

    @staticmethod
    def get_concept_versions(concept_id: int) -> List[History]:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                           SELECT *
                           FROM concept_versions
                           WHERE concept_id = %s
                           ORDER BY version_number DESC
                           """, (concept_id,))
            versions = cursor.fetchall()
        return versions

    @staticmethod
    def add_concept_version(conn, username: str, concept_id: int, field_modified: str, old_version, new_version,
                            note: str = None):
        if old_version == new_version:
            return  # pas de changement, donc pas de version à stocker

            # Obtenir la connexion à la base de données

        if not old_version:
            old_version = ""  # Assurer que cette valeur est une chaîne de caractères

        # Créer un curseur manuellemement
        cursor2 = conn.cursor()

        # Calculer le numéro de version
        cursor2.execute("""
                        SELECT COALESCE(MAX(version_number), 0) + 1
                        FROM concept_versions
                        WHERE concept_id = %s
                          AND field_modified = %s
                        """, (concept_id, field_modified))
        version_number = cursor2.fetchone()[0]

        # Calculer le numéro de version globale
        cursor2.execute("""
                        SELECT COALESCE(MAX(global_version), 0) + 1
                        FROM concept_versions
                        WHERE concept_id = %s
                        """, (concept_id,))
        global_version = cursor2.fetchone()[0]

        # Récupérer l'ID utilisateur
        cursor2.execute("""SELECT id
                           FROM users
                           WHERE username = %s""", (username,))
        row = cursor2.fetchone()

        if not row:
            raise ValueError(f"Utilisateur {username} introuvable")
        user_id = row[0]

        print(user_id, concept_id, field_modified, old_version, new_version, note, global_version, version_number)

        # Insérer une nouvelle version dans la table
        cursor2.execute("""
                        INSERT INTO concept_versions(modified_by, concept_id, field_modified, old_value, new_value,
                                                     note, global_version, version_number)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                        """, (user_id, concept_id, field_modified, old_version, new_version, note, global_version,
                              version_number))


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

        try:
            # Obtenir une connexion
            conn = get_db_connection()
            cursor = conn.cursor()

            # Vérifier si l'ID existe
            cursor.execute("SELECT id FROM concepts WHERE id = %s;", (concept_id,))
            if cursor.fetchone() is None:
                raise HTTPException(status_code=404, detail="ID not found")

            # Champ à mettre à jour
            if data["field"] in ["nom", "enonce", "demonstration", "verification", "date_ajout"]:
                cursor.execute(f"SELECT {data['field']} FROM concepts WHERE id=%s;", (concept_id,))
                old_value = cursor.fetchone()[0]
                new_value = data["value"]
                set_clause = data["field"] + " = %s"  # Ex: "x = %s, y = %s"
                sql = f"UPDATE concepts SET {set_clause} WHERE id = %s;"
                cursor.execute(sql, (data["value"], concept_id))

            elif data["field"] == "type":
                cursor.execute(f"SELECT type_id FROM concepts WHERE id=%s;", (concept_id,))
                old_value = cursor.fetchone()[0]
                cursor.execute("SELECT id FROM type WHERE type = %s;", (data["value"],))
                new_value = cursor.fetchone()[0]
                cursor.execute("UPDATE concepts SET type_id = (SELECT id FROM type WHERE type = %s ) WHERE id = %s;",
                               (data["value"], concept_id))

            elif data["field"] == "categorie":
                cursor.execute(f"SELECT categorie_id FROM concepts WHERE id=%s;", (concept_id,))
                old_value = cursor.fetchone()[0]
                cursor.execute("SELECT id FROM categories WHERE nom = %s;", (data["value"],))
                new_value = cursor.fetchone()[0]
                sql = f"UPDATE concepts SET categorie_id = (SELECT id FROM categories WHERE nom = %s ) WHERE id = %s;"
                cursor.execute(sql, (data["value"], concept_id))

            elif data["field"] == "mathematicien":
                cursor.execute(f"SELECT mathematicien_id FROM concepts WHERE id=%s;", (concept_id,))
                old_value = cursor.fetchone()[0]
                cursor.execute("SELECT id FROM mathematiciens WHERE nom = %s;", (data["value"],))
                new_value = cursor.fetchone()[0]
                sql = f"UPDATE concepts SET mathematicien_id = (SELECT id FROM mathematiciens WHERE nom = %s ) WHERE id = %s;"
                cursor.execute(sql, (data["value"], concept_id))

            elif data["field"] == "relations":
                cursor.execute(f"SELECT concept_source, concept_cible, type_relation, description,date_relation FROM relations WHERE concept_source = %s OR concept_cible = %s;", (concept_id, concept_id))
                query_result = cursor.fetchall()
                old_value = []
                for relation in query_result:
                    a= {"id":concept_id,"concept_source": relation[0], "concept_cible": relation[1], "type_relation": relation[2],
                        "description": relation[3], "date_relation": relation[4]}
                    old_value.append(a)
                #deepcopy nécessaire pour l'utilisation à l'enregistrement
                new_value = copy.deepcopy(data["value"])
                for i in new_value:
                    i["concept_source"] = i["concept_source"]["id"]
                    i["concept_cible"] = i["concept_cible"]["id"]

                #Transformation en json str nécessaire
                old_value = json.dumps(old_value)
                new_value = json.dumps(new_value)


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
                cursor.execute(f"SELECT id,titre,auteur,annee,url,type FROM sources WHERE id IN (SELECT source_id FROM concepts_sources WHERE concept_id = %s);", (concept_id,))
                query = cursor.fetchall()
                old_value = []
                for i in query:
                    old_value.append({"id":i[0],"titre":i[1],"auteur":i[2],"annee":i[3],"url":i[4],"type":i[5]})
                new_value = []
                for i in data["value"]:
                    new_value.append({"id":i["id"],"titre":i["titre"],"auteur":i["auteur"],"annee":i["annee"],"url":i["url"],"type":i["type"]})

                old_value = json.dumps(old_value)
                new_value = json.dumps(new_value)



                for source in data["value"]:
                    cursor.execute(
                        "UPDATE sources SET titre = %s, auteur = %s, annee = %s, url = %s, type = %s WHERE id = %s;",
                        (source["titre"], source["auteur"], source["annee"], source["url"], source["type"],
                         source["id"]))

            elif data["field"] == "aliases":
                cursor.execute(f"SELECT alias FROM aliases WHERE concept_id = %s;", (concept_id,))
                old_value = cursor.fetchall()
                old_value = [i[0] for i in old_value]
                new_value = data["value"]
                old_value = json.dumps(old_value)
                new_value = json.dumps(new_value)


                cursor.execute("DELETE FROM aliases WHERE concept_id = %s;", (concept_id,))
                for alias in data["value"]:
                    cursor.execute("INSERT INTO aliases (concept_id, alias) VALUES (%s, %s);", (concept_id, alias))

            elif data["field"] == "tags":
                cursor.execute(f"SELECT tag_id FROM concept_tags WHERE concept_id = %s;", (concept_id,))
                old_value = cursor.fetchall()
                old_value = [i[0] for i in old_value]
                new_value = data["value"]
                old_value = json.dumps(old_value)
                new_value = json.dumps(new_value)

                for tags in data["value"]:
                    cursor.execute("SELECT concept_id FROM concept_tags WHERE concept_id = %s AND tag_id = %s;",
                                   (concept_id, tags["tag_id"]))
                    if cursor.fetchone():
                        raise HTTPException(status_code=409, detail="Relation already exists")
                    cursor.execute("SELECT id FROM tags WHERE id = %s;", (tags["tag"],))
                    if cursor.fetchone() is None:
                        raise HTTPException(status_code=404, detail="Tag not found")
                    try:
                        cursor.execute("INSERT INTO concept_tags (concept_id, tag_id) VALUES (%s, %s);",
                                       (concept_id, tags["tag"]))
                    except Exception as e:
                        raise HTTPException(status_code=409, detail="An error occurred: " + str(e))

            # Ajouter la version dans l'historique
            ConceptService.add_concept_version(conn,data["username"], concept_id, data["field"], old_value, new_value)

            # Log du changement
            console_log = f"Concept {concept_id} modified by {data['username']} : {data['field']} = {new_value} (old value : {old_value})"
            print(console_log)

            conn.commit()
            # Valider la transaction
        except Exception as e:
            # En cas d'erreur, annuler les changements
            if conn:
                conn.rollback()
            print(f"Erreur dans updateConcept: {e}")
            raise

        finally:
            # Fermer le curseur et la connexion en toute circonstance
            if cursor:
                cursor.close()
            if conn:
                conn.close()

        # Retourner la réponse
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
