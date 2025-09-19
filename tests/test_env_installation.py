import os
from tests.env_test_utils import load_requirements, check_installed


def test_requirements_clean_present():
    assert os.path.exists('requirements-clean.txt'), 'requirements-clean.txt missing'


def test_packages_match_requirements():
    reqs = load_requirements('requirements-clean.txt')
    ok, details = check_installed(reqs)
    msgs = []
    for pkg, expected, found in details:
        msgs.append(f'{pkg}: expected={expected} found={found}')
    assert ok, 'Package versions do not match requirements-clean.txt:\n' + '\n'.join(msgs)
