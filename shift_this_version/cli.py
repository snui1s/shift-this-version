import os
import sys
import shutil
import subprocess
from typing import List, Optional
from pathlib import Path
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.prompt import Confirm
from rich.markup import escape

# Ensure UTF-8 output encoding & ANSI colors on Windows consoles
if sys.platform == "win32":
    os.system("")  # Enable VT100 ANSI terminal processing on Windows
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from shift_this_version import git_ops, analyzer, updater, config, check_update, __version__

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = typer.Typer(
    name="shift-this-version",
    help="Smart SemVer Bumper driven by Code Diff & AI (Gemini, Anthropic, OpenAI, DeepSeek, Groq, OpenRouter, Ollama)",
    no_args_is_help=False,
    context_settings={"help_option_names": ["-h", "--help"]}
)
console = Console(force_terminal=True, color_system="auto")

def run_setup_wizard():
    """Interactive first-time onboarding wizard categorized by AI provider type."""
    console.print(Panel(
        "[bold cyan]Welcome to shift-this-version![/bold cyan]\n"
        "Smart SemVer Bumper driven by Code Diff & AI\n\n"
        "Let's get you set up in less than 30 seconds!",
        title="[bold green]Initial Setup Wizard[/bold green]",
        expand=False
    ))

    console.print("\n[bold yellow]Choose your preferred AI Provider:[/bold yellow]")

    console.print("\n [bold green]── Group 1: Direct Cloud Giants ──[/bold green]")
    console.print("  [bold cyan]1)[/bold cyan] Google Gemini [green](Recommended - Fast & Free at aistudio.google.com)[/green]")
    console.print("  [bold cyan]2)[/bold cyan] Anthropic Claude [dim](Top coder - Claude 3.5 Sonnet / Haiku at anthropic.com)[/dim]")
    console.print("  [bold cyan]3)[/bold cyan] OpenAI [dim](GPT-4o mini, GPT-4o at platform.openai.com)[/dim]")

    console.print("\n [bold magenta]── Group 2: High-Speed & Value Powerhouses ──[/bold magenta]")
    console.print("  [bold cyan]4)[/bold cyan] DeepSeek [dim](Ultra-low cost, coding expert at platform.deepseek.com)[/dim]")
    console.print("  [bold cyan]5)[/bold cyan] Groq [dim](Ultra-fast sub-second inference at console.groq.com)[/dim]")

    console.print("\n [bold blue]── Group 3: Universal Hub (200+ Models in 1 Key) ──[/bold blue]")
    console.print("  [bold cyan]6)[/bold cyan] OpenRouter [dim](Access Claude, GPT, DeepSeek, Llama via openrouter.ai)[/dim]")

    console.print("\n [bold yellow]── Group 4: Local & Self-Hosted (Free & Offline) ──[/bold yellow]")
    console.print("  [bold cyan]7)[/bold cyan] Ollama [dim](100% Free & Local via localhost:11434)[/dim]")
    console.print("  [bold cyan]8)[/bold cyan] Custom OpenAI-Compatible [dim](LM Studio, vLLM, LocalAI)[/dim]")

    choice = typer.prompt("\nSelect provider [1-8]", default="1").strip()

    cfg = config.load_config()
    if "api_keys" not in cfg:
        cfg["api_keys"] = {}
    if "models" not in cfg:
        cfg["models"] = {}
    if "hosts" not in cfg:
        cfg["hosts"] = {}

    if choice == "1":
        provider = "gemini"
        console.print("\n[dim]Tip: You can get a free key in 5 seconds at [bold underline]https://aistudio.google.com[/bold underline][/dim]")
        key = typer.prompt("Enter your Gemini API Key", hide_input=True).strip()
        cfg["api_keys"]["gemini"] = key
        model = typer.prompt("Model name", default="gemini-2.5-flash").strip()
        cfg["models"]["gemini"] = model

    elif choice == "2":
        provider = "anthropic"
        console.print("\n[dim]Tip: Get your Anthropic key at [bold underline]https://console.anthropic.com[/bold underline][/dim]")
        key = typer.prompt("Enter your Anthropic API Key", hide_input=True).strip()
        cfg["api_keys"]["anthropic"] = key
        model = typer.prompt("Model name", default="claude-3-5-haiku-20241022").strip()
        cfg["models"]["anthropic"] = model

    elif choice == "3":
        provider = "openai"
        console.print("\n[dim]Tip: Get your OpenAI key at [bold underline]https://platform.openai.com/api-keys[/bold underline][/dim]")
        key = typer.prompt("Enter your OpenAI API Key", hide_input=True).strip()
        cfg["api_keys"]["openai"] = key
        model = typer.prompt("Model name", default="gpt-4o-mini").strip()
        cfg["models"]["openai"] = model

    elif choice == "4":
        provider = "deepseek"
        console.print("\n[dim]Tip: Get your DeepSeek key at [bold underline]https://platform.deepseek.com[/bold underline][/dim]")
        key = typer.prompt("Enter your DeepSeek API Key", hide_input=True).strip()
        cfg["api_keys"]["deepseek"] = key
        model = typer.prompt("Model name", default="deepseek-chat").strip()
        cfg["models"]["deepseek"] = model

    elif choice == "5":
        provider = "groq"
        console.print("\n[dim]Tip: Get your free Groq key at [bold underline]https://console.groq.com[/bold underline][/dim]")
        key = typer.prompt("Enter your Groq API Key", hide_input=True).strip()
        cfg["api_keys"]["groq"] = key
        model = typer.prompt("Model name", default="llama-3.3-70b-versatile").strip()
        cfg["models"]["groq"] = model

    elif choice == "6":
        provider = "openrouter"
        console.print("\n[dim]Tip: Get your OpenRouter key at [bold underline]https://openrouter.ai/keys[/bold underline][/dim]")
        key = typer.prompt("Enter your OpenRouter API Key", hide_input=True).strip()
        cfg["api_keys"]["openrouter"] = key
        console.print("[dim]Popular models: google/gemini-2.0-flash-001, anthropic/claude-3.5-haiku, deepseek/deepseek-chat[/dim]")
        model = typer.prompt("Enter model name", default="google/gemini-2.0-flash-001").strip()
        cfg["models"]["openrouter"] = model

    elif choice == "7":
        provider = "ollama"
        host = typer.prompt("Enter Ollama Host URL", default="http://localhost:11434").strip()
        cfg["hosts"]["ollama"] = host
        cfg["models"]["ollama"] = "llama3.2"

    elif choice == "8":
        provider = "custom"
        base_url = typer.prompt("Enter Custom Base URL (e.g. LM Studio, vLLM)", default="http://localhost:1234/v1").strip()
        cfg["hosts"]["custom"] = base_url
        model = typer.prompt("Enter Model Name", default="local-model").strip()
        cfg["models"]["custom"] = model
        key = typer.prompt("Enter API Key (press Enter if none required)", default="", hide_input=True).strip()
        if key:
            cfg["api_keys"]["custom"] = key

    else:
        console.print("[yellow]Invalid option. Defaulting to Gemini.[/yellow]")
        provider = "gemini"

    cfg["default_provider"] = provider
    config.save_config(cfg)

    saved_model = cfg.get("models", {}).get(provider, "default")
    saved_host = cfg.get("hosts", {}).get(provider, "")
    details = f"Default Provider: [bold cyan]{provider}[/bold cyan] (Model: [yellow]{saved_model}[/yellow])"
    if saved_host:
        details += f"\nHost / Endpoint: [dim]{saved_host}[/dim]"

    console.print(Panel(
        f"[bold green]Setup Complete![/bold green]\n"
        f"{details}\n"
        f"Config saved to: [dim]{config.get_config_path()}[/dim]\n\n"
        "[bold yellow]Quick Start (No flags needed!):[/bold yellow]\n"
        "  • [bold]shift-this-version[/bold]            ➔ Run AI version shift using your default settings\n"
        "  • [bold]shift-this-version --dry-run[/bold]  ➔ Test AI analysis without modifying files\n"
        "  • [bold]shift-this-version inspect[/bold]    ➔ Check Git diff & detected version files\n"
        "  • [bold]shift-this-version config[/bold]     ➔ Change provider, model, or host anytime",
        title="[bold green]Ready to Go![/bold green]",
        expand=False
    ))

