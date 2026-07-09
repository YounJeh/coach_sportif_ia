# Deploiement GCP - API Coach Sportif IA

Ce guide deploie l'API sur Cloud Run dans le projet GCP:
- projet-coach-sportif-ia

## Prerequis

- gcloud installe et connecte.
- Droits IAM suffisants sur le projet (Cloud Run Admin, Build, IAM Service Account Admin, Secret Manager Admin).
- Fichier .env present a la racine.

## 1) Verifier le projet actif

Commande:

gcloud config set project projet-coach-sportif-ia

gcloud config get-value project

## 2) Configurer CORS pour ton front externe

Dans .env, definir CORS_ALLOW_ORIGINS avec l'URL de ton front, par exemple:

CORS_ALLOW_ORIGINS=https://ton-front.exemple.com

Tu peux definir plusieurs origines separees par des virgules.

## 3) Lancer le deploiement automatise

Commande:

bash scripts/deploy_cloud_run.sh

Le script fait automatiquement:
- activation des APIs GCP requises
- creation du service account runtime Cloud Run
- synchronisation des variables .env vers Secret Manager
- build image via Cloud Build
- deploiement Cloud Run avec variables non sensibles en clair et sensibles en secrets

## 4) Verifier l'API

Le script affiche l'URL du service. Puis:

curl <SERVICE_URL>/health

## Variables du script (optionnelles)

Tu peux overrider les valeurs par defaut:
- PROJECT_ID (defaut: projet-coach-sportif-ia)
- REGION (defaut: europe-west1)
- SERVICE_NAME (defaut: coach-sportif-ia-api)
- SERVICE_ACCOUNT_NAME (defaut: coach-sportif-ia-api-sa)
- SECRET_PREFIX (defaut: coach-api)
- ALLOW_UNAUTH (defaut: true)
- ENV_FILE (defaut: .env)

Exemple:

PROJECT_ID=projet-coach-sportif-ia REGION=europe-west1 SERVICE_NAME=coach-agents-api bash scripts/deploy_cloud_run.sh

## Notes importantes

- Pour integration front directe, ALLOW_UNAUTH=true est le plus simple au debut.
- En production stricte, prefere ALLOW_UNAUTH=false + authentification (IAP, JWT, API Gateway).
- Comme ta base Supabase est externe, pas de VPC connector obligatoire pour ce setup.
- Si DB_URL utilise SSL, garde sslmode=require dans la chaine de connexion.
