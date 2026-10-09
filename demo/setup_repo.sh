#!/usr/bin/env bash
# Builds a throwaway repo whose last commit says "fix:" but removes a public function,
# and points shift-this-version at OpenRouter (key comes from $OPENROUTER_API_KEY).
set -euo pipefail

mkdir -p ~/.shift-this-version
cat > ~/.shift-this-version/config.json <<JSON
{"default_provider": "openrouter", "models": {"openrouter": "${DEMO_MODEL:-google/gemini-2.5-flash}"}}
JSON

rm -rf /tmp/demo-app && mkdir -p /tmp/demo-app && cd /tmp/demo-app
git init -q
git config user.email demo@example.com
git config user.name demo
git config commit.gpgsign false
git config tag.gpgsign false

cat > pyproject.toml <<'TOML'
[project]
name = "demo-app"
version = "1.4.2"
TOML

cat > settings.py <<'PY'
"""Public API of demo-app: load_config() and save_config() are used by downstream projects."""
import json

__all__ = ["load_config", "save_config"]


def load_config(path):
    with open(path) as f:
        return json.load(f)


def save_config(path, data):
    with open(path, "w") as f:
        json.dump(data, f)
PY

git add . && git commit -q -m "feat: config helpers"
git tag -a v1.4.2 -m v1.4.2

cat > settings.py <<'PY'
"""Public API of demo-app: load_config() and save_config() are used by downstream projects."""
import json

__all__ = ["save_config"]


def save_config(path, data):
    with open(path, "w") as f:
        json.dump(data, f)
PY
git commit -q -am "fix: tidy config module"
