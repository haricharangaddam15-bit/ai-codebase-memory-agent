#!/usr/bin/env bash
set -e

echo "=== AI Codebase Memory Agent setup check ==="
echo

python --version
git --version
node --version
npm --version
gh --version | head -1

echo
echo "Python environment:"
python -c "import fastapi, pydantic, github; print('FastAPI/Pydantic/PyGithub: OK')"

echo
echo "Project root:"
pwd

echo
echo "Setup check complete."
