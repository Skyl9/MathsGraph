from tests.constants import *


# Test de l'enregistrement d'utilisateur
def test_register(client, setup_test_db):
    user_data = {
        "email": TEST_USER_EMAIL,
        "password": TEST_PASSWORD,
        "username": TEST_USER_NAME
    }
    response = client.post("/register", json=user_data)

    assert response.status_code == 200, "Test réussi : L'utilisateur a bien pu s'inscrire !"
    assert response.json()["email"] == user_data["email"]
    assert response.json()["username"] == user_data["username"]

    # Vérifier que l'utilisateur est bien dans la base
    setup_test_db.execute("SELECT * FROM users WHERE email = %s;", (user_data["email"],))
    user_in_db = setup_test_db.fetchone()
    assert user_in_db is not None
    assert user_in_db["email"] == user_data["email"]


# Test de connexion
def test_login(client, setup_test_db, setup_test_user):
    login_data = {
        "username": TEST_USER_NAME,
        "password": TEST_PASSWORD  # Utilisez bien le même mot de passe que celui inséré !
    }
    response = client.post("/token", data=login_data)
    assert response.status_code == 200, "Test réussi : Connexion refusée pour un utilisateur invalide"
    # Vérifier que le token est bien retourné
    response_body = response.json()
    assert "access_token" in response_body
    assert response_body["token_type"] == "bearer"
