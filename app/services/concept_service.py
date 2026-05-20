import copy
import json
import logging
from typing import List, Any
from datetime import datetime

from sqlalchemy import select, func, desc, delete, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.core.exceptions import NotFoundException, InternalServerError
from app.schemas import UpdateConceptDict
from app.schemas.concept import ConceptName, ConceptResponse, RollbackConcept
from app.schemas.history import History
from app.services.tags_service import TagsService
from app.db.models import Concept, ConceptVersion, User, Type, Category, Mathematicien, Alias, Source, ForeignName, Relation

logger = logging.getLogger(__name__)


def format_alias(alias):
    string_alias = ""
    for i in alias:
        string = i + "\n"
        string_alias += string
    return string_alias


def format_relation(relation):
    string_relation = ""
    for i in relation:
        string = i["concept_source"] + " -> " + i["concept_cible"] + ", Relation : " + i["type_relation"]
        if i["description"]:
            string += " - " + str(i["description"]) + "\n"
        else:
            string += "\n"
        string_relation += string

    return string_relation


def format_source(source):
    string_source = ""
    for i in source:
        string = "Titre : " + i["titre"] + " - Auteur : " + i["auteur"] + " - année " + str(i["annee"]) + " - type : " + \
                 i["type"]
        if i["url"]:
            string += " - url : " + i["url"] + "\n"
        else:
            string += "\n"
        string_source += string
    return string_source


def format_foreign_name(foreign_name):
    string_foreign_name = ""
    for i in foreign_name:
        string = i + "\n"
        string_foreign_name += string
    return string_foreign_name


