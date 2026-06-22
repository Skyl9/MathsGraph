---
name: audit-cache-strategy
description: Analyse l'utilisation de Redis dans le backend pour vérifier la mise en cache des requêtes lourdes, la pertinence des TTL, et l'invalidation lors des mutations.
---

# Instructions

Tu es un **Ingénieur Backend Expert en Performance**. Ton rôle est d'auditer la stratégie de mise en cache (via Redis) du backend FastAPI de MathGraph. Une mauvaise gestion du cache peut entraîner le renvoi de données obsolètes (stale data) ou, à l'inverse, des problèmes de performance si le cache n'est pas utilisé ou mal invalidé.

Suis strictement les étapes suivantes de manière séquentielle :

## 1. Acquisition de Contexte

1. Lis le fichier `GEMINI.md` du backend : `/Users/tristanrigaud-humbert/PycharmProjects/fastApiProject/GEMINI.md`.
2. Identifie les dossiers clés : `app/services/` (où devrait résider la logique de cache) et `app/api/routes/`.
3. Repère comment Redis est configuré et injecté (ex: `app/core/redis.py` ou des dépendances dans `main.py`).

## 2. Audit de la Mise en Cache des Lectures (GET)

Scanne les services et routes effectuant des requêtes de lecture lourdes (ex: récupération d'un graphe entier, liste de concepts filtrée, recherches) :
1. **Couverture :** Vérifie si ces requêtes complexes lisent d'abord dans Redis avant de taper dans PostgreSQL.
2. **Gestion du TTL :** Vérifie que chaque valeur mise en cache possède un TTL (Time To Live). Signale les TTL infinis (absence d'expiration) ou déraisonnables (ex: 1 seconde, annulant l'intérêt du cache).
3. **Clés de cache (Cache Keys) :** Assure-toi que la clé Redis est unique et déterministe (ex: `concept:graph:{user_id}:{concept_id}`).

## 3. Audit de l'Invalidation du Cache (Mutations)

C'est l'étape la plus critique. Scanne les opérations de mutation de données (`POST`, `PATCH`, `DELETE`) dans les services :
1. **Invalidation ciblée :** Lorsqu'une entité est modifiée (ex: mise à jour d'un concept), vérifie qu'une commande d'invalidation (ex: `redis.delete(...)`) est appelée pour la clé correspondante.
2. **Invalidation large (patterns) :** Si une création impacte des listes entières (ex: ajout d'un concept dans une catégorie), vérifie que le cache des listes associées est purgé (ex: via des suppressions par pattern `KEYS` ou `SCAN`).
3. **Risque de "Stale Data" :** Liste toutes les méthodes de mutation qui oublient d'invalider le cache, ce qui entraînerait un affichage de données périmées côté frontend.

## 4. Génération du Rapport de Remédiation

1. Inspecte le dossier `artifact/Cache/` du projet backend (`/Users/tristanrigaud-humbert/PycharmProjects/fastApiProject/artifact/Cache/`). S'il n'existe pas, crée-le. Détermine le prochain numéro logique pour le fichier (ex: si `rapport_01.md` existe, le tien sera `rapport_02.md`).
2. Crée le fichier Markdown numéroté avec la structure suivante :
   - **Résumé exécutif** : État général de la stratégie de cache, identification des goulots d'étranglement ou des risques de stale data.
   - **Couverture de Cache Manquante** : Liste des endpoints lourds qui ne sont pas mis en cache et qui devraient l'être.
   - **Audit des TTL** : Analyse des durées d'expiration.
   - **Faille d'Invalidation (Stale Data)** : Liste exhaustive des méthodes de mutation qui omettent d'invalider les clés Redis (indiquer le fichier et la fonction).
   - **Recommandations** : Proposer des snippets de code pour standardiser la gestion du cache (ex: via un décorateur `@cache`).
3. Réponds dans le chat avec un bref résumé des failles d'invalidation trouvées et un lien Markdown cliquable vers le rapport généré.
