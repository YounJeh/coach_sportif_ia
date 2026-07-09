# Backlog - MVP Coach Sportif IA

## Epic 1 - Onboarding, objectifs, consentements
US-101
- En tant qu'athlete, je veux definir un objectif et une deadline pour lancer un plan personnalise.
- Acceptance criteria:
  - Saisie objectif + deadline + niveau.
  - Validation de format et date future.
  - Objectif versionne en base.

US-102
- En tant qu'athlete, je veux choisir les sources de donnees autorisees.
- Acceptance criteria:
  - Consentement par source (Strava, Garmin, Calendar).
  - Consentement revocable.
  - Journal d'evenements de consentement.

## Epic 2 - Ingestion et normalisation
US-201
- En tant que systeme, je veux synchroniser les activites Strava/Garmin.
- Acceptance criteria:
  - Endpoint de webhook idempotent.
  - Mapping vers schema canonique.
  - Retry + dead-letter sur erreur.

US-202
- En tant que systeme, je veux ingerer les contraintes agenda quotidiennes.
- Acceptance criteria:
  - Lecture des creneaux disponibles.
  - Detection conflits avec seances planifiees.
  - Timestamp de fraicheur source.

US-203
- En tant que systeme, je veux scorer la qualite des donnees.
- Acceptance criteria:
  - Score de confiance 0-1 par source.
  - Flag anomalies (valeur aberrante, retard sync).
  - Exposition du score au moteur d'adaptation.

## Epic 3 - Planification et adaptation
US-301
- En tant qu'athlete, je veux un plan 7 jours adapte a mon objectif.
- Acceptance criteria:
  - Generation de seances quotidiennes.
  - Intensite et duree cible.
  - Alternative courte si indisponibilite.

US-302
- En tant que coach, je veux un ajustement automatique quand la realite change.
- Acceptance criteria:
  - Recalcul sur nouvel evenement.
  - Justification textuelle.
  - Limites max de variation charge.

US-303
- En tant que coach, je veux valider ou overrider les recommandations.
- Acceptance criteria:
  - Etat propose/valide/rejete.
  - Trace de l'override.
  - Affichage confiance recommendation.

## Epic 4 - Safety et policy
US-401
- En tant que systeme, je veux bloquer les recommandations a risque.
- Acceptance criteria:
  - Regles de progressivite appliquees.
  - Trigger alertes surcharge.
  - Message prudent si confiance faible.

US-402
- En tant qu'utilisateur, je veux comprendre les limites du systeme.
- Acceptance criteria:
  - Disclaimer non-medical visible.
  - Message d'escalade sante sur signaux critiques.

## Epic 5 - Observabilite et operations
US-501
- En tant qu'equipe produit, je veux suivre la qualite de service.
- Acceptance criteria:
  - Logs structures par trace_id.
  - Dashboard latence, erreurs, cout.
  - Alerting sur connecteur indisponible.

US-502
- En tant qu'equipe produit, je veux suivre la valeur utilisateur.
- Acceptance criteria:
  - KPI adherence calcule quotidiennement.
  - KPI WAU/MAU hebdomadaire.
  - Taux acceptance recommandations.

## Plan de livraison 6 semaines
- S1: Epic 1 + fondations base de donnees.
- S2: Epic 2 Strava + Calendar.
- S3: Epic 2 Garmin + score qualite.
- S4: Epic 3 planification + adaptation.
- S5: Epic 4 safety + policy.
- S6: Epic 5 observabilite + pilote.
