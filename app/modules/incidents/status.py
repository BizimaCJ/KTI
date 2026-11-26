"""Incident status rules (SRS section 4.3.1). Used by the admin workflow in a later slice."""
from app.modules.incidents.models import IncidentStatus as S

ALLOWED_TRANSITIONS = {
    S.SUBMITTED: {S.UNDER_REVIEW, S.REJECTED},
    S.UNDER_REVIEW: {S.VERIFIED, S.REJECTED},
    S.VERIFIED: {S.RESOLVED},
    S.RESOLVED: set(),   # final
    S.REJECTED: set(),   # final
}


def can_transition(current: S, new: S) -> bool:
    return new in ALLOWED_TRANSITIONS[current]
