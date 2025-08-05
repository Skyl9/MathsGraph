import copy
import json
from typing import List
import datetime

from fastapi import HTTPException
from psycopg import AsyncConnection, DatabaseError
from psycopg2.extras import RealDictCursor

from app.db.database import get_db_connection
from app.schemas import UpdateConceptDict

from app.schemas.concept import ConceptName, ConceptResponse, RollbackConcept
from app.schemas.history import History
from app.services.tags_service import TagsService

def format_alias(alias):
    string_alias = ""
    for i in alias:
        string = i + "\n"
        string_alias += string
    return string_alias


def format_relation(relation):
    string_relation = ""
    for i in relation:
        string = i["concept_source"]+ " -> " + i["concept_cible"] + ", Relation : " + i["type_relation"]
        if i["description"]:
            string += " - " + str(i["description"]) + "\n"
        else :
            string+= "\n"
        string_relation += string

    return string_relation


def format_source(source):
    string_source = ""
    for i in source:
        string = "Titre : " + i["titre"] + " - Auteur : " + i["auteur"] + " - année " + str(i["annee"]) + " - type : "+ i["type"]
        if i["url"]:
            string += " - url : " + i["url"]+ "\n"
        else :
            string+= "\n"
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
    def __init__(self,db:AsyncConnection):
        self.db = db


    async def get_concept_info(self,concept_id) -> ConceptResponse:
        try:
            async with self.db.cursor() as cursor:
                # Récupérer les informations de base sur le concept
                await cursor.execute("""
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
                result = await cursor.fetchone()

                if not result:
                    return None  # Si le concept n'existe pas

                concept = {
                    "id": result[0],
                    "nom": result[1],
                    "type": result[2],
                    "enonce": result[3],
                    "demonstration": result[4],
                    "verification": result[5],
                    "date_modification": result[6].isoformat() if result[6] else None,
                    "mathematicien": {"id": result[7], "mathematicien": result[8]}
                    if result[7] else None,
                    "categorie": {"id": result[9], "category": result[10]}
                    if result[9] else None,
                }
                # Récupérer les alias du concept
                await cursor.execute("SELECT alias FROM aliases WHERE concept_id = %s", (concept_id,))
                concept["aliases"] = [row[0] for row in await cursor.fetchall()]

                # Récupérer les sources liées au concept
                await cursor.execute("""
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
                    } for row in await cursor.fetchall()
                ]

                # Récupérer les relations du concept (sources ou cibles)
                await cursor.execute("""
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
                    } for row in await cursor.fetchall()
                ]

                await cursor.execute("""
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
                    } for row in await cursor.fetchall()
                ]
                tags = TagsService.get_tags_name_and_id_by_concept_id(concept_id, False)
                if tags:
                    concept["tags"] = tags
                else:
                    concept["tags"] = None
            if not concept:
                raise HTTPException(status_code=404, detail="Concept non trouvé")
            return concept
        except DatabaseError as e:
            raise HTTPException(status_code=500, detail="Erreur DB lors de la récupération du concept")


    async def rollback_history(self,concept_id: int, data: RollbackConcept):
        data = data.model_dump() if isinstance(data, RollbackConcept) else data
        conn = get_db_connection()

        async with self.db.cursor() as cursor:
            await cursor.execute("""
                           SELECT field_modified,old_value,note
                           FROM concept_versions
                           WHERE concept_id = %s
                           AND version_number = %s AND field_modified = %s
                           """, (concept_id, data["version_number"],data["field_modified"]))
            version = await cursor.fetchone()
        note = version[2]
        note = f"Rollback from version number {data['version_number']}" if note is None else f"{note} - Rollback from  {data['version_number']}"
        value = ConceptService.get_name_by_id(version[1],data["field_modified"]) # Traitement des ids / model dump pour la réutilisation dans updateConcept
        data={"field":version[0],"value":value,"note":note,"username":data["username"]}
        await ConceptService.updateConcept(concept_id,data,rollback=True)


    async def get_name_by_id(self,id,type):
        async with self.db.cursor() as cursor:
            if type == "mathematicien":
                await cursor.execute("""
                               SELECT nom
                               FROM mathematiciens
                               WHERE id = %s
                               """, (str(id),))
                result = await cursor.fetchone()
                if result:
                    return result[0]
            if type == "categorie":
                await cursor.execute("""
                               SELECT nom
                               FROM categories
                               WHERE id = %s
                               """, (str(id),))
                result = await cursor.fetchone()
                if result:
                    return result[0]
            if type == "type":
                await cursor.execute("""
                               SELECT type.type
                               FROM type WHERE id = %s
                """,(str(id),))
                result = await cursor.fetchone()
                if result:
                    return result[0]
            if type == "sources":
                id = json.loads(id)
            if type == "aliases":
                id = json.loads(id)
            if type == "noms_etrangers":
                id = json.loads(id)
            if type == "relations":
                id = json.loads(id)
            return id

    async def get_concept_versions(self,concept_id: int) -> List[History]:
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                           SELECT *
                           FROM concept_versions
                           WHERE concept_id = %s
                           ORDER BY version_number DESC
                           """, (concept_id,))
            data = await cursor.fetchall()
            versions = []
            for row in data:
                versions.append({
                        "version_number":row[0],
                        "modified_by":row[1],
                        "modified_at":row[2],
                        "field_modified":row[3],
                        "old_value":row[4],
                        "new_value":row[5],
                        "note":row[6],
                        "global_version":row[7],
                }
                )

        try :
            async with self.db.cursor() as cursor:
                for v in versions:
                    if v["field_modified"] == "mathematicien":
                        old_id = v["old_value"]
                        new_id = v["new_value"]
                        await cursor.execute("""
                                       SELECT nom
                                       FROM mathematiciens
                                       WHERE id = %s
                                       """, (str(old_id),))
                        v["old_value"] = await cursor.fetchone()[0]
                        await cursor.execute("""SELECT nom FROM mathematiciens WHERE id = %s""", (str(new_id),))
                        v["new_value"] = await cursor.fetchone()[0]


                    if v["field_modified"] == "categorie":
                        old_id = v["old_value"]
                        new_id = v["new_value"]
                        await cursor.execute("""
                                       SELECT nom
                                       FROM categories
                                       WHERE id = %s
                                       """, (str(old_id),))
                        v["old_value"] = await cursor.fetchone()[0]
                        await cursor.execute("""SELECT nom FROM categories WHERE id = %s""", (str(new_id),))
                        v["new_value"] = await cursor.fetchone()[0]

                    if v["field_modified"] == "type":
                        old_id = v["old_value"]
                        new_id = v["new_value"]
                        await cursor.execute("""
                                       SELECT type
                                       FROM type Where id =%s
                        """,(str(old_id),))
                        v["old_value"] = await cursor.fetchone()[0]
                        await  cursor.execute("""SELECT type FROM type WHERE id = %s""", (str(new_id),))
                        v["new_value"] = await cursor.fetchone()[0]

                    if v["field_modified"] == "sources":
                        json_old_value = json.loads(v["old_value"])
                        json_new_value = json.loads(v["new_value"])
                        v["old_value"] = format_source(json_old_value)
                        v["new_value"] = format_source(json_new_value)

                    if v["field_modified"] == "aliases":
                        json_old_value = json.loads(v["old_value"])
                        json_new_value = json.loads(v["new_value"])
                        v["old_value"] = format_alias(json_old_value)
                        v["new_value"] = format_alias(json_new_value)


                    if v["field_modified"] == "noms_etrangers":
                        json_old_value = json.loads(v["old_value"])
                        json_new_value = json.loads(v["new_value"])
                        v["old_value"] = format_foreign_name(json_old_value)
                        v["new_value"] = format_foreign_name(json_new_value)

                    if v["field_modified"] == "relations":
                        json_old_value = json.loads(v["old_value"])
                        json_new_value = json.loads(v["new_value"])
                        for i in json_old_value:
                            concept_source_id = i["concept_source"]
                            await cursor.execute(""" SELECT nom
                                               FROM concepts
                                               WHERE id = %s """, (concept_source_id,))
                            nom_source = await cursor.fetchone()[0]
                            i["concept_source"] = nom_source
                            concept_cible_id = i["concept_cible"]
                            await cursor.execute(""" SELECT nom
                                               FROM concepts
                                               WHERE id = %s """, (concept_cible_id,))
                            nom_cible = await cursor.fetchone()[0]

                            i["concept_cible"] = nom_cible
                        for j in json_new_value:
                            concept_source_id = j["concept_source"]
                            await cursor.execute(""" SELECT nom
                                               FROM concepts
                                               WHERE id = %s """, (concept_source_id,))
                            nom_source = await cursor.fetchone()[0]
                            j["concept_source"] = nom_source
                            concept_cible_id = j["concept_cible"]
                            await cursor.execute(""" SELECT nom
                                               FROM concepts
                                               WHERE id = %s """, (concept_cible_id,))
                            nom_cible = await cursor.fetchone()[0]
                            j["concept_cible"] = nom_cible


                        v["old_value"] = format_relation(json_old_value)
                        v["new_value"] = format_relation(json_new_value)

            return versions

        except Exception as e:
            raise HTTPException(status_code=500, detail="Erreur lors de la mise à jour")


    async def add_concept_version(self, username: str, concept_id: int, field_modified: str, old_version, new_version,
                            note: str = None,rollback:bool = False,):
        if old_version == new_version:
            return  # pas de changement, donc pas de version à stocker

            # Obtenir la connexion à la base de données

        if not old_version:
            old_version = ""  # Assurer que cette valeur est une chaîne de caractères

        async with self.db.transaction():
            async with self.db.cursor() as cursor:
                # Calculer le numéro de version
                await cursor.execute("""
                                SELECT COALESCE(MAX(version_number), 0) + 1
                                FROM concept_versions
                                WHERE concept_id = %s
                                  AND field_modified = %s
                                """, (concept_id, field_modified))
                version_number = await cursor.fetchone()[0]

                # Calculer le numéro de version globale
                await cursor.execute("""
                                SELECT COALESCE(MAX(global_version), 0) + 1
                                FROM concept_versions
                                WHERE concept_id = %s
                                """, (concept_id,))
                global_version = await cursor.fetchone()[0]

                # Récupérer l'ID utilisateur
                await cursor.execute("""SELECT id
                                   FROM users
                                   WHERE username = %s""", (username,))
                row = await cursor.fetchone()
                if not row:
                    raise ValueError(f"Utilisateur {username} introuvable")
                user_id = row[0]
                await cursor.execute("""INSERT INTO concept_versions(modified_by, concept_id, field_modified, old_value, new_value,note, global_version, version_number,is_rollback) VALUES (%s, %s, %s, %s, %s, %s, %s, %s,%s); """, (user_id, concept_id, field_modified, old_version, new_version, note, global_version,version_number,rollback))


    async def get_all_concepts_name(self)->list[ConceptName]:
        async with self.db.cursor() as cur:
            await cur.execute("SELECT id,nom FROM concepts")
            concepts = await cur.fetchall()
        conceptList = []
        for i in concepts:
            categoryDict = {
                "id": i[0],
                "nom": i[1],
            }
            conceptList.append(categoryDict)
        return conceptList

    async def updateConcept(self,concept_id: int, data: UpdateConceptDict,rollback:bool = False):
        data = data.model_dump() if isinstance(data, UpdateConceptDict) else data

        try:
            with self.db.transaction():
                with self.db.cursor() as cursor:

                    # Vérifier si l'ID existe
                    await cursor.execute("SELECT id FROM concepts WHERE id = %s;", (concept_id,))
                    if await cursor.fetchone() is None:
                        raise HTTPException(status_code=404, detail="ID not found")
                    # Champ à mettre à jour
                    if data["field"] in ["nom", "enonce", "demonstration", "verification", "date_ajout"]:
                        await cursor.execute(f"SELECT {data['field']} FROM concepts WHERE id=%s;", (concept_id,))
                        old_value = await cursor.fetchone()[0]
                        new_value = data["value"]
                        set_clause = data["field"] + " = %s"  # Ex: "x = %s, y = %s"
                        sql = f"UPDATE concepts SET {set_clause} WHERE id = %s;"
                        await cursor.execute(sql, (data["value"], concept_id))

                    elif data["field"] == "type":
                        await cursor.execute(f"SELECT type_id FROM concepts WHERE id=%s;", (concept_id,))
                        old_value = await cursor.fetchone()[0]
                        await cursor.execute("SELECT id FROM type WHERE type = %s;", (data["value"],))
                        new_value = await cursor.fetchone()[0]
                        await cursor.execute("UPDATE concepts SET type_id = (SELECT id FROM type WHERE type = %s ) WHERE id = %s;",
                                       (data["value"], concept_id))

                    elif data["field"] == "categorie":
                        await cursor.execute(f"SELECT categorie_id FROM concepts WHERE id=%s;", (concept_id,))
                        old_value = await cursor.fetchone()[0]
                        await cursor.execute("SELECT id FROM categories WHERE nom = %s;", (data["value"],))
                        new_value = await cursor.fetchone()[0]
                        sql = f"UPDATE concepts SET categorie_id = (SELECT id FROM categories WHERE nom = %s ) WHERE id = %s;"
                        await cursor.execute(sql, (data["value"], concept_id))

                    elif data["field"] == "mathematicien":
                        await cursor.execute(f"SELECT mathematicien_id FROM concepts WHERE id=%s;", (concept_id,))
                        old_value = await  cursor.fetchone()[0]
                        await cursor.execute("SELECT id FROM mathematiciens WHERE nom = %s;", (data["value"],))
                        new_value = await cursor.fetchone()[0]
                        sql = f"UPDATE concepts SET mathematicien_id = (SELECT id FROM mathematiciens WHERE nom = %s ) WHERE id = %s;"
                        await cursor.execute(sql, (data["value"], concept_id))

                    elif data["field"] == "relations":
                        await cursor.execute(f"SELECT concept_source, concept_cible, type_relation, description,date_relation FROM relations WHERE concept_source = %s OR concept_cible = %s;", (concept_id, concept_id))
                        query_result = await cursor.fetchall()
                        old_value = []
                        for relation in query_result:
                            a= {"id":concept_id,"concept_source": relation[0], "concept_cible": relation[1], "type_relation": relation[2],
                                "description": relation[3], "date_relation": relation[4]}
                            old_value.append(a)
                        #deepcopy nécessaire pour l'utilisation à l'enregistrement
                        new_value = copy.deepcopy(data["value"])

                        for i in new_value:
                            # si concept_source est un dict, on remplace par son id
                            if isinstance(i.get("concept_source"), dict):
                                i["concept_source"] = i["concept_source"]["id"]

                            # même chose pour concept_cible
                            if isinstance(i.get("concept_cible"), dict):
                                i["concept_cible"] = i["concept_cible"]["id"]




                        await cursor.execute("DELETE FROM relations WHERE concept_source = %s OR concept_cible = %s;",
                                       (concept_id, concept_id))
                        for relation in new_value:
                            await cursor.execute("""
                                           INSERT INTO relations (concept_source, concept_cible, type_relation, description)
                                           VALUES (%s, %s, %s, %s);
                                           """, (
                                               relation["concept_source"],
                                               relation["concept_cible"],
                                               relation["type_relation"],
                                               relation.get("description"),
                                           ))
                        #Transformation en json str nécessaire
                        old_value = json.dumps(old_value)
                        new_value = json.dumps(new_value)

                    elif data["field"] == "sources":
                        await cursor.execute(f"SELECT id,titre,auteur,annee,url,type FROM sources WHERE id IN (SELECT source_id FROM concepts_sources WHERE concept_id = %s);", (concept_id,))
                        query = await cursor.fetchall()
                        old_value = []
                        for i in query:
                            old_value.append({"id":i[0],"titre":i[1],"auteur":i[2],"annee":i[3],"url":i[4],"type":i[5]})
                        new_value = []

                        for i in data["value"]:
                            new_value.append({"id":i["id"],"titre":i["titre"],"auteur":i["auteur"],"annee":i["annee"],"url":i["url"],"type":i["type"]})

                        old_value = json.dumps(old_value)
                        new_value = json.dumps(new_value)

                        for source in data["value"]:
                            await cursor.execute(
                                "UPDATE sources SET titre = %s, auteur = %s, annee = %s, url = %s, type = %s WHERE id = %s;",
                                (source["titre"], source["auteur"], source["annee"], source["url"], source["type"],
                                 source["id"]))

                    elif data["field"] == "aliases":
                        await cursor.execute(f"SELECT alias FROM aliases WHERE concept_id = %s;", (concept_id,))
                        old_value = await cursor.fetchall()
                        old_value = [i[0] for i in old_value]
                        new_value = data["value"]
                        old_value = json.dumps(old_value)
                        new_value = json.dumps(new_value)


                        await cursor.execute("DELETE FROM aliases WHERE concept_id = %s;", (concept_id,))
                        for alias in data["value"]:
                            await cursor.execute("INSERT INTO aliases (concept_id, alias) VALUES (%s, %s);", (concept_id, alias))
                    elif data["field"] == "noms_etrangers":
                        await cursor.execute("""SELECT id, concept_id, "Nom_étranger", langue FROM foreign_name WHERE concept_id = %s;""", (concept_id,))
                        query = await cursor.fetchall()
                        old_value = []
                        for i in query:
                            old_value.append({"id":i[0],'concept_id':i[1],"Nom_étranger":i[2],"langue":i[3]})
                        new_value = []
                        for i in data["value"]:
                            new_value.append({"id":i["id"],"langue":i["langue"],"Nom_étranger":i["Nom_étranger"],"concept_id":i["concept_id"]})
                        new_value = data["value"]
                        old_value = json.dumps(old_value)
                        new_value = json.dumps(new_value)

                    # Ajouter la version dans l'historique
                    await ConceptService.add_concept_version(self,data["username"], concept_id, data["field"], old_value, new_value,rollback=rollback)



        except Exception as e:
                # En cas d'erreur, annuler les changements
                 print(f"Erreur dans updateConcept: {e}")



        # Retourner la réponse
        return {"message": "Mise à jour réussie", "status": 200, "data": data}


    async def getEditableFieldsOptions(self):
        async with self.db.cursor() as cursor:
            await cursor.execute("SELECT DISTINCT type FROM type")
            type_concept = [r[0] for r in await cursor.fetchall()]
            await cursor.execute("SELECT DISTINCT nom FROM categories")
            category = [r[0] for r in await cursor.fetchall()]
            await cursor.execute("SELECT DISTINCT nom FROM mathematiciens")
            mathematiciens = [r[0] for r in await cursor.fetchall()]
        data = {"mathematicien": mathematiciens,
                    "categorie": category,
                    "type": type_concept}
        return data
