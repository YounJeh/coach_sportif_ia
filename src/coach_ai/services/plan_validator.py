from __future__ import annotations

from collections import Counter
from datetime import date

from coach_ai.models import GoalInput, PlanValidation, TrainingPlan, ValidationIssue


def validate_plan(goal: GoalInput, plan: TrainingPlan) -> PlanValidation:
    issues: list[ValidationIssue] = []

    if not plan.sessions:
        issues.append(
            ValidationIssue(
                code="EMPTY_PLAN",
                severity="error",
                message="Le programme ne contient aucune seance.",
            )
        )
        return PlanValidation(valid=False, issues=issues)

    dates = [session.session_date for session in plan.sessions]

    duplicate_dates = [
        session_date
        for session_date, count in Counter(dates).items()
        if count > 1
    ]

    for duplicate_date in duplicate_dates:
        issues.append(
            ValidationIssue(
                code="DUPLICATE_SESSION_DATE",
                severity="warning",
                message=f"Plusieurs seances sont prevues le {duplicate_date.isoformat()}.",
            )
        )

    today = date.today()
    for index, session in enumerate(plan.sessions):
        if session.session_date < today:
            issues.append(
                ValidationIssue(
                    code="PAST_DATE",
                    severity="error",
                    session_index=index,
                    message="La seance est planifiee dans le passe.",
                )
            )

        if session.session_date > goal.deadline:
            issues.append(
                ValidationIssue(
                    code="AFTER_DEADLINE",
                    severity="error",
                    session_index=index,
                    message="La seance est posterieure a l'echeance.",
                )
            )

        if (
            goal.max_session_duration_min is not None
            and session.duration_min > goal.max_session_duration_min
        ):
            issues.append(
                ValidationIssue(
                    code="DURATION_EXCEEDED",
                    severity="error",
                    session_index=index,
                    message=(
                        f"La seance dure {session.duration_min} minutes, "
                        f"contre une limite de {goal.max_session_duration_min} minutes."
                    ),
                )
            )

        if session.target_rpe >= 9:
            issues.append(
                ValidationIssue(
                    code="VERY_HIGH_INTENSITY",
                    severity="warning",
                    session_index=index,
                    message="La seance prevoit une intensite tres elevee.",
                )
            )

        total_blocks = len(session.warmup) + len(session.main_work) + len(session.cooldown)
        if total_blocks == 0:
            issues.append(
                ValidationIssue(
                    code="EMPTY_SESSION",
                    severity="error",
                    session_index=index,
                    message="La seance ne contient aucun bloc.",
                )
            )

    error_count = sum(issue.severity == "error" for issue in issues)
    return PlanValidation(valid=error_count == 0, issues=issues)
