# Coach Sportif IA

Orchestration multi-agents avec LangGraph pour generer et adapter un programme sportif personnalise en fonction des objectifs, du calendrier et des donnees d'activite.

## Ce que contient ce repo

- PRD MVP: docs/PRD.md
- Backlog sprintable: docs/BACKLOG.md
- Service API FastAPI + LangGraph: src/coach_ai
- Fichiers de build/deploiement Cloud Run: Dockerfile, cloudbuild.yaml

## Architecture MVP

- API Cloud Run (FastAPI)
- Orchestrateur LangGraph (pipeline agents)
- Connecteurs MCP/adaptateurs (Strava, Garmin, Calendar)
- Safety policy pour limiter les recommandations a risque

Flux principal:

1. Intake objectif + deadline + contraintes
2. Synchronisation des donnees
3. Score qualite des sources
4. Construction du contexte
5. Planification 7 jours
6. Filtre safety
7. Briefing coach et athlete

## Demarrage local

Prerequis:

- Python 3.11+

Installation:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
```

Lancement API:

```bash
uvicorn coach_ai.main:app --reload --host 0.0.0.0 --port 8080
```

Healthcheck:

```bash
curl http://localhost:8080/health
```

Exemple generation plan:

```bash
curl -X POST http://localhost:8080/v1/plan \
	-H "Content-Type: application/json" \
	-d '{
		"user_id": "athlete_001",
		"objective": "Courir un semi-marathon",
		"deadline": "2026-10-01",
		"available_slots": ["Mon-07:00", "Tue-18:30", "Thu-07:00", "Sat-09:00"],
		"off_days": ["Sunday"]
	}'
```

## Deploiement GCP Cloud Run

Projet cible:

- projet-coach-sportif-ia

Deploiement automatise recommande:

```bash
gcloud config set project projet-coach-sportif-ia
bash scripts/deploy_cloud_run.sh
```

Guide complet:

- docs/DEPLOY_GCP.md

Deploiement manuel (alternative):

Build image:

```bash
gcloud builds submit --config cloudbuild.yaml --substitutions _IMAGE=gcr.io/PROJECT_ID/coach-sportif-ia:latest .
```

Deploy service:

```bash
gcloud run deploy coach-sportif-ia \
	--image gcr.io/PROJECT_ID/coach-sportif-ia:latest \
	--region europe-west1 \
	--platform managed \
	--allow-unauthenticated
```

## Notes securite

- Le projet est positionne bien-etre/performance, non medical.
- Ajouter consentement granulaire et journalisation RGPD avant production.