def prompt_version_selection(
    current_ver: str,
    recommended_bump: str = "patch",
    title: str = "Version Selection"
) -> str:
    """Prompt user to select SemVer bump level (Patch, Minor, Major, Custom, Cancel) with default recommendation."""
    patch_v = updater.calculate_next_version(current_ver, "patch")
    minor_v = updater.calculate_next_version(current_ver, "minor")
    major_v = updater.calculate_next_version(current_ver, "major")

    bump_lower = recommended_bump.lower()
    default_opt = "1"
    rec_tags = {"patch": "", "minor": "", "major": ""}
    if bump_lower == "major":
        default_opt = "3"
        rec_tags["major"] = " [bold green]★ AI Recommended[/bold green]"
    elif bump_lower == "minor":
        default_opt = "2"
        rec_tags["minor"] = " [bold green]★ AI Recommended[/bold green]"
    elif bump_lower == "patch":
        default_opt = "1"
        rec_tags["patch"] = " [bold green]★ AI Recommended[/bold green]"

    console.print(f"\n [bold cyan]{title}[/bold cyan] (Current: [yellow]{current_ver}[/yellow]):")
    console.print(f"   [bold cyan][1] Patch[/bold cyan]  ➔ [bold white]{patch_v}[/bold white]{rec_tags['patch']}  [dim](Bug fixes, backwards-compatible)[/dim]")
    console.print(f"   [bold cyan][2] Minor[/bold cyan]  ➔ [bold white]{minor_v}[/bold white]{rec_tags['minor']}  [dim](New features, backwards-compatible)[/dim]")
    console.print(f"   [bold cyan][3] Major[/bold cyan]  ➔ [bold white]{major_v}[/bold white]{rec_tags['major']}  [dim](Breaking changes, major redesign)[/dim]")
    console.print(f"   [bold cyan][4] Custom[/bold cyan] ➔ [dim]Enter a custom version string[/dim]")
    console.print(f"   [bold red][0] Cancel[/bold red]")

    choice = typer.prompt(" Select version option [1/2/3/4/0]", default=default_opt).strip()
    if choice == "1":
        return patch_v
    elif choice == "2":
        return minor_v
    elif choice == "3":
        return major_v
    elif choice == "4":
        custom = typer.prompt("   Enter custom version").strip()
        if not custom:
            console.print("[yellow]Aborted.[/yellow]")
            raise typer.Exit(code=0)
        return custom
    else:
        console.print("[yellow]Aborted by user.[/yellow]")
        raise typer.Exit(code=0)

def prompt_manual_bump(current_ver: str) -> str:
    """Prompt user to select SemVer bump level manually without AI."""
    return prompt_version_selection(
        current_ver,
        recommended_bump="patch",
        title="Manual Version Shift (No AI)"
    )

