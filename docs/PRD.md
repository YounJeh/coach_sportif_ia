# PRD - Coach Sportif IA (MVP)

## 1. Vision Produit
Coach Sportif IA est un copilote d'entrainement qui combine objectifs, disponibilites calendrier, donnees d'activite (Strava, Garmin) et contexte personnel pour proposer un plan adapte et le mettre a jour chaque jour.

## 2. Problem Statement
Les coachs et athletes amateurs manquent de temps pour ajuster les plans quand la realite change (fatigue, agenda, seances manquees). Les plans statiques deviennent vite obsoletes.

## 3. Proposition de Valeur
- Transformer des donnees dispersees en decisions quotidiennes actionnables.
- Reduire le temps de planification coach par athlete.
- Augmenter l'adherence et limiter les surcharges via des ajustements prudents.

## 4. Personas
- Coach independant (20 a 80 athletes).
- Athlete amateur avec agenda variable.
- Head coach qui veut supervision et tracabilite des decisions IA.

## 5. Jobs To Be Done
- Quand mon athlete rate une seance, je veux un recalcul automatique credible pour garder le cap vers la deadline.
- Quand mon agenda change, je veux une seance alternative faisable aujourd'hui.
- Quand je prepare la semaine, je veux un plan 7 jours explique et validable en quelques minutes.

## 6. Scope MVP (6 semaines)
Inclus:
- Onboarding objectif et contraintes.
- Connexion Strava, Garmin, Google Calendar (via adaptateurs MCP).
- Plan 7 jours + adaptation quotidienne.
- Briefing coach et briefing athlete.
- Fallback en mode conservateur si donnees partielles.

Exclus MVP:
- Nutrition personnalisee complete.
- Diagnostic medical.
- Segmentation avancee multi-sports elite.

## 7. Functional Requirements
- FR1: L'utilisateur peut definir un objectif, une deadline, et des contraintes hebdomadaires.
- FR2: Le systeme ingere les activites et events agenda chaque jour.
- FR3: Le systeme genere un plan 7 jours avec intensite, duree et alternatives.
- FR4: Le systeme recalcule la seance du lendemain sur evenement nouveau.
- FR5: Le systeme expose une justification textuelle des adaptations.
- FR6: Le coach peut valider, modifier, ou rejeter une recommandation.
- FR7: Chaque decision IA est journalisee (raison, confiance, sources utilisees).

## 8. Non Functional Requirements
- NFR1: Disponibilite API cible >= 99.5%.
- NFR2: Latence generation briefing <= 5 secondes en P95.
- NFR3: Idempotence sur webhooks de sync.
- NFR4: Donnees chiffrees en transit et au repos.
- NFR5: Consentement granulaire et revocable.

## 9. Multi-Agent Design (LangGraph)
- IntakeConsentAgent: capture objectif, contraintes, consentements.
- DataSyncAgent: recupere donnees connecteurs.
- DataQualityAgent: score fraicheur/coherence.
- ContextBuilderAgent: compose contexte RAG minimal.
- PlanningAgent: propose plan 7 jours.
- AdaptationAgent: ajuste selon prevu/realise.
- SafetyPolicyAgent: applique limites de progressivite et alertes.
- BriefingAgent: produit messages coach/athlete.

## 10. Data Model (Minimal)
- profile: user_id, coach_id, level, timezone, preferences.
- goals: goal_id, user_id, objective, deadline, status, versions.
- constraints: user_id, available_slots, off_days, equipment.
- planned_sessions: session_id, user_id, date, type, target_duration, target_intensity.
- completed_sessions: source, date, duration, distance, hr, power, rpe.
- daily_metrics: readiness_score, load_7d, load_28d, freshness.
- ai_decisions: decision_id, timestamp, confidence, explanation, override.

## 11. Event Flows
- Initialisation objectif:
  1) intake -> 2) validation consent -> 3) first sync -> 4) plan initial -> 5) briefing.
- Ajustement quotidien:
  1) event recu (activite/calendrier) -> 2) quality check -> 3) adaptation -> 4) safety -> 5) briefing.

## 12. Risks and Mitigations
- Donnees manquantes: score de confiance + fallback conservateur.
- OAuth fragile: reconnect guide + monitoring erreurs par connecteur.
- Surcharge entrainement: regles hard de variation charge.
- Conformite: journal des consentements + retention/purge.

## 13. Success Metrics
- WAU/MAU.
- Taux adherence planifie vs realise.
- Temps coach economise par athlete/semaine.
- Taux acceptation recommandations sans override.
- Taux alertes securite pertinentes.

## 14. Compliance and Safety
- Produit bien-etre et performance non medicale.
- Disclaimer explicite au premier usage et lors de signaux critiques.
- Escalade vers professionnel de sante en cas de symptomes declaratifs.
