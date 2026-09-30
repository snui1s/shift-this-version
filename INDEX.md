# Codebase Symbol Index

## bin/run.js
- const `fs` @13
- const `path` @14
- const `os` @15
- const `https` @16
- const `http` @17
- const `{ spawn, spawnSync }` @18
- const `pkg` @20
- const `VERSION` @21
- const `GITHUB_REPO` @22
- function `commandExists()` @24 (calls: `spawnSync`)
- function `runCommand()` @35 (calls: `spawn`, `child.on`, `process.kill`, `process.exit`, `fallbackToStandaloneBinary`, `process.argv.slice`)
- function `getBinaryName()` @50
- function `downloadFile()` @66 (calls: `url.startsWith`, `on`, `client.get`, `downloadFile`, `callback`, `Error`, `parseInt`, `fs.createWriteStream`, `res.on`, `Math.round`, `process.stderr.write`, `toFixed`, `res.pipe`, `fileStream.on`, `fileStream.close`, `fs.unlink`)
- function `fallbackToStandaloneBinary()` @105 (calls: `getBinaryName`, `console.error`, `process.exit`, `path.join`, `os.homedir`, `fs.mkdirSync`, `fs.existsSync`, `runCommand`, `downloadFile`, `fs.chmodSync`)
- function `main()` @146 (calls: `process.argv.slice`, `console.log`, `commandExists`, `runCommand`, `fallbackToStandaloneBinary`)

## examples/custom_release.py
- `run_custom_release_pipeline()` @15 (calls: `print`, `stv.find_version_targets`, `len`, `simulated_result_type.upper`, `stv.calculate_next_version`, `stv.apply_version_bump`)

## run_tests.py
- `main()` @10 (calls: `print`, `pytest.main`, `sys.exit`, `subprocess.run`)

## shift_this_version/analyzer.py
- class `BumpAnalysis` @9
  - `normalize_input()` @37 (calls: `isinstance`, `err.get`, `str`, `inner.items`, `data.setdefault`, `strip`, `lower`, `data.get`, `float`, `max`, `min`; raises: `ValueError`)
- `extract_json_from_text()` @158: ทำความสะอาดและแปลงข้อความตอบกลับจาก LLM ให้เป็น JSON dict อย่างแม่นยำและทนทาน (calls: `text.strip`, `strip`, `re.sub`, `re.search`, `match.group`, `json.loads`, `isinstance`, `cleaned.find`, `cleaned.rfind`, `len`; raises: `ValueError`)
- `get_key_for_provider()` @215: ดึง API Key ตามลำดับความสำคัญ: (calls: `provider.lower`, `config.get_configured_key`, `env_names.get`, `os.getenv`)
- `is_ollama_running()` @248: Check if local Ollama daemon is reachable with a fast 1.0s timeout. (calls: `httpx.Client`, `client.get`, `host.rstrip`)
- `detect_default_provider()` @257: ตรวจจับ provider และ key ที่พร้อมใช้งานอัตโนมัติ (calls: `config.get_default_provider`, `get_key_for_provider`, `config.get_configured_host`, `os.getenv`, `is_ollama_running`)
- `call_gemini()` @282: เรียก Google Gemini REST API (calls: `join`, `httpx.Client`, `client.post`, `resp.raise_for_status`, `resp.json`, `extract_json_from_text`, `BumpAnalysis`)
- `call_anthropic()` @305: เรียก Anthropic Claude Messages REST API (calls: `join`, `httpx.Client`, `client.post`, `resp.raise_for_status`, `resp.json`, `extract_json_from_text`, `BumpAnalysis`)
- `call_openai_compatible()` @331: เรียก OpenAI-compatible API (รองรับ OpenAI, OpenRouter, DeepSeek, Groq, Custom) (calls: `headers.update`, `base_url.rstrip`, `join`, `httpx.Client`, `client.post`, `resp.text.lower`, `payload.pop`, `resp.raise_for_status`, `resp.json`, `err.get`, `str`, `isinstance`, `data.get`, `get`, `msg.get`, `extract_json_from_text`, `BumpAnalysis`; raises: `ValueError`)
- `call_ollama()` @381: เรียก Ollama Local REST API (calls: `host.rstrip`, `join`, `httpx.Client`, `client.post`, `resp.raise_for_status`, `resp.json`, `extract_json_from_text`, `BumpAnalysis`)
- `analyze()` @403: ฟังก์ชันหลักสำหรับส่ง Diff ไปให้ AI วิเคราะห์ (calls: `detect_default_provider`, `provider.lower`, `config.get_configured_model`, `config.get_configured_host`, `get_key_for_provider`, `call_gemini`, `call_anthropic`, `call_openai_compatible`, `os.getenv`, `is_ollama_running`, `call_ollama`; raises: `ValueError`, `ConnectionError`)