def execute_shift(
    provider: Optional[str] = "auto",
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    host: Optional[str] = None,
    dry_run: bool = False,
    yes: bool = False,
    tag: bool = True,
    commit: bool = True,
    push: bool = True,
    var_name: Optional[List[str]] = None,
    manual: bool = False,
):
    """Core logic to analyze diff with AI and shift SemVer across targets."""
    console.print("\n[bold blue]Starting Smart SemVer Shift[/bold blue]")
    check_update.show_update_notification_if_available(console, __version__)

    # 1. Inspect Git status and workspace changes
    in_git = git_ops.is_git_repo()
    latest_tag = git_ops.get_latest_tag() if in_git else None
    commits = git_ops.get_commits_since(latest_tag) if in_git else []
    dirty_files = git_ops.get_dirty_files() if in_git else []

    if not in_git:
        console.print("[bold yellow]Notice: Current directory is not a Git repository.[/bold yellow]")
        if not manual:
            if not yes:
                fallback = Confirm.ask("Would you like to shift version in project files manually?", default=True)
                if not fallback:
                    raise typer.Exit(code=0)
                manual = True
            else:
                console.print("[red]Cannot run AI diff analysis outside a Git repository.[/red]")
                raise typer.Exit(code=1)

    # 1.1 Pre-AI Scope Decision: Decide whether to include uncommitted workspace changes (modified & new files)
    stage_all_modified = True
    if in_git and dirty_files:
        console.print(f"\n[bold yellow]Workspace Changes Detected ({len(dirty_files)} file{'s' if len(dirty_files) > 1 else ''}):[/bold yellow]")
        status_map = {
            "M": ("[yellow]modified[/yellow]", "~"),
            "A": ("[green]added[/green]", "+"),
            "D": ("[red]deleted[/red]", "-"),
            "??": ("[bold green]new file[/bold green]", "+"),
            "R": ("[cyan]renamed[/cyan]", "→"),
        }
        for status, file_path in dirty_files[:15]:
            label, symbol = status_map.get(status, (f"[cyan]{status}[/cyan]", "*"))
            console.print(f"  {symbol} {label}: [white]{file_path}[/white]")
        if len(dirty_files) > 15:
            console.print(f"  ... and {len(dirty_files) - 15} more files.")

        if not yes:
            stage_all_modified = Confirm.ask(
                f"\n[bold cyan]Include all {len(dirty_files)} workspace changes (modified & new files) in this release & AI analysis?[/bold cyan]",
                default=True
            )
        else:
            stage_all_modified = True
    elif in_git and not dirty_files:
        stage_all_modified = False

    # 1.2 Extract diff strictly scoped to user's decision (with read-only untracked support)
    diff = git_ops.get_diff_summary(latest_tag, include_uncommitted=stage_all_modified, max_chars=18000) if in_git else ""

    if in_git and not diff and not commits:
        if dirty_files and not stage_all_modified:
            console.print("[yellow]No committed changes detected since the last release (workspace changes were excluded).[/yellow]")
        else:
            console.print("[yellow]No commits or diff changes detected since the last release.[/yellow]")
        raise typer.Exit(code=0)

    # 2. Find version targets
    targets = updater.find_version_targets(custom_var_names=var_name)
    if not targets:
        console.print("[red]Error: Could not find any version targets (pyproject.toml, package.json, or code variable like VERSION).[/red]")
        raise typer.Exit(code=1)

    current_ver = (latest_tag.lstrip("v") if latest_tag else targets[0].current_version)

    # 3. Determine if running in Manual Mode or AI Mode
    is_manual = manual or (provider and provider.lower() in ("manual", "none")) or (not in_git)
    next_ver: Optional[str] = None
    bump_type: str = "MANUAL"

    if is_manual:
        console.print("[bold cyan]Running in Manual Mode (No AI)[/bold cyan]")
        next_ver = prompt_manual_bump(current_ver)
    else:
        saved_prov = config.get_default_provider()
        active_prov = provider if (provider and provider != "auto") else saved_prov

        if not active_prov or active_prov == "auto":
            detected_prov, _ = analyzer.detect_default_provider()
            active_prov = detected_prov

        if not active_prov:
            console.print("[bold yellow]Notice: No AI provider or API key configured.[/bold yellow]")
            if not yes:
                fallback_to_manual = Confirm.ask("Would you like to shift version manually?", default=True)
                if not fallback_to_manual:
                    console.print("[yellow]Run 'shift-this-version config' to configure an AI provider.[/yellow]")
                    raise typer.Exit(code=0)
                next_ver = prompt_manual_bump(current_ver)
            else:
                console.print("[red]Cannot proceed in non-interactive mode without a configured provider.[/red]")
                raise typer.Exit(code=1)
        else:
            active_model = model or config.get_configured_model(active_prov)
            active_host = host or config.get_configured_host(active_prov)
            model_disp = f" ({active_model})" if active_model else ""

            # 4. Call AI analyzer with graceful fallback
            analysis: Optional[analyzer.BumpAnalysis] = None
            ai_error: Optional[Exception] = None
            with console.status(f"[bold green]AI is analyzing code diff & commits using [cyan]{active_prov}[/cyan]{model_disp}..."):
                try:
                    analysis = analyzer.analyze(
                        diff=diff,
                        commits=commits,
                        provider=active_prov,
                        model=active_model,
                        api_key=api_key,
                        host=active_host
                    )
                except Exception as e:
                    ai_error = e

            if ai_error is not None:
                console.print(f"[bold red]AI Analysis Failed:[/bold red] {ai_error}")
                if not yes:
                    fallback_to_manual = Confirm.ask("\nWould you like to continue and shift version manually?", default=True)
                    if not fallback_to_manual:
                        raise typer.Exit(code=1)
                    next_ver = prompt_manual_bump(current_ver)
                else:
                    raise typer.Exit(code=1)

            if analysis is not None:
                bump_type = analysis.bump_type.upper()
                next_ver = updater.calculate_next_version(current_ver, analysis.bump_type)

                color_map = {
                    "MAJOR": "bold red",
                    "MINOR": "bold yellow",
                    "PATCH": "bold green",
                    "NONE": "bold white"
                }
                bump_color = color_map.get(bump_type, "bold cyan")

                # 6. Display recommendation
                panel_content = (
                    f"[bold]Current Version:[/bold] {current_ver}\n"
                    f"[bold]Suggested Version:[/bold] [{bump_color}]{next_ver}[/{bump_color}]  ([bold]{bump_type}[/bold] shift)\n"
                    f"[bold]Confidence:[/bold] {analysis.confidence * 100:.1f}%\n"
                )

                suggested_msg = getattr(analysis, "commit_message", "") if analysis else ""
                if suggested_msg:
                    panel_content += f"[bold]Suggested Commit Message:[/bold] [bold green]{suggested_msg}[/bold green]\n"

                panel_content += f"\n[bold]Reasoning:[/bold]\n{analysis.reasoning}\n"

                if analysis.breaking_changes:
                    panel_content += f"\n[bold red]Breaking Changes Detected:[/bold red]\n"
                    for b in analysis.breaking_changes:
                        panel_content += f"  • [red]{b}[/red]\n"

                if analysis.key_changes:
                    panel_content += f"\n[bold cyan]Key Changes:[/bold cyan]\n"
                    for k in analysis.key_changes:
                        panel_content += f"  • {k}\n"

                console.print(Panel(panel_content, title=f"[{bump_color}]AI Recommendation: {bump_type}[/{bump_color}]", expand=False))

    # Display targets to update
    console.print("\n[bold]Version Targets to Update:[/bold]")
    for t in targets:
        console.print(f"  • [bold white]{t.file_path}[/bold white]:{t.line_number} ([yellow]{t.current_version}[/yellow] -> [bold green]{next_ver}[/bold green])")

    if dirty_files:
        scope_status = "[bold green]included[/bold green]" if stage_all_modified else "[yellow]excluded[/yellow]"
        console.print(f"  [dim]Workspace changes: {len(dirty_files)} file(s) ({scope_status} in release)[/dim]")

    if bump_type == "NONE" or current_ver == next_ver:
        console.print("\n[green]No version shift required.[/green]")
        raise typer.Exit(code=0)

    if dry_run:
        console.print("\n[bold yellow][DRY RUN] No files or git state were modified.[/bold yellow]")
        raise typer.Exit(code=0)

    # 7. Interactive Stage-by-Stage Confirmation (skipped if --yes)
    chosen_ver = next_ver
    do_commit = commit
    ai_commit_msg = (getattr(analysis, "commit_message", "") or "").strip() if analysis else ""
    commit_msg = ai_commit_msg or f"chore(release): shift version to {next_ver}"
    do_tag = tag
    do_push = push

    if not yes:
        console.print("\n[bold yellow]── Release Confirmation Stages ───────────────────────────[/bold yellow]")

        # Stage 1: Version Selection
        chosen_ver = prompt_version_selection(
            current_ver,
            recommended_bump=bump_type,
            title=f"Stage 1 (Version Selection across {len(targets)} target{'s' if len(targets) > 1 else ''})"
        )
        if chosen_ver != next_ver and ai_commit_msg:
            commit_msg = ai_commit_msg.replace(next_ver, chosen_ver)
        else:
            commit_msg = ai_commit_msg or f"chore(release): shift version to {chosen_ver}"

        # Stage 2: Git Commit [y/n]
        if in_git:
            scope_hint = f" (including {len(dirty_files)} workspace changes)" if (dirty_files and stage_all_modified) else ""
            do_commit = Confirm.ask(
                f" [bold cyan]Stage 2 (Git Commit)[/bold cyan]: Create Git commit for this release{scope_hint}?",
                default=commit
            )
        else:
            do_commit = False

        # Stage 3: Commit Message [y/n]
        if do_commit:
            msg_label = "AI-suggested message" if ai_commit_msg else "default message"
            use_default_msg = Confirm.ask(
                f" [bold cyan]Stage 3 (Commit Message)[/bold cyan]: Use {msg_label}: [bold green]'{commit_msg}'[/bold green]?",
                default=True
            )
            if not use_default_msg:
                commit_msg = typer.prompt("  Enter custom commit message", default=commit_msg).strip()

        # Stage 4: Git Tag [y/n]
        if in_git:
            tag_name = f"v{chosen_ver}"
            tag_already_exists = git_ops.tag_exists(tag_name)
            tag_notice = " [bold red](Notice: Tag already exists locally)[/bold red]" if tag_already_exists else ""
            do_tag = Confirm.ask(
                f" [bold cyan]Stage 4 (Git Tag)[/bold cyan]: Create Git tag [bold cyan]{tag_name}[/bold cyan]?{tag_notice}",
                default=(tag and not tag_already_exists)
            )
        else:
            do_tag = False

        # Stage 5: Git Push [y/n]
        if (do_commit or do_tag) and in_git:
            active_branch = git_ops.get_current_branch()
            has_origin = git_ops.has_remote("origin")
            has_upstream = git_ops.has_upstream_branch()
            action_label = "Publish & push" if not has_upstream else "Push"
            remote_notice = "" if has_origin else " [bold yellow](Notice: No remote 'origin' configured)[/bold yellow]"
            do_push = Confirm.ask(
                f" [bold cyan]Stage 5 (Git Push)[/bold cyan]: {action_label} commit and tag to remote repository (origin/{active_branch})?{remote_notice}",
                default=(push and has_origin)
            )
        else:
            do_push = False

    # 8. Apply updates to files
    updated_files: List[str] = []
    for t in targets:
        success = updater.apply_version_bump(t, chosen_ver, dry_run=False)
        if success:
            updated_files.append(str(t.file_path))
            console.print(f"  [green]Updated[/green] [cyan]{t.file_path}[/cyan] -> [green]{chosen_ver}[/green]")
        else:
            console.print(f"  [red]Failed to update[/red] [cyan]{t.file_path}[/cyan]")

    # 8.1 Sync lockfiles if present (e.g. uv.lock, poetry.lock)
    synced_locks = updater.sync_lockfiles()
    for lock_path in synced_locks:
        if lock_path not in updated_files:
            updated_files.append(lock_path)
            console.print(f"  [green]Synced Lockfile[/green] [cyan]{lock_path}[/cyan] -> [green]{chosen_ver}[/green]")

    # 9. Git Commit
    if updated_files and do_commit:
        if git_ops.commit_version_bump(updated_files, chosen_ver, stage_all=stage_all_modified, message=commit_msg):
            scope_desc = f"{len(updated_files)} version target(s) + {len(dirty_files)} workspace file(s)" if stage_all_modified and dirty_files else f"{len(updated_files)} version target(s) only"
            console.print(f"  Git committed: '[green]{commit_msg}[/green]' ([dim]{scope_desc}[/dim])")
        else:
            console.print("  Git commit skipped or no changes staged.")

    # 10. Git Tag
    tag_created = False
    if do_tag:
        tag_name = f"v{chosen_ver}"
        tag_msg_payload = git_ops.format_tag_message(tag_name, commit_msg=commit_msg, analysis=analysis)
        tag_ok, tag_msg = git_ops.create_git_tag(tag_name, message=tag_msg_payload)
        if tag_ok:
            console.print(f"  [bold green]Created Git Tag:[/bold green] [bold cyan]{tag_name}[/bold cyan]")
            tag_created = True
        else:
            console.print(f"  [yellow]Tag notice:[/yellow] {tag_msg}")

    # 11. Git Push to Remote
    if do_push and (do_commit or tag_created):
        with console.status("[bold green]Pushing commit and tags to remote repository..."):
            tag_to_push = f"v{chosen_ver}" if tag_created else None
            success, msg = git_ops.push_to_remote(tag_name=tag_to_push)
        if success:
            console.print(f"  Pushed to remote: [bold cyan]{msg}[/bold cyan]")
        else:
            console.print(f"  [yellow]Push skipped or remote notice:[/yellow] {msg}")

