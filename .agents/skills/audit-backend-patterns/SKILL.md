---
name: audit-backend-patterns
description: Analyse l'architecture backend FastAPI pour détecter les God Services, la logique mal placée, les incohérences de nommage et les validations Pydantic incomplètes.
---
# Instructions

Tu es un **Architecte Backend Senior** expert en design patterns Python et en Clean Architecture. Ton rôle est d'auditer la qualité architecturale du backend MathGraph (FastAPI + SQLAlchemy + Pydantic v2) pour garantir la maintenabilité, la testabilité et le respect des principes SOLID.

Suis strictement les étapes suivantes de manière séquentielle :

## 1. Acquisition de Contexte

1. Lis le fichier `GEMINI.md` du backend : `/Users/tristanrigaud-humbert/PycharmProjects/fastApiProject/GEMINI.md`. Note en particulier :
   - Le pattern **Service Layer** : toute logique métier dans `app/services/`, les routes ne font que valider les E/S.
   - La gestion des erreurs via les exceptions personnalisées de `app/core/exceptions.py`.
   - Le système de versioning des concepts via `concept_versions`.
2. Lis le fichier d'exceptions personnalisées `app/core/exceptions.py` pour connaître les exceptions disponibles : `BadRequestException`, `AuthenticationException`, `ForbiddenException`, `NotFoundException`, `ConflictException`, `InternalServerError`.
3. Prends note de la structure du projet :
   - **Routes** : `app/api/routes/` (15 fichiers de routes)
   - **Services** : `app/services/` (16 services)
   - **Repositories** : `app/repositories/` (16 repositories)
   - **Schemas** : `app/schemas/` (24 fichiers de schémas Pydantic)

## 2. Détection des God Services

Scanne le dossier `app/services/` et mesure pour chaque fichier :
- **Le nombre de lignes.**
- **La taille en octets.**
- **Le nombre de méthodes publiques.**

Signale tout service qui dépasse **au moins un** des seuils suivants :
- **> 200 lignes**
- **> 8 Ko (8192 octets)**
- **> 10 méthodes publiques**

Pour chaque God Service identifié :
- **Analyse** les responsabilités mélangées (ex: le service gère à la fois du CRUD simple, de la logique métier complexe, et de la transformation de données).
- **Propose** un plan de découpage en services spécialisés (ex: `ConceptCrudService`, `ConceptVersioningService`, `ConceptValidationService`).
- **Estime** l'effort de refactorisation (⚡ Facile / 🔧 Moyen / 🏗️ Complexe).

## 3. Logique métier résiduelle dans les routes

Scanne tous les fichiers de `app/api/routes/` et vérifie que chaque fonction de route respecte le pattern Service Layer :

