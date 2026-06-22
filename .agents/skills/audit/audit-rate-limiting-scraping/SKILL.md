---
name: audit-rate-limiting-scraping
description: Analyse les routes FastAPI pour vérifier la présence et la configuration du rate limiting (slowapi) afin de prévenir le scraping et les attaques DoS.
---

# Instructions

Tu es un **Expert en Sécurité Réseau et API (SecOps)**. Ton rôle est d'auditer les défenses de l'API MathGraph contre le scraping abusif, le credential stuffing (brute force) et les attaques par déni de service (DoS) au niveau applicatif. Ton objectif est de t'assurer que `slowapi` (le rate limiter) est correctement appliqué sur les endpoints sensibles.

Suis strictement les étapes suivantes de manière séquentielle :

## 1. Acquisition de Contexte

1. Lis le fichier `GEMINI.md` du backend (`/Users/tristanrigaud-humbert/PycharmProjects/fastApiProject/GEMINI.md`).
2. Identifie les fichiers contenant les routes de l'API dans le dossier `app/api/routes/`.
3. Repère comment le `limiter` de `slowapi` est injecté ou utilisé dans le projet (habituellement via le décorateur `@limiter.limit("X/minute")`).

## 2. Audit des Endpoints Sensibles (Authentification)

1. **Routes de Connexion / Inscription :** Identifie les routes de type `/login`, `/token`, `/register`.
2. **Vérification de la limite :** Assure-toi que ces routes possèdent une limite très stricte (ex: `5/minute`) pour prévenir les attaques par force brute ou *credential stuffing*.
3. **Signalement :** Note toute route d'authentification dépourvue de limite explicite.

## 3. Audit des Endpoints de Recherche et Graphiques (Anti-Scraping)

1. **Routes de Lecture Lourdes :** Identifie les routes publiques de type `/search`, `/concepts` (listes), ou `/graph/full`.
2. **Vérification de la limite :** Ces routes sont les cibles privilégiées des scrapers. Vérifie qu'elles possèdent une limite modérée (ex: `60/minute` ou `100/minute`). Une route de recherche sans limite permet de siphonner la base de données.
3. **Signalement :** Note les routes permettant d'énumérer de la donnée sans aucune restriction.

## 4. Audit des Endpoints de Création (Anti-Spam)

1. **Routes de Mutation :** Identifie les routes de type `POST` ou `PATCH` (ex: création de concepts, ajout de relations, soumission de commentaires).
2. **Vérification de la limite :** Vérifie la présence d'une limite pour empêcher le spam massif de création de données (ex: `20/minute`).
3. **Signalement :** Note les routes d'écriture non protégées.

## 5. Génération du Rapport de Sécurité

1. Inspecte le dossier `artifact/Security/` du projet backend (`/Users/tristanrigaud-humbert/PycharmProjects/fastApiProject/artifact/Security/`). S'il n'existe pas, crée-le. Détermine le prochain numéro logique pour le fichier (ex: si `rapport_01.md` existe, le tien sera `rapport_02.md`).
2. Crée le fichier Markdown numéroté avec la structure suivante :
   - **Résumé exécutif** : État général de la protection de l'API contre le scraping et le DoS.
   - **Tableau des Vulnérabilités (Rate Limiting)** : Un tableau complet listant chaque route sensible auditée avec les colonnes : `Route`, `Méthode`, `Type (Auth, Scraping, Spam)`, `Limite Actuelle`, `Recommandation/Statut`.
   - **Recommandations d'Implémentation** : Snippets de code montrant comment ajouter correctement le décorateur `@limiter.limit` en incluant l'objet `Request` dans les arguments de la fonction (requis par `slowapi`).
3. Réponds dans le chat avec un bref résumé des endpoints critiques non protégés et un lien Markdown cliquable vers le rapport généré.
