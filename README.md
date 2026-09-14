# shift-this-version

> Smart SemVer bumper driven by code diff and AI.

`shift-this-version` is an automated release utility that inspects Git diffs and commit histories since the last release tag. Using LLMs (Google Gemini, OpenRouter, OpenAI, or local Ollama instances), it analyzes code modifications against the [SemVer 2.0.0](https://semver.org/) specification to recommend the appropriate version increment (`major`, `minor`, `patch`).

The tool updates version fields in standard project configurations (`pyproject.toml`, `package.json`, `Cargo.toml`, `setup.cfg`) as well as designated version variables directly within source code (e.g., `VERSION = "1.0.0"`, `export const VERSION = "1.0.0"`, `__version__ = "1.0.0"`). It also manages optional Git commits and Git release tags.

## Table of Contents

- [Background](#background)
- [Install](#install)
- [Usage](#usage)
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

## Install

### Requirements
- Python >= 3.14 (or a compatible modern Python runtime)
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

Run `shift-this-version` with no arguments on first use. The interactive setup wizard will welcome you, prompt for your preferred AI provider, save your API key securely to `~/.shift-this-version/config.json`, and print a quick-start guide:

```sh
shift-this-version
```

To reconfigure your provider or update your API key at any time, run:
```sh
shift-this-version config
```

*(Optional: You can also supply keys via environment variables such as `GEMINI_API_KEY`, `OPENROUTER_API_KEY`, or `OPENAI_API_KEY` for CI/CD environments.)*


### 2. Inspect Repository

Verify the current Git state, recent commits, filtered diff preview, and detected version targets:

```sh
shift-this-version inspect
```

### 3. Shift Version

#### Interactive Mode (Default)
Analyzes the diff, displays the recommendation and rationale, and prompts for confirmation before applying changes:
```sh
shift-this-version shift
```

#### Dry-Run Mode
Simulate the AI evaluation without modifying any files or Git state:
```sh
shift-this-version shift --dry-run
```

#### Specify Provider, Model, or Host

Providers are organized into 4 categories:

- **Group 1: Direct Cloud Giants**
  ```sh
  # Google Gemini (Default: gemini-2.5-flash)
  shift-this-version shift --provider gemini --model gemini-2.5-flash

  # Anthropic Claude (Default: claude-3-5-haiku-20241022)
  shift-this-version shift --provider anthropic --model claude-3-5-sonnet-20241022

  # OpenAI (Default: gpt-4o-mini)
  shift-this-version shift --provider openai --model gpt-4o
  ```

- **Group 2: High-Speed & Value Powerhouses**
  ```sh
  # DeepSeek (Default: deepseek-chat)
  shift-this-version shift --provider deepseek --model deepseek-chat

  # Groq (Default: llama-3.3-70b-versatile)
  shift-this-version shift --provider groq --model llama-3.3-70b-versatile
  ```

- **Group 3: Universal Hub**
  ```sh
  # OpenRouter (Choose any model available on openrouter.ai)
  shift-this-version shift --provider openrouter --model anthropic/claude-3.5-haiku
  shift-this-version shift --provider openrouter --model deepseek/deepseek-chat
  ```

- **Group 4: Local & Self-Hosted**
  ```sh
  # Ollama (Local LLM via custom host URL and model)
  shift-this-version shift --provider ollama --host http://localhost:11434 --model llama3.2

  # Custom OpenAI-Compatible Endpoint (LM Studio, vLLM, LocalAI)
  shift-this-version shift --provider custom --host http://localhost:1234/v1 --model local-model
  ```


#### Custom Code Variables
Target specific variable names defined in frontend or backend code:
```sh
shift-this-version shift --var APP_VERSION --var RELEASE_VERSION
```

#### Non-Interactive CI/CD Mode
Automatically apply version updates, Git commit, and Git tag without confirmation prompts:
```sh
shift-this-version shift --yes --provider gemini
```

Disable Git commit or tag generation if needed:
```sh
shift-this-version shift --no-tag --no-commit
```

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

- API keys are read from environment variables or explicit parameters and are never written to disk or logged.
- Git diff extraction excludes ignored directories (`.git`, `.venv`, `node_modules`), secrets, and common configuration files.
- For private or sensitive source code, use the local `ollama` provider to ensure data remains strictly on your local machine.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Run the test suite before submitting changes:
```sh
python tests/test_core.py
```

## License

[MIT](LICENSE)
