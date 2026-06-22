---
name: audit-async-concurrency
description: Scanne le backend pour identifier les anti-patterns asynchrones (I/O bloquants, await manquants, requêtes en série).
---

# Instructions

Tu es un **Ingénieur Backend Expert en Asynchronisme (Python/FastAPI)**. Ton rôle est d'auditer le code source du backend MathGraph pour débusquer tous les anti-patterns liés à l'exécution concurrente (async/await) qui pourraient créer des goulots d'étranglement ou geler l'Event Loop.

Suis strictement les étapes suivantes de manière séquentielle :

## 1. Acquisition de Contexte

1. Lis le fichier `GEMINI.md` du backend : `/Users/tristanrigaud-humbert/PycharmProjects/fastApiProject/GEMINI.md` pour t'imprégner de l'architecture.
2. Identifie les répertoires contenant la logique : `app/api/routes/`, `app/services/` et `app/repositories/`.

## 2. Détection d'I/O Bloquants dans l'Event Loop

L'Event Loop Python est mono-thread. Une fonction I/O synchrone à l'intérieur d'une fonction `async def` va bloquer toutes les autres requêtes en cours.
1. Scanne le code à la recherche d'appels à des librairies synchrones bloquantes à l'intérieur de fonctions `async def`.
   - **Requêtes HTTP :** Cherche l'utilisation de `requests.get()` ou `urllib`. Elles doivent être remplacées par `httpx.AsyncClient` ou `aiohttp`.
   - **Fichiers :** Cherche les appels à `open()` ou `json.load()` sans `aiofiles`.
   - **Calculs lourds (CPU-bound) :** Identifie les boucles très lourdes (ex: traitement d'images, parsing de gros graphes) qui devraient être déportées via `run_in_threadpool` ou Celery/BackgroundTasks.

## 3. Détection des Oublis d'`await` (Coroutines non attendues)

1. **Fonctions asynchrones non attendues :** Repère les appels à des fonctions `async` ou des méthodes de repository asynchrones où le développeur a oublié le mot clé `await` (ce qui retourne un objet coroutine au lieu du résultat escompté).
2. **Warning FastAPI :** Vérifie particulièrement les dépendances (`Depends()`) pour t'assurer qu'elles sont correctement déclarées.

## 4. Opportunités de Parallélisation (`asyncio.gather`)

1. **Requêtes en série dans des boucles :** Cherche les patterns inefficaces où des requêtes I/O (base de données ou API externes) sont exécutées l'une après l'autre dans une boucle `for`.
   ```python
   # ❌ Anti-pattern :
   results = []
   for item in items:
       res = await db.get_something(item.id) # Bloque à chaque itération
       results.append(res)
   ```
2. **Remédiation :** Propose de remplacer ces appels séquentiels par une exécution concurrente utilisant `asyncio.gather` (ou la gestion native `in_` de SQLAlchemy pour la DB).
   ```python
   # ✅ Bon pattern :
   tasks = [db.get_something(item.id) for item in items]
   results = await asyncio.gather(*tasks)
   ```

## 5. Génération du Rapport de Performance

1. Inspecte le dossier `artifact/Concurrency/` du projet backend (`/Users/tristanrigaud-humbert/PycharmProjects/fastApiProject/artifact/Concurrency/`). S'il n'existe pas, crée-le. Détermine le prochain numéro logique pour le fichier (ex: si `rapport_01.md` existe, le tien sera `rapport_02.md`).
2. Crée le fichier Markdown numéroté avec la structure suivante :
   - **Résumé exécutif** : Bilan de la santé asynchrone de l'API (Sévérité globale, impact potentiel sur les performances).
   - **I/O Bloquants Détectés** : Liste des appels synchrones trouvés dans l'Event Loop (Fichier, ligne, solution).
   - **Oublis d'`await`** : Liste des coroutines non résolues.
   - **Opportunités de Parallélisation (`asyncio.gather`)** : Liste des boucles séquentielles avec snippets de refactorisation proposés.
3. Réponds dans le chat avec un bref résumé des problèmes de concurrence les plus graves et un lien Markdown cliquable vers le rapport généré.
