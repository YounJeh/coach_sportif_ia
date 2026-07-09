#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-projet-coach-sportif-ia}"
REGION="${REGION:-europe-west1}"
SERVICE_NAME="${SERVICE_NAME:-coach-sportif-ia-api}"
IMAGE="${IMAGE:-gcr.io/${PROJECT_ID}/${SERVICE_NAME}:$(date +%Y%m%d-%H%M%S)}"
SERVICE_ACCOUNT_NAME="${SERVICE_ACCOUNT_NAME:-coach-sportif-ia-api-sa}"
SECRET_PREFIX="${SECRET_PREFIX:-coach-api}"
ALLOW_UNAUTH="${ALLOW_UNAUTH:-true}"
ENV_FILE="${ENV_FILE:-.env}"

# Variables non sensibles attendues en runtime.
NON_SECRET_VARS=("APP_ENV" "APP_PORT" "LOG_LEVEL" "LLM_PROVIDER" "GCP_PROJECT_ID" "GCP_LOCATION" "CORS_ALLOW_ORIGINS")

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Erreur: fichier $ENV_FILE introuvable"
  exit 1
fi

gcloud config set project "$PROJECT_ID"

echo "Activation APIs necessaires..."
gcloud services enable run.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com --project "$PROJECT_ID"

PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

if ! gcloud iam service-accounts describe "$SERVICE_ACCOUNT_EMAIL" --project "$PROJECT_ID" >/dev/null 2>&1; then
  gcloud iam service-accounts create "$SERVICE_ACCOUNT_NAME" --display-name="Coach API Cloud Run SA" --project "$PROJECT_ID"
fi

echo "Role Secret Manager accessor pour le service account runtime..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
  --role="roles/secretmanager.secretAccessor" >/dev/null

echo "Permission lecture image pour l'agent Cloud Run service..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:service-${PROJECT_NUMBER}@serverless-robot-prod.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer" >/dev/null || true

echo "Sync .env -> Secret Manager"
"$(dirname "$0")/sync_env_to_secret_manager.sh" "$PROJECT_ID" "$SECRET_PREFIX" "$ENV_FILE"

is_non_secret() {
  local candidate="$1"
  for allowed in "${NON_SECRET_VARS[@]}"; do
    if [[ "$allowed" == "$candidate" ]]; then
      return 0
    fi
  done
  return 1
}

SECRETS_FLAGS=()
while IFS= read -r key; do
  if is_non_secret "$key"; then
    continue
  fi
  SECRETS_FLAGS+=("${key}=${SECRET_PREFIX}-${key}:latest")
done < <(awk -F= 'NF>=2 && $1 !~ /^\s*#/ {gsub(/^\s+|\s+$/, "", $1); if(length($1)>0) print $1}' "$ENV_FILE")

set_env_pairs=()
for key in "${NON_SECRET_VARS[@]}"; do
  value="$(grep -E "^${key}=" "$ENV_FILE" | head -n1 | cut -d= -f2- || true)"
  if [[ -n "$value" ]]; then
    set_env_pairs+=("${key}=${value}")
  fi
done

SECRETS_ARG="$(IFS=,; echo "${SECRETS_FLAGS[*]}")"
SET_ENV_ARG="$(IFS=,; echo "${set_env_pairs[*]}")"

echo "Build image: $IMAGE"
gcloud builds submit --config cloudbuild.yaml --substitutions _IMAGE="$IMAGE" --project "$PROJECT_ID" .

DEPLOY_ARGS=(
  run deploy "$SERVICE_NAME"
  --image "$IMAGE"
  --region "$REGION"
  --platform managed
  --service-account "$SERVICE_ACCOUNT_EMAIL"
  --project "$PROJECT_ID"
)

if [[ -n "$SECRETS_ARG" ]]; then
  DEPLOY_ARGS+=(--set-secrets "$SECRETS_ARG")
fi

if [[ -n "$SET_ENV_ARG" ]]; then
  DEPLOY_ARGS+=(--set-env-vars "$SET_ENV_ARG")
fi

if [[ "$ALLOW_UNAUTH" == "true" ]]; then
  DEPLOY_ARGS+=(--allow-unauthenticated)
else
  DEPLOY_ARGS+=(--no-allow-unauthenticated)
fi

echo "Deploiement Cloud Run en cours..."
gcloud "${DEPLOY_ARGS[@]}"

URL="$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --project "$PROJECT_ID" --format='value(status.url)')"

echo "Deploiement termine"
echo "Service URL: ${URL}"
echo "Health: ${URL}/health"
