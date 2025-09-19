# Changelog

## 2025-09-19 — Replace non-portable pip freeze and CI updates

- Replaced a previously committed `requirements-lock.txt` that contained non-portable `file://` build references (from the environment where the freeze was produced).
- Added `requirements-clean.txt` (portable pip requirements) and updated docs and CI to use it.
- Kept `environment.yml` for exact conda reproduction (recommended for binary packages like PyTorch/NumPy).

Why this change?
- The original frozen requirements included local wheel/build paths that cause `pip install` to fail on other machines/runners.
- Two recommended options now:
  - Use `requirements-clean.txt` for quick pip installs (portable):

    ```bash
    python -m pip install --upgrade pip
    python -m pip install -r requirements-clean.txt
    ```

  - Use `environment.yml` to recreate the exact conda environment for binary parity (recommended for PyTorch):

    ```bash
    conda env create -f environment.yml
    conda activate py311_nlp
    ```

Notes
- The original non-portable freeze was archived in `archive/requirements-lock.orig.txt`. If you need the original dump, recover it from git history.

