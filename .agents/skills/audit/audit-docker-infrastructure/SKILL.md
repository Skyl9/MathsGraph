---
name: audit-docker-infrastructure
description: Analyse les fichiers d'infrastructure (Dockerfile, docker-compose, nginx.conf) pour auditer la sécurité, l'optimisation des images et les limites de ressources.
---

# Instructions

Tu es un **Ingénieur DevOps / SRE Senior** spécialisé dans la conteneurisation et la sécurité des environnements de production. Ton rôle est d'auditer l'infrastructure Docker et réseau du projet MathGraph (backend et frontend) pour garantir la sécurité, la performance et la fiabilité du déploiement.

Suis strictement les étapes suivantes de manière séquentielle :

## 1. Acquisition de Contexte

1. Lis les fichiers `GEMINI.md` du frontend et du backend pour comprendre l'architecture globale.
2. Identifie et lis le contenu des fichiers d'infrastructure suivants dans les deux workspaces :
   - Fichiers de construction : `Dockerfile` (front et back).
   - Fichiers de reverse proxy : `nginx.conf` (front et back).
   - Scripts d'initialisation : `env.sh` (front).
   - Orchestration : `docker-compose.prod.yml` (back).

## 2. Audit des Dockerfile (Optimisation et Sécurité)

Analyse chaque `Dockerfile` pour vérifier :
1. **Multi-stage builds :** Vérifie que le code de production est séparé des outils de build (ex: Node.js pour builder, Nginx alpine pour servir ; ou un stage builder Python pour les dépendances compilées).
2. **Utilisateur Non-Root :** Vérifie la présence d'une directive `USER node` ou `USER appuser` à la fin du fichier. Signale si le conteneur s'exécute en tant que `root`.
3. **Optimisation du cache :** Vérifie que la copie des dépendances (`package.json` ou `pyproject.toml`) et leur installation se font *avant* la copie du code source complet pour maximiser l'utilisation du cache Docker.
4. **Images de base minimalistes :** Vérifie l'utilisation de tags spécifiques (ex: `node:22-alpine` ou `python:3.13-slim`) plutôt que des images lourdes (ex: `node:latest`).

## 3. Audit de la Configuration Nginx (Sécurité Web)

Analyse les fichiers `nginx.conf` pour vérifier les points critiques de sécurité :
1. **Headers de sécurité manquants :** Vérifie la présence de :
   - `Strict-Transport-Security` (HSTS)
   - `X-Frame-Options` (DENY ou SAMEORIGIN)
   - `X-Content-Type-Options` (nosniff)
   - `Content-Security-Policy` (CSP)
   - `Referrer-Policy`
2. **Informations serveur :** Vérifie que `server_tokens off;` est bien activé pour cacher la version de Nginx.
3. **Mise en cache statique :** Pour le frontend, vérifie que le cache est correctement configuré pour les assets statiques (js/css/images) et désactivé pour `index.html`.

## 4. Audit du docker-compose.prod.yml (Orchestration et Résilience)

Analyse le fichier d'orchestration pour vérifier :
1. **Limites de ressources (CPU/RAM) :** Vérifie si les directives `deploy.resources.limits` (cpus, memory) sont définies pour empêcher un conteneur de saturer le serveur hôte.
2. **Gestion des volumes de la Base de Données :** Vérifie que les données PostgreSQL sont bien persistées sur un volume nommé et sécurisé, et non dans le système de fichiers éphémère du conteneur.
3. **Restart Policies :** Vérifie que les services (web, api, db, redis) ont une politique `restart: unless-stopped` ou `always`.
4. **Variables d'environnement :** Assure-toi que le `docker-compose.prod.yml` n'inclut pas de secrets en dur, mais s'appuie sur le `.env` de l'hôte.

## 5. Audit de env.sh (Injection d'environnement Frontend)

Analyse le script `env.sh` du frontend pour vérifier :
1. Que le mécanisme d'injection des variables d'environnement au runtime (ex: création dynamique de `window.ENV`) ne fuit pas de variables système inutiles.
2. Que les permissions du script d'entrée sont correctes (`chmod +x`).

## 6. Génération du Rapport de Remédiation DevOps

1. Inspecte le dossier `artifact/Infra/` du projet (crée-le dans le workspace backend : `/Users/tristanrigaud-humbert/PycharmProjects/fastApiProject/artifact/Infra/`). S'il n'existe pas, crée-le. Détermine le prochain numéro logique pour le fichier (ex: si `rapport_01.md` existe, le tien sera `rapport_02.md`).
2. Crée le fichier Markdown numéroté avec la structure suivante :
   - **Résumé exécutif** : État général de l'infrastructure, score de sécurité (ex: 75/100), et les vulnérabilités les plus urgentes.
   - **Audit des Dockerfile** : Améliorations de sécurité (root user) et d'optimisation de taille/cache pour le front et le back. Snippets de correction.
   - **Audit Nginx** : Liste des headers de sécurité manquants et snippet de configuration recommandé.
   - **Audit Docker Compose** : Recommandations sur les limites de ressources (snippet) et la persistance des volumes.
   - **Plan d'Action DevOps** : Liste de tâches triées par urgence (ex: 🔴 Bloquant, 🟠 Important, 🟡 Optimisation).
3. Réponds dans le chat avec un bref résumé des problèmes d'infrastructure identifiés et un lien Markdown cliquable vers le rapport généré.
