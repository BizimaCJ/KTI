import pytest

from app.modules.incidents.models import IncidentStatus as S
from app.modules.incidents.status import can_transition


@pytest.mark.parametrize(
    "current,new",
    [(S.SUBMITTED, S.UNDER_REVIEW), (S.UNDER_REVIEW, S.VERIFIED), (S.VERIFIED, S.RESOLVED),
     (S.SUBMITTED, S.REJECTED), (S.UNDER_REVIEW, S.REJECTED)],
)
def test_allowed(current, new):
    assert can_transition(current, new)


@pytest.mark.parametrize(
    "current,new",
    [(S.SUBMITTED, S.VERIFIED), (S.SUBMITTED, S.RESOLVED), (S.VERIFIED, S.REJECTED),
     (S.RESOLVED, S.VERIFIED), (S.REJECTED, S.UNDER_REVIEW), (S.UNDER_REVIEW, S.SUBMITTED)],
)
def test_not_allowed(current, new):
    assert not can_transition(current, new)


def test_final_states_have_no_exit():
    for final in (S.RESOLVED, S.REJECTED):
        assert not any(can_transition(final, other) for other in S)
