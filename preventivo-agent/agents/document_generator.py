from datetime import date
from pathlib import Path
from anthropic import Anthropic
from rich.console import Console
from models.brief import ProjectBrief
from models.quote import Quote

console = Console()


class DocumentGenerator:
    def __init__(self):
        self.output_base = Path("output")
        self.client = Anthropic()

    def generate(self, brief: ProjectBrief, quote: Quote) -> Path:
        dir_name = f"{date.today().strftime('%Y%m%d')}_{brief.client_name.replace(' ', '_').lower() or 'cliente'}"
        output_dir = self.output_base / dir_name
        output_dir.mkdir(parents=True, exist_ok=True)

        self._generate_fatture_in_cloud(quote, output_dir)
        self._generate_email(brief, quote, output_dir)
        self._generate_technical_notes(brief, quote, output_dir)

        return output_dir

    def _generate_fatture_in_cloud(self, quote: Quote, output_dir: Path):
        lines = [
            f"PREVENTIVO — {quote.project_name}",
            f"Cliente: {quote.client_name}",
            f"Data: {quote.date}",
            "=" * 60,
            "",
        ]

        one_time = [i for i in quote.items if i.item_type == "one_time"]
        monthly = [i for i in quote.items if i.item_type == "monthly"]
        optional = [i for i in quote.items if i.item_type == "optional"]

        if one_time:
            lines += ["VOCI UNA TANTUM:", "-" * 40]
            for item in one_time:
                lines += [
                    f"Prodotto/Servizio: {item.name}",
                    f"Descrizione: {item.description}",
                    f"Importo: €{item.amount:,.0f}",
                ]
                if item.notes:
                    lines.append(f"Note: {item.notes}")
                lines.append("")
            lines += [f"TOTALE SVILUPPO: €{quote.total_one_time:,.0f}", ""]

        if monthly:
            lines += ["=" * 60, "", "VOCI MENSILI RICORRENTI:", "-" * 40]
            for item in monthly:
                lines += [
                    f"Prodotto/Servizio: {item.name}",
                    f"Descrizione: {item.description}",
                    f"Importo: €{item.amount:,.0f}/mese",
                ]
                if item.notes:
                    lines.append(f"Note: {item.notes}")
                lines.append("")
            lines += [f"TOTALE MENSILE: €{quote.total_monthly:,.0f}/mese", ""]

        if optional:
            lines += ["=" * 60, "", "VOCI OPZIONALI:", "-" * 40]
            for item in optional:
                lines += [
                    f"Prodotto/Servizio: {item.name}",
                    f"Descrizione: {item.description}",
                    f"Importo: €{item.amount:,.0f}",
                ]
                if item.notes:
                    lines.append(f"Note: {item.notes}")
                lines.append("")
            lines += [f"TOTALE OPZIONALI: €{quote.total_optional:,.0f}", ""]

        (output_dir / "fatture_in_cloud.txt").write_text("\n".join(lines), encoding="utf-8")
        console.print("[green]✓ fatture_in_cloud.txt[/green]")

    def _generate_email(self, brief: ProjectBrief, quote: Quote, output_dir: Path):
        prompt = f"""Scrivi un'email professionale in italiano per presentare un preventivo al cliente.

Progetto: {quote.project_name}
Cliente: {quote.client_name}
Totale sviluppo (una tantum): €{quote.total_one_time:,.0f}
Totale canone mensile: €{quote.total_monthly:,.0f}/mese
Riassunto progetto: {brief.raw_summary}

Linee guida:
- Tono professionale ma cordiale
- Struttura: saluto → riferimento alla nostra conversazione → riepilogo progetto → riepilogo costi → prossimi passi → disponibilità per chiarimenti
- Massimo 20 righe
- Non inserire il nome del mittente (lo aggiunge il cliente)
- Non usare emoji"""

        response = self.client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )

        (output_dir / "email_cliente.txt").write_text(response.content[0].text, encoding="utf-8")
        console.print("[green]✓ email_cliente.txt[/green]")

    def _generate_technical_notes(self, brief: ProjectBrief, quote: Quote, output_dir: Path):
        lines = [
            f"NOTE TECNICHE — {quote.project_name}",
            f"Data: {quote.date}",
            "=" * 60,
            "",
        ]

        if quote.prerequisites:
            lines += ["PREREQUISITI (a carico del cliente):", "-" * 40]
            for p in quote.prerequisites:
                lines.append(f"  [ ] {p}")
            lines.append("")

        if quote.risks:
            lines += ["RISCHI E NOTE:", "-" * 40]
            for r in quote.risks:
                lines.append(f"  ! {r}")
            lines.append("")

        lines += [
            "PIANO DI SVILUPPO INDICATIVO:",
            "-" * 40,
            "  Fase 0 — Raccolta prerequisiti e asset cliente",
            "  Fase 1 — Setup progetto, ambienti e configurazione API",
            "  Fase 2 — Sviluppo moduli core",
            "  Fase 3 — Sviluppo interfaccia e dashboard approvazione",
            "  Fase 4 — Integrazioni piattaforme social",
            "  Fase 5 — Test, messa in produzione e manuale d'uso",
            "",
            "Durata stimata: 4-6 settimane lavorative",
        ]

        (output_dir / "note_tecniche.txt").write_text("\n".join(lines), encoding="utf-8")
        console.print("[green]✓ note_tecniche.txt[/green]")