def version_callback(value: bool):
    """Show the application version and exit."""
    if value:
        console.print(f"[bold cyan]shift-this-version[/bold cyan] [bold green]{__version__}[/bold green]", highlight=False)
        raise typer.Exit()

@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        "--v",
        help="Show version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
):
    """Smart SemVer Bumper driven by Code Diff & AI"""
    check_update.show_update_notification_if_available(console, __version__)
    if ctx.invoked_subcommand is None:
        if config.is_first_run():
            run_setup_wizard()
        else:
            cfg = config.load_config()
            def_prov = cfg.get("default_provider", "auto")
            def_model = cfg.get("models", {}).get(def_prov, "default")
            console.print(Panel(
                f"[bold cyan]shift-this-version[/bold cyan] is ready!\n"
                f"Configured Provider: [bold green]{def_prov}[/bold green] (Model: [yellow]{def_model}[/yellow])\n\n"
                "[bold yellow]Commands:[/bold yellow]\n"
                "  • [bold green]shift-this-version shift[/bold green]           ➔ Analyze diff with AI & shift version\n"
                "  • [bold green]shift-this-version status[/bold green]          ➔ Inspect Git state, diff & version targets\n"
                "  • [bold green]shift-this-version doctor[/bold green]          ➔ Check Git, version targets, AI key & network\n"
                "  • [bold green]shift-this-version update[/bold green]          ➔ Check and upgrade to latest release\n"
                "  • [bold green]shift-this-version config[/bold green]          ➔ Reconfigure AI provider, model, or host\n"
                "  • [bold green]shift-this-version --version[/bold green]       ➔ Show version number\n"
                "  • [bold green]shift-this-version help[/bold green]            ➔ Show detailed command guide",
                title="[bold blue]shift-this-version[/bold blue]",
                expand=False
            ))

