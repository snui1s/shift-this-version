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

# ป้องกัน UnicodeEncodeError บน Windows terminal เก่า
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from shift_this_version import git_ops, analyzer, updater, config

app = typer.Typer(
    name="shift-this-version",
    help="Smart SemVer Bumper driven by Code Diff & AI (Gemini, OpenRouter, OpenAI, Ollama)",
    no_args_is_help=False
)
console = Console(force_terminal=False)

def run_setup_wizard():
    """ตัวช่วยตั้งค่าครั้งแรกและแสดงคำแนะนำการใช้งานเบื้องต้น โดยแบ่งกลุ่ม AI ตามประเภท"""
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
        model = typer.prompt("Enter Ollama Model name (e.g. llama3.2, qwen2.5-coder)", default="llama3.2").strip()
        cfg["models"]["ollama"] = model

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
        "[bold yellow]Quick Start Guide:[/bold yellow]\n"
        "  • [bold]shift-this-version inspect[/bold]   ➔ Check Git diff & detected version files\n"
        "  • [bold]shift-this-version shift --dry-run[/bold] ➔ Test AI analysis without modifying files\n"
        "  • [bold]shift-this-version shift[/bold]           ➔ Run interactive AI version bump\n"
        "  • [bold]shift-this-version config[/bold]          ➔ Change provider, model, or host anytime",
        title="[bold green]Ready to Go![/bold green]",
        expand=False
    ))


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Smart SemVer Bumper driven by Code Diff & AI"""
    if ctx.invoked_subcommand is None:
        if config.is_first_run():
            run_setup_wizard()
        else:
            cfg = config.load_config()
            def_prov = cfg.get("default_provider", "auto")
            console.print(Panel(
                f"[bold cyan]shift-this-version[/bold cyan] is ready!\n"
                f"Configured Provider: [bold green]{def_prov}[/bold green]\n\n"
                "Available Commands:\n"
                "  • [bold]shift-this-version inspect[/bold]   ➔ View Git state & version targets\n"
                "  • [bold]shift-this-version shift[/bold]     ➔ Analyze diff with AI & shift version\n"
                "  • [bold]shift-this-version config[/bold]    ➔ Reconfigure AI provider & keys\n"
                "  • [bold]shift-this-version --help[/bold]    ➔ Show all options and flags",
                title="[bold blue]shift-this-version[/bold blue]",
                expand=False
            ))

@app.command("config")
def configure():
    """ตั้งค่าหรือเปลี่ยน AI Provider และ API Key ใหม่"""
    run_setup_wizard()


@app.command()
def inspect():
    """สแกนและแสดงประวัติ Git, Diff และไฟล์ระบุเวอร์ชันในโปรเจกต์"""
    with console.status("[bold green]Inspecting repository..."):
        latest_tag = git_ops.get_latest_tag()
        commits = git_ops.get_commits_since(latest_tag)
        diff = git_ops.get_filtered_diff(latest_tag)
        targets = updater.find_version_targets()

    console.print(Panel(
        f"[bold cyan]Latest Tag:[/bold cyan] {latest_tag or 'No previous tag (Initial Release)'}\n"
        f"[bold cyan]Commits Ahead:[/bold cyan] {len(commits)}",
        title="[bold green]Git State[/bold green]"
    ))

    # แสดงรายการไฟล์/ตัวแปรเวอร์ชันที่ค้นพบ
    if targets:
        table = Table(title="Detected Version Targets (Files & Code Variables)", show_header=True)
        table.add_column("Type", style="cyan")
        table.add_column("File Path", style="bold")
        table.add_column("Line", justify="right", style="yellow")
        table.add_column("Current Version", style="green")
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
        console.print("\n[bold yellow]Recent Commits:[/bold yellow]")
        for c in commits[:10]:
            console.print(f"  • {c}")
        if len(commits) > 10:
            console.print(f"  ... and {len(commits) - 10} more commits.")

    if diff:
        console.print(f"\n[bold green]Filtered Diff Size:[/bold green] {len(diff)} characters")
        diff_preview = "\n".join(diff.split("\n")[:25])
        console.print(Syntax(diff_preview, "diff", theme="monokai", line_numbers=True))
    else:
        console.print("\n[yellow]No changes detected between latest tag and HEAD.[/yellow]")

@app.command("shift")
def shift(
    provider: str = typer.Option("auto", "--provider", "-p", help="AI provider: auto, gemini, anthropic, openai, deepseek, groq, openrouter, ollama, custom"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Specific model name (e.g. gemini-2.5-flash, claude-3-5-haiku, deepseek-chat, llama-3.3-70b)"),
    api_key: Optional[str] = typer.Option(None, "--api-key", help="API Key (or set via config/environment variable)"),
    host: Optional[str] = typer.Option(None, "--host", help="Custom host / Base URL (for Ollama, LM Studio, vLLM)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate the shift without modifying files or git"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Automatic yes to prompts; run non-interactively"),
    tag: bool = typer.Option(True, "--tag/--no-tag", help="Create a git tag for the new version"),
    commit: bool = typer.Option(True, "--commit/--no-commit", help="Commit updated version files"),
    var_name: Optional[List[str]] = typer.Option(None, "--var", help="Custom variable name to update in code files (e.g. VERSION)")
):
    """
    วิเคราะห์ Diff ด้วย AI และ Shift เลข SemVer ให้ทุกไฟล์ที่เกี่ยวข้องอัตโนมัติ
    """
    console.print("\n[bold blue]🚀 Starting Smart SemVer Shift[/bold blue]")

    # 1. ตรวจสอบ Git Status และ Diff
    latest_tag = git_ops.get_latest_tag()
    commits = git_ops.get_commits_since(latest_tag)
    diff = git_ops.get_diff_summary(latest_tag, max_chars=18000)

    if not diff and not commits:
        console.print("[yellow]⚠️ No commits or diff changes detected since the last release.[/yellow]")
        raise typer.Exit(code=0)

    # 2. ค้นหา Version Targets
    targets = updater.find_version_targets(custom_var_names=var_name)
    if not targets:
        console.print("[red]❌ Error: Could not find any version targets (pyproject.toml, package.json, or code variable like VERSION).[/red]")
        raise typer.Exit(code=1)

    # กำหนดเลขเวอร์ชันปัจจุบัน
    current_ver = latest_tag.lstrip("v") if latest_tag else targets[0].current_version

    # 3. ส่งให้ AI วิเคราะห์
    analysis: Optional[analyzer.BumpAnalysis] = None
    with console.status(f"[bold green]AI is analyzing code diff & commits using '{provider}'..."):
        try:
            analysis = analyzer.analyze(
                diff=diff,
                commits=commits,
                provider=provider,
                model=model,
                api_key=api_key,
                host=host
            )
        except Exception as e:
            console.print(f"[bold red]❌ AI Analysis Failed:[/bold red] {e}")
            raise typer.Exit(code=1)

    # 4. คำนวณเลขเวอร์ชันใหม่
    bump_type = analysis.bump_type.upper()
    next_ver = updater.calculate_next_version(current_ver, analysis.bump_type)

    # สไตล์สีตามระดับการ shift
    color_map = {
        "MAJOR": "bold red",
        "MINOR": "bold yellow",
        "PATCH": "bold green",
        "NONE": "bold white"
    }
    bump_color = color_map.get(bump_type, "bold cyan")

    # 5. แสดงผลลัพธ์
    panel_content = (
        f"[bold]Current Version:[/bold] {current_ver}\n"
        f"[bold]Suggested Version:[/bold] [{bump_color}]{next_ver}[/{bump_color}]  ([bold]{bump_type}[/bold] shift)\n"
        f"[bold]Confidence:[/bold] {analysis.confidence * 100:.1f}%\n\n"
        f"[bold]Reasoning:[/bold]\n{analysis.reasoning}\n"
    )

    if analysis.breaking_changes:
        panel_content += f"\n[bold red]⚠️ Breaking Changes Detected:[/bold red]\n"
        for b in analysis.breaking_changes:
            panel_content += f"  • [red]{b}[/red]\n"

    if analysis.key_changes:
        panel_content += f"\n[bold cyan]Key Changes:[/bold cyan]\n"
        for k in analysis.key_changes:
            panel_content += f"  • {k}\n"

    console.print(Panel(panel_content, title=f"[{bump_color}]AI Recommendation: {bump_type}[/{bump_color}]", expand=False))

    # แสดงรายการไฟล์ที่จะถูกแก้ไข
    console.print("\n[bold]Files to update:[/bold]")
    for t in targets:
        console.print(f"  📝 [cyan]{t.file_path}[/cyan]:{t.line_number} ({t.current_version} ➔ [green]{next_ver}[/green])")

    if bump_type == "NONE" or current_ver == next_ver:
        console.print("\n[green]No version shift required.[/green]")
        raise typer.Exit(code=0)

    if dry_run:
        console.print("\n[bold yellow]🔍 [DRY RUN] No files or git state were modified.[/bold yellow]")
        raise typer.Exit(code=0)

    # 6. ถามยืนยันใน Interactive Mode
    if not yes:
        confirm = Confirm.ask(
            f"\nDo you want to shift version to [bold green]{next_ver}[/bold green] across {len(targets)} targets?",
            default=True
        )
        if not confirm:
            console.print("[yellow]Aborted by user.[/yellow]")
            raise typer.Exit(code=0)

    # 7. ดำเนินการอัปเดตไฟล์
    updated_files: List[str] = []
    for t in targets:
        success = updater.apply_version_bump(t, next_ver, dry_run=False)
        if success:
            updated_files.append(str(t.file_path))
            console.print(f"  ✅ Updated [cyan]{t.file_path}[/cyan]")
        else:
            console.print(f"  ❌ Failed to update [cyan]{t.file_path}[/cyan]")

    # 8. Git Commit & Git Tag
    if updated_files and commit:
        if git_ops.commit_version_bump(updated_files, next_ver):
            console.print(f"  📦 Git committed: 'chore(release): shift version to {next_ver}'")
        else:
            console.print("  ⚠️ Git commit failed or no changes staged.")

    if tag:
        tag_name = f"v{next_ver}"
        if git_ops.create_git_tag(tag_name):
            console.print(f"  🏷️ Created Git Tag: [bold cyan]{tag_name}[/bold cyan]")
        else:
            console.print(f"  ⚠️ Could not create Git tag {tag_name}")

    console.print(f"\n[bold green]🎉 Successfully shifted version to {next_ver}![/bold green]\n")

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
    var_name: Optional[List[str]] = typer.Option(None, "--var")
):
    shift(provider=provider, model=model, api_key=api_key, host=host, dry_run=dry_run, yes=yes, tag=tag, commit=commit, var_name=var_name)


if __name__ == "__main__":
    app()