import sys
import subprocess
import json
from datetime import datetime


def run_cmd(cmd, env=None):
    print(f'RUN: {cmd}')
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
    out, _ = p.communicate()
    return p.returncode, out.decode('utf-8', errors='replace')


def main():
    summary = {
        'started_at': datetime.utcnow().isoformat() + 'Z',
        'results': {}
    }

    # 1) Check package installation
    rc, out = run_cmd('python -m pytest tests/test_env_installation.py -q')
    summary['results']['env_installation'] = {'rc': rc, 'output': out}

    # 2) Check Flask health (assumes app is running locally)
    rc, out = run_cmd('python -m pytest tests/test_flask_health.py -q')
    summary['results']['flask_health'] = {'rc': rc, 'output': out}

    # 3) Check models offline
    rc, out = run_cmd('python -m pytest tests/test_models_offline.py -q')
    summary['results']['models_offline'] = {'rc': rc, 'output': out}

    summary['finished_at'] = datetime.utcnow().isoformat() + 'Z'

    with open('test_run_summary.json', 'w') as fh:
        json.dump(summary, fh, indent=2)

    # Print summary and exit non-zero if any rc != 0
    any_fail = any(v['rc'] != 0 for v in summary['results'].values())
    print(json.dumps(summary, indent=2))
    sys.exit(1 if any_fail else 0)


if __name__ == '__main__':
    main()