@app.command("config")
def configure():
    """Configure or change AI Provider and API Keys."""
    run_setup_wizard()

@app.command("help")
def show_help(
    command: Optional[str] = typer.Argument(None, help="Specific command name (e.g. shift, inspect, doctor, update, config)")
):
    """Show detailed guide for all commands or a specific command."""
    if command:
        cmd_name = command.lower()
        if cmd_name in ("shift", "bump"):
            console.print(Panel(
                "[bold cyan]shift-this-version [shift][/bold cyan]\n"
                "Analyze Git diff & recent commits with AI to automatically decide and bump SemVer.\n"
                "[dim]By default, runs automatically using your saved provider and model from setup.[/dim]\n\n"
                "[bold yellow]Options (Optional Overrides):[/bold yellow]\n"
                "  --provider, -p  : Override provider (gemini, anthropic, openai, deepseek, groq, openrouter, ollama, custom)\n"
                "  --model, -m     : Override model name\n"
                "  --dry-run       : Simulate without modifying any files or Git state\n"
                "  --yes, -y       : Skip confirmation prompts (for CI/CD pipelines)\n"
                "  --host          : Custom Host / Base URL for Ollama, LM Studio, or vLLM\n"
                "  --var           : Target specific variable names in code (e.g. VERSION, APP_VERSION)\n"
                "  --manual        : Run in manual mode (select Patch/Minor/Major interactively without AI)\n"
                "  --no-tag        : Disable automatic Git tag creation\n"
                "  --no-commit     : Disable automatic Git commit creation",
                title="[bold green]Command: shift[/bold green]",
                expand=False
            ))
            return
        elif cmd_name in ("inspect", "status", "check"):
            console.print(Panel(
                "[bold cyan]shift-this-version inspect (aliases: status, check)[/bold cyan]\n"
                "Scan repository for Git status, recent commits, diff, and all detected version targets.",
                title="[bold green]Command: inspect / status / check[/bold green]",
                expand=False
            ))
            return
        elif cmd_name == "doctor":
            console.print(Panel(
                "[bold cyan]shift-this-version doctor[/bold cyan]\n"
                "Run diagnostic checks on Git, project version files, AI configuration, and update status.",
                title="[bold green]Command: doctor[/bold green]",
                expand=False
            ))
            return
        elif cmd_name in ("update", "upgrade"):
            console.print(Panel(
                "[bold cyan]shift-this-version update (alias: upgrade)[/bold cyan]\n"
                "Check PyPI for the latest version and upgrade shift-this-version.\n\n"
                "[bold yellow]Options:[/bold yellow]\n"
                "  --check     : Check for updates without installing\n"
                "  --yes, -y   : Automatically accept upgrade prompt",
                title="[bold green]Command: update[/bold green]",
                expand=False
            ))
            return
        elif cmd_name == "config":
            console.print(Panel(
                "[bold cyan]shift-this-version config[/bold cyan]\n"
                "Launch the onboarding setup wizard to reconfigure AI provider, model, or host.",
                title="[bold green]Command: config[/bold green]",
                expand=False
            ))
            return
        else:
            console.print(f"[red]Unknown command: '{command}'[/red]")

    console.print(Panel(
        "[bold cyan]shift-this-version[/bold cyan] - Smart SemVer Bumper driven by Code Diff & AI\n\n"
        "[bold yellow]Commands:[/bold yellow]\n"
        "  • [bold green]shift-this-version shift[/bold green]           ➔ Analyze diff with AI, bump version & push\n"
        "  • [bold green]shift-this-version status[/bold green]          ➔ Inspect Git diff, history, and version targets (alias)\n"
        "  • [bold green]shift-this-version doctor[/bold green]          ➔ Diagnose Git, version files, AI & connectivity\n"
        "  • [bold green]shift-this-version update[/bold green]          ➔ Check and upgrade to latest release\n"
        "  • [bold green]shift-this-version config[/bold green]          ➔ Change default provider, model, or host\n"
        "  • [bold green]shift-this-version --version[/bold green]       ➔ Show application version number (-v, --v)\n\n"
        "[bold yellow]Optional Overrides:[/bold yellow]\n"
        "  $ shift-this-version shift --manual\n"
        "  $ shift-this-version shift -p gemini\n"
        "  $ shift-this-version shift -p openrouter -m anthropic/claude-3.5-haiku\n"
        "  $ shift-this-version shift --no-push",
        title="[bold blue]Help & Usage Guide[/bold blue]",
        expand=False
    ))