## shift_this_version/check_update.py
- `is_newer_version()` @18: Compare two semver strings to determine if latest_ver is strictly newer than current_ver. (calls: `strip`, `current_ver.lstrip`, `latest_ver.lstrip`, `parse_semver`)
- `fetch_latest_pypi_version()` @41: Fetch the latest released version from the official PyPI JSON API. (calls: `urllib.request.Request`, `urllib.request.urlopen`, `json.loads`, `decode`, `resp.read`, `get`, `data.get`)
- `load_update_cache()` @55: Read update_cache.json returning (latest_version, last_check_timestamp). (calls: `CACHE_FILE.is_file`, `json.loads`, `CACHE_FILE.read_text`, `data.get`, `float`)
- `save_update_cache()` @65: Save latest version and current timestamp to update_cache.json. (calls: `CONFIG_DIR.mkdir`, `time.time`, `CACHE_FILE.write_text`, `json.dumps`)
- `refresh_cache_in_background()` @77: Fetch PyPI version in a background worker thread and update cache file. (calls: `fetch_latest_pypi_version`, `save_update_cache`)
- `check_for_update_notice()` @83: Check if a newer version is available. (calls: `time.time`, `load_update_cache`, `threading.Thread`, `t.start`, `is_newer_version`)
- `show_update_notification_if_available()` @103: Display update notification panel if a newer version is detected. (calls: `check_for_update_notice`, `print_update_banner`)
- `print_update_banner()` @114: Render a sleek, eye-catching update notification panel using Rich (Windows-safe). (calls: `console.print`, `Panel`)

