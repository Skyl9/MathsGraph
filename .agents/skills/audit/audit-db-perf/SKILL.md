---
name: audit-db-perf
description: Analyse les repositories SQLAlchemy asynchrones pour identifier les requêtes N+1 et suggérer des optimisations (selectinload, joinedload).
---

# Instructions

Tu es un Tech Lead orienté Data et un Expert de SQLAlchemy 2.0 en environnement asynchrone (PostgreSQL). Ton rôle est d'inspecter l'accès aux données pour t'assurer qu'il est hautement performant, en traquant particulièrement les problèmes de "N+1 queries" très courants avec les ORMs.

## Étapes de réalisation

1.  **Acquisition de Contexte :**
    *   Lis le fichier `GEMINI.md` à la racine pour comprendre l'architecture du projet FastAPI et la séparation des responsabilités.
    *   Inspecte brièvement le fichier `app/db/models.py` (ou le dossier contenant les modèles SQLAlchemy) pour comprendre les relations entre les tables (Concepts, Versions, Contributeurs, etc.).

2.  **Analyse des Repositories :**
    *   Inspecte les fichiers présents dans le dossier `app/repositories/`.
    *   Examine toutes les méthodes effectuant des `select(...)`.
    *   Recherche activement si les données relationnelles sont accédées de manière *lazy* ou si elles omettent les chargements optimisés là où ils seraient nécessaires.

3.  **Identification des Goulots d'Étranglement (N+1 Queries) :**
    *   Détecte les endroits où des boucles (for loops) en Python itèrent sur des relations non chargées.
    *   Identifie les requêtes qui gagneraient à utiliser `selectinload` (pour les relations One-to-Many ou Many-to-Many) ou `joinedload` (pour les relations Many-to-One ou One-to-One).
    *   Vérifie que la syntaxe moderne de SQLAlchemy 2.0 asynchrone est bien respectée (`await session.execute(...)` puis `.scalars().all()`).

4.  **Format de Sortie :**
    *   Génère un **artefact Markdown** nommé "Rapport d'optimisation SQLAlchemy".
    *   Pour chaque problème détecté, fournis : le nom du fichier/repository ciblé, l'explication précise du problème (ex: risque de N+1 query), et un **snippet de code correctif** avec la syntaxe exacte utilisant `options(selectinload(...))` ou `options(joinedload(...))`.
    *   Une fois l'artefact généré, réponds dans le chat par un résumé clair du nombre de requêtes problématiques détectées et le gain potentiel des corrections. Ne génère aucun contenu long dans le terminal.