def format_diff_stat_colors(stat_text: str) -> str:
    """Format git diff --stat with vivid colors for files, numbers, + (green), and - (red)."""
    colored_lines = []
    for line in stat_text.split("\n"):
        if "|" in line:
            parts = line.split("|", 1)
            file_part = escape(parts[0])
            rest = parts[1]
            colored_rest = ""
            for char in rest:
                if char == "+":
                    colored_rest += "[bold green]+[/bold green]"
                elif char == "-":
                    colored_rest += "[bold red]-[/bold red]"
                else:
                    colored_rest += escape(char)
            colored_lines.append(f"[bold cyan]{file_part}[/bold cyan]|{colored_rest}")
        elif "changed" in line and ("insertion" in line or "deletion" in line):
            colored_lines.append(f"[bold yellow]{escape(line)}[/bold yellow]")
        else:
            colored_lines.append(escape(line))
    return "\n".join(colored_lines)

def format_diff_with_colors(diff_text: str, max_lines: int = 40) -> str:
    """Highlight diff lines with bold green (+), bold red (-), cyan (@@), and yellow headers."""
    lines = diff_text.split("\n")[:max_lines]
    colored = []
    for raw_line in lines:
        line = escape(raw_line)
        if raw_line.startswith("+++") or raw_line.startswith("---"):
            colored.append(f"[bold magenta]{line}[/bold magenta]")
        elif raw_line.startswith("+"):
            colored.append(f"[bold green]{line}[/bold green]")
        elif raw_line.startswith("-"):
            colored.append(f"[bold red]{line}[/bold red]")
        elif raw_line.startswith("@@"):
            colored.append(f"[bold cyan]{line}[/bold cyan]")
        elif raw_line.startswith("diff --git"):
            colored.append(f"[bold yellow]{line}[/bold yellow]")
        elif raw_line.startswith("index ") or raw_line.startswith("warning:"):
            colored.append(f"[dim]{line}[/dim]")
        else:
            colored.append(f"[white]{line}[/white]")
    return "\n".join(colored)

@app.command()
def inspect():
    """Scan and display Git history, diff preview, and detected version files/variables."""
    check_update.show_update_notification_if_available(console, __version__)
    in_git = git_ops.is_git_repo()
    targets = updater.find_version_targets()

    if not in_git:
        console.print("\n[bold yellow]Notice: Current directory is not a Git repository.[/bold yellow]")
        console.print("\n[bold magenta]── Detected Version Files & Variables ─────────────────[/bold magenta]")
        if targets:
            table = Table(title="Targets Found in Project", show_header=True)
            table.add_column("Type", style="cyan")
            table.add_column("File Path", style="bold white")
            table.add_column("Line", justify="right", style="yellow")
            table.add_column("Current Version", style="bold green")
            table.add_column("Snippet", style="dim")
            for t in targets:
                table.add_row(t.target_type, str(t.file_path), str(t.line_number), t.current_version, t.matched_line)
            console.print(table)
        else:
            console.print("[yellow]No version files or variables detected.[/yellow]")
        return

    latest_tag = git_ops.get_latest_tag()
    commits = git_ops.get_commits_since(latest_tag)
    diff_stat = git_ops.get_diff_stat(latest_tag)
    sample_label, sample_diff = git_ops.get_latest_diff_sample(latest_tag)
    total_diff = git_ops.get_filtered_diff(latest_tag)

    # 1. Git State
    console.print("\n[bold blue]── 1. Git State ──────────────────────────────────────────[/bold blue]")
    console.print(Panel(
        f"[bold]Latest Tag:[/bold] [bold green]{latest_tag or 'No previous tag (Initial Release)'}[/bold green]\n"
        f"[bold]Commits Ahead:[/bold] [bold yellow]{len(commits)} commits ahead[/bold yellow]",
        title="[bold blue]Git Repository Info[/bold blue]",
        expand=False
    ))

    # 2. Version Targets
    console.print("\n[bold magenta]── 2. Detected Version Files & Variables ─────────────────[/bold magenta]")
    if targets:
        table = Table(title="Targets Found in Project", show_header=True)
        table.add_column("Type", style="cyan")
        table.add_column("File Path", style="bold white")
        table.add_column("Line", justify="right", style="yellow")
        table.add_column("Current Version", style="bold green")
        table.add_column("Snippet", style="dim")

        for t in targets:
            table.add_row(
                t.target_type,
                str(t.file_path),
                str(t.line_number),
                t.current_version,
                t.matched_line
            )
        console.print(table)
    else:
        console.print("[yellow]No version files or variables (e.g. pyproject.toml, package.json, VERSION) detected.[/yellow]")

    if commits:
        console.print("\n[bold cyan]Recent Commits:[/bold cyan]")
        for c in commits[:10]:
            console.print(f"  • [cyan]{c}[/cyan]")
        if len(commits) > 10:
            console.print(f"  ... and {len(commits) - 10} more commits.")

    # 3. Changed Files (Diff Stat)
    if diff_stat:
        console.print("\n[bold yellow]── 3. Changed Files Summary ──────────────────────────────[/bold yellow]")
        colored_stat = format_diff_stat_colors(diff_stat)
        console.print(Panel(colored_stat, title="[bold yellow]Files Modified (+Add / -Del)[/bold yellow]", expand=False))

    # 4. Latest Diff Sample Preview
    if sample_diff.strip():
        console.print(f"\n[bold green]── 4. {sample_label} ──────────────────────────────[/bold green]")
        colored_diff = format_diff_with_colors(sample_diff, max_lines=40)
        console.print(Panel(
            colored_diff,
            title=f"[bold green]{sample_label}[/bold green] ([dim]{len(total_diff)} total characters[/dim])",
            expand=False
        ))
        if len(sample_diff.split("\n")) > 40:
            console.print("[dim]... remaining diff lines truncated in preview ...[/dim]")
    else:
        console.print("\n[green]No changes detected between latest tag and current workspace.[/green]")

