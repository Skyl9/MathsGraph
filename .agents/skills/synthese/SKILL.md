---
name: synthese
description: Analyse le projet courant de manière exhaustive et génère un document de synthèse détaillé sur l'architecture, la stack, les conventions et les règles métier.
---

# Instructions

Tu es un expert technique (Tech Lead / Architecte) chargé d'auditer ce projet. Suis ces étapes avec rigueur pour produire une synthèse complète :

1.  **Revue de la documentation existante :** Avant d'explorer le code, recherche et lis systématiquement les fichiers de contexte et de documentation existants (ex: `README.md`, `GEMINI.md`, `CONTRIBUTING.md`, ou les dossiers `docs/`). Ces fichiers contiennent souvent les règles métier de base et la vision du projet.
2.  **Analyse exhaustive de la stack :** Inspecte les fichiers de configuration à la racine de manière exhaustive. Ne te limite pas à `package.json` ou `requirements.txt` ; prends en compte les outils modernes (ex: `pyproject.toml`, `uv.lock`, `Cargo.toml`), les fichiers Docker (`Dockerfile`, `docker-compose.yml`), et les configurations CI/CD (`.github/workflows`, etc.).
3.  **Architecture profonde :** Explore l'arborescence des dossiers principaux (`app/`, `src/`, `tests/`, `migrations/`, etc.). Ne te limite pas à la racine. Comprends comment les couches communiquent (ex: pattern Controller-Service-Repository, middlewares, injection de dépendances).
4.  **Conventions et Patterns :** Scanne des fichiers clés spécifiques (point d'entrée principal, un contrôleur/route typique, un service, un modèle de DB, et les tests comme `conftest.py`). Identifie concrètement :
    *   Les stratégies de gestion d'erreur (exceptions personnalisées).
    *   La validation des données (ex: Pydantic).
    *   Les conventions de nommage et de style.
    *   La structure et l'isolation des tests automatiques.
5.  **Génération du document :** Rédige et sauvegarde un fichier nommé `PROJECT_SYNTHESIS.md` à la racine du projet. Structure-le avec les sections suivantes (ajoute des snippets de code si cela illustre bien une convention) :
    *   Vue d'ensemble et Objectifs
    *   Stack Technique (détaillée par catégorie)
    *   Architecture et Organisation des dossiers
    *   Conventions Observées (incluant gestion d'erreurs, tests, et data-flow)
6.  **Confirmation :** Termine en répondant directement dans le chat avec un court résumé de tes découvertes et fournis un lien Markdown cliquable vers le fichier `PROJECT_SYNTHESIS.md`. Ne mentionne pas de terminal.