### 3.1 Logique métier dans les routes
- **Identifie** toute logique métier qui devrait résider dans un service :
  - Conditions `if/else` sur des données métier (pas de la validation d'entrée).
  - Boucles de transformation de données.
  - Appels directs au repository depuis la route (sans passer par le service).
  - Calculs ou agrégations de données.
- **Tolère** dans les routes : la validation d'entrées (Pydantic), l'extraction des dépendances (`Depends`), la construction de la réponse HTTP, et le commit/rollback de la session DB.

### 3.2 Responsabilités de la route
- **Vérifie** que chaque route suit ce schéma minimal :
  1. Extraire les dépendances (DB session, current_user).
  2. Appeler le service.
  3. Commit si nécessaire.
  4. Retourner la réponse.
- **Signale** les routes qui font plus de 15 lignes de corps (hors signature et décorateurs), car c'est un indicateur de logique mal placée.

## 4. Cohérence du nommage

### 4.1 Nommage des fonctions de service
- **Vérifie** la cohérence des conventions de nommage entre les services :
  - CRUD standard : `create_*`, `get_*`, `update_*`, `delete_*`, `get_all_*`, `get_*_by_id`, `get_*_by_name`.
  - Logique métier : verbes descriptifs (ex: `rollback_concept`, `recalculate_layout`).
- **Signale** les incohérences (ex: `updateConcept` en camelCase vs `update_type` en snake_case, `get_one_type_E` avec un suffixe ambigu `_E`).

### 4.2 Nommage des fonctions de route
- **Vérifie** que les noms des fonctions de route sont descriptifs et cohérents.
- **Signale** les noms ambigus ou incohérents (ex: `mathematicienName` au lieu de `get_mathematicien_by_name`).

### 4.3 Nommage des fichiers
- **Vérifie** la cohérence entre le nom des fichiers routes, services et repositories :
  - Ex: `categorie_routes.py` vs `category_service.py` vs `category_repository.py` → incohérence FR/EN dans le nom.

## 5. Validation Pydantic

Scanne les fichiers de `app/schemas/` et vérifie :

### 5.1 Champs sans validation
- **Identifie** les champs qui acceptent des valeurs sans aucune contrainte alors qu'une validation serait pertinente :
  - `str` sans `min_length`, `max_length`, ou `pattern` (regex).
  - `int` sans `ge`, `le`, `gt`, `lt`.
  - Champs email sans `EmailStr`.
  - Champs URL sans `HttpUrl`.
- **Propose** les validators ou les `Field(...)` appropriés pour chaque cas.

### 5.2 Schémas sans `model_config`
- **Vérifie** si les schémas de réponse (ceux retournés par les routes) possèdent `model_config = ConfigDict(from_attributes=True)` pour la sérialisation depuis les modèles SQLAlchemy.
- **Vérifie** la présence d'exemples (`json_schema_extra` / `model_config`) pour la documentation Swagger.

### 5.3 Séparation Create / Update / Response
- **Vérifie** que chaque entité possède des schémas distincts pour la création (input), la mise à jour (input partiel), et la réponse (output), plutôt qu'un schéma unique utilisé partout.

## 6. Dépendances circulaires et couplage

### 6.1 Imports croisés entre services
- **Scanne** les imports de chaque fichier de service pour détecter les dépendances circulaires :
  - Service A importe Service B ET Service B importe Service A.
- **Propose** des solutions : extraction de la logique partagée dans un service utilitaire, inversion de dépendance, ou événements (pub/sub).

### 6.2 Couplage service ↔ repository
- **Vérifie** que chaque service utilise son propre repository principal et ne manipule pas directement les repositories d'autres entités (sauf pour des jointures légitimes).
- **Signale** les services qui instancient directement un modèle SQLAlchemy au lieu de passer par un repository.

## 7. Usage des exceptions personnalisées

- **Scanne** tous les fichiers de `app/services/` et `app/api/routes/` pour vérifier que :
  - Les exceptions levées proviennent de `app/core/exceptions.py` (et non de `HTTPException` brut ou de `raise Exception(...)`).
  - Chaque service qui accède à une ressource par ID lève `NotFoundException` si la ressource n'existe pas.
  - Les validations métier utilisent `BadRequestException` (et non un `return` silencieux ou un `ValueError`).
  - Les contrôles d'accès utilisent `ForbiddenException`.

## 8. Génération du Rapport

1. Inspecte le dossier `artifact/Architecture/` du backend (`/Users/tristanrigaud-humbert/PycharmProjects/fastApiProject/artifact/Architecture/`). S'il n'existe pas, crée-le. Détermine le prochain numéro logique pour le fichier.
2. Crée le fichier Markdown numéroté avec la structure suivante :
   - **Résumé exécutif** : Score d'architecture global (ex: 65/100), nombre de violations par catégorie, et top 3 des refactorisations prioritaires.
   - **Section God Services** : Détail de chaque service volumineux avec plan de découpage.
   - **Section Logique mal placée** : Liste des routes avec de la logique métier résiduelle.
   - **Section Nommage** : Tableau des incohérences avec les renommages proposés.
   - **Section Validation Pydantic** : Liste des champs sans validation avec les correctifs.
   - **Section Dépendances** : Graphe de dépendances et cycles détectés.
   - **Section Exceptions** : Liste des usages incorrects.
   - **Tableau récapitulatif** : Colonnes : Catégorie, Fichier, Sévérité, Description, Action proposée.
3. Réponds dans le chat avec un bref résumé des résultats et un lien Markdown cliquable vers le rapport généré.
