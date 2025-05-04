def test_get_concept(client):
    response = client.get("/concepts")
    assert response.status_code == 200


def test_get_concept_by_id(client, setup_test_db,setup_test_concept):
    id = setup_test_concept
    response = client.get(f"/getNode/{id}")
    assert response.status_code == 200, "Test réussi : L'utilisateur a bien pu récupérer le noeud 1 !"

def test_concept_admin(client, setup_test_db,setup_test_concept):
    response = client.get("/getAlldatabaseInfo")
    print(response.read())
    assert response.status_code == 200