## shift_this_version/cli.py
- `make_badge()` @28: Format a styled pill badge.
- `render_confidence_bar()` @32: Format a minimalist block-based progress bar. (calls: `max`, `min`, `int`, `round`)
- `run_setup_wizard()` @64: Interactive first-time onboarding wizard categorized by AI provider type. (calls: `console.print`, `Panel`, `make_badge`, `strip`, `typer.prompt`, `config.load_config`, `config.save_config`, `get`, `cfg.get`, `config.get_config_path`)
- `prompt_version_selection()` @196: Prompt user to select SemVer bump level (Patch, Minor, Major, Custom, Cancel) with default recommendation. (calls: `updater.calculate_next_version`, `recommended_bump.lower`, `make_badge`, `console.print`, `strip`, `typer.prompt`; raises: `typer.Exit`)
- `prompt_manual_bump()` @243: Prompt user to select SemVer bump level manually without AI. (calls: `prompt_version_selection`)
- `execute_shift()` @251: Core logic to analyze diff with AI and shift SemVer across targets. (calls: `console.print`, `check_update.show_update_notification_if_available`, `git_ops.is_git_repo`, `git_ops.get_latest_tag`, `git_ops.get_commits_since`, `git_ops.get_dirty_files`, `Confirm.ask`, `len`, `status_map.get`, `git_ops.get_diff_summary`, `updater.find_version_targets`, `latest_tag.lstrip`, `provider.lower`, `prompt_manual_bump`, `config.get_default_provider`, `analyzer.detect_default_provider`, `config.get_configured_model`, `config.get_configured_host`, `console.status`, `analyzer.analyze`, `analysis.bump_type.upper`, `updater.calculate_next_version`, `bump_color_map.get`, `make_badge`, `render_confidence_bar`, `getattr`, `Panel`, `Table`, `target_table.add_column`, `target_table.add_row`, `str`, `strip`, `prompt_version_selection`, `ai_commit_msg.replace`, `typer.prompt`, `git_ops.tag_exists`, `git_ops.get_current_branch`, `git_ops.has_remote`, `git_ops.has_upstream_branch`, `updater.apply_version_bump`, `updated_files.append`, `updater.sync_lockfiles`, `git_ops.commit_version_bump`, `git_ops.format_tag_message`, `git_ops.create_git_tag`, `git_ops.push_to_remote`; raises: `typer.Exit`)
- `version_callback()` @584: Show the application version and exit. (calls: `console.print`, `make_badge`; raises: `typer.Exit`)
- `main()` @591: Smart SemVer Bumper driven by Code Diff & AI (calls: `check_update.show_update_notification_if_available`, `config.is_first_run`, `run_setup_wizard`, `config.load_config`, `cfg.get`, `get`, `make_badge`, `console.print`, `Panel`)
- `configure()` @636: Configure or change AI Provider and API Keys. (calls: `run_setup_wizard`)
- `show_help()` @641: Show detailed guide for all commands or a specific command. (calls: `command.lower`, `console.print`, `Panel`)
- `format_diff_stat_colors()` @734: Format git diff --stat with vivid colors for files, numbers, + (green), and - (red). (calls: `stat_text.split`, `line.split`, `escape`, `colored_lines.append`, `join`)
- `format_diff_with_colors()` @757: Highlight diff lines with bold green (+), bold red (-), cyan (@@), and yellow headers. (calls: `diff_text.split`, `escape`, `raw_line.startswith`, `colored.append`, `join`)
- `inspect()` @780: Scan and display Git history, diff preview, and detected version files/variables. (calls: `check_update.show_update_notification_if_available`, `git_ops.is_git_repo`, `updater.find_version_targets`, `console.print`, `Table`, `table.add_column`, `table.add_row`, `str`, `git_ops.get_latest_tag`, `git_ops.get_commits_since`, `git_ops.get_diff_stat`, `git_ops.get_latest_diff_sample`, `git_ops.get_filtered_diff`, `Panel`, `len`, `format_diff_stat_colors`, `sample_diff.strip`, `format_diff_with_colors`, `sample_diff.split`)
- `shift_cmd()` @872: Analyze diff with AI and shift SemVer across all relevant files automatically. (calls: `execute_shift`)
- `bump_alias()` @902 (calls: `execute_shift`)
- `status_cmd()` @930: Scan repository for Git status, recent commits, diff, and detected version targets (alias for inspect). (calls: `inspect`)
- `check_cmd()` @935: Scan repository for Git status, recent commits, diff, and detected version targets (alias for inspect). (calls: `inspect`)
- `doctor()` @940: Run diagnostic checks on Git, project version files, AI configuration, and update status. (calls: `console.print`, `Table`, `diag_table.add_column`, `shutil.which`, `diag_table.add_row`, `make_badge`, `git_ops.is_git_repo`, `git_ops.get_latest_tag`, `git_ops.get_commits_since`, `len`, `git_ops.run_git`, `remotes.strip`, `split`, `updater.find_version_targets`, `list`, `join`, `config.load_config`, `cfg.get`, `get`, `analyzer.get_key_for_provider`, `httpx.get`, `ollama_host.rstrip`, `host.rstrip`, `check_update.fetch_latest_pypi_version`, `check_update.is_newer_version`)
- `update_cmd()` @1043: Check PyPI for the latest version and upgrade shift-this-version. (calls: `console.print`, `check_update.fetch_latest_pypi_version`, `check_update.is_newer_version`, `Panel`, `shutil.which`, `join`, `Confirm.ask`, `subprocess.run`)
- `upgrade_alias()` @1098: Alias for update. (calls: `update_cmd`)

