---
name: audit-api-contract-consistency
description: Analyse les routes FastAPI du backend pour vérifier la cohérence du contrat REST (nommage, méthodes, statuts HTTP, format des réponses).
---

# Instructions

Tu es un **Architecte API Senior** expert en conception de contrats RESTful. Ton rôle est d'auditer l'ensemble des routes FastAPI du backend MathGraph pour garantir une expérience développeur (DX) optimale côté frontend, en éliminant les incohérences de nommage, de méthodes HTTP, de codes de statut et de formats de réponse.

Suis strictement les étapes suivantes de manière séquentielle :

## 1. Acquisition de Contexte

1. Lis le fichier `GEMINI.md` du backend : `/Users/tristanrigaud-humbert/PycharmProjects/fastApiProject/GEMINI.md`.
2. Identifie les fichiers cibles à analyser : Tous les fichiers dans le répertoire `app/api/routes/`.
3. Repère le fichier de configuration central ou le constructeur FastAPI (`app/main.py` ou similaire) pour vérifier la configuration globale des erreurs.

## 2. Audit des Conventions d'URL et de Méthodes HTTP

Scanne tous les fichiers de `app/api/routes/` et vérifie les points suivants pour chaque décorateur de route (`@router.get`, `@router.post`, etc.) :

### 2.1 Nommage des URLs
- **Pluriel vs Singulier :** Vérifie que les ressources racines utilisent le pluriel (ex: `/users/`, `/concepts/`) et non le singulier.
- **Casse (Case Convention) :** Vérifie que les URLs utilisent le `kebab-case` (ex: `/math-concepts/`) et non le `snake_case` (`/math_concepts/`) ou le `camelCase` (`/mathConcepts/`).
- **Signale** toutes les URLs qui ne respectent pas ces standards.

### 2.2 Sémantique des Méthodes HTTP
- **PUT vs PATCH :** Vérifie que les mises à jour partielles utilisent bien `PATCH` et que `PUT` est réservé aux remplacements complets.
- **GET avec Body :** Assure-toi qu'aucune route `GET` ne s'attend à recevoir un payload dans son corps (body).
- **POST pour la Recherche :** Tolère l'usage de `POST` pour des recherches complexes (si les filtres sont trop gros pour l'URL), mais signale si des recherches simples n'utilisent pas `GET` avec des query parameters.

## 3. Audit des Codes de Statut HTTP

Vérifie l'attribut `status_code` dans les décorateurs de routes :

### 3.1 Succès (2xx)
- **POST (Création) :** Vérifie que les routes de création retournent bien `201 Created` (au lieu du `200 OK` par défaut).
- **DELETE (Suppression) :** Vérifie que les routes de suppression retournent `204 No Content` (si aucun body n'est retourné) ou `200 OK` (si la ressource supprimée est retournée).
- **GET/PATCH/PUT :** Vérifie qu'elles retournent `200 OK`.

### 3.2 Erreurs (4xx/5xx)
- **Format Uniforme :** Vérifie (en inspectant `app/core/exceptions.py` et les dépendances) que le format de réponse en cas d'erreur est consistant (ex: toujours un objet JSON `{"detail": "Message"}`).

## 4. Audit des Formats de Données (Pagination, Tri, Filtres)

Examine les signatures des fonctions de routes (en particulier les routes `get_all_*`) :

### 4.1 Pagination
- **Vérifie** que la pagination est gérée de manière uniforme sur toutes les listes (ex: utilisation systématique de `skip`/`limit` ou de `page`/`size`).
- **Identifie** les routes de listage qui ne sont pas paginées et pourraient poser des problèmes de performance avec beaucoup de données.
- **Vérifie** le format de réponse paginée (ex: `{ "data": [...], "total": 100, "page": 1 }`).

### 4.2 Tri et Filtrage
- **Vérifie** si les conventions de nommage des paramètres de tri (ex: `sort_by`, `order`) et de filtrage sont constantes d'une route à l'autre.

## 5. Audit des Headers

- **Vérifie** si des headers de mise en cache (`Cache-Control`) sont présents sur les ressources statiques ou peu volatiles (ex: catégories, types).
- **Assure-toi** que les réponses retournent le bon `Content-Type` (géré par défaut par FastAPI, mais à vérifier si des `Response` personnalisées sont utilisées).

## 6. Génération du Rapport

1. Inspecte le dossier `artifact/ApiContract/` du projet backend (`/Users/tristanrigaud-humbert/PycharmProjects/fastApiProject/artifact/ApiContract/`). S'il n'existe pas, crée-le. Détermine le prochain numéro logique pour le fichier (ex: si `rapport_01.md` existe, le tien sera `rapport_02.md`).
2. Crée le fichier Markdown numéroté avec la structure suivante :
   - **Résumé exécutif** : Bilan de la cohérence de l'API (Sévérité globale, top 3 des problèmes les plus récurrents).
   - **Conventions d'URL & Méthodes** : Tableau listant les routes non conformes (Chemin actuel, Méthode, Correction proposée).
   - **Codes HTTP** : Liste des routes retournant des statuts inappropriés (ex: POST retournant 200 au lieu de 201).
   - **Formatage & Pagination** : Analyse de l'homogénéité des listes, de la pagination et des formats d'erreurs.
   - **Tableau récapitulatif** : Regroupement de toutes les anomalies détectées avec la priorité de correction.
3. Réponds dans le chat avec un bref résumé des résultats clés et un lien Markdown cliquable vers le rapport généré.
