import json
from anthropic import Anthropic
from rich.console import Console
from models.brief import ProjectBrief

console = Console()

SYSTEM_PROMPT = """Sei un esperto analista di progetti digitali che lavora per un'agenzia di sviluppo software italiana.
Il tuo compito è raccogliere tutte le informazioni necessarie per elaborare un preventivo professionale per un nuovo progetto cliente.

Conduci una conversazione naturale in italiano per raccogliere queste informazioni:
1. Nome cliente e settore di appartenenza
2. Tipo di progetto (es: automazione social, landing page, e-commerce, app, ecc.)
3. Piattaforme coinvolte (Facebook, LinkedIn, Instagram, ecc.)
4. Funzionalità richieste (lista dettagliata)
5. Origine dei contenuti (PDF cliente, generati da AI, inseriti manualmente, ecc.)
6. Presenza brand (logo, palette colori già esistenti o da creare)
7. Workflow di approvazione (il cliente approva prima della pubblicazione?)
8. Frequenza di pubblicazione (se applicabile)
9. Target audience e obiettivi di marketing
10. Obiettivi futuri (fase 2, monetizzazione, ecc.)
11. Necessità di landing page e/o email marketing
12. Timeline e budget indicativo

Fai domande chiare e contestuali. Non fare tutte le domande insieme — vai per gradi in modo naturale.
Quando hai raccolto abbastanza informazioni, scrivi esattamente "BRIEF COMPLETATO" e poi fornisci un JSON strutturato.

Il JSON deve avere questo formato:
{
  "client_name": "",
  "project_name": "",
  "client_sector": "",
  "project_types": [],
  "platforms": [],
  "features": [],
  "content_source": "",
  "has_brand": false,
  "brand_assets": [],
  "needs_brand_creation": false,
  "approval_workflow": true,
  "posts_frequency": "",
  "target_audience": "",
  "phase2_goals": "",
  "needs_landing_page": false,
  "needs_email_marketing": false,
  "timeline": "",
  "budget_hint": "",
  "special_notes": "",
  "raw_summary": "breve riassunto del progetto in 2-3 righe"
}"""


class BriefCollector:
    def __init__(self):
        self.messages = []
        self.client = Anthropic()

    def collect(self) -> ProjectBrief | None:
        console.print("[dim]Descrivi il progetto del cliente. Digita 'fine' per annullare.[/dim]\n")

        self.messages.append({
            "role": "user",
            "content": "Ciao, devo raccogliere il brief per un nuovo progetto cliente. Inizia con la prima domanda."
        })

        while True:
            response = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                system=[{
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"}
                }],
                messages=self.messages
            )

            assistant_message = response.content[0].text
            self.messages.append({
                "role": "assistant",
                "content": assistant_message
            })

            if "BRIEF COMPLETATO" in assistant_message:
                return self._parse_brief(assistant_message)

            console.print(f"\n[bold cyan]Agente:[/bold cyan] {assistant_message}\n")

            user_input = console.input("[bold white]Tu:[/bold white] ").strip()

            if user_input.lower() in ("fine", "exit", "quit"):
                return None

            self.messages.append({
                "role": "user",
                "content": user_input
            })

    def _parse_brief(self, text: str) -> ProjectBrief:
        start = text.find("{")
        end = text.rfind("}") + 1

        if start == -1 or end == 0:
            console.print("[yellow]Impossibile parsare il brief JSON, uso dati parziali[/yellow]")
            return ProjectBrief()

        try:
            data = json.loads(text[start:end])
            valid_fields = ProjectBrief.__dataclass_fields__.keys()
            filtered = {k: v for k, v in data.items() if k in valid_fields}
            brief = ProjectBrief(**filtered)
            console.print("\n[green]✓ Brief raccolto con successo[/green]")
            return brief
        except (json.JSONDecodeError, TypeError) as e:
            console.print(f"[yellow]Errore nel parsing: {e}. Uso dati parziali.[/yellow]")
            return ProjectBrief()
