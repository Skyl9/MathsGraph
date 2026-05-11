import pytest
from httpx import AsyncClient

from tests.utils import create_headers_token


@pytest.mark.asyncio
async def test_get_concept_success(async_client: AsyncClient, setup_full_test_concept):
    """
    Teste la récupération réussie d'un concept avec toutes ses informations associées.
    """
    concept_id = setup_full_test_concept["concept"]["id"]
    response = await async_client.get(f"/concept/{concept_id}")

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert "data" in data
    concept = data["data"]

    assert concept["id"] == concept_id
    assert concept["nom"] == setup_full_test_concept["concept"]["nom"]
    assert concept["type"] == setup_full_test_concept["type"]  # 'type' field from Type table
    assert concept["enonce"] == setup_full_test_concept["concept"]["enonce"]
    assert "aliases" in concept
    assert sorted(concept["aliases"]) == sorted(setup_full_test_concept["aliases"])
    assert "sources" in concept
    assert len(concept["sources"]) >= 1
    assert any(s["titre"] == setup_full_test_concept["source"]["titre"] for s in concept["sources"])
    assert "noms_etrangers" in concept
    assert len(concept["noms_etrangers"]) >= 1
    assert any(
        n["Nom_étranger"] == setup_full_test_concept["foreign_name"]["Nom_étranger"] for n in concept["noms_etrangers"])
    assert "relations" in concept
    assert len(concept["relations"]) >= 1
    assert any(
        r["concept_source"]["id"] == concept_id or r["concept_cible"]["id"] == concept_id for r in concept["relations"])
    assert concept["mathematicien"]["mathematicien"] == setup_full_test_concept["mathematicien"]
    assert concept["categorie"]["category"] == setup_full_test_concept["categorie"]


@pytest.mark.asyncio
async def test_get_concept_not_found(async_client: AsyncClient):
    """
    Teste la récupération d'un concept inexistant.
    """
    response = await async_client.get("/concept/99999")
    assert response.status_code == 404  # Si NotFoundException est convertie en InternalServerError
    data = response.json()
    assert data["success"] is False
    assert "Concept non trouvé" in data["error"]


@pytest.mark.asyncio
async def test_get_all_concept_name_success(async_client: AsyncClient, setup_test_concept, setup_full_test_concept):
    """
    Teste la récupération de tous les noms de concepts.
    """
    response = await async_client.get("/getAllConceptName")
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert "data" in data
    concept_names = data["data"]

    assert isinstance(concept_names, list)
    assert len(concept_names) >= 2  # Au moins le concept de base et le full test concept

    # Vérifier que les noms de concepts connus sont présents
    known_names = [setup_test_concept["nom"], setup_full_test_concept["concept"]["nom"]]
    retrieved_names = [c["nom"] for c in concept_names]
    for name in known_names:
        assert name in retrieved_names


@pytest.mark.asyncio
async def test_get_editable_fields_options_success(async_client: AsyncClient, setup_test_type, setup_test_categorie,
                                                   setup_test_mathematicien):
    """
    Teste la récupération des options pour les champs éditables.
    """
    response = await async_client.get("/getEditableFieldsOptions")
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert "data" in data
    options = data["data"]

    assert "mathematicien" in options
    assert isinstance(options["mathematicien"], list)
    assert setup_test_mathematicien["nom"] in options["mathematicien"]

    assert "categorie" in options
    assert isinstance(options["categorie"], list)
    assert setup_test_categorie["nom"] in options["categorie"]

    assert "type" in options
    assert isinstance(options["type"], list)
    assert setup_test_type["type"] in options["type"]