class ConceptService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_concept_info(self, concept_id: int) -> dict[str | Any, None | dict[str, Any] | list[Any] | Any]:
        query = (
            select(Concept)
            .where(Concept.id == concept_id)
            .options(
                joinedload(Concept.type),
                joinedload(Concept.mathematicien),
                joinedload(Concept.category),
                selectinload(Concept.aliases),
                selectinload(Concept.sources),
                selectinload(Concept.tags),
                selectinload(Concept.foreign_names),
                selectinload(Concept.outgoing_relations).joinedload(Relation.target_concept),
                selectinload(Concept.incoming_relations).joinedload(Relation.source_concept),
            )
        )
        result = await self.db.execute(query)
        concept_obj = result.scalars().first()

        if not concept_obj:
            raise NotFoundException(detail="Concept non trouvé")

        # Fusion des relations entrantes et sortantes pour correspondre au format attendu
        all_relations = []
        for r in concept_obj.outgoing_relations:
            all_relations.append({
                "id": r.id,
                "concept_source": {"id": r.concept_source, "nom": concept_obj.nom},
                "concept_cible": {"id": r.concept_cible, "nom": r.target_concept.nom if r.target_concept else None},
                "type_relation": r.type_relation,
                "description": r.description,
            })
        for r in concept_obj.incoming_relations:
            all_relations.append({
                "id": r.id,
                "concept_source": {"id": r.concept_source, "nom": r.source_concept.nom if r.source_concept else None},
                "concept_cible": {"id": r.concept_cible, "nom": concept_obj.nom},
                "type_relation": r.type_relation,
                "description": r.description,
            })

        tags = await TagsService(self.db).get_tags_name_and_id_by_concept_id(concept_id, False)

        return {
            "id": concept_obj.id,
            "nom": concept_obj.nom,
            "type": concept_obj.type.type if concept_obj.type else None,
            "enonce": concept_obj.enonce,
            "demonstration": concept_obj.demonstration,
            "verification": concept_obj.verification,
            "date_modification": concept_obj.date_modification,
            "mathematicien": {"id": concept_obj.mathematicien_id, "mathematicien": concept_obj.mathematicien.nom}
            if concept_obj.mathematicien else None,
            "categorie": {"id": concept_obj.categorie_id, "category": concept_obj.category.nom}
            if concept_obj.category else None,
            "aliases": [a.alias for a in concept_obj.aliases],
            "sources": [
                {
                    "id": s.id,
                    "titre": s.titre,
                    "auteur": s.auteur,
                    "annee": s.annee,
                    "url": s.url,
                    "type": s.type,
                } for s in concept_obj.sources
            ],
            "relations": all_relations,
            "noms_etrangers": [
                {
                    "id": n.id,
                    "Nom_francais": concept_obj.nom,
                    "Nom_étranger": n.nom_etranger,
                    "langue": n.langue,
                } for n in concept_obj.foreign_names
            ],
            "tags": tags if tags else None
        }

    async def rollback_history(self, concept_id: int, data: RollbackConcept) -> None:
        data_dict = data.model_dump() if isinstance(data, RollbackConcept) else data
        
        query = select(ConceptVersion).where(
            ConceptVersion.concept_id == concept_id,
            ConceptVersion.version_number == data_dict["version_number"],
            ConceptVersion.field_modified == data_dict["field_modified"]
        )
        result = await self.db.execute(query)
        version = result.scalars().first()
        
        if not version:
            raise NotFoundException(detail="Version non trouvée")
            
        note = version.note
        note = f"Rollback from version number {data_dict['version_number']}" if note is None else f"{note} - Rollback from {data_dict['version_number']}"
        
        value = await self.get_name_by_id(version.old_value, data_dict["field_modified"])
        
        update_data = UpdateConceptDict(
            field=version.field_modified,
            value=value,
            username=data_dict["username"],
            note=note
        )
        await self.updateConcept(concept_id, update_data, rollback=True)

    async def get_name_by_id(self, id_val, field_type):
        if not id_val:
            return id_val
            
        if field_type == "mathematicien":
            math = await self.db.get(Mathematicien, int(id_val))
            return math.nom if math else id_val
        if field_type == "categorie":
            cat = await self.db.get(Category, int(id_val))
            return cat.nom if cat else id_val
        if field_type == "type":
            t = await self.db.get(Type, int(id_val))
            return t.type if t else id_val
            
        if field_type in ["sources", "aliases", "noms_etrangers", "relations"]:
            try:
                return json.loads(id_val)
            except (TypeError, json.JSONDecodeError):
                return id_val
        return id_val

    async def get_concept_versions(self, concept_id: int) -> List[History]:
        query = (
            select(ConceptVersion)
            .where(ConceptVersion.concept_id == concept_id)
            .order_by(desc(ConceptVersion.version_number))
        )
        result = await self.db.execute(query)
        versions = result.scalars().all()
        
        res_versions = []
        for v in versions:
            v_dict = {
                "id": v.id,
                "concept_id": v.concept_id,
                "modified_by": v.modified_by,
                "modified_at": v.modified_at,
                "field_modified": v.field_modified,
                "old_value": v.old_value,
                "new_value": v.new_value,
                "version_number": v.version_number,
                "global_version": v.global_version,
                "is_rollback": v.is_rollback,
                "note": v.note,
            }
            
            # Résolution des noms
            if v.field_modified == "mathematicien":
                if v.old_value and v.old_value.isdigit():
                    old_m = await self.db.get(Mathematicien, int(v.old_value))
                    v_dict["old_value"] = old_m.nom if old_m else v.old_value
                if v.new_value and v.new_value.isdigit():
                    new_m = await self.db.get(Mathematicien, int(v.new_value))
                    v_dict["new_value"] = new_m.nom if new_m else v.new_value
            
            elif v.field_modified == "categorie":
                if v.old_value and v.old_value.isdigit():
                    old_c = await self.db.get(Category, int(v.old_value))
                    v_dict["old_value"] = old_c.nom if old_c else v.old_value
                if v.new_value and v.new_value.isdigit():
                    new_c = await self.db.get(Category, int(v.new_value))
                    v_dict["new_value"] = new_c.nom if new_c else v.new_value
                    
            elif v.field_modified == "type":
                if v.old_value and v.old_value.isdigit():
                    old_t = await self.db.get(Type, int(v.old_value))
                    v_dict["old_value"] = old_t.type if old_t else v.old_value
                if v.new_value and v.new_value.isdigit():
                    new_t = await self.db.get(Type, int(v.new_value))
                    v_dict["new_value"] = new_t.type if new_t else v.new_value

            elif v.field_modified == "sources":
                try:
                    v_dict["old_value"] = format_source(json.loads(v.old_value)) if v.old_value else ""
                    v_dict["new_value"] = format_source(json.loads(v.new_value)) if v.new_value else ""
                except (json.JSONDecodeError, TypeError): pass

            elif v.field_modified == "aliases":
                try:
                    v_dict["old_value"] = format_alias(json.loads(v.old_value)) if v.old_value else ""
                    v_dict["new_value"] = format_alias(json.loads(v.new_value)) if v.new_value else ""
                except (json.JSONDecodeError, TypeError): pass

            elif v.field_modified == "noms_etrangers":
                try:
                    v_dict["old_value"] = format_foreign_name(json.loads(v.old_value)) if v.old_value else ""
                    v_dict["new_value"] = format_foreign_name(json.loads(v.new_value)) if v.new_value else ""
                except (json.JSONDecodeError, TypeError): pass

            elif v.field_modified == "relations":
                try:
                    old_rels = json.loads(v.old_value) if v.old_value else []
                    new_rels = json.loads(v.new_value) if v.new_value else []
                    
                    for i in old_rels:
                        src = await self.db.get(Concept, i["concept_source"])
                        tgt = await self.db.get(Concept, i["concept_cible"])
                        i["concept_source"] = src.nom if src else str(i["concept_source"])
                        i["concept_cible"] = tgt.nom if tgt else str(i["concept_cible"])
                    for j in new_rels:
                        src = await self.db.get(Concept, j["concept_source"])
                        tgt = await self.db.get(Concept, j["concept_cible"])
                        j["concept_source"] = src.nom if src else str(j["concept_source"])
                        j["concept_cible"] = tgt.nom if tgt else str(j["concept_cible"])
                        
                    v_dict["old_value"] = format_relation(old_rels)
                    v_dict["new_value"] = format_relation(new_rels)
                except (json.JSONDecodeError, TypeError): pass
            
            res_versions.append(v_dict)
            
        return res_versions

    async def add_concept_version(self, username: str, concept_id: int, field_modified: str, old_version, new_version,
                                  note: str = None, rollback: bool = False):
        if str(old_version) == str(new_version):
            return

        # Obtenir l'ID utilisateur
        query_user = select(User.id).where(User.username == username)
        res_user = await self.db.execute(query_user)
        user_id = res_user.scalar_one_or_none()
        if not user_id:
            raise NotFoundException(detail=f"Utilisateur {username} introuvable")

        # Calculer le numéro de version
        query_v = select(func.coalesce(func.max(ConceptVersion.version_number), 0) + 1).where(
            ConceptVersion.concept_id == concept_id,
            ConceptVersion.field_modified == field_modified
        )
        version_number = await self.db.scalar(query_v)

        # Calculer le numéro de version globale
        query_gv = select(func.coalesce(func.max(ConceptVersion.global_version), 0) + 1).where(
            ConceptVersion.concept_id == concept_id
        )
        global_version = await self.db.scalar(query_gv)

        new_v = ConceptVersion(
            modified_by=user_id,
            concept_id=concept_id,
            field_modified=field_modified,
            old_value=str(old_version) if old_version is not None else None,
            new_value=str(new_version) if new_version is not None else None,
            note=note,
            global_version=global_version,
            version_number=version_number,
            is_rollback=rollback
        )
        self.db.add(new_v)
        await self.db.flush()

    async def get_all_concepts_name(self) -> list[ConceptName]:
        query = select(Concept.id, Concept.nom)
        result = await self.db.execute(query)
        return [{"id": row[0], "nom": row[1]} for row in result.all()]

    async def updateConcept(self, concept_id: int, data: UpdateConceptDict, rollback: bool = False) -> None:
        data_dict = data.model_dump() if isinstance(data, UpdateConceptDict) else data

        concept = await self.db.get(Concept, concept_id)
        if not concept:
            raise NotFoundException(detail="Concept non trouvé")

        field_name = data_dict["field"]
        new_value_raw = data_dict["value"]

        # Routage propre vers les méthodes spécialisées
        if field_name in ["nom", "enonce", "demonstration", "verification"]:
            old_value = getattr(concept, field_name)
            setattr(concept, field_name, new_value_raw)
            new_value = new_value_raw
        elif field_name == "type":
            old_value, new_value = await self._update_type(concept, new_value_raw)
        elif field_name == "categorie":
            old_value, new_value = await self._update_category(concept, new_value_raw)
        elif field_name == "mathematicien":
            old_value, new_value = await self._update_mathematicien(concept, new_value_raw)
        elif field_name == "relations":
            old_value, new_value = await self._update_relations(concept_id, new_value_raw)
        elif field_name == "sources":
            old_value, new_value = await self._update_sources(concept_id, new_value_raw)
        elif field_name == "aliases":
            old_value, new_value = await self._update_aliases(concept_id, new_value_raw)
        elif field_name == "noms_etrangers":
            old_value, new_value = await self._update_foreign_names(concept_id, new_value_raw)
        else:
            old_value, new_value = None, None

        # Historisation centralisée
        await self.add_concept_version(
            username=data_dict["username"],
            concept_id=concept_id,
            field_modified=field_name,
            old_version=old_value,
            new_version=new_value,
            rollback=rollback,
            note=data_dict.get("note")
        )
        await self.db.flush()

    async def _update_type(self, concept: Concept, new_value_raw: str):
        old_value = concept.type_id
        query = select(Type.id).where(Type.type == new_value_raw)
        new_id = await self.db.scalar(query)
        concept.type_id = new_id
        return old_value, new_id

    async def _update_category(self, concept: Concept, new_value_raw: str):
        old_value = concept.categorie_id
        query = select(Category.id).where(Category.nom == new_value_raw)
        new_id = await self.db.scalar(query)
        concept.categorie_id = new_id
        return old_value, new_id

    async def _update_mathematicien(self, concept: Concept, new_value_raw: str):
        old_value = concept.mathematicien_id
        query = select(Mathematicien.id).where(Mathematicien.nom == new_value_raw)
        new_id = await self.db.scalar(query)
        concept.mathematicien_id = new_id
        return old_value, new_id

    async def _update_relations(self, concept_id: int, new_value_raw: list):
        query = select(Relation).where(or_(Relation.concept_source == concept_id, Relation.concept_cible == concept_id))
        res = await self.db.execute(query)
        current_rels = res.scalars().all()

        old_value_list = [{
            "id": r.id, "concept_source": r.concept_source, "concept_cible": r.concept_cible,
            "type_relation": r.type_relation, "description": r.description
        } for r in current_rels]

        await self.db.execute(
            delete(Relation).where(or_(Relation.concept_source == concept_id, Relation.concept_cible == concept_id)))

        new_value_list = copy.deepcopy(new_value_raw)
        for r_data in new_value_list:
            src_id = r_data["concept_source"]["id"] if isinstance(r_data["concept_source"], dict) else r_data[
                "concept_source"]
            tgt_id = r_data["concept_cible"]["id"] if isinstance(r_data["concept_cible"], dict) else r_data[
                "concept_cible"]

            new_rel = Relation(
                concept_source=src_id,
                concept_cible=tgt_id,
                type_relation=r_data["type_relation"],
                description=r_data.get("description")
            )
            self.db.add(new_rel)

        return json.dumps(old_value_list), json.dumps(new_value_list)

    async def _update_sources(self, concept_id: int, new_value_raw: list):
        query = select(Source).join(Concept.sources).where(Concept.id == concept_id)
        res = await self.db.execute(query)
        current_sources = res.scalars().all()

        old_value_list = [
            {"id": s.id, "titre": s.titre, "auteur": s.auteur, "annee": s.annee, "url": s.url, "type": s.type}
            for s in current_sources
        ]

        for s_data in new_value_raw:
            source = await self.db.get(Source, s_data["id"])
            if source:
                source.titre = s_data["titre"]
                source.auteur = s_data["auteur"]
                source.annee = s_data["annee"]
                source.url = s_data["url"]
                source.type = s_data["type"]

        new_value_list = [
            {"id": s["id"], "titre": s["titre"], "auteur": s["auteur"], "annee": s["annee"], "url": s["url"],
             "type": s["type"]}
            for s in new_value_raw
        ]
        return json.dumps(old_value_list), json.dumps(new_value_list)

    async def _update_aliases(self, concept_id: int, new_value_raw: list):
        query = select(Alias).where(Alias.concept_id == concept_id)
        res = await self.db.execute(query)
        current_aliases = res.scalars().all()
        old_value = json.dumps([a.alias for a in current_aliases])

        await self.db.execute(delete(Alias).where(Alias.concept_id == concept_id))
        for alias_val in new_value_raw:
            self.db.add(Alias(concept_id=concept_id, alias=alias_val))

        return old_value, json.dumps(new_value_raw)

    async def _update_foreign_names(self, concept_id: int, new_value_raw: list):
        query = select(ForeignName).where(ForeignName.concept_id == concept_id)
        res = await self.db.execute(query)
        current_fn = res.scalars().all()
        old_value = json.dumps(
            [{"id": n.id, "concept_id": n.concept_id, "Nom_étranger": n.nom_etranger, "langue": n.langue} for n in
             current_fn])

        new_value = json.dumps(new_value_raw)
        return old_value, new_value
    async def get_editable_fields_options(self):
        types = (await self.db.execute(select(Type.type).distinct())).scalars().all()
        categories = (await self.db.execute(select(Category.nom).distinct())).scalars().all()
        mathematiciens = (await self.db.execute(select(Mathematicien.nom).distinct())).scalars().all()
        
        return {
            "mathematicien": list(mathematiciens),
            "categorie": list(categories),
            "type": list(types)
        }

    async def get_recent_history(self, limit: int = 50) -> list[dict]:
        query = (
            select(ConceptVersion)
            .options(joinedload(ConceptVersion.modifier), joinedload(ConceptVersion.concept))
            .order_by(desc(ConceptVersion.modified_at))
            .limit(limit)
        )
        result = await self.db.execute(query)
        versions = result.scalars().all()

        return [{
            "id": v.id,
            "concept_id": v.concept_id,
            "concept_nom": v.concept.nom if v.concept else None,
            "username": v.modifier.username if v.modifier else None,
            "modified_at": v.modified_at.isoformat() if v.modified_at else None,
            "field_modified": v.field_modified,
            "is_rollback": v.is_rollback
        } for v in versions]
