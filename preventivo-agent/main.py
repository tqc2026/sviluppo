import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

sys.path.insert(0, str(Path(__file__).parent))

from agents.brief_collector import BriefCollector
from agents.feasibility_analyzer import FeasibilityAnalyzer
from agents.document_generator import DocumentGenerator
from models.quote import Quote

load_dotenv()
console = Console()


def main():
    console.print(Panel.fit(
        "[bold blue]Sistema Preventivi Automatico[/bold blue]\n[dim]Powered by Claude AI — Agenzia Sviluppo[/dim]",
        border_style="blue"
    ))

    if not os.getenv("ANTHROPIC_API_KEY"):
        console.print("[red]Errore: ANTHROPIC_API_KEY non trovata nel file .env[/red]")
        sys.exit(1)

    hourly_rate = float(os.getenv("HOURLY_RATE", "60"))

    # Fase 1: raccolta brief
    console.print("\n[bold yellow][ FASE 1 ][/bold yellow] Raccolta Brief\n")
    collector = BriefCollector()
    brief = collector.collect()

    if not brief or not brief.client_name:
        console.print("\n[yellow]Brief non completato. Uscita.[/yellow]")
        return

    # Fase 2: analisi e preventivo
    console.print("\n[bold yellow][ FASE 2 ][/bold yellow] Analisi Fattibilità e Generazione Preventivo\n")
    analyzer = FeasibilityAnalyzer(hourly_rate=hourly_rate)
    quote = analyzer.analyze(brief)

    if not quote.items:
        console.print("[red]Impossibile generare il preventivo. Riprova.[/red]")
        return

    show_quote(quote)

    adjust = console.input("\n[yellow]Vuoi modificare qualche voce? (s/n): [/yellow]").strip().lower()
    if adjust == "s":
        quote = manual_adjust(quote)
        show_quote(quote)

    # Fase 3: generazione documenti
    console.print("\n[bold yellow][ FASE 3 ][/bold yellow] Generazione Documenti\n")
    generator = DocumentGenerator()
    output_dir = generator.generate(brief, quote)

    console.print(Panel.fit(
        f"[bold green]Documenti salvati in:[/bold green] {output_dir}\n\n"
        "  fatture_in_cloud.txt  — voci pronte per Fatture in Cloud\n"
        "  email_cliente.txt     — bozza email al cliente\n"
        "  note_tecniche.txt     — prerequisiti, rischi, piano di sviluppo",
        title="Completato",
        border_style="green"
    ))


def show_quote(quote: Quote):
    table = Table(title=f"Preventivo — {quote.project_name}", show_header=True, header_style="bold")
    table.add_column("Voce", style="cyan", width=38)
    table.add_column("Tipo", style="magenta", width=12)
    table.add_column("Importo", style="green", justify="right", width=12)

    type_labels = {"one_time": "Una tantum", "monthly": "Mensile", "optional": "Opzionale"}

    for item in quote.items:
        label = type_labels.get(item.item_type, item.item_type)
        note = f" *" if item.notes else ""
        table.add_row(f"{item.name}{note}", label, f"€{item.amount:,.0f}")

    table.add_section()
    table.add_row("[bold]TOTALE SVILUPPO[/bold]", "", f"[bold]€{quote.total_one_time:,.0f}[/bold]")
    if quote.total_monthly > 0:
        table.add_row("[bold]TOTALE MENSILE[/bold]", "", f"[bold]€{quote.total_monthly:,.0f}/mese[/bold]")
    if quote.total_optional > 0:
        table.add_row("[bold]TOTALE OPZIONALI[/bold]", "", f"[bold]€{quote.total_optional:,.0f}[/bold]")

    console.print(table)

    notes_items = [i for i in quote.items if i.notes]
    if notes_items:
        console.print("\n[dim]* Note:[/dim]")
        for item in notes_items:
            console.print(f"  [dim]{item.name}: {item.notes}[/dim]")

    if quote.risks:
        console.print("\n[yellow]Rischi:[/yellow]")
        for r in quote.risks:
            console.print(f"  [yellow]![/yellow] {r}")


def manual_adjust(quote: Quote) -> Quote:
    console.print("\n[bold]Modifica importi:[/bold]")
    for i, item in enumerate(quote.items):
        console.print(f"  [{i}] {item.name}: €{item.amount:,.0f}")

    while True:
        idx_str = console.input("\nIndice voce da modificare (invio per terminare): ").strip()
        if not idx_str:
            break
        try:
            idx = int(idx_str)
            amount_str = console.input(f"Nuovo importo per '{quote.items[idx].name}': €").strip()
            quote.items[idx].amount = float(amount_str.replace(",", "."))
            console.print("[green]✓ Aggiornato[/green]")
        except (ValueError, IndexError):
            console.print("[red]Input non valido[/red]")

    return quote


if __name__ == "__main__":
    main()
