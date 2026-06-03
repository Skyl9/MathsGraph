# MathsGraph API (Backend)

Bienvenue dans le dépôt backend du projet **MathsGraph**. Il s'agit d'une API RESTful construite avec FastAPI, servant de moteur pour le projet graphique interactif.

## 🛠 Stack Technique

- **Framework :** [FastAPI](https://fastapi.tiangolo.com/) (Python 3.12+)
- **Base de Données :** PostgreSQL avec [SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/) (Mode Asynchrone `AsyncSession`)
- **Gestionnaire de paquets :** [`uv`](https://docs.astral.sh/uv/)
- **Validation des données :** Pydantic v2
- **Authentification :** JWT (JSON Web Tokens) & Bcrypt
- **Tests :** `pytest`, `pytest-asyncio`, `pytest-cov`

---

## 🏗 Architecture du Projet

L'architecture est découpée en couches distinctes pour séparer la logique métier de la présentation API :

```text
app/
├── api/             # Couche présentation (Endpoints, Routeurs FastAPI)
│   └── routes/      # Définition des routes (ex: concept_routes.py)
├── core/            # Configuration et sécurité (JWT, CORS, Settings)
├── db/              # Configuration DB, Session asynchrone et Modèles (SQLAlchemy)
├── schemas/         # Modèles Pydantic pour la validation des requêtes et réponses
├── services/        # Couche logique métier (Business Logic)
└── utils/           # Fonctions utilitaires diverses
tests/               # Tests automatisés (Pytest)
```

- **Routes (`app/api/routes`)** : Elles ne font que recevoir la requête, appeler le service correspondant et renvoyer la réponse formatée. Aucune logique métier complexe ne doit s'y trouver.
- **Services (`app/services`)** : Contient toute la logique métier. Le service manipule les requêtes SQL (via SQLAlchemy) et retourne des objets ou lève des exceptions métier.
- **Exceptions Métier** : Les erreurs doivent utiliser les exceptions personnalisées du dossier `core/exceptions.py` (ex: `NotFoundException`, `ForbiddenException`).

---

## 🚀 Installation & Lancement en local

### 1. Prérequis
- Python 3.12+
- `uv` installé (`pip install uv` ou via brew/curl)
- Une base de données PostgreSQL locale (ou Docker)
- Redis (facultatif)

### 2. Cloner et Installer les dépendances

```bash
# Dans le dossier backend
uv sync
```

### 3. Configuration de l'environnement
Créez un fichier `.env` à la racine en vous basant sur le fichier de configuration :

```dotenv title=dev
ENVIRONMENT=development
DB_USER=postgres
DB_PASSWORD=votre_mot_de_passe
DB_HOST=localhost
DB_PORT=5432
DB_NAME=app_db
DATABASE_URL=postgresql+psycopg://postgres:votre_mot_de_passe@localhost:5432/app_db

SECRET_KEY=une_clé_très_secrète_pour_jwt
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

NEW_FRONTEND_URL=http://localhost:8000
```

### 4. Lancer l'application
Démarrez le serveur de développement avec rechargement à chaud :

```bash
uv run fastapi dev app/main.py
# ou
uv run uvicorn app.main:app --reload
```
L'API sera disponible sur `http://127.0.0.1:8000`. 
📚 **La documentation Swagger interactive sera générée sur `http://127.0.0.1:8000/docs`.**

---

## 🧪 Tests et Qualité de code

Le projet utilise `pytest` avec une base de données de test jetable (isolation totale via `transaction.rollback()`).

**Exécuter toute la suite de tests :**
```bash
uv run pytest tests/
```

**Exécuter les tests avec le rapport de couverture :**
```bash
uv run pytest tests/ --cov=app --cov-report=term-missing
```

**Linter / Formatter :**
Le projet est formaté et vérifié via **Ruff**.
```bash
uv run ruff check .    # Vérifier le code
uv run ruff check --fix . # Corriger automatiquement
```

---

## 🔒 Sécurité et Bonnes Pratiques

- **Protection des Routes :** Toute modification de données (POST, PATCH, DELETE) requiert l'injection de la dépendance `Depends(get_current_user_payload)`.
- **Typage Strict :** Les données entrantes doivent toujours passer par un validateur **Pydantic** (`app/schemas/`). Jamais de manipulation de dictionnaires bruts non typés dans les routes.
- **SQL Injection :** Grâce à l'utilisation de `SQLAlchemy` (v2.0) avec les requêtes asynchrones ou les requêtes paramétrées, l'application est protégée contre les injections SQL classiques.
