#!/usr/bin/env python3
import sys
import time
from pathlib import Path
from PIL import Image  # type: ignore
import humanize  # type: ignore

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
from rich.theme import Theme
from rich.prompt import Prompt
from rich import print as rprint
from rich.layout import Layout
from rich.live import Live

# Custom theme for a premium look
custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
    "header": "bold magenta",
    "dim": "grey50"
})

console = Console(theme=custom_theme)

def print_header():
    console.clear()
    header_text = """
    ██╗ ██████╗███╗   ██╗███████╗    ████████╗ ██████╗     ██████╗ ███╗   ██╗ ██████╗ 
    ██║██╔════╝████╗  ██║██╔════╝    ╚══██╔══╝██╔═══██╗    ██╔══██╗████╗  ██║██╔════╝ 
    ██║██║     ██╔██╗ ██║███████╗       ██║   ██║   ██║    ██████╔╝██╔██╗ ██║██║  ███╗
    ██║██║     ██║╚██╗██║╚════██║       ██║   ██║   ██║    ██╔═══╝ ██║╚██╗██║██║   ██║
    ██║╚██████╗██║ ╚████║███████║       ██║   ╚██████╔╝    ██║     ██║ ╚████║╚██████╔╝
    ╚═╝ ╚═════╝╚═╝  ╚═══╝╚══════╝       ╚═╝    ╚═════╝     ╚═╝     ╚═╝  ╚═══╝ ╚═════╝ 
    """
    console.print(Panel(header_text, subtitle="[bold cyan]ICNS to PNG Converter | By W1xced[/bold cyan]", border_style="magenta"))

def ask_output_format():
    choice = Prompt.ask(
        "[bold green]Select action[/bold green]",
        choices=["1", "q"],
        default="1",
        show_choices=False
    )
    
    if choice.lower() == 'q':
        console.print("\n[yellow]Exiting...[/yellow]")
        sys.exit(0)
    
    console.print("[info]Output format set to: [bold white]PNG (Preserve transparency)[/bold white][/info]")
    return "png"

def convert_files():
    script_dir = Path(__file__).resolve().parent
    input_dir = script_dir / "input"
    output_dir = script_dir / "output"
    input_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)

    files = [f for f in input_dir.iterdir() if f.is_file() and f.suffix.lower() == '.icns']

    if not files:
        console.print(Panel("[error]No .icns files found in 'input' folder![/error]", border_style="red"))
        choice = Prompt.ask("[yellow]Press Enter to return, or Q to quit[/yellow]", default="", show_choices=False)
        if choice.lower() == 'q':
            sys.exit(0)
        return None

    console.print(f"\n[info]Found [bold]{len(files)}[/bold] .icns file(s). Starting conversion...[/info]\n")

    stats = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=None, pulse_style="magenta"),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        console=console
    ) as progress:
        
        main_task = progress.add_task("[magenta]Converting files...", total=len(files))
        
        for fp in files:
            try:
                progress.update(main_task, description=f"[dim]Processing: {fp.name}[/dim]")
                orig_size = fp.stat().st_size
                
                with Image.open(fp) as img:
                    img.load()
                    if img.mode not in ("RGB", "RGBA"):
                        img = img.convert("RGBA")
                    out_path = output_dir / (fp.stem + ".png")
                    img.save(out_path, "PNG", optimize=False)

                stats.append({
                    'filename': fp.name,
                    'original_size': orig_size,
                    'converted_size': out_path.stat().st_size,
                })
            except Exception as e:
                console.print(f"[error]Error converting {fp.name}: {e}[/error]")
            
            progress.advance(main_task)

    return stats

def print_summary(stats):
    if not stats:
        return

    table = Table(title="[bold magenta]Conversion Summary[/bold magenta]", border_style="dim")
    table.add_column("File Name", style="cyan")
    table.add_column("Original Size", justify="right")
    table.add_column("Converted Size", justify="right")
    table.add_column("Ratio", justify="right")

    total_orig = 0
    total_conv = 0

    for s in stats:
        total_orig += s['original_size']
        total_conv += s['converted_size']
        ratio = s['converted_size'] / s['original_size'] if s['original_size'] else 1
        table.add_row(
            s['filename'],
            humanize.naturalsize(s['original_size']),
            humanize.naturalsize(s['converted_size']),
            f"{ratio:.2f}x"
        )

    console.print("\n")
    console.print(table)

    delta = total_conv - total_orig
    change_text = f"[red]↑ {humanize.naturalsize(abs(delta))}[/red]" if delta > 0 else f"[green]↓ {humanize.naturalsize(abs(delta))}[/green]"
    
    summary_panel = Panel(
        f"[bold white]Total stats:[/bold white]\n"
        f"  Files processed: [bold cyan]{len(stats)}[/bold cyan]\n"
        f"  Total original: [bold cyan]{humanize.naturalsize(total_orig)}[/bold cyan]\n"
        f"  Total converted: [bold cyan]{humanize.naturalsize(total_conv)}[/bold cyan]\n"
        f"  Total Change: {change_text}",
        title="[bold green]Success[/bold green]",
        border_style="green",
        expand=False
    )
    console.print(summary_panel)

def main():
    while True:
        print_header()
        console.print("[dim]1.[/dim] [bold blue]Start conversion[/bold blue]")
        console.print("[dim]Q.[/dim] [bold red]Quit[/bold red]")
        
        ask_output_format()
        stats = convert_files()

        if stats is not None:
            print_summary(stats)
            console.print("\n[success]Ready for next conversion.[/success]")
        
        choice = Prompt.ask("[yellow]Press Enter to restart, or Q to quit[/yellow]", default="", show_choices=False)
        if choice.lower() == 'q':
            console.print("\n[yellow]Goodbye![/yellow]")
            break

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[warning]Operation interrupted by user.[/warning]")
    except Exception as e:
        console.print(f"\n[error]Fatal error: {e}[/error]")
