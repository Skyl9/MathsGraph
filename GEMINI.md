# 🤖 Context Assistant - Backend (FastAPI)

Ce fichier sert de guide contextuel pour toute IA ou développeur travaillant sur l'API de MathGraph.

## 🛠 Stack Technique
- **Framework :** FastAPI (Python 3.12).
- **Base de données :** PostgreSQL.
- **Driver DB :** SQLalchemy.
- **Validation :** Pydantic v2.
- **Auth :** JWT (OAuth2PasswordBearer) + Bcrypt pour le hashage.

## 🏗 Architecture & Patterns
- **Service Layer :** Toute la logique métier réside dans `app/services/`. Les routes (`app/api/routes/`) ne servent qu'à valider les entrées/sorties.
- **Gestion des erreurs :** Utiliser les exceptions personnalisées de `app/core/exceptions.py`.
- **Versioning :** Le système de rollback des concepts s'appuie sur la table `concept_versions`. Chaque modification de champ sensible doit créer une entrée via `add_concept_version`.

## 🔒 Règles de Sécurité
- **Access Control :** Toutes les routes POST, PATCH et DELETE doivent utiliser la dépendance `Depends(get_current_user)` ou `get_current_admin_payload`.
- **SQL Injection :** Utiliser les requêtes préparées par SQLAlchemy et éviter d'insérer des valeurs directement dans les chaînes de texte (`f-strings`) pour interroger la base de données.
- **CORS :** Configurer `BACKEND_CORS_ORIGINS` dans le `.env` pour restreindre les accès.

## 🧪 Tests
- Le projet utilise `pytest` avec `pytest-asyncio`.
- **Isolation :** La fixture `transaction` dans `conftest.py` assure un `ROLLBACK` automatique après chaque test. Ne jamais tester sur une DB de production.