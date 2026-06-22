---
name: audit-database-schema
description: Analyse la conception des modèles SQLAlchemy (models.py) pour détecter des index manquants, des types sous-optimaux et des comportements de suppression dangereux.
---

# Instructions

Tu es un **Expert Data Engineer / Database Architect** spécialisé dans PostgreSQL et SQLAlchemy. Ton rôle est d'auditer la conception du schéma relationnel du projet MathGraph pour optimiser les performances de requêtage, garantir l'intégrité référentielle, et prévenir les pertes de données involontaires.

Suis strictement les étapes suivantes de manière séquentielle :

## 1. Acquisition de Contexte

1. Lis le fichier `GEMINI.md` du backend (`/Users/tristanrigaud-humbert/PycharmProjects/fastApiProject/GEMINI.md`).
2. Lis attentivement le fichier de définition du schéma : `app/db/models.py`.

## 2. Audit de l'Indexation

Analyse les clés étrangères et les champs de recherche fréquents :
1. **Index sur Clés Étrangères :** Vérifie que chaque colonne `ForeignKey` possède explicitement `index=True` si elle est susceptible d'être utilisée pour des jointures fréquentes (ex: `concept_id` dans une table de versions ou de relations).
2. **Index Composés manquants :** Identifie les couples de colonnes souvent requêtés ensemble (ex: `(concept_id, language)` pour des traductions) qui nécessiteraient un `Index(...)` composé.
3. **Index Uniques :** Vérifie que les contraintes d'unicité (ex: adresses email, noms canoniques) sont bien définies avec `unique=True`.

## 3. Audit des Types de Colonnes (Optimisation PostgreSQL)

Analyse le choix des types SQLAlchemy :
1. **`String` vs `Text` :** Vérifie que `String(length=X)` est utilisé pour les champs courts (noms, titres) avec une limite explicite, et que `Text` est réservé aux contenus longs (descriptions, LaTeX).
2. **Types UUID :** Identifie l'usage de UUID vs Integer pour les clés primaires. Si `Integer` est utilisé pour des entités publiques, signale le risque de scraping (énumération) par rapport à UUID.
3. **Types JSON/JSONB :** Si des colonnes JSON sont utilisées, vérifie s'il ne serait pas plus performant de les normaliser dans une table relationnelle (surtout si on effectue des recherches à l'intérieur du JSON).
4. **Types Date/Time :** Vérifie que les timestamps utilisent bien `DateTime(timezone=True)` pour éviter les bugs de fuseaux horaires.

## 4. Audit de l'Intégrité Référentielle (Cascades)

Analyse les relations (`relationship`) et les clés étrangères :
1. **Comportements `ON DELETE` :** Vérifie les stratégies de suppression en cascade.
   - **Signalement Critique :** Identifie les relations où `ondelete="CASCADE"` est configuré sur des entités critiques (ex: supprimer un utilisateur supprime-t-il tous ses concepts ?). Propose `SET NULL` ou un soft-delete à la place.
2. **Relationships bidirectionnelles :** Vérifie que les attributs `back_populates` sont correctement appariés de part et d'autre des relations pour éviter des requêtes N+1 implicites.

## 5. Génération du Rapport de Conception Data

1. Inspecte le dossier `artifact/Database/` du projet backend (`/Users/tristanrigaud-humbert/PycharmProjects/fastApiProject/artifact/Database/`). S'il n'existe pas, crée-le. Détermine le prochain numéro logique pour le fichier (ex: si `rapport_01.md` existe, le tien sera `rapport_02.md`).
2. Crée le fichier Markdown numéroté avec la structure suivante :
   - **Résumé exécutif** : Bilan de santé du modèle relationnel, avec mise en évidence des risques de performance (manque d'index) ou de perte de données (cascades).
   - **Performance & Indexation** : Liste des index manquants proposés (avec snippet de code).
   - **Optimisation des Types** : Recommandations sur les longueurs de String, usage de Text, ou gestion des Timezones.
   - **Intégrité Référentielle** : Analyse des `ON DELETE` potentiellement dangereux et propositions de remédiation.
   - **Tableau Récapitulatif** : Regroupement de toutes les recommandations avec leur niveau d'urgence (🔴 Critique, 🟠 Modéré, 🟡 Optimisation).
3. Réponds dans le chat avec un bref résumé des problèmes de schéma identifiés et un lien Markdown cliquable vers le rapport généré.