## shift_this_version/config.py
- `get_config_path()` @9: คืนค่า path ของไฟล์ config
- `load_config()` @13: โหลดค่า config จาก ~/.shift-this-version/config.json (calls: `CONFIG_FILE.is_file`, `CONFIG_FILE.read_text`, `json.loads`)
- `save_config()` @23: บันทึกค่า config ลง ~/.shift-this-version/config.json (calls: `CONFIG_DIR.mkdir`, `CONFIG_FILE.write_text`, `json.dumps`, `CONFIG_FILE.chmod`)
- `is_first_run()` @33: ตรวจสอบว่าเป็นครั้งแรกที่รันเครื่องมือหรือไม่ (calls: `CONFIG_FILE.is_file`)
- `get_configured_key()` @37: ดึง API Key ของ provider ที่บันทึกไว้ใน config (calls: `load_config`, `cfg.get`, `keys.get`, `provider.lower`)
- `get_default_provider()` @43: ดึงค่า default provider จาก config (calls: `load_config`, `cfg.get`)
- `get_configured_model()` @48: ดึงค่า model ที่บันทึกไว้สำหรับ provider นั้นๆ (calls: `load_config`, `cfg.get`, `models.get`, `provider.lower`)
- `get_configured_host()` @54: ดึงค่า host/base_url ที่บันทึกไว้สำหรับ provider นั้นๆ (เช่น ollama, custom) (calls: `load_config`, `cfg.get`, `hosts.get`, `provider.lower`)

## shift_this_version/git_ops.py
- `run_git()` @20: Execute a git command with timeout and return stdout as a stripped string. (calls: `subprocess.run`, `result.stdout.strip`; raises: `subprocess.SubprocessError`)
- `is_git_repo()` @44: Check if the current directory is inside a valid Git repository. (calls: `run_git`, `output.strip`)
- `has_remote()` @52: Check if the specified Git remote is configured. (calls: `run_git`, `remotes.split`)
- `has_upstream_branch()` @60: Check if the current active branch has an upstream tracking branch configured. (calls: `run_git`, `bool`, `output.strip`)
- `get_latest_tag()` @68: Retrieve the latest reachable Git tag from the current commit. (calls: `run_git`)
- `tag_exists()` @75: Check if a Git tag exists in local repository. (calls: `run_git`, `bool`, `output.strip`)
- `get_commits_since()` @83: Retrieve list of one-line commit logs from the latest tag up to HEAD. (calls: `run_git`, `logs.split`)
- `get_committed_diff()` @92: Extract diff of committed changes between tag and HEAD excluding noise files. (calls: `run_git`)
- `get_uncommitted_diff()` @100: Extract diff of uncommitted working tree changes excluding noise files. (calls: `run_git`)
- `get_uncommitted_diff_with_untracked()` @110: Extract diff of uncommitted working tree changes, including untracked (new) files, (calls: `get_dirty_files`, `any`, `get_uncommitted_diff`, `tempfile.mkstemp`, `os.close`, `os.environ.copy`, `run_git`, `subprocess.run`, `diff_cmd.insert`, `os.path.exists`, `os.remove`)
- `get_filtered_diff()` @178: Extract source code Git diff excluding noise files. (calls: `cmd.append`, `run_git`)
- `get_diff_stat()` @192: Retrieve git diff --stat to view summary of file changes. (calls: `cmd.append`, `run_git`)
- `get_diff_summary()` @202: Retrieve diff intelligently separated into committed vs uncommitted changes. (calls: `get_committed_diff`, `get_uncommitted_diff_with_untracked`, `uncommitted_diff.strip`, `sections.append`, `committed_diff.strip`, `join`, `get_filtered_diff`, `len`, `get_diff_stat`, `max`)
- `has_uncommitted_changes()` @242: Check if the repository has uncommitted or dirty changes. (calls: `run_git`, `bool`, `output.strip`)
- `get_dirty_files()` @250: Retrieve all dirty, modified, untracked, and deleted files in the workspace. (calls: `subprocess.run`, `res.stdout.splitlines`, `line.strip`, `len`, `strip`, `path.startswith`, `path.endswith`, `results.append`)
- `get_current_branch()` @278: Retrieve current active Git branch name. (calls: `run_git`)
- `commit_version_bump()` @286: Stage modified version files and optionally all workspace changes, then create a release commit. (calls: `run_git`)
- `format_tag_message()` @302: Format a rich, structured Git release tag message including: (calls: `commit_msg.strip`, `startswith`, `clean_commit.lower`, `lower`, `getattr`, `isinstance`, `join`, `item.strip`, `sections.append`, `reasoning.strip`, `bump_type.upper`, `strip`)
- `create_git_tag()` @352: Create an annotated Git release tag (e.g. v1.2.0). Returns (success, message). (calls: `tag_exists`, `run_git`, `strip`, `str`)
- `push_to_remote()` @366: Push current branch and release tag to remote git repository. (calls: `get_current_branch`, `has_upstream_branch`, `run_git`, `strip`, `str`, `err_msg.strip`)
- `get_latest_diff_sample()` @389: Retrieve the most recent diff sample: (calls: `get_uncommitted_diff_with_untracked`, `uncommitted.strip`, `get_dirty_files`, `join`, `len`, `run_git`, `commit_diff.strip`, `get_filtered_diff`)

