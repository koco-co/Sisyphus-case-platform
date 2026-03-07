import pytest

from app.common.auth import PermissionDeniedError, require_role


def test_require_role_allows_matching_role():
    assert require_role(['tester', 'test_lead'], 'test_lead') == 'test_lead'


def test_require_role_raises_for_missing_role():
    with pytest.raises(PermissionDeniedError):
        require_role(['tester'], 'admin')
