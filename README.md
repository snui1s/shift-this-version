# shift-this-version

> Smart SemVer bumper driven by code diff and AI.

`shift-this-version` is an automated release utility that inspects Git diffs and commit histories since the last release tag. Using LLMs (Google Gemini, OpenRouter, OpenAI, DeepSeek, Groq, or local Ollama instances), it analyzes code modifications against the [SemVer 2.0.0](https://semver.org/) specification to recommend the appropriate version increment (`major`, `minor`, `patch`).

The tool updates version fields in standard project configurations (`pyproject.toml`, `package.json`, `Cargo.toml`, `setup.cfg`) as well as designated version variables directly within source code (e.g., `VERSION = "1.0.0"`, `export const VERSION = "1.0.0"`, `__version__ = "1.0.0"`). It also manages Git commits, release tags, and remote pushes.

## Table of Contents

- [Background](#background)
- [Install](#install)
- [Usage](#usage)
  - [1. First-Time Setup Wizard](#1-first-time-setup-wizard)
  - [2. Inspect Repository](#2-inspect-repository)
  - [3. Shift Version](#3-shift-version)
    - [Standard Run (Zero Flags Needed)](#31-standard-run-zero-flags-needed)
    - [Dry-Run Mode](#32-dry-run-mode)
    - [Interactive Confirmation Stages](#33-interactive-confirmation-stages)
    - [Manual SemVer Mode (No AI Required)](#34-manual-semver-mode-no-ai-required)
    - [Provider Options (Optional Overrides)](#35-provider-options-optional-overrides)
    - [Custom Code Variables](#36-custom-code-variables)
    - [Disable Commit, Tag, or Push](#37-disable-commit-tag-or-push)
    - [CI/CD Integration](#38-cicd-integration)
  - [4. Command Reference](#4-command-reference)
- [API](#api)
- [Security](#security)
- [Contributing](#contributing)
- [License](#license)

## Background

Traditional version-bumping tools either require manual developer input (e.g. choosing between patch, minor, or major) or rely strictly on Conventional Commit messages. In reality, commit histories can be incomplete or inaccurate, increasing the risk of unflagged breaking changes or improper releases.

`shift-this-version` solves this by examining actual source code diffs:
- Noise reduction: automatically ignores lockfiles, minified bundles, documentation, and image assets.
- Token management: summarizes and truncates large diffs using `git diff --stat` to prevent context window overflow.
- Semantic evaluation: prompts the AI to identify API signature breaks, additions, bug fixes, and non-functional changes.
- Fallback resilience: operates seamlessly in manual mode when offline or when no AI provider is configured.

## Install

### Requirements
- Python >= 3.10
- Git CLI accessible in PATH

### Via uv or pip
```sh
# Install as a global CLI tool
uv tool install shift-this-version

# Or install via pip
pip install shift-this-version
```

### Local Development Setup
```sh
git clone https://github.com/snui1s/shift-this-version.git
cd shift-this-version
uv sync
```

## Usage

### 1. First-Time Setup Wizard

Run `shift-this-version` with no arguments on first use. The interactive setup wizard guides you through selecting your preferred AI provider, securely storing your configuration in `~/.shift-this-version/config.json`:

```sh
shift-this-version
```

#### What the wizard does:
1. **Presents Provider Categories**: Choose from 4 groups:
   - Group 1 (Direct Cloud Giants): Google Gemini, Anthropic Claude, OpenAI
   - Group 2 (High-Speed & Value Powerhouses): DeepSeek, Groq
   - Group 3 (Universal Hub): OpenRouter (Access 200+ models with 1 key)
   - Group 4 (Local & Self-Hosted): Ollama, Custom OpenAI-Compatible
2. **Prompts for Provider Credentials**:
   - For Cloud providers: Prompts for API key (securely masked)
   - For OpenRouter: Prompts for API key and lets you specify any model
   - For Ollama: Prompts only for the Host URL (defaults to `http://localhost:11434`, no API key needed)
   - For Custom endpoints: Prompts for Base URL, model name, and optional key
3. **Saves Configuration**: Saves settings securely to `~/.shift-this-version/config.json`.
4. **Displays Quick-Start Guide**: Shows next recommended commands.

To reconfigure your provider or update your API key at any time, run:
```sh
shift-this-version config
```

*(Optional: You can also supply keys via environment variables such as `GEMINI_API_KEY`, `OPENROUTER_API_KEY`, or `OPENAI_API_KEY` for CI/CD environments.)*

---

### 2. Inspect Repository

Verify the current Git state, recent commits, diff summary, and all detected version targets:

```sh
shift-this-version inspect
```

#### Sample Output:
```text
── 1. Git State ──────────────────────────────────────────
┌───────────────────────────────── Git State ─────────────────────────────────┐
│ Latest Tag: v0.1.0                                                          │
│ Commits Ahead: 2 commits ahead                                              │
└─────────────────────────────────────────────────────────────────────────────┘

── 2. Detected Version Files & Variables ─────────────────
Targets Found in Project:
┌──────────┬─────────────────────────┬──────┬─────────────────┬───────────────┐
│ Type     │ File Path               │ Line │ Current Version │ Snippet       │
├──────────┼─────────────────────────┼──────┼─────────────────┼───────────────┤
│ config   │ pyproject.toml          │    3 │ 0.1.0           │ version = …   │
│ code_var │ frontend/src/config.ts  │    8 │ 0.1.0           │ const VERSION…│
└──────────┴─────────────────────────┴──────┴─────────────────┴───────────────┘

Recent Commits:
  • feat: add OAuth2 login handler
  • fix: correct button padding

── 3. Changed Files Summary ──────────────────────────────
pyproject.toml         |  2 +-
frontend/src/config.ts |  2 +-
2 files changed, 2 insertions(+), 2 deletions(-)

── 4. Latest Uncommitted Changes ─────────────────────────
diff --git a/frontend/src/config.ts b/frontend/src/config.ts
...
```

---

### 3. Shift Version

#### 3.1 Standard Run (Zero Flags Needed)
Run `shift-this-version shift` to analyze code changes with AI, bump version files, commit, tag, and push to remote automatically using your saved AI configuration:

```sh
shift-this-version shift
```

#### 3.2 Dry-Run Mode
Simulate the AI evaluation without modifying any files or Git state:

```sh
shift-this-version shift --dry-run
```

#### 3.3 Interactive Confirmation Stages
When running `shift-this-version shift`, the CLI guides you through 5 discrete confirmation stages:

1. **AI Recommendation Display**:
   ```text
   ╭───────────────────── AI Recommendation: MINOR ──────────────────────╮
   │ Current Version: 0.1.0                                              │
   │ Suggested Version: 0.2.0  (MINOR shift)                             │
   │ Confidence: 95.0%                                                   │
   │                                                                     │
   │ Reasoning:                                                          │
   │ Added OAuth login support without breaking existing endpoints.      │
   │                                                                     │
   │ Key Changes:                                                        │
   │   • Added Google OAuth login handler                                │
   ╰─────────────────────────────────────────────────────────────────────╯

   Files to update:
     • pyproject.toml:3 (0.1.0 -> 0.2.0)
     • frontend/src/config.ts:8 (0.1.0 -> 0.2.0)
   ```

2. **Stage-by-Stage Confirmation**:
   - **Stage 1 (Version)**: Confirm `0.2.0` across all target files `[Y/n]` (enter `n` to provide a custom version).
   - **Stage 2 (Git Commit)**: Confirm creating a Git commit `[Y/n]`.
   - **Stage 3 (Commit Message)**: Accept default message (`chore(release): shift version to 0.2.0`) or provide a custom message.
   - **Stage 4 (Git Tag)**: Confirm creating Git tag `v0.2.0` `[Y/n]` (automatically warns if tag already exists).
   - **Stage 5 (Git Push)**: Confirm pushing branch and tag to remote repository `[Y/n]`.

```text
  Updated pyproject.toml -> 0.2.0
  Updated frontend/src/config.ts -> 0.2.0
  Git committed: 'chore(release): shift version to 0.2.0'
  Created Git Tag: v0.2.0
  Pushed to remote: main & v0.2.0

Successfully shifted version to 0.2.0!
```

*(Note: Automatic pushing is enabled by default. Use `--no-push` if you prefer to push manually.)*

#### 3.4 Manual SemVer Mode (No AI Required)
If you are working offline, have not configured an AI provider, or prefer to choose the SemVer bump yourself, use the `--manual` flag:

```sh
shift-this-version shift --manual
```

The tool also falls back to manual mode automatically if your AI provider is unreachable or unconfigured.

```text
╭──────────────── Manual Version Shift (No AI) ────────────────╮
│ Current Version: 0.1.0                                       │
│                                                              │
│   [1] Patch  ➔ 0.1.1  (Bug fixes, backwards-compatible)      │
│   [2] Minor  ➔ 0.2.0  (New features, backwards-compatible)   │
│   [3] Major  ➔ 1.0.0  (Breaking changes, major redesign)     │
│   [4] Custom ➔ Enter a custom version string                 │
│   [0] Cancel                                                 │
╰──────────────────────────────────────────────────────────────╯
Select bump level [1/2/3/4/0] (1): 
```

After selection, it proceeds through the same 5 confirmation stages (Version -> Commit -> Commit Message -> Tag -> Push).

#### 3.5 Provider Options (Optional Overrides)
You can optionally override your saved default provider or model for a single run:

- **Group 1: Direct Cloud Giants**
  ```sh
  # Google Gemini (Default: gemini-2.5-flash)
  shift-this-version shift -p gemini -m gemini-2.5-flash

  # Anthropic Claude (Default: claude-3-5-haiku-20241022)
  shift-this-version shift -p anthropic -m claude-3-5-sonnet-20241022

  # OpenAI (Default: gpt-4o-mini)
  shift-this-version shift -p openai -m gpt-4o
  ```

- **Group 2: High-Speed & Value Powerhouses**
  ```sh
  # DeepSeek (Default: deepseek-chat)
  shift-this-version shift -p deepseek -m deepseek-chat

  # Groq (Default: llama-3.3-70b-versatile)
  shift-this-version shift -p groq -m llama-3.3-70b-versatile
  ```

- **Group 3: Universal Hub**
  ```sh
  # OpenRouter (Choose any model available on openrouter.ai)
  shift-this-version shift -p openrouter -m anthropic/claude-3.5-haiku
  shift-this-version shift -p openrouter -m deepseek/deepseek-chat
  ```

- **Group 4: Local & Self-Hosted**
  ```sh
  # Ollama: Specify host URL (no API key needed)
  shift-this-version shift -p ollama --host http://localhost:11434

  # Custom OpenAI-Compatible Endpoint (LM Studio, vLLM, LocalAI)
  shift-this-version shift -p custom --host http://localhost:1234/v1 -m local-model
  ```

#### 3.6 Custom Code Variables
Target specific variable names defined in frontend or backend code:
```sh
shift-this-version shift --var APP_VERSION --var RELEASE_VERSION
```

#### 3.7 Disable Commit, Tag, or Push
Disable Git commit, tag generation, or remote push when needed:
```sh
# Update version files only without creating git commits, tags, or pushing
shift-this-version shift --no-tag --no-commit --no-push
```

#### 3.8 CI/CD Integration
For non-interactive pipelines (GitHub Actions, GitLab CI), use `--yes` or `-y`:

```sh
shift-this-version shift -p gemini --yes
```

##### GitHub Actions Workflow Example (`.github/workflows/release.yml`):
```yaml
name: AI Version Shift

on:
  push:
    branches:
      - main

jobs:
  shift-version:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install shift-this-version
        run: pip install shift-this-version

      - name: Run AI Shift
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: |
          shift-this-version shift --yes -p gemini
          git push --tags
```

---

### 4. Command Reference

| Command | Description |
| :--- | :--- |
| `shift-this-version` | Run setup wizard on first run, or show provider status and commands overview |
| `shift-this-version shift` | Analyze diff with AI and shift SemVer across targets |
| `shift-this-version shift --manual` | Run interactive SemVer bump without AI |
| `shift-this-version shift --dry-run` | Preview AI recommendation without modifying files |
| `shift-this-version shift -y` | Non-interactive auto-confirm mode for CI/CD |
| `shift-this-version inspect` | Inspect Git diff, commit history, and detected version targets |
| `shift-this-version config` | Reconfigure default provider, API key, model, or host |
| `shift-this-version help` | Display detailed command guide and usage examples |

---

## API

`shift-this-version` can also be integrated into custom automation scripts as a Python library:

```python
import shift_this_version as stv

# 1. Locate version files and variables
targets = stv.find_version_targets()

# 2. Retrieve Git context
tag = stv.get_latest_tag()
diff = stv.get_filtered_diff(tag=tag)
commits = stv.get_commits_since(tag=tag)

# 3. Analyze changes via AI
analysis = stv.analyze(
    diff=diff,
    commits=commits,
    provider="gemini"
)

print(f"Recommendation: {analysis.bump_type}")
print(f"Reasoning: {analysis.reasoning}")
print(f"Breaking Changes: {analysis.breaking_changes}")

# 4. Compute next version and update files
current_version = targets[0].current_version
next_version = stv.calculate_next_version(current_version, analysis.bump_type)

for target in targets:
    stv.apply_version_bump(target, next_version)
```

## Security

- API keys are stored locally in `~/.shift-this-version/config.json` with restricted user permissions, or read from environment variables. Keys are never logged or transmitted except to your chosen provider endpoint.
- Git diff extraction excludes ignored directories (`.git`, `.venv`, `node_modules`), secrets, and common binary/image assets.
- For private or sensitive source code, use the local `ollama` provider to ensure data remains strictly on your local machine.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Run the test suite before submitting changes:
```sh
python tests/test_core.py
```

## License

[MIT](LICENSE)