## shift_this_version/updater.py
- class `VersionTarget` @8
- `parse_semver()` @82: แยกส่วน major, minor, patch ออกจากสตริงเวอร์ชัน (calls: `version_str.lstrip`, `re.match`, `int`, `match.group`; raises: `ValueError`)
- `calculate_next_version()` @95: คำนวณเลข SemVer ถัดไปตาม bump_type ('major', 'minor', 'patch', 'none') (calls: `current_ver.startswith`, `parse_semver`, `bump_type.lower`; raises: `ValueError`)
- `find_version_targets()` @133: ค้นหาไฟล์ทั้งหมดในโปรเจกต์ที่มีการระบุเวอร์ชัน (calls: `set`, `cfg_path.is_file`, `cfg_path.read_text`, `content.splitlines`, `enumerate`, `search`, `targets.append`, `VersionTarget`, `match.group`, `line.strip`, `seen_files.add`, `cfg_path.resolve`, `join`, `re.escape`, `re.compile`, `root_dir.rglob`, `any`, `p.is_file`, `p.suffix.lower`, `p.resolve`, `p.stat`, `p.read_text`, `p.stem.lower`, `lower_stem.startswith`, `lower_stem.endswith`, `stripped.startswith`, `var_pattern.search`)
- `apply_version_bump()` @217: เขียนเลขเวอร์ชันใหม่ลงในไฟล์เป้าหมายอย่างแม่นยำด้วย Regex span (calls: `new_version.lstrip`, `target.file_path.read_text`, `content.splitlines`, `len`, `search`, `m.group`, `m.span`, `CODE_VAR_REGEX.search`, `re.finditer`, `old_line.rfind`, `target.file_path.write_text`, `join`, `print`)
- `sync_lockfiles()` @277: Check if supported lockfiles (uv.lock, poetry.lock) exist in the project, (calls: `uv_lock.is_file`, `shutil.which`, `Path.home`, `candidate.is_file`, `str`, `subprocess.run`, `synced.append`, `poetry_lock.is_file`)

