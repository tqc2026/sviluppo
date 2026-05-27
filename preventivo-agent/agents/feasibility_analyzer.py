import json
from anthropic import Anthropic
from rich.console import Console
from models.brief import ProjectBrief
from models.quote import Quote, QuoteItem

console = Console()
client = Anthropic()

REFERENCE_PROJECT = """
PROGETTO DI RIFERIMENTO (usa come calibrazione prezzi):
Progetto: Automazione social "Amministrativi in Sanità"
- Analisi e architettura sistema: €300
- Creazione pagine social (Facebook + LinkedIn): €200
- Configurazione API (Meta, LinkedIn, Anthropic): €200
- Modulo lettura PDF: €350
- Motore AI generazione contenuti: €500
- Generatore grafiche brandizzate: €600
- Dashboard approvazione post: €700
- Modulo pubblicazione social: €500
- Scheduler pubblicazioni: €250
- Test, deploy e manuale d'uso: €400
- Landing page one-page: €600
- Integrazione email marketing (Brevo): €150
TOTALE SVILUPPO: €4.750
Costi mensili: Hosting VPS €10, Anthropic API €5, manutenzione opzionale €150
"""

SYSTEM_PROMPT_TEMPLATE = """Sei un esperto analista tecnico e commerciale di un'agenzia di sviluppo software italiana.
Analizza il project brief e genera un preventivo dettagliato e professionale.

Tariffe base dell'agenzia: HOURLY_RATE€/ora.
Aggiungi 20-30% di markup per progetti complessi.
Considera sempre rischi tecnici (API con approvazione, limitazioni platform, qualità materiale cliente).

REFERENCE_PROJECT_PLACEHOLDER

Genera un preventivo JSON con questo formato:
{
  "project_name": "",
  "client_name": "",
  "items": [
    {
      "name": "Nome voce breve (max 6 parole)",
      "description": "Descrizione professionale di 1 riga",
      "amount": 0.0,
      "item_type": "one_time",
      "notes": ""
    }
  ],
  "risks": ["rischio 1", "rischio 2"],
  "prerequisites": ["cosa deve fornire il cliente 1", "cosa deve fornire il cliente 2"]
}

Valori validi per item_type: "one_time", "monthly", "optional"

Regole:
- Includi SEMPRE: analisi architettura, configurazione API, test e deploy
- Per progetti social: aggiungi setup pagine, API social, modulo pubblicazione
- Per landing page: includi design, sviluppo, SEO base
- Per AI: includi prompt engineering e calibrazione tono
- Separa chiaramente costi una tantum, mensili e opzionali
- I prerequisiti sono cose che il cliente deve fornire, non attività di sviluppo"""


class FeasibilityAnalyzer:
    def __init__(self, hourly_rate: float = 60.0):
        self.hourly_rate = hourly_rate

    def analyze(self, brief: ProjectBrief) -> Quote:
        console.print("[dim]Analisi in corso...[/dim]")

        system_prompt = (
            SYSTEM_PROMPT_TEMPLATE
            .replace("HOURLY_RATE", str(self.hourly_rate))
            .replace("REFERENCE_PROJECT_PLACEHOLDER", REFERENCE_PROJECT)
        )

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            system=[{
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"}
            }],
            messages=[{
                "role": "user",
                "content": f"Genera il preventivo per questo progetto:\n\n{self._brief_to_text(brief)}"
            }]
        )

        return self._parse_quote(response.content[0].text)

    def _brief_to_text(self, brief: ProjectBrief) -> str:
        return "\n".join([
            f"Cliente: {brief.client_name}",
            f"Progetto: {brief.project_name}",
            f"Settore: {brief.client_sector}",
            f"Tipo progetto: {', '.join(brief.project_types)}",
            f"Piattaforme: {', '.join(brief.platforms)}",
            f"Funzionalità richieste: {', '.join(brief.features)}",
            f"Origine contenuti: {brief.content_source}",
            f"Brand esistente: {'Sì' if brief.has_brand else 'No'} — Asset: {', '.join(brief.brand_assets)}",
            f"Brand da creare: {'Sì' if brief.needs_brand_creation else 'No'}",
            f"Workflow approvazione: {'Sì' if brief.approval_workflow else 'No'}",
            f"Frequenza pubblicazioni: {brief.posts_frequency}",
            f"Target audience: {brief.target_audience}",
            f"Obiettivi fase 2: {brief.phase2_goals}",
            f"Landing page: {'Sì' if brief.needs_landing_page else 'No'}",
            f"Email marketing: {'Sì' if brief.needs_email_marketing else 'No'}",
            f"Timeline: {brief.timeline}",
            f"Budget indicativo: {brief.budget_hint}",
            f"Note speciali: {brief.special_notes}",
            f"\nRiassunto: {brief.raw_summary}",
        ])

    def _parse_quote(self, text: str) -> Quote:
        start = text.find("{")
        end = text.rfind("}") + 1

        if start == -1 or end == 0:
            console.print("[red]Errore: impossibile parsare il preventivo generato[/red]")
            return Quote()

        try:
            data = json.loads(text[start:end])
            quote = Quote(
                project_name=data.get("project_name", ""),
                client_name=data.get("client_name", ""),
                risks=data.get("risks", []),
                prerequisites=data.get("prerequisites", []),
            )
            for item in data.get("items", []):
                quote.items.append(QuoteItem(
                    name=item.get("name", ""),
                    description=item.get("description", ""),
                    amount=float(item.get("amount", 0)),
                    item_type=item.get("item_type", "one_time"),
                    notes=item.get("notes", ""),
                ))
            console.print("[green]✓ Preventivo generato[/green]")
            return quote
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            console.print(f"[red]Errore parsing preventivo: {e}[/red]")
            return Quote()
