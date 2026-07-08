from app.core.redis_client import invalidate_graph_cache
import asyncio
import copy
import json
import logging
from typing import List, Any, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ConflictException
from app.db.models import Concept, Relation, Alias, ForeignName, ConceptVersion
from app.schemas import UpdateConceptDict
from app.schemas.concept import ConceptName, RollbackConcept, ConceptCreate
from app.schemas.history import History
from app.services.tags_service import TagsService
from app.repositories.concept_repository import ConceptRepository
from app.core.redis_client import redis_db
from sqlalchemy import select
from app.db.models import UserFavorite
from app.services.notification_service import NotificationService

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
        string = (
            "Titre : "
            + i["titre"]
            + " - Auteur : "
            + i["auteur"]
            + " - année "
            + str(i["annee"])
            + " - type : "
            + i["type"]
        )
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
        self.repo = ConceptRepository(db)

    async def get_concept_info(self, concept_id: int) -> dict[str | Any, None | dict[str, Any] | list[Any] | Any]:
        concept_obj = await self.repo.get_concept_info(concept_id)

        if not concept_obj:
            raise NotFoundException(detail="Concept non trouvé")

        # Fusion des relations entrantes et sortantes pour correspondre au format attendu
        all_relations = []
        for r in concept_obj.outgoing_relations:
            all_relations.append(
                {
                    "id": r.id,
                    "concept_source": {"id": r.concept_source, "nom": concept_obj.nom},
                    "concept_cible": {"id": r.concept_cible, "nom": r.target_concept.nom if r.target_concept else None},
                    "type_relation": r.type_relation,
                    "description": r.description,
                }
            )
        for r in concept_obj.incoming_relations:
            all_relations.append(
                {
                    "id": r.id,
                    "concept_source": {
                        "id": r.concept_source,
                        "nom": r.source_concept.nom if r.source_concept else None,
                    },
                    "concept_cible": {"id": r.concept_cible, "nom": concept_obj.nom},
                    "type_relation": r.type_relation,
                    "description": r.description,
                }
            )

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
            if concept_obj.mathematicien
            else None,
            "categorie": {"id": concept_obj.categorie_id, "category": concept_obj.category.nom}
            if concept_obj.category
            else None,
            "aliases": [a.alias for a in concept_obj.aliases],
            "sources": [
                {
                    "id": s.id,
                    "titre": s.titre,
                    "auteur": s.auteur,
                    "annee": s.annee,
                    "url": s.url,
                    "type": s.type,
                }
                for s in concept_obj.sources
            ],
            "relations": all_relations,
            "noms_etrangers": [
                {
                    "id": n.id,
                    "Nom_francais": concept_obj.nom,
                    "Nom_étranger": n.nom_etranger,
                    "langue": n.langue,
                }
                for n in concept_obj.foreign_names
            ],
            "tags": tags if tags else None,
        }

    async def rollback_history(self, concept_id: int, data: RollbackConcept) -> None:
        data_dict = data.model_dump() if isinstance(data, RollbackConcept) else data

        version = await self.repo.get_version_for_rollback(
            concept_id, data_dict["version_number"], data_dict["field_modified"]
        )

        if not version:
            raise NotFoundException(detail="Version non trouvée")

        note = version.note
        note = (
            f"Rollback from version number {data_dict['version_number']}"
            if note is None
            else f"{note} - Rollback from {data_dict['version_number']}"
        )

        value = await self.get_name_by_id(version.old_value, data_dict["field_modified"])

        update_data = UpdateConceptDict(
            field=version.field_modified, value=value, username=data_dict["username"], note=note
        )
        await self.updateConcept(concept_id, update_data, rollback=True)

    async def get_name_by_id(self, id_val, field_type):
        if not id_val:
            return id_val

        if field_type == "mathematicien":
            math = await self.repo.get_mathematicien_by_id(int(id_val))
            return math.nom if math else id_val
        if field_type == "categorie":
            cat = await self.repo.get_category_by_id(int(id_val))
            return cat.nom if cat else id_val
        if field_type == "type":
            t = await self.repo.get_type_by_id(int(id_val))
            return t.type if t else id_val

        if field_type in ["sources", "aliases", "noms_etrangers", "relations"]:
            try:
                return json.loads(id_val)
            except (TypeError, json.JSONDecodeError):
                return id_val
        return id_val

    async def _resolve_version_values(self, versions: Sequence[ConceptVersion]) -> list[dict]:
        math_ids = set()
        cat_ids = set()
        type_ids = set()
        concept_ids = set()

        for v in versions:
            if v.field_modified == "mathematicien":
                if v.old_value and v.old_value.isdigit():
                    math_ids.add(int(v.old_value))
                if v.new_value and v.new_value.isdigit():
                    math_ids.add(int(v.new_value))
            elif v.field_modified == "categorie":
                if v.old_value and v.old_value.isdigit():
                    cat_ids.add(int(v.old_value))
                if v.new_value and v.new_value.isdigit():
                    cat_ids.add(int(v.new_value))
            elif v.field_modified == "type":
                if v.old_value and v.old_value.isdigit():
                    type_ids.add(int(v.old_value))
                if v.new_value and v.new_value.isdigit():
                    type_ids.add(int(v.new_value))
            elif v.field_modified == "relations":
                try:
                    old_rels = json.loads(v.old_value) if v.old_value else []
                    new_rels = json.loads(v.new_value) if v.new_value else []
                    for i in old_rels + new_rels:
                        if isinstance(i.get("concept_source"), (int, str)) and str(i["concept_source"]).isdigit():
                            concept_ids.add(int(i["concept_source"]))
                        if isinstance(i.get("concept_cible"), (int, str)) and str(i["concept_cible"]).isdigit():
                            concept_ids.add(int(i["concept_cible"]))
                except (json.JSONDecodeError, TypeError):
                    pass

        # Prefetching
        async def fetch_if(ids, fetch_func):
            return await fetch_func(ids) if ids else {}

        math_dict, cat_dict, type_dict, concept_dict = await asyncio.gather(
            fetch_if(math_ids, self.repo.get_math_dict),
            fetch_if(cat_ids, self.repo.get_cat_dict),
            fetch_if(type_ids, self.repo.get_type_dict),
            fetch_if(concept_ids, self.repo.get_concept_dict),
        )

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
                    v_dict["old_value"] = math_dict.get(int(v.old_value), v.old_value)
                if v.new_value and v.new_value.isdigit():
                    v_dict["new_value"] = math_dict.get(int(v.new_value), v.new_value)

            elif v.field_modified == "categorie":
                if v.old_value and v.old_value.isdigit():
                    v_dict["old_value"] = cat_dict.get(int(v.old_value), v.old_value)
                if v.new_value and v.new_value.isdigit():
                    v_dict["new_value"] = cat_dict.get(int(v.new_value), v.new_value)

            elif v.field_modified == "type":
                if v.old_value and v.old_value.isdigit():
                    v_dict["old_value"] = type_dict.get(int(v.old_value), v.old_value)
                if v.new_value and v.new_value.isdigit():
                    v_dict["new_value"] = type_dict.get(int(v.new_value), v.new_value)

            elif v.field_modified == "sources":
                try:
                    v_dict["old_value"] = format_source(json.loads(v.old_value)) if v.old_value else ""
                    v_dict["new_value"] = format_source(json.loads(v.new_value)) if v.new_value else ""
                except (json.JSONDecodeError, TypeError):
                    pass

            elif v.field_modified == "aliases":
                try:
                    v_dict["old_value"] = format_alias(json.loads(v.old_value)) if v.old_value else ""
                    v_dict["new_value"] = format_alias(json.loads(v.new_value)) if v.new_value else ""
                except (json.JSONDecodeError, TypeError):
                    pass

            elif v.field_modified == "noms_etrangers":
                try:
                    v_dict["old_value"] = format_foreign_name(json.loads(v.old_value)) if v.old_value else ""
                    v_dict["new_value"] = format_foreign_name(json.loads(v.new_value)) if v.new_value else ""
                except (json.JSONDecodeError, TypeError):
                    pass

            elif v.field_modified == "relations":
                try:
                    old_rels = json.loads(v.old_value) if v.old_value else []
                    new_rels = json.loads(v.new_value) if v.new_value else []

                    for i in old_rels:
                        src_id = int(i["concept_source"]) if str(i["concept_source"]).isdigit() else None
                        tgt_id = int(i["concept_cible"]) if str(i["concept_cible"]).isdigit() else None
                        i["concept_source"] = (
                            concept_dict.get(src_id, str(i["concept_source"])) if src_id else str(i["concept_source"])
                        )
                        i["concept_cible"] = (
                            concept_dict.get(tgt_id, str(i["concept_cible"])) if tgt_id else str(i["concept_cible"])
                        )
                    for j in new_rels:
                        src_id = int(j["concept_source"]) if str(j["concept_source"]).isdigit() else None
                        tgt_id = int(j["concept_cible"]) if str(j["concept_cible"]).isdigit() else None
                        j["concept_source"] = (
                            concept_dict.get(src_id, str(j["concept_source"])) if src_id else str(j["concept_source"])
                        )
                        j["concept_cible"] = (
                            concept_dict.get(tgt_id, str(j["concept_cible"])) if tgt_id else str(j["concept_cible"])
                        )

                    v_dict["old_value"] = format_relation(old_rels)
                    v_dict["new_value"] = format_relation(new_rels)
                except (json.JSONDecodeError, TypeError):
                    pass

            res_versions.append(v_dict)

        return res_versions

    async def get_concept_versions(self, concept_id: int) -> List[History]:
        versions = await self.repo.get_concept_versions(concept_id)

        res_versions_dict = await self._resolve_version_values(versions)

        res_versions = [
            History(
                id=v_dict["id"],  # type: ignore
                concept_id=v_dict["concept_id"],  # type: ignore
                modified_by=v_dict["modified_by"],  # type: ignore
                modified_at=v_dict["modified_at"],  # type: ignore
                field_modified=v_dict["field_modified"],  # type: ignore
                old_value=v_dict["old_value"],
                new_value=v_dict["new_value"],
                version_number=v_dict["version_number"],  # type: ignore
                global_version=v_dict["global_version"],  # type: ignore
                is_rollback=v_dict["is_rollback"],  # type: ignore
                note=v_dict["note"],  # type: ignore
            )
            for v_dict in res_versions_dict
        ]
        return res_versions

    async def add_concept_version(
        self,
        username: str,
        concept_id: int,
        field_modified: str,
        old_version,
        new_version,
        note: str | None = None,
        rollback: bool = False,
    ):
        if str(old_version) == str(new_version):
            return

        # Obtenir l'ID utilisateur
        user_id = await self.repo.get_user_id_by_username(username)
        if not user_id:
            raise NotFoundException(detail=f"Utilisateur {username} introuvable")

        # Calculer le numéro de version
        version_number = await self.repo.get_next_version_number(concept_id, field_modified)

        # Calculer le numéro de version globale
        global_version = await self.repo.get_next_global_version(concept_id)

        new_v = ConceptVersion(
            modified_by=user_id,
            concept_id=concept_id,
            field_modified=field_modified,
            old_value=str(old_version) if old_version is not None else None,
            new_value=str(new_version) if new_version is not None else None,
            note=note,
            global_version=global_version,
            version_number=version_number,
            is_rollback=rollback,
        )
        await self.repo.add(new_v)
        await self.repo.flush()

    async def get_all_concepts_name(self) -> list[ConceptName]:
        rows = await self.repo.get_all_concepts_name()
        return [ConceptName(id=row.id, nom=row.nom) for row in rows]

    async def updateConcept(self, concept_id: int, data: UpdateConceptDict, rollback: bool = False) -> None:
        data_dict = data.model_dump() if isinstance(data, UpdateConceptDict) else data

        concept = await self.repo.get_concept_by_id(concept_id)
        if not concept:
            raise NotFoundException(detail="Concept non trouvé")

        field_name = data_dict["field"]
        new_value_raw = data_dict["value"]

        # Routage propre vers les méthodes spécialisées
        if field_name in ["nom", "enonce", "demonstration", "verification"]:
            old_value = getattr(concept, field_name)
            setattr(concept, field_name, new_value_raw)
            new_value = new_value_raw

            # Mettre à jour l'embedding si nom ou enonce change
            if field_name in ["nom", "enonce"]:
                from app.services.embedding_service import embedding_service

                text_to_embed = f"{concept.nom}. {concept.enonce}"
                concept.embedding = embedding_service.get_embedding(text_to_embed)

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
            note=data_dict.get("note"),
        )
        await self.repo.commit()

        # Invalidation du cache Redis global du graphe
        try:
            await invalidate_graph_cache()
            await redis_db.delete(f"mathgraph:concept:{concept_id}")
        except Exception as e:
            logger.warning(f"Erreur lors de l'invalidation du cache Redis: {e}")

        # Notifications pour les abonnés
        try:
            query = select(UserFavorite.user_id).where(
                UserFavorite.concept_id == concept_id, UserFavorite.notify_on_change.is_(True)
            )
            result = await self.db.execute(query)
            user_ids = result.scalars().all()
            if user_ids:
                message = f"Le concept a été modifié ({field_name}) par {data_dict['username']}."
                notif_service = NotificationService(self.db)
                for u_id in user_ids:
                    await notif_service.create_notification(u_id, message, concept_id)
        except Exception as e:
            logger.warning(f"Erreur lors de la création des notifications: {e}")

    async def _update_type(self, concept: Concept, new_value_raw: str):
        old_value = concept.type_id
        new_id = await self.repo.get_type_id_by_name(new_value_raw)
        if new_id is not None:
            concept.type_id = new_id
        return old_value, new_id

    async def _update_category(self, concept: Concept, new_value_raw: str):
        old_value = concept.categorie_id
        new_id = await self.repo.get_category_id_by_name(new_value_raw)
        concept.categorie_id = new_id
        return old_value, new_id

    async def _update_mathematicien(self, concept: Concept, new_value_raw: str):
        old_value = concept.mathematicien_id
        new_id = await self.repo.get_mathematicien_id_by_name(new_value_raw)
        concept.mathematicien_id = new_id
        return old_value, new_id

    async def _update_relations(self, concept_id: int, new_value_raw: list):
        current_rels = await self.repo.get_concept_relations(concept_id)

        old_value_list = [
            {
                "id": r.id,
                "concept_source": r.concept_source,
                "concept_cible": r.concept_cible,
                "type_relation": r.type_relation,
                "description": r.description,
            }
            for r in current_rels
        ]

        await self.repo.delete_concept_relations(concept_id)

        new_value_list = copy.deepcopy(new_value_raw)
        for r_data in new_value_list:
            src_id = (
                r_data["concept_source"]["id"]
                if isinstance(r_data["concept_source"], dict)
                else r_data["concept_source"]
            )
            tgt_id = (
                r_data["concept_cible"]["id"] if isinstance(r_data["concept_cible"], dict) else r_data["concept_cible"]
            )

            new_rel = Relation(
                concept_source=src_id,
                concept_cible=tgt_id,
                type_relation=r_data["type_relation"],
                description=r_data.get("description"),
            )
            await self.repo.add(new_rel)

        return json.dumps(old_value_list), json.dumps(new_value_list)

    async def _update_sources(self, concept_id: int, new_value_raw: list):
        current_sources = await self.repo.get_concept_sources(concept_id)

        old_value_list = [
            {"id": s.id, "titre": s.titre, "auteur": s.auteur, "annee": s.annee, "url": s.url, "type": s.type}
            for s in current_sources
        ]

        for s_data in new_value_raw:
            source = await self.repo.get_source_by_id(s_data["id"])
            if source:
                source.titre = s_data["titre"]
                source.auteur = s_data["auteur"]
                source.annee = s_data["annee"]
                source.url = s_data["url"]
                source.type = s_data["type"]

        new_value_list = [
            {
                "id": s["id"],
                "titre": s["titre"],
                "auteur": s["auteur"],
                "annee": s["annee"],
                "url": s["url"],
                "type": s["type"],
            }
            for s in new_value_raw
        ]
        return json.dumps(old_value_list), json.dumps(new_value_list)

    async def _update_aliases(self, concept_id: int, new_value_raw: list):
        current_aliases = await self.repo.get_concept_aliases(concept_id)
        old_value = json.dumps([a.alias for a in current_aliases])

        await self.repo.delete_concept_aliases(concept_id)
        for alias_val in new_value_raw:
            await self.repo.add(Alias(concept_id=concept_id, alias=alias_val))

        return old_value, json.dumps(new_value_raw)

    async def _update_foreign_names(self, concept_id: int, new_value_raw: list):
        current_fn = await self.repo.get_concept_foreign_names(concept_id)
        old_value = json.dumps(
            [
                {"id": n.id, "concept_id": n.concept_id, "Nom_étranger": n.nom_etranger, "langue": n.langue}
                for n in current_fn
            ]
        )

        # Supprimer les anciens noms étrangers et insérer les nouveaux
        await self.repo.delete_concept_foreign_names(concept_id)
        for fn_data in new_value_raw:
            await self.repo.add(
                ForeignName(
                    concept_id=concept_id,
                    nom_etranger=fn_data.get("nom_etranger") or fn_data.get("Nom_étranger", ""),
                    langue=fn_data.get("langue", ""),
                )
            )

        new_value = json.dumps(new_value_raw)
        return old_value, new_value

    async def get_editable_fields_options(self):
        return await self.repo.get_editable_fields_options()

    async def get_recent_history(self, limit: int = 50) -> list[dict]:
        versions = await self.repo.get_recent_history(limit)

        res_versions_dict = await self._resolve_version_values(versions)

        return [
            {
                "id": v.id,
                "concept_id": v.concept_id,
                "concept_nom": v.concept.nom if v.concept else None,
                "username": v.modifier.username if v.modifier else None,
                "modified_at": v.modified_at.isoformat() if v.modified_at else None,
                "field_modified": v.field_modified,
                "is_rollback": v.is_rollback,
                "old_value": v_dict["old_value"],
                "new_value": v_dict["new_value"],
            }
            for v, v_dict in zip(versions, res_versions_dict)
        ]

    async def create_concept(self, data: ConceptCreate, username: str) -> dict:
        data_dict = data.model_dump()

        # Vérifier que le nom n'existe pas déjà
        concept_id = await self.repo.get_concept_id_by_name(data_dict["nom"])
        if concept_id:
            raise ConflictException("Un concept avec ce nom existe déjà.")

        # Résolution des types par défaut si non fournis
        type_val = data_dict.get("type")
        type_id = await self.repo.get_type_id_by_name(str(type_val)) if type_val else None
        if not type_id:
            type_id = await self.repo.get_type_id_by_name("théorème")

        # Générer l'embedding
        from app.services.embedding_service import embedding_service

        text_to_embed = f"{data_dict['nom']}. {data_dict['enonce']}"
        initial_embedding = embedding_service.get_embedding(text_to_embed)

        new_concept = Concept(
            nom=data_dict["nom"],
            enonce=data_dict["enonce"],
            demonstration=data_dict.get("demonstration"),
            type_id=type_id,
            categorie_id=data_dict.get("categorie_id"),
            mathematicien_id=data_dict.get("mathematicien_id"),
            verification=False,
            embedding=initial_embedding,
        )

        await self.repo.add(new_concept)
        await self.repo.flush()  # Pour récupérer l'ID généré

        # Historisation de la création
        await self.add_concept_version(
            username=username,
            concept_id=new_concept.id,
            field_modified="creation",
            old_version=None,
            new_version=data_dict["nom"],
            note="Création initiale",
        )
        await self.repo.commit()

        # Invalidation du cache Redis global du graphe
        try:
            await invalidate_graph_cache()
        except Exception as e:
            logger.warning(f"Erreur lors de l'invalidation du cache Redis: {e}")

        return {"id": new_concept.id, "nom": new_concept.nom}

    async def get_wanted_concepts(self) -> list[dict]:
        concepts = await self.repo.get_wanted_concepts()
        result = []
        for c in concepts:
            missing = []
            if not c.demonstration or c.demonstration == "<p><br></p>":
                missing.append("demonstration")
            if not c.sources:
                missing.append("sources")

            result.append(
                {
                    "id": c.id,
                    "nom": c.nom,
                    "categorie": c.category.nom if c.category else None,
                    "missing_fields": missing,
                }
            )
        return result