## tests/test_check_update.py
- `test_is_newer_version()` @9 (calls: `check_update.is_newer_version`)
- `test_cache_save_and_load()` @28 (calls: `patch.object`, `check_update.load_update_cache`, `check_update.save_update_cache`, `mock_cache_file.is_file`, `time.time`)
- `test_check_for_update_notice_with_cached_newer()` @48 (calls: `patch.object`, `check_update.save_update_cache`, `check_update.check_for_update_notice`)
- `test_print_update_banner()` @64 (calls: `Console`, `check_update.print_update_banner`, `console.export_text`)

## tests/test_core.py
- `test_calculate_next_version()` @10 (calls: `calculate_next_version`)
- `test_extract_json_from_text()` @30 (calls: `extract_json_from_text`, `BumpAnalysis`, `len`)
- `test_find_and_bump_version_targets()` @105 (calls: `pyproject_file.write_text`, `frontend_dir.mkdir`, `ts_file.write_text`, `find_version_targets`, `len`, `apply_version_bump`, `pyproject_file.read_text`, `ts_file.read_text`)
- `test_apply_version_bump_precision()` @133 (calls: `code_file.write_text`, `find_version_targets`, `len`, `apply_version_bump`, `code_file.read_text`)
- `test_config_and_key_lookup()` @149 (calls: `config.is_first_run`, `config.save_config`, `config.get_default_provider`, `config.get_configured_key`, `config.get_configured_model`, `config.get_configured_host`, `analyzer.get_key_for_provider`)
- `test_ollama_and_provider_detection()` @187 (calls: `analyzer.is_ollama_running`, `analyzer.detect_default_provider`)
- `test_git_ops_tag_functions()` @204 (calls: `git_ops.is_git_repo`, `isinstance`, `git_ops.has_remote`, `git_ops.has_upstream_branch`, `git_ops.tag_exists`, `git_ops.format_tag_message`, `BumpAnalysis`, `git_ops.get_latest_tag`, `git_ops.create_git_tag`)
- `test_additional_config_patterns()` @240 (calls: `setup_file.write_text`, `composer_file.write_text`, `pubspec_file.write_text`, `find_version_targets`, `apply_version_bump`, `setup_file.read_text`, `composer_file.read_text`, `pubspec_file.read_text`)
- `test_sync_lockfiles()` @269 (calls: `sync_lockfiles`)
- `test_prompt_manual_bump()` @275 (calls: `cli.prompt_manual_bump`)
- `test_cli_version_flag()` @292 (calls: `CliRunner`, `runner.invoke`)
- `test_cli_help_flag()` @308 (calls: `CliRunner`, `runner.invoke`)
- `test_cli_status_and_check()` @319 (calls: `CliRunner`, `runner.invoke`)
- `test_cli_doctor()` @329 (calls: `CliRunner`, `runner.invoke`)
- `test_cli_update_check()` @337 (calls: `CliRunner`, `runner.invoke`)

## tests/test_git_ops_untracked.py
- `test_untracked_diff_extraction_and_readonly()` @10: Test that get_uncommitted_diff_with_untracked(): (calls: `Path`, `test_file_path.write_text`, `git_ops.get_dirty_files`, `any`, `git_ops.get_uncommitted_diff_with_untracked`, `git_ops.run_git`, `git_ops.get_latest_tag`, `git_ops.get_diff_summary`, `test_file_path.exists`, `test_file_path.unlink`)
- `test_untracked_noise_files_excluded()` @63: Test that untracked noise files (like dummy.lock, image.png) (calls: `Path`, `noise_file.write_text`, `git_ops.get_uncommitted_diff_with_untracked`, `noise_file.exists`, `noise_file.unlink`)
- `test_clean_working_tree_fallback()` @85: Test that when there are no untracked files matching, (calls: `git_ops.get_uncommitted_diff_with_untracked`, `isinstance`)