@pytest.mark.asyncio
async def test_update_concept_simple_field_success(async_client: AsyncClient, setup_full_test_concept, setup_test_user,setup_user_token_admin):
    """
    Teste la mise à jour réussie d'un champ simple (e.g., 'nom').
    """

    headers = create_headers_token(setup_user_token_admin)

    concept_id = setup_full_test_concept["concept"]["id"]
    updated_name = "New Updated Concept Name"
    update_data = {
        "field": "nom",
        "value": updated_name,
        "username": setup_test_user["username"],
        "note": "Test simple field update"
    }

    get_response = await async_client.get(f"/concept/{concept_id}")
    get_data = get_response.json()

    response = await async_client.patch(f"/update/{concept_id}", json=update_data, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"] is None

    # Vérifier que le nom a bien été mis à jour en le récupérant
    get_response = await async_client.get(f"/concept/{concept_id}")
    get_data = get_response.json()

    assert get_data["success"] is True
    assert get_data["data"]["nom"] == updated_name

    # Vérifier qu'une entrée d'historique a été créée
    history_response = await async_client.get(f"/concept/history/{concept_id}")
    print(history_response)
    print(history_response.json())
    history_data = history_response.json()
    assert history_data["success"] is True
    assert len(history_data["data"]) >= 1
    history_entry = next((h for h in history_data["data"] if h["field_modified"] == "nom"), None)
    assert history_entry is not None
    assert history_entry["new_value"] == updated_name
    assert history_entry["note"] == update_data["note"]


@pytest.mark.asyncio
async def test_update_concept_invalid_id(async_client: AsyncClient, setup_test_user,setup_user_token_admin):
    """
    Teste la mise à jour d'un concept avec un ID inexistant.
    """
    headers = create_headers_token(setup_user_token_admin)

    update_data = {
        "field": "nom",
        "value": "Invalid Concept",
        "note": "Test invalid ID",
        "username": setup_test_user["username"]
    }
    response = await async_client.patch("/update/99999", json=update_data,headers=headers)
    assert response.status_code == 404  # Si NotFoundException est convertie en InternalServerError
    data = response.json()
    assert data["success"] is False
    assert "ID not found" in data["error"]


@pytest.mark.asyncio
async def test_rollback_concept_success(async_client: AsyncClient, setup_full_test_concept, setup_test_user,setup_user_token_admin):
    """
    Teste la restauration d'une version précédente d'un concept.
    Ceci dépend de l'historique créé par test_update_concept_simple_field_success.
    """

    headers = create_headers_token(setup_user_token_admin)
    concept_id = setup_full_test_concept["concept"]["id"]
    original_name = setup_full_test_concept["concept"]["nom"]  # Nom initial du concept de la fixture

    # Étape 1: Mettre à jour le concept pour créer une entrée d'historique
    first_update_data = {
        "field": "nom",
        "value": "Temp Name for Rollback",
        "note": "Temporary name",
        "username": setup_test_user["username"]
    }
    await async_client.patch(f"/update/{concept_id}", json=first_update_data, headers=headers)

    # Étape 2: Obtenir l'historique pour trouver la version originale (avant la mise à jour)
    history_response = await async_client.get(f"/concept/history/{concept_id}")
    history_data = history_response.json()
    assert history_data["success"] is True
    assert len(history_data["data"]) >= 1

    # Trouver l'entrée d'historique qui représente le nom original du concept
    # C'est l'entrée la plus ancienne pour le champ 'nom' avant la mise à jour temporaire.
    # Ou la version 1 si c'est la première modification du nom.
    history_entries_for_nom = [h for h in history_data["data"] if h["field_modified"] == "nom"]

    # On prend la dernière entrée (la plus ancienne version) comme cible de rollback
    # C'est un peu simpliste, une approche plus robuste serait de se baser sur un numéro de version spécifique
    # ou une note pour identifier la version exacte à laquelle revenir.
    # Pour ce test, nous allons simuler un rollback à la première version du nom.
    target_history_entry = None
    if len(history_entries_for_nom) > 0:
        # Trouver l'entrée correspondant au nom original de la fixture
        for entry in history_entries_for_nom:
            if entry["old_value"] == original_name:  # Si l'old_value de cette version correspond à notre original
                target_history_entry = entry
                break
        if not target_history_entry:  # Si l'original n'a pas été trouvé, prendre la plus ancienne version 'nom'
            target_history_entry = history_entries_for_nom[-1]  # Assuming oldest is last

    assert target_history_entry is not None, "Impossible de trouver une entrée d'historique pour le rollback."

    rollback_data = {
        "version_number": target_history_entry["version_number"],
        "field_modified": "nom",  # Le champ que nous voulons restaurer
        "username": setup_test_user["username"]
    }

    response = await async_client.patch(f"/concept/rollback/{concept_id}", json=rollback_data,headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"] is None

    # Vérifier que le concept a été restauré à son nom original
    get_response = await async_client.get(f"/concept/{concept_id}")
    get_data = get_response.json()
    assert get_data["success"] is True
    assert get_data["data"]["nom"] == original_name


@pytest.mark.asyncio
async def test_get_concept_history_success(async_client: AsyncClient, setup_full_test_concept, setup_test_user,setup_user_token_admin):
    """
    Teste la récupération de l'historique des versions d'un concept.
    """
    headers = create_headers_token(setup_user_token_admin)
    concept_id = setup_full_test_concept["concept"]["id"]

    # Créer quelques entrées d'historique via des mises à jour API
    await async_client.patch(f"/update/{concept_id}", json={
        "field": "nom", "value": "Name Change 1", "note": "Note 1", "username": setup_test_user["username"]
    },headers=headers)
    await async_client.patch(f"/update/{concept_id}", json={
        "field": "enonce", "value": "Enonce Change 1", "note": "Note 2", "username": setup_test_user["username"]
    },headers=headers)
    await async_client.patch(f"/update/{concept_id}", json={
        "field": "nom", "value": "Name Change 2", "note": "Note 3", "username": setup_test_user["username"]
    },headers=headers)

    response = await async_client.get(f"/concept/history/{concept_id}",headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert "data" in data
    history_list = data["data"]

    assert isinstance(history_list, list)
    assert len(history_list) >= 3  # Au moins les 3 mises à jour effectuées

    # Vérifier la présence des entrées d'historique créées
    assert any(h["field_modified"] == "nom" and h["new_value"] == "Name Change 2" for h in history_list)
    assert any(h["field_modified"] == "enonce" and h["new_value"] == "Enonce Change 1" for h in history_list)
    assert any(h["note"] == "Note 1" for h in history_list)
    assert all(h["modified_by"] is not None for h in history_list)  # Vérifier que l'utilisateur est bien lié

