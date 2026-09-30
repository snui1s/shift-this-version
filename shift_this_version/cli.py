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
from rich.box import ROUNDED, HEAVY, DOUBLE, SIMPLE

# Minimalist Modern Dark Theme Palette
COLOR_PRIMARY = "#38bdf8"       # Electric Cyan / Slate Ice
COLOR_SECONDARY = "#818cf8"     # Soft Indigo / Violet
COLOR_SUCCESS = "#34d399"       # Emerald Mint
COLOR_WARNING = "#fbbf24"       # Amber Sand
COLOR_DANGER = "#fb7185"        # Coral Rose
COLOR_MUTED = "#94a3b8"         # Slate Grey
COLOR_DIM = "#64748b"           # Dark Slate Grey
COLOR_BORDER = "#334155"        # Slate Border
COLOR_TEXT = "#f8fafc"          # Crisp White
COLOR_SUBTEXT = "#cbd5e1"       # Light Slate

def make_badge(text: str, bg_color: str, fg_color: str = "black") -> str:
    """Format a styled pill badge."""
    return f"[bold {fg_color} on {bg_color}] {text} [/bold {fg_color} on {bg_color}]"

def render_confidence_bar(confidence: float, width: int = 14) -> str:
    """Format a minimalist block-based progress bar."""
    filled = max(0, min(width, int(round(confidence * width))))
    bar = "█" * filled + "░" * (width - filled)
    return f"[bold {COLOR_SUCCESS}]{bar}[/bold {COLOR_SUCCESS}] [{COLOR_SUBTEXT}]{confidence * 100:.1f}%[/{COLOR_SUBTEXT}]"


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
        f"[bold {COLOR_TEXT}]✦ Welcome to shift-this-version ✦[/bold {COLOR_TEXT}]\n"
        f"[{COLOR_SUBTEXT}]AI-driven Semantic Versioning & automated Git release flow.[/{COLOR_SUBTEXT}]\n\n"
        f"[{COLOR_PRIMARY}]Let's get your preferred AI provider configured in less than 30 seconds![/{COLOR_PRIMARY}]",
        title=f"[bold {COLOR_PRIMARY}]✦ Onboarding Setup Wizard ✦[/bold {COLOR_PRIMARY}]",
        border_style=COLOR_PRIMARY,
        box=ROUNDED,
        expand=False
    ))

    console.print(f"\n[bold {COLOR_TEXT}]Select your preferred AI Provider:[/bold {COLOR_TEXT}]")

    console.print(f"\n {make_badge('GROUP 1', COLOR_SUCCESS)} [bold {COLOR_TEXT}]Direct Cloud Giants[/bold {COLOR_TEXT}]")
    console.print(f"  [bold {COLOR_PRIMARY}]1)[/bold {COLOR_PRIMARY}] Google Gemini      [bold {COLOR_SUCCESS}]★ RECOMMENDED[/bold {COLOR_SUCCESS}] [{COLOR_DIM}](Fast & Free tier at aistudio.google.com)[/{COLOR_DIM}]")
    console.print(f"  [bold {COLOR_PRIMARY}]2)[/bold {COLOR_PRIMARY}] Anthropic Claude   [{COLOR_DIM}](Top coding model - Claude 3.5 Haiku / Sonnet)[/{COLOR_DIM}]")
    console.print(f"  [bold {COLOR_PRIMARY}]3)[/bold {COLOR_PRIMARY}] OpenAI             [{COLOR_DIM}](GPT-4o mini, GPT-4o at platform.openai.com)[/{COLOR_DIM}]")

    console.print(f"\n {make_badge('GROUP 2', COLOR_SECONDARY)} [bold {COLOR_TEXT}]High-Speed & Value Powerhouses[/bold {COLOR_TEXT}]")
    console.print(f"  [bold {COLOR_PRIMARY}]4)[/bold {COLOR_PRIMARY}] DeepSeek           [{COLOR_DIM}](Ultra-low cost, coding expert at platform.deepseek.com)[/{COLOR_DIM}]")
    console.print(f"  [bold {COLOR_PRIMARY}]5)[/bold {COLOR_PRIMARY}] Groq               [{COLOR_DIM}](Sub-second ultra-fast inference at console.groq.com)[/{COLOR_DIM}]")

    console.print(f"\n {make_badge('GROUP 3', COLOR_PRIMARY)} [bold {COLOR_TEXT}]Universal Hub (200+ Models in 1 Key)[/bold {COLOR_TEXT}]")
    console.print(f"  [bold {COLOR_PRIMARY}]6)[/bold {COLOR_PRIMARY}] OpenRouter         [{COLOR_DIM}](Access Claude, GPT, DeepSeek, Llama via openrouter.ai)[/{COLOR_DIM}]")

    console.print(f"\n {make_badge('GROUP 4', COLOR_WARNING)} [bold {COLOR_TEXT}]Local & Self-Hosted (Free & Offline)[/bold {COLOR_TEXT}]")
    console.print(f"  [bold {COLOR_PRIMARY}]7)[/bold {COLOR_PRIMARY}] Ollama             [{COLOR_DIM}](100% Free & Local via localhost:11434)[/{COLOR_DIM}]")
    console.print(f"  [bold {COLOR_PRIMARY}]8)[/bold {COLOR_PRIMARY}] Custom Endpoint    [{COLOR_DIM}](LM Studio, vLLM, LocalAI OpenAI-compatible)[/{COLOR_DIM}]")

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
    details = f"{make_badge('ACTIVE', COLOR_SUCCESS)} Provider: [bold {COLOR_PRIMARY}]{provider}[/bold {COLOR_PRIMARY}]  [dim]│[/dim]  Model: [bold {COLOR_WARNING}]{saved_model}[/bold {COLOR_WARNING}]"
    if saved_host:
        details += f"\nEndpoint: [{COLOR_DIM}]{saved_host}[/{COLOR_DIM}]"

    console.print(Panel(
        f"{details}\n"
        f"Config saved to: [{COLOR_DIM}]{config.get_config_path()}[/{COLOR_DIM}]\n\n"
        f"[bold {COLOR_TEXT}]Quick Start (No flags needed!):[/bold {COLOR_TEXT}]\n"
        f"  • [bold {COLOR_PRIMARY}]shift-this-version shift[/bold {COLOR_PRIMARY}]    [{COLOR_SUBTEXT}]➔ Run AI version shift using saved settings[/{COLOR_SUBTEXT}]\n"
        f"  • [bold {COLOR_PRIMARY}]shift-this-version --dry-run[/bold {COLOR_PRIMARY}] [{COLOR_SUBTEXT}]➔ Test AI analysis without modifying files[/{COLOR_SUBTEXT}]\n"
        f"  • [bold {COLOR_PRIMARY}]shift-this-version status[/bold {COLOR_PRIMARY}]   [{COLOR_SUBTEXT}]➔ Check Git diff & detected version files[/{COLOR_SUBTEXT}]\n"
        f"  • [bold {COLOR_PRIMARY}]shift-this-version config[/bold {COLOR_PRIMARY}]   [{COLOR_SUBTEXT}]➔ Change provider, model, or host anytime[/{COLOR_SUBTEXT}]",
        title=f"[bold {COLOR_SUCCESS}]✦ Setup Complete! ✦[/bold {COLOR_SUCCESS}]",
        border_style=COLOR_SUCCESS,
        box=ROUNDED,
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
        rec_tags["major"] = f" {make_badge('★ AI RECOMMENDED', COLOR_DANGER, fg_color='white')}"
    elif bump_lower == "minor":
        default_opt = "2"
        rec_tags["minor"] = f" {make_badge('★ AI RECOMMENDED', COLOR_WARNING)}"
    elif bump_lower == "patch":
        default_opt = "1"
        rec_tags["patch"] = f" {make_badge('★ AI RECOMMENDED', COLOR_SUCCESS)}"

    console.print(f"\n[bold {COLOR_TEXT}]{title}[/bold {COLOR_TEXT}] [dim]│ Current:[/dim] [bold {COLOR_PRIMARY}]{current_ver}[/bold {COLOR_PRIMARY}]")
    console.print(f"  [bold {COLOR_PRIMARY}][1][/bold {COLOR_PRIMARY}] [bold white]Patch[/bold white]   ➔  [bold {COLOR_SUCCESS}]{patch_v:<10}[/bold {COLOR_SUCCESS}]{rec_tags['patch']}  [{COLOR_MUTED}](Bug fixes, backward-compatible)[/{COLOR_MUTED}]")
    console.print(f"  [bold {COLOR_PRIMARY}][2][/bold {COLOR_PRIMARY}] [bold white]Minor[/bold white]   ➔  [bold {COLOR_WARNING}]{minor_v:<10}[/bold {COLOR_WARNING}]{rec_tags['minor']}  [{COLOR_MUTED}](New features, backward-compatible)[/{COLOR_MUTED}]")
    console.print(f"  [bold {COLOR_PRIMARY}][3][/bold {COLOR_PRIMARY}] [bold white]Major[/bold white]   ➔  [bold {COLOR_DANGER}]{major_v:<10}[/bold {COLOR_DANGER}]{rec_tags['major']}  [{COLOR_MUTED}](Breaking changes / major redesign)[/{COLOR_MUTED}]")
    console.print(f"  [bold {COLOR_PRIMARY}][4][/bold {COLOR_PRIMARY}] [bold white]Custom[/bold white]  ➔  [dim]Enter a custom version string[/dim]")
    console.print(f"  [bold {COLOR_DANGER}][0][/bold {COLOR_DANGER}] [dim]Cancel[/dim]")

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
            console.print(f"[{COLOR_WARNING}]Aborted.[/{COLOR_WARNING}]")
            raise typer.Exit(code=0)
        return custom
    else:
        console.print(f"[{COLOR_WARNING}]Aborted by user.[/{COLOR_WARNING}]")
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
    console.print(f"\n[bold {COLOR_TEXT}]✦ Smart SemVer Shift ✦[/bold {COLOR_TEXT}] [{COLOR_DIM}]Driven by Code Diff & AI[/{COLOR_DIM}]")
    check_update.show_update_notification_if_available(console, __version__)

    # 1. Inspect Git status and workspace changes
    in_git = git_ops.is_git_repo()
    latest_tag = git_ops.get_latest_tag() if in_git else None
    commits = git_ops.get_commits_since(latest_tag) if in_git else []
    dirty_files = git_ops.get_dirty_files() if in_git else []

    if not in_git:
        console.print(f"[bold {COLOR_WARNING}]Notice: Current directory is not a Git repository.[/bold {COLOR_WARNING}]")
        if not manual:
            if not yes:
                fallback = Confirm.ask("Would you like to shift version in project files manually?", default=True)
                if not fallback:
                    raise typer.Exit(code=0)
                manual = True
            else:
                console.print(f"[{COLOR_DANGER}]Cannot run AI diff analysis outside a Git repository.[/{COLOR_DANGER}]")
                raise typer.Exit(code=1)

    # 1.1 Pre-AI Scope Decision: Decide whether to include uncommitted workspace changes (modified & new files)
    stage_all_modified = True
    if in_git and dirty_files:
        console.print(f"\n[bold {COLOR_TEXT}]Workspace Changes Detected ({len(dirty_files)} file{'s' if len(dirty_files) > 1 else ''}):[/bold {COLOR_TEXT}]")
        status_map = {
            "M": (f"[{COLOR_WARNING}]modified[/{COLOR_WARNING}]", "~"),
            "A": (f"[{COLOR_SUCCESS}]added[/{COLOR_SUCCESS}]", "+"),
            "D": (f"[{COLOR_DANGER}]deleted[/{COLOR_DANGER}]", "-"),
            "??": (f"[bold {COLOR_SUCCESS}]new file[/bold {COLOR_SUCCESS}]", "+"),
            "R": (f"[{COLOR_PRIMARY}]renamed[/{COLOR_PRIMARY}]", "→"),
        }
        for status, file_path in dirty_files[:15]:
            label, symbol = status_map.get(status, (f"[{COLOR_PRIMARY}]{status}[/{COLOR_PRIMARY}]", "*"))
            console.print(f"  {symbol} {label}: [white]{file_path}[/white]")
        if len(dirty_files) > 15:
            console.print(f"  ... and {len(dirty_files) - 15} more files.")

        if not yes:
            stage_all_modified = Confirm.ask(
                f"\n[bold {COLOR_PRIMARY}]Include all {len(dirty_files)} workspace changes (modified & new files) in this release & AI analysis?[/bold {COLOR_PRIMARY}]",
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
            console.print(f"[{COLOR_WARNING}]No committed changes detected since the last release (workspace changes were excluded).[/{COLOR_WARNING}]")
        else:
            console.print(f"[{COLOR_WARNING}]No commits or diff changes detected since the last release.[/{COLOR_WARNING}]")
        raise typer.Exit(code=0)

    # 2. Find version targets
    targets = updater.find_version_targets(custom_var_names=var_name)
    if not targets:
        console.print(f"[{COLOR_DANGER}]Error: Could not find any version targets (pyproject.toml, package.json, or code variable like VERSION).[/{COLOR_DANGER}]")
        raise typer.Exit(code=1)

    current_ver = (latest_tag.lstrip("v") if latest_tag else targets[0].current_version)

    # 3. Determine if running in Manual Mode or AI Mode
    is_manual = manual or (provider and provider.lower() in ("manual", "none")) or (not in_git)
    next_ver: Optional[str] = None
    bump_type: str = "MANUAL"

    if is_manual:
        console.print(f"[bold {COLOR_PRIMARY}]Running in Manual Mode (No AI)[/bold {COLOR_PRIMARY}]")
        next_ver = prompt_manual_bump(current_ver)
    else:
        saved_prov = config.get_default_provider()
        active_prov = provider if (provider and provider != "auto") else saved_prov

        if not active_prov or active_prov == "auto":
            detected_prov, _ = analyzer.detect_default_provider()
            active_prov = detected_prov

        if not active_prov:
            console.print(f"[bold {COLOR_WARNING}]Notice: No AI provider or API key configured.[/bold {COLOR_WARNING}]")
            if not yes:
                fallback_to_manual = Confirm.ask("Would you like to shift version manually?", default=True)
                if not fallback_to_manual:
                    console.print(f"[{COLOR_WARNING}]Run 'shift-this-version config' to configure an AI provider.[/{COLOR_WARNING}]")
                    raise typer.Exit(code=0)
                next_ver = prompt_manual_bump(current_ver)
            else:
                console.print(f"[{COLOR_DANGER}]Cannot proceed in non-interactive mode without a configured provider.[/{COLOR_DANGER}]")
                raise typer.Exit(code=1)
        else:
            active_model = model or config.get_configured_model(active_prov)
            active_host = host or config.get_configured_host(active_prov)
            model_disp = f" ({active_model})" if active_model else ""

            # 4. Call AI analyzer with graceful fallback
            analysis: Optional[analyzer.BumpAnalysis] = None
            ai_error: Optional[Exception] = None
            with console.status(f"[bold {COLOR_SUCCESS}]AI is analyzing code diff & commits using [{COLOR_PRIMARY}]{active_prov}[/{COLOR_PRIMARY}]{model_disp}..."):
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
                console.print(f"[bold {COLOR_DANGER}]AI Analysis Failed:[/bold {COLOR_DANGER}] {ai_error}")
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

                bump_color_map = {
                    "MAJOR": (COLOR_DANGER, "white"),
                    "MINOR": (COLOR_WARNING, "black"),
                    "PATCH": (COLOR_SUCCESS, "black"),
                    "NONE": (COLOR_MUTED, "black"),
                }
                pill_bg, pill_fg = bump_color_map.get(bump_type, (COLOR_PRIMARY, "black"))
                badge_str = make_badge(f"{bump_type} SHIFT", pill_bg, fg_color=pill_fg)

                # 6. Display recommendation in Modern Minimalist Dark Card
                panel_content = (
                    f"  [dim]Current[/dim] [bold {COLOR_TEXT}]v{current_ver}[/bold {COLOR_TEXT}]   "
                    f"[bold {COLOR_PRIMARY}]──────────▶[/bold {COLOR_PRIMARY}]   "
                    f"[dim]Target[/dim] [bold {pill_bg}]v{next_ver}[/bold {pill_bg}]   "
                    f"{badge_str}\n\n"
                    f"  [bold {COLOR_TEXT}]Confidence :[/bold {COLOR_TEXT}] {render_confidence_bar(analysis.confidence)}\n"
                )

                suggested_msg = getattr(analysis, "commit_message", "") if analysis else ""
                if suggested_msg:
                    panel_content += f"  [bold {COLOR_TEXT}]Suggested  :[/bold {COLOR_TEXT}] [bold {COLOR_SUCCESS}]{suggested_msg}[/bold {COLOR_SUCCESS}]\n"

                panel_content += f"\n  [bold {COLOR_TEXT}]Reasoning  :[/bold {COLOR_TEXT}]\n  [{COLOR_SUBTEXT}]{analysis.reasoning}[/{COLOR_SUBTEXT}]\n"

                if analysis.breaking_changes:
                    panel_content += f"\n  [bold {COLOR_DANGER}]Breaking Changes Detected:[/bold {COLOR_DANGER}]\n"
                    for b in analysis.breaking_changes:
                        panel_content += f"    ▲ [bold {COLOR_DANGER}]{b}[/bold {COLOR_DANGER}]\n"

                if analysis.key_changes:
                    panel_content += f"\n  [bold {COLOR_PRIMARY}]Key Changes:[/bold {COLOR_PRIMARY}]\n"
                    for k in analysis.key_changes:
                        panel_content += f"    • [{COLOR_SUBTEXT}]{k}[/{COLOR_SUBTEXT}]\n"

                console.print(Panel(
                    panel_content,
                    title=f"[bold {COLOR_TEXT}]✦ AI Recommendation: {badge_str} ✦[/bold {COLOR_TEXT}]",
                    border_style=pill_bg,
                    box=ROUNDED,
                    expand=False
                ))

    # Display targets to update in modern table
    target_table = Table(
        title="Version Targets to Update",
        box=ROUNDED,
        border_style=COLOR_BORDER,
        header_style=f"bold {COLOR_PRIMARY}",
        title_style=f"bold {COLOR_TEXT}",
        show_header=True
    )
    target_table.add_column("Target Type", style=COLOR_SECONDARY, width=14)
    target_table.add_column("File Path", style=f"bold {COLOR_TEXT}")
    target_table.add_column("Line", justify="right", style=COLOR_WARNING)
    target_table.add_column("Update Plan", style=f"bold {COLOR_SUCCESS}")
    for t in targets:
        target_table.add_row(
            t.target_type,
            str(t.file_path),
            str(t.line_number),
            f"[{COLOR_MUTED}]v{t.current_version}[/{COLOR_MUTED}] ➔ [bold {COLOR_SUCCESS}]v{next_ver}[/bold {COLOR_SUCCESS}]"
        )
    console.print(target_table)

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
        console.print(f"\n[bold {COLOR_TEXT}]── Release Confirmation Stages ───────────────────────────[/bold {COLOR_TEXT}]")

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
                f" [bold {COLOR_PRIMARY}]Stage 2 (Git Commit)[/bold {COLOR_PRIMARY}]: Create Git commit for this release{scope_hint}?",
                default=commit
            )
        else:
            do_commit = False

        # Stage 3: Commit Message [y/n]
        if do_commit:
            msg_label = "AI-suggested message" if ai_commit_msg else "default message"
            use_default_msg = Confirm.ask(
                f" [bold {COLOR_PRIMARY}]Stage 3 (Commit Message)[/bold {COLOR_PRIMARY}]: Use {msg_label}: [bold {COLOR_SUCCESS}]'{commit_msg}'[/bold {COLOR_SUCCESS}]?",
                default=True
            )
            if not use_default_msg:
                commit_msg = typer.prompt("  Enter custom commit message", default=commit_msg).strip()

        # Stage 4: Git Tag [y/n]
        if in_git:
            tag_name = f"v{chosen_ver}"
            tag_already_exists = git_ops.tag_exists(tag_name)
            tag_notice = f" [bold {COLOR_DANGER}](Notice: Tag already exists locally)[/bold {COLOR_DANGER}]" if tag_already_exists else ""
            do_tag = Confirm.ask(
                f" [bold {COLOR_PRIMARY}]Stage 4 (Git Tag)[/bold {COLOR_PRIMARY}]: Create Git tag [bold {COLOR_PRIMARY}]{tag_name}[/bold {COLOR_PRIMARY}]?{tag_notice}",
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
            remote_notice = "" if has_origin else f" [bold {COLOR_WARNING}](Notice: No remote 'origin' configured)[/bold {COLOR_WARNING}]"
            do_push = Confirm.ask(
                f" [bold {COLOR_PRIMARY}]Stage 5 (Git Push)[/bold {COLOR_PRIMARY}]: {action_label} commit and tag to remote repository (origin/{active_branch})?{remote_notice}",
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
            console.print(f"  {make_badge('UPDATED', COLOR_SUCCESS)} [bold {COLOR_TEXT}]{t.file_path}[/bold {COLOR_TEXT}] ➔ [bold {COLOR_SUCCESS}]v{chosen_ver}[/bold {COLOR_SUCCESS}]")
        else:
            console.print(f"  {make_badge('FAILED', COLOR_DANGER, fg_color='white')} [bold {COLOR_TEXT}]{t.file_path}[/bold {COLOR_TEXT}]")

    # 8.1 Sync lockfiles if present (e.g. uv.lock, poetry.lock)
    synced_locks = updater.sync_lockfiles()
    for lock_path in synced_locks:
        if lock_path not in updated_files:
            updated_files.append(lock_path)
            console.print(f"  {make_badge('SYNCED', COLOR_SECONDARY)} [bold {COLOR_TEXT}]{lock_path}[/bold {COLOR_TEXT}] ➔ [bold {COLOR_SUCCESS}]v{chosen_ver}[/bold {COLOR_SUCCESS}]")

    # 9. Git Commit
    if updated_files and do_commit:
        if git_ops.commit_version_bump(updated_files, chosen_ver, stage_all=stage_all_modified, message=commit_msg):
            scope_desc = f"{len(updated_files)} version target(s) + {len(dirty_files)} workspace file(s)" if stage_all_modified and dirty_files else f"{len(updated_files)} version target(s) only"
            console.print(f"  {make_badge('COMMITTED', COLOR_SUCCESS)} '[bold {COLOR_TEXT}]{commit_msg}[/bold {COLOR_TEXT}]' ([dim]{scope_desc}[/dim])")
        else:
            console.print(f"  [{COLOR_DIM}]Git commit skipped or no changes staged.[/{COLOR_DIM}]")

    # 10. Git Tag
    tag_created = False
    if do_tag:
        tag_name = f"v{chosen_ver}"
        tag_msg_payload = git_ops.format_tag_message(tag_name, commit_msg=commit_msg, analysis=analysis)
        tag_ok, tag_msg = git_ops.create_git_tag(tag_name, message=tag_msg_payload)
        if tag_ok:
            console.print(f"  {make_badge('TAGGED', COLOR_SUCCESS)} [bold {COLOR_PRIMARY}]{tag_name}[/bold {COLOR_PRIMARY}]")
            tag_created = True
        else:
            console.print(f"  [{COLOR_WARNING}]Tag notice:[/{COLOR_WARNING}] {tag_msg}")

    # 11. Git Push to Remote
    if do_push and (do_commit or tag_created):
        with console.status(f"[bold {COLOR_SUCCESS}]Pushing commit and tags to remote repository..."):
            tag_to_push = f"v{chosen_ver}" if tag_created else None
            success, msg = git_ops.push_to_remote(tag_name=tag_to_push)
        if success:
            console.print(f"  {make_badge('PUSHED', COLOR_SUCCESS)} [bold {COLOR_PRIMARY}]{msg}[/bold {COLOR_PRIMARY}]")
        else:
            console.print(f"  [{COLOR_WARNING}]Push skipped or remote notice:[/{COLOR_WARNING}] {msg}")

def version_callback(value: bool):
    """Show the application version and exit."""
    if value:
        console.print(f"[bold {COLOR_TEXT}]shift-this-version[/bold {COLOR_TEXT}] {make_badge('v' + __version__, COLOR_PRIMARY)}", highlight=False)
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

            banner_body = (
                f"[bold {COLOR_TEXT}]✦ SHIFT-THIS-VERSION ✦[/bold {COLOR_TEXT}]  "
                f"[bold black on {COLOR_PRIMARY}] v{__version__} [/bold black on {COLOR_PRIMARY}]\n"
                f"[{COLOR_MUTED}]AI-Driven Semantic Versioning & Automated Release Automation[/{COLOR_MUTED}]\n\n"
                f"{make_badge('PROVIDER', COLOR_PRIMARY)} [bold {COLOR_TEXT}]{def_prov}[/bold {COLOR_TEXT}] [{COLOR_DIM}]({def_model})[/{COLOR_DIM}]  "
                f"{make_badge('STATUS', COLOR_SUCCESS)} [bold {COLOR_TEXT}]Ready[/bold {COLOR_TEXT}]\n\n"
                f"[bold {COLOR_TEXT}]Available Commands:[/bold {COLOR_TEXT}]\n"
                f"  ⚡ [bold {COLOR_PRIMARY}]shift[/bold {COLOR_PRIMARY}]     [{COLOR_SUBTEXT}]➔ Analyze diff with AI & shift SemVer across targets[/{COLOR_SUBTEXT}]\n"
                f"  🔍 [bold {COLOR_PRIMARY}]status[/bold {COLOR_PRIMARY}]    [{COLOR_SUBTEXT}]➔ Inspect Git diff, commits & version targets[/{COLOR_SUBTEXT}]\n"
                f"  🩺 [bold {COLOR_PRIMARY}]doctor[/bold {COLOR_PRIMARY}]    [{COLOR_SUBTEXT}]➔ System, Git, version files & AI diagnostics[/{COLOR_SUBTEXT}]\n"
                f"  ⚙️  [bold {COLOR_PRIMARY}]config[/bold {COLOR_PRIMARY}]    [{COLOR_SUBTEXT}]➔ Reconfigure AI provider, model, or custom host[/{COLOR_SUBTEXT}]\n"
                f"  🚀 [bold {COLOR_PRIMARY}]update[/bold {COLOR_PRIMARY}]    [{COLOR_SUBTEXT}]➔ Check PyPI and self-upgrade to latest release[/{COLOR_SUBTEXT}]\n"
                f"  📖 [bold {COLOR_PRIMARY}]help[/bold {COLOR_PRIMARY}]      [{COLOR_SUBTEXT}]➔ Show detailed command guide and option flags[/{COLOR_SUBTEXT}]\n\n"
                f"[{COLOR_DIM}]Run 'shift-this-version shift --dry-run' to preview AI analysis safely.[/{COLOR_DIM}]"
            )
            console.print(Panel(
                banner_body,
                border_style=COLOR_PRIMARY,
                box=ROUNDED,
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
                f"[bold {COLOR_TEXT}]shift-this-version [shift][/bold {COLOR_TEXT}]\n"
                f"[{COLOR_SUBTEXT}]Analyze Git diff & recent commits with AI to automatically decide and bump SemVer.[/{COLOR_SUBTEXT}]\n"
                f"[{COLOR_DIM}]By default, runs automatically using your saved provider and model from setup.[/{COLOR_DIM}]\n\n"
                f"[bold {COLOR_WARNING}]Options (Optional Overrides):[/bold {COLOR_WARNING}]\n"
                f"  [bold {COLOR_PRIMARY}]--provider, -p[/bold {COLOR_PRIMARY}]  : Override provider (gemini, anthropic, openai, deepseek, groq, openrouter, ollama, custom)\n"
                f"  [bold {COLOR_PRIMARY}]--model, -m[/bold {COLOR_PRIMARY}]     : Override model name\n"
                f"  [bold {COLOR_PRIMARY}]--dry-run[/bold {COLOR_PRIMARY}]       : Simulate without modifying any files or Git state\n"
                f"  [bold {COLOR_PRIMARY}]--yes, -y[/bold {COLOR_PRIMARY}]       : Skip confirmation prompts (for CI/CD pipelines)\n"
                f"  [bold {COLOR_PRIMARY}]--host[/bold {COLOR_PRIMARY}]          : Custom Host / Base URL for Ollama, LM Studio, or vLLM\n"
                f"  [bold {COLOR_PRIMARY}]--var[/bold {COLOR_PRIMARY}]           : Target specific variable names in code (e.g. VERSION, APP_VERSION)\n"
                f"  [bold {COLOR_PRIMARY}]--manual[/bold {COLOR_PRIMARY}]        : Run in manual mode (select Patch/Minor/Major interactively without AI)\n"
                f"  [bold {COLOR_PRIMARY}]--no-tag[/bold {COLOR_PRIMARY}]        : Disable automatic Git tag creation\n"
                f"  [bold {COLOR_PRIMARY}]--no-commit[/bold {COLOR_PRIMARY}]     : Disable automatic Git commit creation",
                title=f"[bold {COLOR_PRIMARY}]✦ Command: shift ✦[/bold {COLOR_PRIMARY}]",
                border_style=COLOR_PRIMARY,
                box=ROUNDED,
                expand=False
            ))
            return
        elif cmd_name in ("inspect", "status", "check"):
            console.print(Panel(
                f"[bold {COLOR_TEXT}]shift-this-version inspect (aliases: status, check)[/bold {COLOR_TEXT}]\n"
                f"[{COLOR_SUBTEXT}]Scan repository for Git status, recent commits, diff, and all detected version targets.[/{COLOR_SUBTEXT}]",
                title=f"[bold {COLOR_PRIMARY}]✦ Command: inspect / status ✦[/bold {COLOR_PRIMARY}]",
                border_style=COLOR_PRIMARY,
                box=ROUNDED,
                expand=False
            ))
            return
        elif cmd_name == "doctor":
            console.print(Panel(
                f"[bold {COLOR_TEXT}]shift-this-version doctor[/bold {COLOR_TEXT}]\n"
                f"[{COLOR_SUBTEXT}]Run diagnostic checks on Git, project version files, AI configuration, and update status.[/{COLOR_SUBTEXT}]",
                title=f"[bold {COLOR_PRIMARY}]✦ Command: doctor ✦[/bold {COLOR_PRIMARY}]",
                border_style=COLOR_PRIMARY,
                box=ROUNDED,
                expand=False
            ))
            return
        elif cmd_name in ("update", "upgrade"):
            console.print(Panel(
                f"[bold {COLOR_TEXT}]shift-this-version update (alias: upgrade)[/bold {COLOR_TEXT}]\n"
                f"[{COLOR_SUBTEXT}]Check PyPI for the latest version and upgrade shift-this-version.[/{COLOR_SUBTEXT}]\n\n"
                f"[bold {COLOR_WARNING}]Options:[/bold {COLOR_WARNING}]\n"
                f"  [bold {COLOR_PRIMARY}]--check[/bold {COLOR_PRIMARY}]     : Check for updates without installing\n"
                f"  [bold {COLOR_PRIMARY}]--yes, -y[/bold {COLOR_PRIMARY}]   : Automatically accept upgrade prompt",
                title=f"[bold {COLOR_PRIMARY}]✦ Command: update ✦[/bold {COLOR_PRIMARY}]",
                border_style=COLOR_PRIMARY,
                box=ROUNDED,
                expand=False
            ))
            return
        elif cmd_name == "config":
            console.print(Panel(
                f"[bold {COLOR_TEXT}]shift-this-version config[/bold {COLOR_TEXT}]\n"
                f"[{COLOR_SUBTEXT}]Launch the onboarding setup wizard to reconfigure AI provider, model, or host.[/{COLOR_SUBTEXT}]",
                title=f"[bold {COLOR_PRIMARY}]✦ Command: config ✦[/bold {COLOR_PRIMARY}]",
                border_style=COLOR_PRIMARY,
                box=ROUNDED,
                expand=False
            ))
            return
        else:
            console.print(f"[{COLOR_DANGER}]Unknown command: '{command}'[/{COLOR_DANGER}]")

    console.print(Panel(
        f"[bold {COLOR_TEXT}]shift-this-version[/bold {COLOR_TEXT}] - [{COLOR_SUBTEXT}]Smart SemVer Bumper driven by Code Diff & AI[/{COLOR_SUBTEXT}]\n\n"
        f"[bold {COLOR_TEXT}]Commands:[/bold {COLOR_TEXT}]\n"
        f"  • [bold {COLOR_PRIMARY}]shift-this-version shift[/bold {COLOR_PRIMARY}]           [{COLOR_SUBTEXT}]➔ Analyze diff with AI, bump version & push[/{COLOR_SUBTEXT}]\n"
        f"  • [bold {COLOR_PRIMARY}]shift-this-version status[/bold {COLOR_PRIMARY}]          [{COLOR_SUBTEXT}]➔ Inspect Git diff, history, and version targets[/{COLOR_SUBTEXT}]\n"
        f"  • [bold {COLOR_PRIMARY}]shift-this-version doctor[/bold {COLOR_PRIMARY}]          [{COLOR_SUBTEXT}]➔ Diagnose Git, version files, AI & connectivity[/{COLOR_SUBTEXT}]\n"
        f"  • [bold {COLOR_PRIMARY}]shift-this-version update[/bold {COLOR_PRIMARY}]          [{COLOR_SUBTEXT}]➔ Check and upgrade to latest release[/{COLOR_SUBTEXT}]\n"
        f"  • [bold {COLOR_PRIMARY}]shift-this-version config[/bold {COLOR_PRIMARY}]          [{COLOR_SUBTEXT}]➔ Change default provider, model, or host[/{COLOR_SUBTEXT}]\n"
        f"  • [bold {COLOR_PRIMARY}]shift-this-version --version[/bold {COLOR_PRIMARY}]       [{COLOR_SUBTEXT}]➔ Show application version number (-v, --v)[/{COLOR_SUBTEXT}]\n\n"
        f"[bold {COLOR_TEXT}]Optional Overrides:[/bold {COLOR_TEXT}]\n"
        f"  [{COLOR_MUTED}]$ shift-this-version shift --manual[/{COLOR_MUTED}]\n"
        f"  [{COLOR_MUTED}]$ shift-this-version shift -p gemini[/{COLOR_MUTED}]\n"
        f"  [{COLOR_MUTED}]$ shift-this-version shift -p openrouter -m anthropic/claude-3.5-haiku[/{COLOR_MUTED}]\n"
        f"  [{COLOR_MUTED}]$ shift-this-version shift --no-push[/{COLOR_MUTED}]",
        title=f"[bold {COLOR_PRIMARY}]✦ Help & Usage Guide ✦[/bold {COLOR_PRIMARY}]",
        border_style=COLOR_PRIMARY,
        box=ROUNDED,
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
                    colored_rest += f"[bold {COLOR_SUCCESS}]+[/bold {COLOR_SUCCESS}]"
                elif char == "-":
                    colored_rest += f"[bold {COLOR_DANGER}]-[/bold {COLOR_DANGER}]"
                else:
                    colored_rest += escape(char)
            colored_lines.append(f"[bold {COLOR_PRIMARY}]{file_part}[/bold {COLOR_PRIMARY}]|{colored_rest}")
        elif "changed" in line and ("insertion" in line or "deletion" in line):
            colored_lines.append(f"[bold {COLOR_WARNING}]{escape(line)}[/bold {COLOR_WARNING}]")
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
            colored.append(f"[bold {COLOR_SECONDARY}]{line}[/bold {COLOR_SECONDARY}]")
        elif raw_line.startswith("+"):
            colored.append(f"[bold {COLOR_SUCCESS}]{line}[/bold {COLOR_SUCCESS}]")
        elif raw_line.startswith("-"):
            colored.append(f"[bold {COLOR_DANGER}]{line}[/bold {COLOR_DANGER}]")
        elif raw_line.startswith("@@"):
            colored.append(f"[bold {COLOR_PRIMARY}]{line}[/bold {COLOR_PRIMARY}]")
        elif raw_line.startswith("diff --git"):
            colored.append(f"[bold {COLOR_TEXT}]{line}[/bold {COLOR_TEXT}]")
        elif raw_line.startswith("index ") or raw_line.startswith("warning:"):
            colored.append(f"[{COLOR_DIM}]{line}[/{COLOR_DIM}]")
        else:
            colored.append(f"[{COLOR_SUBTEXT}]{line}[/{COLOR_SUBTEXT}]")
    return "\n".join(colored)

@app.command()
def inspect():
    """Scan and display Git history, diff preview, and detected version files/variables."""
    check_update.show_update_notification_if_available(console, __version__)
    in_git = git_ops.is_git_repo()
    targets = updater.find_version_targets()

    if not in_git:
        console.print(f"\n[bold {COLOR_WARNING}]Notice: Current directory is not a Git repository.[/bold {COLOR_WARNING}]")
        console.print(f"\n[bold {COLOR_SECONDARY}]── Detected Version Files & Variables ─────────────────[/bold {COLOR_SECONDARY}]")
        if targets:
            table = Table(title="Targets Found in Project", box=ROUNDED, border_style=COLOR_BORDER, header_style=f"bold {COLOR_PRIMARY}", show_header=True)
            table.add_column("Type", style=COLOR_SECONDARY)
            table.add_column("File Path", style=f"bold {COLOR_TEXT}")
            table.add_column("Line", justify="right", style=COLOR_WARNING)
            table.add_column("Current Version", style=f"bold {COLOR_SUCCESS}")
            table.add_column("Snippet", style=COLOR_DIM)
            for t in targets:
                table.add_row(t.target_type, str(t.file_path), str(t.line_number), f"v{t.current_version}", t.matched_line)
            console.print(table)
        else:
            console.print(f"[{COLOR_WARNING}]No version files or variables detected.[/{COLOR_WARNING}]")
        return

    latest_tag = git_ops.get_latest_tag()
    commits = git_ops.get_commits_since(latest_tag)
    diff_stat = git_ops.get_diff_stat(latest_tag)
    sample_label, sample_diff = git_ops.get_latest_diff_sample(latest_tag)
    total_diff = git_ops.get_filtered_diff(latest_tag)

    # 1. Git State
    console.print(f"\n[bold {COLOR_PRIMARY}]── 1. Git State ──────────────────────────────────────────[/bold {COLOR_PRIMARY}]")
    console.print(Panel(
        f"[bold {COLOR_TEXT}]Latest Tag:[/bold {COLOR_TEXT}] [bold {COLOR_SUCCESS}]{latest_tag or 'No previous tag (Initial Release)'}[/bold {COLOR_SUCCESS}]\n"
        f"[bold {COLOR_TEXT}]Commits Ahead:[/bold {COLOR_TEXT}] [bold {COLOR_WARNING}]{len(commits)} commit(s) ahead[/bold {COLOR_WARNING}]",
        title=f"[bold {COLOR_PRIMARY}]Git Repository Info[/bold {COLOR_PRIMARY}]",
        border_style=COLOR_PRIMARY,
        box=ROUNDED,
        expand=False
    ))

    # 2. Version Targets
    console.print(f"\n[bold {COLOR_SECONDARY}]── 2. Detected Version Files & Variables ─────────────────[/bold {COLOR_SECONDARY}]")
    if targets:
        table = Table(title="Targets Found in Project", box=ROUNDED, border_style=COLOR_BORDER, header_style=f"bold {COLOR_PRIMARY}", show_header=True)
        table.add_column("Type", style=COLOR_SECONDARY)
        table.add_column("File Path", style=f"bold {COLOR_TEXT}")
        table.add_column("Line", justify="right", style=COLOR_WARNING)
        table.add_column("Current Version", style=f"bold {COLOR_SUCCESS}")
        table.add_column("Snippet", style=COLOR_DIM)

        for t in targets:
            table.add_row(
                t.target_type,
                str(t.file_path),
                str(t.line_number),
                f"v{t.current_version}",
                t.matched_line
            )
        console.print(table)
    else:
        console.print(f"[{COLOR_WARNING}]No version files or variables (e.g. pyproject.toml, package.json, VERSION) detected.[/{COLOR_WARNING}]")

    if commits:
        console.print(f"\n[bold {COLOR_TEXT}]Recent Commits:[/bold {COLOR_TEXT}]")
        for c in commits[:10]:
            console.print(f"  • [{COLOR_PRIMARY}]{c}[/{COLOR_PRIMARY}]")
        if len(commits) > 10:
            console.print(f"  ... and {len(commits) - 10} more commits.")

    # 3. Changed Files (Diff Stat)
    if diff_stat:
        console.print(f"\n[bold {COLOR_WARNING}]── 3. Changed Files Summary ──────────────────────────────[/bold {COLOR_WARNING}]")
        colored_stat = format_diff_stat_colors(diff_stat)
        console.print(Panel(colored_stat, title=f"[bold {COLOR_WARNING}]Files Modified (+Add / -Del)[/bold {COLOR_WARNING}]", border_style=COLOR_WARNING, box=ROUNDED, expand=False))

    # 4. Latest Diff Sample Preview
    if sample_diff.strip():
        console.print(f"\n[bold {COLOR_SUCCESS}]── 4. {sample_label} ──────────────────────────────[/bold {COLOR_SUCCESS}]")
        colored_diff = format_diff_with_colors(sample_diff, max_lines=40)
        console.print(Panel(
            colored_diff,
            title=f"[bold {COLOR_SUCCESS}]{sample_label}[/bold {COLOR_SUCCESS}] [{COLOR_DIM}]({len(total_diff)} total characters)[/{COLOR_DIM}]",
            border_style=COLOR_SUCCESS,
            box=ROUNDED,
            expand=False
        ))
        if len(sample_diff.split("\n")) > 40:
            console.print(f"[{COLOR_DIM}]... remaining diff lines truncated in preview ...[/{COLOR_DIM}]")
    else:
        console.print(f"\n[bold {COLOR_SUCCESS}]No changes detected between latest tag and current workspace.[/bold {COLOR_SUCCESS}]")

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
    console.print(f"\n[bold {COLOR_TEXT}]✦ System Diagnostics (doctor) ✦[/bold {COLOR_TEXT}]\n")

    diag_table = Table(
        box=ROUNDED,
        border_style=COLOR_BORDER,
        header_style=f"bold {COLOR_PRIMARY}",
        show_header=True
    )
    diag_table.add_column("Component", style=f"bold {COLOR_SECONDARY}", width=18)
    diag_table.add_column("Status", justify="center", width=16)
    diag_table.add_column("Details", style=COLOR_SUBTEXT)

    # 1. Git Environment
    git_bin = shutil.which("git")
    if git_bin:
        diag_table.add_row("🛠  Git CLI", make_badge("● READY", COLOR_PRIMARY), f"[{COLOR_PRIMARY}]{git_bin}[/{COLOR_PRIMARY}]")
    else:
        diag_table.add_row("🛠  Git CLI", make_badge("✖ FAILED", COLOR_DANGER, fg_color="white"), f"[{COLOR_DANGER}]Not found on PATH[/{COLOR_DANGER}]")

    in_git = git_ops.is_git_repo()
    if in_git:
        latest_tag = git_ops.get_latest_tag()
        commits = git_ops.get_commits_since(latest_tag)
        diag_table.add_row("📦 Git Repository", make_badge("● SYNCED", COLOR_SUCCESS), f"Latest tag: [{COLOR_WARNING}]{latest_tag or 'None (initial)'}[/{COLOR_WARNING}] │ Ahead: [{COLOR_WARNING}]{len(commits)} commit(s)[/{COLOR_WARNING}]")
        try:
            remotes = git_ops.run_git(["remote", "-v"])
            if remotes.strip():
                first_remote = remotes.strip().split("\n")[0].split()[0]
                diag_table.add_row("🌐 Git Remote", make_badge("● ONLINE", COLOR_SECONDARY), f"[{COLOR_PRIMARY}]{first_remote}[/{COLOR_PRIMARY}]")
            else:
                diag_table.add_row("🌐 Git Remote", make_badge("▲ NOTICE", COLOR_WARNING), f"[{COLOR_WARNING}]No remote configured[/{COLOR_WARNING}]")
        except Exception:
            diag_table.add_row("🌐 Git Remote", make_badge("▲ NOTICE", COLOR_WARNING), f"[{COLOR_WARNING}]Unable to query remotes[/{COLOR_WARNING}]")
    else:
        diag_table.add_row("📦 Git Repository", make_badge("▲ NOTICE", COLOR_WARNING), f"[{COLOR_WARNING}]Current directory is not a Git repository[/{COLOR_WARNING}]")

    # 2. Version Targets in Workspace
    targets = updater.find_version_targets()
    if targets:
        versions = {t.current_version for t in targets}
        target_files = [f"{t.file_path.name}:{t.line_number}" for t in targets]
        if len(versions) == 1:
            ver = list(versions)[0]
            diag_table.add_row("🎯 Version Targets", make_badge("● IN-SYNC", COLOR_WARNING), f"[{COLOR_SUCCESS}]{len(targets)} target(s)[/{COLOR_SUCCESS}] (v{ver} in {', '.join(target_files[:3])}{'...' if len(target_files) > 3 else ''})")
        else:
            diag_table.add_row("🎯 Version Targets", make_badge("▲ MISMATCH", COLOR_DANGER, fg_color="white"), f"[{COLOR_WARNING}]{len(targets)} targets with mismatched versions: {versions}[/{COLOR_WARNING}]")
    else:
        diag_table.add_row("🎯 Version Targets", make_badge("▲ MISSING", COLOR_WARNING), f"[{COLOR_WARNING}]No version files detected[/{COLOR_WARNING}]")

    # 3. AI Configuration & Connectivity
    cfg = config.load_config()
    provider = cfg.get("default_provider", "auto")
    model = cfg.get("models", {}).get(provider, "default")
    api_key = analyzer.get_key_for_provider(provider) if provider != "auto" else None
    host = cfg.get("hosts", {}).get(provider, "")

    if provider == "ollama":
        ollama_host = host or "http://localhost:11434"
        try:
            import httpx
            resp = httpx.get(f"{ollama_host.rstrip('/')}/api/tags", timeout=2.5)
            if resp.status_code == 200:
                diag_table.add_row("🤖 AI Provider", make_badge("● ACTIVE", "#2dd4bf"), f"[{COLOR_PRIMARY}]Ollama[/{COLOR_PRIMARY}] reachable at [{COLOR_DIM}]{ollama_host}[/{COLOR_DIM}] ({model})")
            else:
                diag_table.add_row("🤖 AI Provider", make_badge("▲ NOTICE", COLOR_WARNING), f"Ollama HTTP {resp.status_code} at {ollama_host}")
        except Exception as e:
            diag_table.add_row("🤖 AI Provider", make_badge("✖ FAILED", COLOR_DANGER, fg_color="white"), f"Ollama unreachable: {e}")
    elif provider == "custom":
        if host:
            try:
                import httpx
                resp = httpx.get(host.rstrip("/"), timeout=2.5)
                diag_table.add_row("🤖 AI Provider", make_badge("● ACTIVE", "#2dd4bf"), f"Custom endpoint reachable at [{COLOR_DIM}]{host}[/{COLOR_DIM}] ({model})")
            except Exception as e:
                diag_table.add_row("🤖 AI Provider", make_badge("▲ NOTICE", COLOR_WARNING), f"Custom ping warning: {e}")
        else:
            diag_table.add_row("🤖 AI Provider", make_badge("▲ NOTICE", COLOR_WARNING), "Custom endpoint without Base URL")
    else:
        if api_key:
            masked = api_key[:4] + "..." + api_key[-4:] if len(api_key) > 8 else "***"
            diag_table.add_row("🤖 AI Provider", make_badge("● ACTIVE", "#2dd4bf"), f"[{COLOR_PRIMARY}]{provider}[/{COLOR_PRIMARY}] ({model}) │ Key: [{COLOR_DIM}]{masked}[/{COLOR_DIM}]")
        else:
            diag_table.add_row("🤖 AI Provider", make_badge("▲ NO-KEY", COLOR_WARNING), f"[{COLOR_WARNING}]No key configured for '{provider}'[/{COLOR_WARNING}]")

    # 4. Package Release & Update Check
    try:
        latest = check_update.fetch_latest_pypi_version(timeout=2.5)
        if latest:
            if check_update.is_newer_version(__version__, latest):
                diag_table.add_row("🚀 Release Status", make_badge("▲ UPDATE", COLOR_WARNING), f"Installed: [{COLOR_DIM}]v{__version__}[/{COLOR_DIM}] ➔ Latest: [bold {COLOR_WARNING}]v{latest}[/bold {COLOR_WARNING}]")
            else:
                diag_table.add_row("🚀 Release Status", make_badge("● LATEST", "#c084fc"), f"Installed: [bold {COLOR_SUCCESS}]v{__version__}[/bold {COLOR_SUCCESS}] (Up to date)")
        else:
            diag_table.add_row("🚀 Release Status", make_badge("○ OFFLINE", COLOR_MUTED), f"Installed: [{COLOR_PRIMARY}]v{__version__}[/{COLOR_PRIMARY}] (PyPI ping skipped)")
    except Exception:
        diag_table.add_row("🚀 Release Status", make_badge("● LATEST", "#c084fc"), f"Installed: [{COLOR_PRIMARY}]v{__version__}[/{COLOR_PRIMARY}]")

    console.print(diag_table)
    console.print(f"\n[bold {COLOR_SUCCESS}]✔ Diagnostics complete![/bold {COLOR_SUCCESS}]\n")

@app.command("update")
def update_cmd(
    check: bool = typer.Option(False, "--check", help="Check for updates without installing"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Automatic yes to upgrade prompt")
):
    """Check PyPI for the latest version and upgrade shift-this-version."""
    console.print(f"\n[{COLOR_SUBTEXT}]Checking for updates (current version: [bold {COLOR_PRIMARY}]v{__version__}[/bold {COLOR_PRIMARY}])...[/{COLOR_SUBTEXT}]")
    latest = check_update.fetch_latest_pypi_version(timeout=4.0)
    if not latest:
        console.print(f"[{COLOR_WARNING}]Could not reach PyPI to check for updates. Please check your internet connection.[/{COLOR_WARNING}]\n")
        return

    if not check_update.is_newer_version(__version__, latest):
        console.print(f"[bold {COLOR_SUCCESS}]shift-this-version is already up to date (v{__version__})![/bold {COLOR_SUCCESS}]\n")
        return

    console.print(Panel(
        f"[bold {COLOR_WARNING}]New version available![/bold {COLOR_WARNING}]\n"
        f"Installed: [{COLOR_DIM}]v{__version__}[/{COLOR_DIM}]\n"
        f"Latest:    [bold {COLOR_SUCCESS}]v{latest}[/bold {COLOR_SUCCESS}]",
        title=f"[bold {COLOR_SUCCESS}]✦ Update Found ✦[/bold {COLOR_SUCCESS}]",
        border_style=COLOR_SUCCESS,
        box=ROUNDED,
        expand=False
    ))

    if check:
        console.print(f"Run [bold {COLOR_PRIMARY}]shift-this-version update[/bold {COLOR_PRIMARY}] to perform the upgrade.\n")
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
            console.print(f"[{COLOR_WARNING}]Upgrade cancelled.[/{COLOR_WARNING}]\n")
            return

    console.print(f"\n[{COLOR_SUBTEXT}]Running upgrade: [bold {COLOR_PRIMARY}]{cmd_str}[/bold {COLOR_PRIMARY}]...[/{COLOR_SUBTEXT}]")
    try:
        res = subprocess.run(upgrade_cmd, check=False)
        if res.returncode == 0:
            console.print(f"\n[bold {COLOR_SUCCESS}]Successfully upgraded shift-this-version to v{latest}![/bold {COLOR_SUCCESS}]\n")
        else:
            console.print(f"\n[bold {COLOR_DANGER}]Upgrade command exited with code {res.returncode}.[/{COLOR_DANGER}]")
            console.print(f"You can try running manually: [{COLOR_PRIMARY}]{cmd_str}[/{COLOR_PRIMARY}]\n")
    except Exception as e:
        console.print(f"[{COLOR_DANGER}]Error executing upgrade: {e}[/{COLOR_DANGER}]\n")

@app.command("upgrade", hidden=True)
def upgrade_alias(
    check: bool = typer.Option(False, "--check", help="Check for updates without installing"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Automatic yes to upgrade prompt")
):
    """Alias for update."""
    update_cmd(check=check, yes=yes)

if __name__ == "__main__":
    app()