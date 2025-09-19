# Contributing — Reproducing the Development Environment
k

This project uses a mixed conda + pip workflow to ensure reproducible binaries for compiled packages (PyTorch, NumPy, spaCy) while keeping Python-only packages managed with `pip`.

Reproduce the environment locally (recommended):

```bash
# 1) Create and activate conda env with the same Python version
conda create -n py311_nlp python=3.11 -y
conda activate py311_nlp

# 2) Install binary packages via conda (recommended)
conda install -c pytorch -c conda-forge pytorch=2.6 cpuonly -y

# 3) Install Python packages via pip
# For pip-based installs use the cleaned, portable requirements file:
python -m pip install -r requirements-clean.txt

# 4) (Optional) install spaCy English model
python -m spacy download en_core_web_sm

# 5) If you need exact conda reproduction, use the exported file
conda env create -f environment.yml
```

Running the app offline

```bash
conda activate py311_nlp
# set offline flags and start the app on port 5050
./run_offline.sh 5050
```

Testing

- Run unit tests locally: `pytest tests/offline_test.py -q`
 - If you need exact binary parity (recommended for PyTorch/NumPy), recreate the conda env:

```bash
conda env create -f environment.yml
conda activate py311_nlp
```
- CI runs a lightweight offline smoke test on pushes and PRs to `main` using GitHub Actions.

Contributions

- Please open a PR against `main`. The CI workflow will run the offline smoke tests. If you'd prefer, request that maintainers open the PR for you.
