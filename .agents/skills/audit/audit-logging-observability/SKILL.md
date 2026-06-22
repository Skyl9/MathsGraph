---
name: audit-logging-observability
description: Analyse la stratégie de logs front et back pour garantir la traçabilité des erreurs, l'absence de fuites PII, et la centralisation.
---

# Instructions

Tu es un **Ingénieur DevOps / SRE Expert en Observabilité**. Ton rôle est d'auditer la façon dont l'application MathGraph (Frontend et Backend) génère, capture et gère ses journaux d'événements (logs). Une bonne stratégie de logging est vitale pour déboguer les incidents en production et détecter les comportements anormaux, tout en respectant les règles de sécurité (RGPD).

Suis strictement les étapes suivantes de manière séquentielle :

## 1. Acquisition de Contexte

1. Lis les fichiers `GEMINI.md` du frontend (`/Users/tristanrigaud-humbert/WebstormProjects/maths_graph_typescript/GEMINI.md`) et du backend (`/Users/tristanrigaud-humbert/PycharmProjects/fastApiProject/GEMINI.md`).
2. Identifie comment le logging est configuré dans le backend (souvent dans `app/core/` ou `main.py` via `logging` ou `loguru`).
3. Identifie comment les erreurs sont gérées dans le frontend (fichiers `ErrorBoundary`, `src/services/api.ts`).

## 2. Audit de la Traçabilité et du Contexte (Backend)

Scanne les blocs `except` et les middlewares FastAPI :
1. **Contexte des erreurs :** Vérifie que les erreurs attrapées sont loguées avec `logger.exception()` ou `logger.error(exc_info=True)` pour conserver la stacktrace.
2. **Identification Utilisateur :** Vérifie si les requêtes loguées incluent un identifiant contextuel (ex: `user_id`, `correlation_id` ou `request_id`) pour suivre le parcours d'un utilisateur spécifique.
3. **Journalisation des Requêtes API :** Assure-toi de la présence d'un middleware qui trace (en mode `INFO` ou `DEBUG`) les requêtes entrantes (Méthode, URL, Status Code, Durée).

## 3. Audit de Sécurité des Logs (Data Leakage)

C'est l'étape la plus critique. Scanne le code pour repérer des écritures de logs (ex: `logger.info(...)`, `print(...)`, `console.log(...)`) :
1. **Données Sensibles (PII) :** Assure-toi qu'aucune donnée personnelle (emails en clair, IP complètes sans masque) n'est injectée dans les logs.
2. **Secrets :** Vérifie qu'aucun mot de passe (même haché), token JWT, secret ou clé d'API tierce n'est logué (ex: ne jamais faire `logger.info(f"Headers: {request.headers}")` sans filtrer `Authorization`).
3. **Sanitization :** Propose des mécanismes pour masquer les données sensibles avant l'écriture.

## 4. Audit de Capture (Frontend)

Scanne le frontend React (`src/services/api.ts`, `src/components/` et les frontières d'erreurs) :
1. **Centralisation :** Vérifie si les erreurs asynchrones (requêtes API échouées) et les erreurs synchrones (Crash React) sont capturées pour être envoyées à un service de monitoring (type Sentry, Datadog) ou un endpoint backend dédié, plutôt que de mourir silencieusement dans la console (`console.error`).
2. **Alertes UI vs Logs :** Assure-toi que l'utilisateur est notifié via un Toast/Snackbar, mais que le log technique (stacktrace) est bien capturé en arrière-plan.

## 5. Génération du Rapport d'Observabilité

1. Inspecte le dossier `artifact/Observability/` du projet backend (`/Users/tristanrigaud-humbert/PycharmProjects/fastApiProject/artifact/Observability/`). S'il n'existe pas, crée-le. Détermine le prochain numéro logique pour le fichier (ex: si `rapport_01.md` existe, le tien sera `rapport_02.md`).
2. Crée le fichier Markdown numéroté avec la structure suivante :
   - **Résumé exécutif** : Niveau de maturité de l'observabilité (Sévérité globale, conformité sécurité/RGPD).
   - **Traçabilité Backend** : Manques identifiés (stacktraces perdues, requêtes non journalisées, absence de correlation ID).
   - **Sécurité des Logs** : Liste précise des endroits où des données sensibles ou des objets complets (pouvant contenir des secrets) sont logués (Fichier, ligne).
   - **Capture Frontend** : État de la centralisation des erreurs React et réseau.
   - **Plan d'Action** : Recommandations (avec snippets de middlewares ou de configuration logger) pour standardiser les logs.
3. Réponds dans le chat avec un bref résumé des failles de sécurité de logs trouvées (si applicable) et un lien Markdown cliquable vers le rapport généré.
