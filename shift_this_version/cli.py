import os
import sys
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

from shift_this_version import git_ops, analyzer, updater, config

app = typer.Typer(
    name="shift-this-version",
    help="Smart SemVer Bumper driven by Code Diff & AI (Gemini, Anthropic, OpenAI, DeepSeek, Groq, OpenRouter, Ollama)",
    no_args_is_help=False
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
):
    """Core logic to analyze diff with AI and shift SemVer across targets."""
    console.print("\n[bold blue]Starting Smart SemVer Shift[/bold blue]")

    # 1. Inspect Git status and diff
    latest_tag = git_ops.get_latest_tag()
    commits = git_ops.get_commits_since(latest_tag)
    diff = git_ops.get_diff_summary(latest_tag, max_chars=18000)

    if not diff and not commits:
        console.print("[yellow]No commits or diff changes detected since the last release.[/yellow]")
        raise typer.Exit(code=0)

    # 2. Find version targets
    targets = updater.find_version_targets(custom_var_names=var_name)
    if not targets:
        console.print("[red]Error: Could not find any version targets (pyproject.toml, package.json, or code variable like VERSION).[/red]")
        raise typer.Exit(code=1)

    current_ver = latest_tag.lstrip("v") if latest_tag else targets[0].current_version

    # 3. Resolve active provider, model, and host from saved config if not passed
    saved_prov = config.get_default_provider() or "gemini"
    active_prov = provider if (provider and provider != "auto") else saved_prov
    active_model = model or config.get_configured_model(active_prov)
    active_host = host or config.get_configured_host(active_prov)
    model_disp = f" ({active_model})" if active_model else ""

    # 4. Call AI analyzer
    analysis: Optional[analyzer.BumpAnalysis] = None
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
            console.print(f"[bold red]AI Analysis Failed:[/bold red] {e}")
            raise typer.Exit(code=1)

    # 5. Compute next SemVer
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
        f"[bold]Confidence:[/bold] {analysis.confidence * 100:.1f}%\n\n"
        f"[bold]Reasoning:[/bold]\n{analysis.reasoning}\n"
    )

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
    console.print("\n[bold]Files to update:[/bold]")
    for t in targets:
        console.print(f"  • [cyan]{t.file_path}[/cyan]:{t.line_number} ({t.current_version} -> [green]{next_ver}[/green])")

    if bump_type == "NONE" or current_ver == next_ver:
        console.print("\n[green]No version shift required.[/green]")
        raise typer.Exit(code=0)

    if dry_run:
        console.print("\n[bold yellow][DRY RUN] No files or git state were modified.[/bold yellow]")
        raise typer.Exit(code=0)

    # 7. Interactive Stage-by-Stage Confirmation (skipped if --yes)
    chosen_ver = next_ver
    do_commit = commit
    commit_msg = f"chore(release): shift version to {next_ver}"
    do_tag = tag
    do_push = push

    if not yes:
        console.print("\n[bold yellow]── Release Confirmation Stages ───────────────────────────[/bold yellow]")

        # Stage 1: Version Confirmation
        confirm_ver = Confirm.ask(
            f" [bold cyan]Stage 1 (Version)[/bold cyan]: Shift version to [bold green]{next_ver}[/bold green] across {len(targets)} targets?",
            default=True
        )
        if not confirm_ver:
            custom_v = typer.prompt("  Enter custom version (press Enter to cancel)", default="").strip()
            if not custom_v:
                console.print("[yellow]Aborted by user.[/yellow]")
                raise typer.Exit(code=0)
            chosen_ver = custom_v

        # Stage 2: Git Commit [y/n]
        do_commit = Confirm.ask(
            f" [bold cyan]Stage 2 (Git Commit)[/bold cyan]: Create Git commit for this release?",
            default=commit
        )

        # Stage 3: Commit Message [y/n]
        if do_commit:
            default_msg = f"chore(release): shift version to {chosen_ver}"
            use_default_msg = Confirm.ask(
                f" [bold cyan]Stage 3 (Commit Message)[/bold cyan]: Use default message: [dim]'{default_msg}'[/dim]?",
                default=True
            )
            if not use_default_msg:
                commit_msg = typer.prompt("  Enter custom commit message", default=default_msg).strip()
            else:
                commit_msg = default_msg

        # Stage 4: Git Tag [y/n]
        tag_name = f"v{chosen_ver}"
        do_tag = Confirm.ask(
            f" [bold cyan]Stage 4 (Git Tag)[/bold cyan]: Create Git tag [bold cyan]{tag_name}[/bold cyan]?",
            default=tag
        )

        # Stage 5: Git Push [y/n]
        if do_commit or do_tag:
            do_push = Confirm.ask(
                f" [bold cyan]Stage 5 (Git Push)[/bold cyan]: Push commit and tag to remote repository (origin)?",
                default=push
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

    # 9. Git Commit
    if updated_files and do_commit:
        if git_ops.commit_version_bump(updated_files, chosen_ver, stage_all=True, message=commit_msg):
            console.print(f"  Git committed: '[green]{commit_msg}[/green]'")
        else:
            console.print("  Git commit skipped or no changes staged.")

    # 10. Git Tag
    tag_created = False
    if do_tag:
        tag_name = f"v{chosen_ver}"
        if git_ops.create_git_tag(tag_name):
            console.print(f"  Created Git Tag: [bold cyan]{tag_name}[/bold cyan]")
            tag_created = True
        else:
            console.print(f"  Could not create Git tag {tag_name}")

    # 11. Git Push to Remote
    if do_push and (do_commit or tag_created):
        with console.status("[bold green]Pushing commit and tags to remote repository..."):
            tag_to_push = f"v{chosen_ver}" if tag_created else None
            success, msg = git_ops.push_to_remote(tag_name=tag_to_push)
        if success:
            console.print(f"  Pushed to remote: [bold cyan]{msg}[/bold cyan]")
        else:
            console.print(f"  [yellow]Push skipped or remote notice:[/yellow] {msg}")

    console.print(f"\n[bold green]Successfully shifted version to {chosen_ver}![/bold green]\n")

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Smart SemVer Bumper driven by Code Diff & AI"""
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
                "  • [bold green]shift-this-version shift --dry-run[/bold green] ➔ Preview AI recommendation safely\n"
                "  • [bold green]shift-this-version inspect[/bold green]         ➔ Inspect Git state, diff & version files\n"
                "  • [bold green]shift-this-version config[/bold green]          ➔ Reconfigure AI provider, model, or host\n"
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
    command: Optional[str] = typer.Argument(None, help="Specific command name (e.g. shift, inspect, config)")
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
                "  --no-tag        : Disable automatic Git tag creation\n"
                "  --no-commit     : Disable automatic Git commit creation",
                title="[bold green]Command: shift[/bold green]",
                expand=False
            ))
            return
        elif cmd_name == "inspect":
            console.print(Panel(
                "[bold cyan]shift-this-version inspect[/bold cyan]\n"
                "Scan repository for Git status, recent commits, diff, and all detected version targets.",
                title="[bold green]Command: inspect[/bold green]",
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
        "  • [bold green]shift-this-version shift --dry-run[/bold green] ➔ Preview AI recommendation without modifying files\n"
        "  • [bold green]shift-this-version shift -y[/bold green]        ➔ Non-interactive auto-confirm (for CI/CD)\n"
        "  • [bold green]shift-this-version inspect[/bold green]         ➔ Inspect Git diff, history, and version targets\n"
        "  • [bold green]shift-this-version config[/bold green]          ➔ Change default provider, model, or host\n\n"
        "[bold yellow]Optional Overrides:[/bold yellow]\n"
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
    latest_tag = git_ops.get_latest_tag()
    commits = git_ops.get_commits_since(latest_tag)
    diff = git_ops.get_filtered_diff(latest_tag)
    diff_stat = git_ops.get_diff_stat(latest_tag)
    targets = updater.find_version_targets()

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

    diff_stat = git_ops.get_diff_stat(latest_tag)
    sample_label, sample_diff = git_ops.get_latest_diff_sample(latest_tag)
    total_diff = git_ops.get_filtered_diff(latest_tag)

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
    var_name: Optional[List[str]] = typer.Option(None, "--var", help="Custom variable name to update in code files (e.g. VERSION)")
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
    var_name: Optional[List[str]] = typer.Option(None, "--var")
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
    )

if __name__ == "__main__":
    app()