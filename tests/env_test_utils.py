import pkg_resources
import subprocess
import json
from pathlib import Path


def load_requirements(req_path: str):
    lines = Path(req_path).read_text().splitlines()
    reqs = []
    for ln in lines:
        ln = ln.strip()
        if not ln or ln.startswith('#'):
            continue
        # skip URL wheel lines for now
        if ' @ ' in ln or ln.startswith('http'):
            # normalize by package==version if possible
            if '==' in ln:
                reqs.append(ln)
            continue
        reqs.append(ln)
    return reqs


def check_installed(reqs):
    """Return a tuple (ok:boolean, details:list) where details are (pkg, expected, found)"""
    details = []
    ok = True
    for r in reqs:
        if '==' in r:
            pkg, expected = r.split('==', 1)
        elif '>=' in r:
            pkg, expected = r.split('>=', 1)
        else:
            pkg = r
            expected = None
        try:
            dist = pkg_resources.get_distribution(pkg)
            found = dist.version
        except Exception:
            found = None
        details.append((pkg, expected, found))
        if expected and found != expected:
            ok = False
        if expected and found is None:
            ok = False
    return ok, details