@app.command("shift")
def shift_cmd(
    provider: str = typer.Option("auto", "--provider", "-p", help="AI provider: auto, gemini, anthropic, openai, deepseek, groq, openrouter, ollama, custom"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Specific model name (defaults to configured model)"),
    api_key: Optional[str] = typer.Option(None, "--api-key", help="API Key override"),
    host: Optional[str] = typer.Option(None, "--host", help="Custom host / Base URL override"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate the shift without modifying files or git"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Automatic yes to prompts; run non-interactively"),
    tag: bool = typer.Option(True, "--tag/--no-tag", help="Create a git tag for the new version"),
    commit: bool = typer.Option(True, "--commit/--no-commit", help="Commit updated version files"),
    push: bool = typer.Option(True, "--push/--no-push", help="Push commit and tag to remote git repository (default: True)"),
    var_name: Optional[List[str]] = typer.Option(None, "--var", help="Custom variable name to update in code files (e.g. VERSION)"),
    manual: bool = typer.Option(False, "--manual", help="Run in manual SemVer shift mode without calling AI")
):
    """Analyze diff with AI and shift SemVer across all relevant files automatically."""
    execute_shift(
        provider=provider,
        model=model,
        api_key=api_key,
        host=host,
        dry_run=dry_run,
        yes=yes,
        tag=tag,
        commit=commit,
        push=push,
        var_name=var_name,
        manual=manual,
    )

# Alias: bump -> shift (hidden command)
@app.command("bump", hidden=True)
def bump_alias(
    provider: str = typer.Option("auto", "--provider", "-p"),
    model: Optional[str] = typer.Option(None, "--model", "-m"),
    api_key: Optional[str] = typer.Option(None, "--api-key"),
    host: Optional[str] = typer.Option(None, "--host"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    yes: bool = typer.Option(False, "--yes", "-y"),
    tag: bool = typer.Option(True, "--tag/--no-tag"),
    commit: bool = typer.Option(True, "--commit/--no-commit"),
    push: bool = typer.Option(True, "--push/--no-push"),
    var_name: Optional[List[str]] = typer.Option(None, "--var"),
    manual: bool = typer.Option(False, "--manual")
):
    execute_shift(
        provider=provider,
        model=model,
        api_key=api_key,
        host=host,
        dry_run=dry_run,
        yes=yes,
        tag=tag,
        commit=commit,
        push=push,
        var_name=var_name,
        manual=manual,
    )

@app.command("status")
def status_cmd():
    """Scan repository for Git status, recent commits, diff, and detected version targets (alias for inspect)."""
    inspect()

@app.command("check")
def check_cmd():
    """Scan repository for Git status, recent commits, diff, and detected version targets (alias for inspect)."""
    inspect()

@app.command("doctor")
def doctor():
    """Run diagnostic checks on Git, project version files, AI configuration, and update status."""
    console.print("\n[bold blue]=== shift-this-version System Diagnostics (doctor) ===[/bold blue]\n")

    # 1. Git Environment
    git_bin = shutil.which("git")
    if git_bin:
        console.print(f"  [bold green]✔[/bold green] Git Executable: [cyan]{git_bin}[/cyan]")
    else:
        console.print("  [bold red]✖[/bold red] Git Executable: [red]Not found on PATH[/red]")

    in_git = git_ops.is_git_repo()
    if in_git:
        latest_tag = git_ops.get_latest_tag()
        commits = git_ops.get_commits_since(latest_tag)
        console.print(f"  [bold green]✔[/bold green] Git Repository: [cyan]Detected[/cyan] (Latest tag: [yellow]{latest_tag or 'None (initial)'}[/yellow], Ahead: [yellow]{len(commits)} commit(s)[/yellow])")
        try:
            remotes = git_ops.run_git(["remote", "-v"])
            if remotes.strip():
                first_remote = remotes.strip().split("\n")[0].split()[0]
                console.print(f"  [bold green]✔[/bold green] Git Remote: [cyan]{first_remote}[/cyan]")
            else:
                console.print("  [bold yellow]⚠[/bold yellow] Git Remote: [yellow]No remote configured[/yellow]")
        except Exception:
            console.print("  [bold yellow]⚠[/bold yellow] Git Remote: [yellow]Unable to query remotes[/yellow]")
    else:
        console.print("  [bold yellow]⚠[/bold yellow] Git Repository: [yellow]Current directory is not a Git repository[/yellow]")

    # 2. Version Targets in Workspace
    targets = updater.find_version_targets()
    if targets:
        versions = {t.current_version for t in targets}
        target_files = [f"{t.file_path.name}:{t.line_number}" for t in targets]
        if len(versions) == 1:
            ver = list(versions)[0]
            console.print(f"  [bold green]✔[/bold green] Version Targets: [cyan]{len(targets)} target(s) in sync[/cyan] (v{ver} in {', '.join(target_files[:3])}{'...' if len(target_files) > 3 else ''})")
        else:
            console.print(f"  [bold yellow]⚠[/bold yellow] Version Targets: [yellow]{len(targets)} targets with mismatched versions: {versions}[/yellow]")
    else:
        console.print("  [bold yellow]⚠[/bold yellow] Version Targets: [yellow]No version files (package.json, pyproject.toml, etc.) detected[/yellow]")

    # 3. AI Configuration & Connectivity
    cfg = config.load_config()
    provider = cfg.get("default_provider", "auto")
    model = cfg.get("models", {}).get(provider, "default")
    api_key = analyzer.get_key_for_provider(provider) if provider != "auto" else None
    host = cfg.get("hosts", {}).get(provider, "")

    console.print(f"  [bold green]✔[/bold green] AI Provider: [cyan]{provider}[/cyan] (Model: [yellow]{model}[/yellow])")

    if provider == "ollama":
        ollama_host = host or "http://localhost:11434"
        console.print(f"    Target Host: [dim]{ollama_host}[/dim]")
        try:
            import httpx
            resp = httpx.get(f"{ollama_host.rstrip('/')}/api/tags", timeout=2.5)
            if resp.status_code == 200:
                console.print("  [bold green]✔[/bold green] Ollama Server: [bold green]Reachable & responsive[/bold green]")
            else:
                console.print(f"  [bold yellow]⚠[/bold yellow] Ollama Server: [yellow]Responded with HTTP {resp.status_code}[/yellow]")
        except Exception as e:
            console.print(f"  [bold red]✖[/bold red] Ollama Server: [red]Could not connect to {ollama_host} ({e})[/red]")
    elif provider == "custom":
        if host:
            console.print(f"    Base URL: [dim]{host}[/dim]")
            try:
                import httpx
                resp = httpx.get(host.rstrip("/"), timeout=2.5)
                console.print(f"  [bold green]✔[/bold green] Custom Endpoint: [bold green]Reachable (HTTP {resp.status_code})[/bold green]")
            except Exception as e:
                console.print(f"  [bold yellow]⚠[/bold yellow] Custom Endpoint: [yellow]Ping warning ({e})[/yellow]")
        else:
            console.print("  [bold yellow]⚠[/bold yellow] Custom Endpoint: [yellow]No Base URL configured[/yellow]")
    else:
        # Cloud providers
        if api_key:
            masked = api_key[:4] + "..." + api_key[-4:] if len(api_key) > 8 else "***"
            console.print(f"  [bold green]✔[/bold green] API Key: [cyan]{masked}[/cyan]")
        else:
            console.print(f"  [bold yellow]⚠[/bold yellow] API Key: [yellow]No API key configured for '{provider}' (Run 'shift-this-version config')[/yellow]")

    # 4. Package Release & Update Check
    console.print(f"  [bold green]✔[/bold green] Installed Version: [cyan]v{__version__}[/cyan]")
    try:
        latest = check_update.fetch_latest_pypi_version(timeout=2.5)
        if latest:
            if check_update.is_newer_version(__version__, latest):
                console.print(f"  [bold yellow]⚠[/bold yellow] Latest PyPI Release: [bold yellow]v{latest}[/bold yellow] (Update available! Run 'shift-this-version update')")
            else:
                console.print(f"  [bold green]✔[/bold green] PyPI Release Status: [bold green]Up to date[/bold green]")
        else:
            console.print("  [dim]• PyPI Release Status: Unable to reach PyPI (offline or timeout)[/dim]")
    except Exception:
        pass

    console.print("\n[bold green]Diagnostics complete![/bold green]\n")

@app.command("update")
def update_cmd(
    check: bool = typer.Option(False, "--check", help="Check for updates without installing"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Automatic yes to upgrade prompt")
):
    """Check PyPI for the latest version and upgrade shift-this-version."""
    console.print(f"\nChecking for updates (current version: [cyan]v{__version__}[/cyan])...")
    latest = check_update.fetch_latest_pypi_version(timeout=4.0)
    if not latest:
        console.print("[yellow]Could not reach PyPI to check for updates. Please check your internet connection.[/yellow]\n")
        return

    if not check_update.is_newer_version(__version__, latest):
        console.print(f"[bold green]shift-this-version is already up to date (v{__version__})![/bold green]\n")
        return

    console.print(Panel(
        f"[bold yellow]New version available![/bold yellow]\n"
        f"Installed: [dim]v{__version__}[/dim]\n"
        f"Latest:    [bold green]v{latest}[/bold green]",
        title="[bold green]Update Found[/bold green]",
        expand=False
    ))

    if check:
        console.print("Run [bold cyan]shift-this-version update[/bold cyan] to perform the upgrade.\n")
        return

    if shutil.which("uv"):
        upgrade_cmd = ["uv", "tool", "update", "shift-this-version"]
    elif shutil.which("pipx"):
        upgrade_cmd = ["pipx", "upgrade", "shift-this-version"]
    else:
        upgrade_cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "shift-this-version"]

    cmd_str = " ".join(upgrade_cmd)
    if not yes:
        proceed = Confirm.ask(f"Do you want to upgrade now using '{cmd_str}'?", default=True)
        if not proceed:
            console.print("[yellow]Upgrade cancelled.[/yellow]\n")
            return

    console.print(f"\nRunning upgrade: [cyan]{cmd_str}[/cyan]...")
    try:
        res = subprocess.run(upgrade_cmd, check=False)
        if res.returncode == 0:
            console.print(f"\n[bold green]Successfully upgraded shift-this-version to v{latest}![/bold green]\n")
        else:
            console.print(f"\n[bold red]Upgrade command exited with code {res.returncode}.[/bold red]")
            console.print(f"You can try running manually: [cyan]{cmd_str}[/cyan]\n")
    except Exception as e:
        console.print(f"[red]Error executing upgrade: {e}[/red]\n")

@app.command("upgrade", hidden=True)
def upgrade_alias(
    check: bool = typer.Option(False, "--check", help="Check for updates without installing"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Automatic yes to upgrade prompt")
):
    """Alias for update."""
    update_cmd(check=check, yes=yes)

if __name__ == "__main__":
    app()