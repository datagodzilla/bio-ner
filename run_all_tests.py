import sys
import subprocess
import json
import time
import os
from datetime import datetime


def run_cmd(cmd, env=None, capture=True):
    print(f'RUN: {cmd}')
    if capture:
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
        out, _ = p.communicate()
        return p.returncode, out.decode('utf-8', errors='replace')
    else:
        p = subprocess.Popen(cmd, shell=True, env=env)
        return 0, str(p.pid)


def wait_for_health(url='http://127.0.0.1:5050/health', timeout=30, poll=1):
    import requests
    t0 = time.time()
    last_exc = None
    while time.time() - t0 < timeout:
        try:
            r = requests.get(url, timeout=3)
            if r.status_code == 200:
                return True, r.text
            last_exc = f'status={r.status_code}'
        except Exception as e:
            last_exc = str(e)
        time.sleep(poll)
    return False, last_exc


def main():
    summary = {'started_at': datetime.utcnow().isoformat() + 'Z', 'results': {}}

    # 0) Run package installation tests first
    rc, out = run_cmd('python -m pytest tests/test_env_installation.py -q')
    summary['results']['env_installation'] = {'rc': rc, 'output': out}

    # Start the Flask app in background
    env = os.environ.copy()
    env.update({'TRANSFORMERS_OFFLINE': '1', 'HF_DATASETS_OFFLINE': '1', 'HF_HOME': os.path.join(os.getcwd(), '.hf_home')})
    # start server and capture output to a log file
    logfile = open('server_run.log', 'w')
    server_proc = subprocess.Popen([sys.executable, 'app.py', '5050'], stdout=logfile, stderr=subprocess.STDOUT, env=env)
    summary['server_pid'] = server_proc.pid
    print('Started server pid', server_proc.pid)

    try:
        ok, info = wait_for_health(timeout=45)
        summary['results']['flask_health_check'] = {'ok': ok, 'info': info}

        if not ok:
            # capture current server log
            logfile.flush()
            with open('server_run.log', 'r') as fh:
                summary['results']['server_log_tail'] = fh.read()[-5000:]
        # run flask health pytest (will do HTTP GET to /health)
        rc, out = run_cmd('python -m pytest tests/test_flask_health.py -q')
        summary['results']['flask_health'] = {'rc': rc, 'output': out}

        # run models offline tests
        rc, out = run_cmd('python -m pytest tests/test_models_offline.py -q')
        summary['results']['models_offline'] = {'rc': rc, 'output': out}

    finally:
        # stop server
        try:
            server_proc.terminate()
            server_proc.wait(timeout=5)
        except Exception:
            try:
                server_proc.kill()
            except Exception:
                pass
        logfile.close()

    summary['finished_at'] = datetime.utcnow().isoformat() + 'Z'
    with open('test_run_summary.json', 'w') as fh:
        json.dump(summary, fh, indent=2)

    any_fail = any((v.get('rc', 0) != 0) or (v.get('ok') is False) for v in summary['results'].values())
    print(json.dumps(summary, indent=2))
    sys.exit(1 if any_fail else 0)


if __name__ == '__main__':
    main()
