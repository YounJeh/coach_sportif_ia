#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${1:-projet-coach-sportif-ia}"
SECRET_PREFIX="${2:-coach-api}"
ENV_FILE="${3:-.env}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Erreur: fichier $ENV_FILE introuvable"
  exit 1
fi

gcloud config set project "$PROJECT_ID" >/dev/null

while IFS='=' read -r raw_key raw_value || [[ -n "${raw_key:-}" ]]; do
  key="$(echo "$raw_key" | xargs)"

  if [[ -z "$key" || "$key" == \#* ]]; then
    continue
  fi

  # Preserve full value (including '=' if present after first '=').
  value="${raw_value:-}"

  # Trim surrounding spaces.
  value="$(printf '%s' "$value" | sed 's/^ *//;s/ *$//')"

  if [[ -z "$value" ]]; then
    continue
  fi

  secret_id="${SECRET_PREFIX}-${key}"

  if gcloud secrets describe "$secret_id" --project "$PROJECT_ID" >/dev/null 2>&1; then
    printf '%s' "$value" | gcloud secrets versions add "$secret_id" --data-file=- --project "$PROJECT_ID" >/dev/null
    echo "Secret mis a jour: $secret_id"
  else
    printf '%s' "$value" | gcloud secrets create "$secret_id" --replication-policy=automatic --data-file=- --project "$PROJECT_ID" >/dev/null
    echo "Secret cree: $secret_id"
  fi
done < "$ENV_FILE"

echo "Synchronisation Secret Manager terminee pour $PROJECT_ID"
