# CLI User Guide (`shift-this-version`)

Comprehensive guide and reference for using `shift-this-version` from the command line.

---

## Table of Contents
1. [First-Time Setup Wizard](#1-first-time-setup-wizard)
2. [Command: `inspect`](#2-command-inspect)
3. [Command: `shift`](#3-command-shift)
4. [Command: `help`](#4-command-help)
5. [Advanced Options & Providers](#5-advanced-options--providers)
6. [CI/CD Integration](#6-cicd-integration)

---

## 1. First-Time Setup Wizard

Run `shift-this-version` with no arguments on first use. The interactive setup wizard will guide you through configuration:

```bash
shift-this-version
```

### What the wizard does:
1. **Presents Provider Categories**: Choose from 4 groups:
   - Group 1 (Direct Cloud Giants): Google Gemini, Anthropic Claude, OpenAI
   - Group 2 (High-Speed & Value Powerhouses): DeepSeek, Groq
   - Group 3 (Universal Hub): OpenRouter (Access 200+ models with 1 key)
   - Group 4 (Local & Self-Hosted): Ollama, Custom OpenAI-Compatible
2. **Prompts for Provider Credentials**:
   - For Cloud providers: Prompts for API key (securely masked)
   - For OpenRouter: Prompts for API key and lets you specify any model
   - For Ollama: Prompts **only for the Host URL** (defaults to `http://localhost:11434`, no API key needed!)
   - For Custom endpoints: Prompts for Base URL, model name, and optional key
3. **Saves Configuration**: Saves settings securely to `~/.shift-this-version/config.json`.
4. **Displays Quick-Start Guide**: Shows next recommended commands.

> Note: To change providers, models, or keys at any time, run:  
> `shift-this-version config`

---

## 2. Command: `inspect`

Scan Git history, commit count, code diff preview, and all detected version files and variables:

```bash
shift-this-version inspect
```

### Sample Output:
```text
┌───────────────────────────────── Git State ─────────────────────────────────┐
│ Latest Tag: v0.1.0                                                          │
│ Commits Ahead: 2                                                            │
└─────────────────────────────────────────────────────────────────────────────┘
               Detected Version Targets (Files & Code Variables)               
┌──────────┬─────────────────────────┬──────┬─────────────────┬───────────────┐
│ Type     │ File Path               │ Line │ Current Version │ Snippet       │
├──────────┼─────────────────────────┼──────┼─────────────────┼───────────────┤
│ config   │ pyproject.toml          │    3 │ 0.1.0           │ version = …   │
│ code_var │ frontend/src/config.ts  │    8 │ 0.1.0           │ const VERSION…│
└──────────┴─────────────────────────┴──────┴─────────────────┴───────────────┘

Recent Commits:
  • feat: add OAuth2 login handler
  • fix: correct button padding

Filtered Diff Size: 1,420 characters
```

---

## 3. Command: `shift` (Standard Usage)

Once initial setup is complete, running `shift-this-version shift` automatically analyzes your Git diff and commits using your saved AI provider and model:

```bash
# Standard shift (uses your saved AI configuration from setup - no flags needed!)
shift-this-version shift
```

### 3.1 Dry-Run Mode (Preview without modifying files)
```bash
# Preview AI recommendation safely:
shift-this-version shift --dry-run
```

### 3.2 Interactive Confirmation (Default)
When you run `shift-this-version shift`:

**Workflow:**
1. AI analyzes diff and commits.
2. Displays structured recommendation:
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
3. Prompts for confirmation:
   ```text
   Do you want to shift version to 0.2.0 across 2 targets? [Y/n]: y
   ```
4. Updates files, commits changes, creates Git tag, and pushes to remote:
   ```text
     Updated pyproject.toml
     Updated frontend/src/config.ts
     Git committed: 'chore(release): shift version to 0.2.0'
     Created Git Tag: v0.2.0
     Pushed to remote: main & v0.2.0

   Successfully shifted version to 0.2.0!
   ```

   *(Note: Automatic pushing is enabled by default. Use `--no-push` if you want to push manually.)*

### 3.3 Manual SemVer Mode (No AI Required)
If you are working offline, have not configured an AI provider, or simply prefer to select the bump level yourself:

```bash
shift-this-version shift --manual
```

This presents a fast interactive selection:
- `[1] Patch  -> 1.2.4 (Bug fixes, backwards-compatible)`
- `[2] Minor  -> 1.3.0 (New features, backwards-compatible)`
- `[3] Major  -> 2.0.0 (Breaking changes, major redesign)`
- `[4] Custom -> Enter custom version string`

After choosing, it flows directly into the 5 discrete release confirmation stages (Version -> Commit -> Commit Message -> Tag -> Push).

---

## 4. Command: `help`

Display usage guide and command syntax:

```bash
# General help and examples
shift-this-version help

# Command-specific help
shift-this-version help shift
shift-this-version help inspect
shift-this-version help config
```

---

## 5. Advanced Options & Providers

### Provider Selection:

#### Group 1: Direct Cloud Giants
```bash
# Google Gemini
shift-this-version shift -p gemini -m gemini-2.5-flash

# Anthropic Claude
shift-this-version shift -p anthropic -m claude-3-5-sonnet-20241022

# OpenAI
shift-this-version shift -p openai -m gpt-4o
```

#### Group 2: High-Speed & Value Powerhouses
```bash
# DeepSeek
shift-this-version shift -p deepseek -m deepseek-chat

# Groq
shift-this-version shift -p groq -m llama-3.3-70b-versatile
```

#### Group 3: Universal Hub (OpenRouter)
```bash
# Specify any model available on openrouter.ai
shift-this-version shift -p openrouter -m anthropic/claude-3.5-haiku
shift-this-version shift -p openrouter -m deepseek/deepseek-chat
```

#### Group 4: Local & Self-Hosted
```bash
# Ollama: Specify host URL (no API key needed!)
shift-this-version shift -p ollama --host http://localhost:11434

# Custom OpenAI-compatible endpoint (LM Studio, vLLM, LocalAI)
shift-this-version shift -p custom --host http://localhost:1234/v1 -m local-model
```

### Custom Code Variables (`--var`)
If your project uses non-standard variable names in code:
```bash
shift-this-version shift --var RELEASE_VER --var APP_VERSION
```

### Disable Git Commit or Tag
```bash
# Modify version files only without creating git tags or commits
shift-this-version shift --no-tag --no-commit
```

---

## 6. CI/CD Integration

For non-interactive pipelines (GitHub Actions, GitLab CI):

```bash
shift-this-version shift -p gemini --yes
```

### GitHub Actions Workflow Example (`.github/workflows/release.yml`):
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
