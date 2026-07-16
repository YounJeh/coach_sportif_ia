#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-all}"

PROJECT_ID="${PROJECT_ID:-projet-coach-sportif-ia}"
REGION="${REGION:-europe-west1}"
SERVICE_NAME="${SERVICE_NAME:-coach-sportif-ia-api}"
IMAGE="${IMAGE:-gcr.io/${PROJECT_ID}/${SERVICE_NAME}:$(date +%Y%m%d-%H%M%S)}"
SERVICE_ACCOUNT_NAME="${SERVICE_ACCOUNT_NAME:-coach-sportif-ia-api-sa}"
SECRET_PREFIX="${SECRET_PREFIX:-coach-api}"
ALLOW_UNAUTH="${ALLOW_UNAUTH:-true}"
ENV_FILE="${ENV_FILE:-.env}"

NON_SECRET_VARS=(
  "APP_ENV"
  "APP_PORT"
  "LOG_LEVEL"
  "LLM_PROVIDER"
  "GCP_PROJECT_ID"
  "GCP_LOCATION"
  "CORS_ALLOW_ORIGINS"
)

case "$MODE" in
  init|deploy|all)
    ;;
  *)
    echo "Usage: $0 {init|deploy|all}"
    exit 1
    ;;
esac

gcloud config set project "$PROJECT_ID"

SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

if [[ "$MODE" == "init" || "$MODE" == "all" ]]; then
  if [[ ! -f "$ENV_FILE" ]]; then
    echo "Erreur : fichier $ENV_FILE introuvable"
    exit 1
  fi

  echo "Initialisation du projet..."

  gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    secretmanager.googleapis.com \
    --project "$PROJECT_ID"

  PROJECT_NUMBER="$(
    gcloud projects describe "$PROJECT_ID" \
      --format="value(projectNumber)"
  )"

  if ! gcloud iam service-accounts describe \
    "$SERVICE_ACCOUNT_EMAIL" \
    --project "$PROJECT_ID" >/dev/null 2>&1
  then
    gcloud iam service-accounts create "$SERVICE_ACCOUNT_NAME" \
      --display-name="Coach API Cloud Run SA" \
      --project "$PROJECT_ID"
  fi

  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/secretmanager.secretAccessor" \
    >/dev/null

  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:service-${PROJECT_NUMBER}@serverless-robot-prod.iam.gserviceaccount.com" \
    --role="roles/storage.objectViewer" \
    >/dev/null || true

  echo "Synchronisation du fichier .env vers Secret Manager..."

  "$(dirname "$0")/sync_env_to_secret_manager.sh" \
    "$PROJECT_ID" \
    "$SECRET_PREFIX" \
    "$ENV_FILE"
fi

if [[ "$MODE" == "deploy" || "$MODE" == "all" ]]; then
  echo "Build de l'image : $IMAGE"

  gcloud builds submit \
    --config cloudbuild.yaml \
    --substitutions "_IMAGE=$IMAGE" \
    --project "$PROJECT_ID" \
    .

  echo "Déploiement Cloud Run..."

  gcloud run deploy "$SERVICE_NAME" \
    --image "$IMAGE" \
    --region "$REGION" \
    --platform managed \
    --project "$PROJECT_ID"

  URL="$(
    gcloud run services describe "$SERVICE_NAME" \
      --region "$REGION" \
      --project "$PROJECT_ID" \
      --format="value(status.url)"
  )"

  echo "Déploiement terminé"
  echo "Service URL : $URL"
  echo "Health : $URL/health"
fi