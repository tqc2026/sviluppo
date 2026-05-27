import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from agents.feasibility_analyzer import FeasibilityAnalyzer
from agents.document_generator import DocumentGenerator
from models.brief import ProjectBrief

load_dotenv()

brief = ProjectBrief(
    client_name="Amerigo",
    project_name="Amministrativi in Sanità",
    client_sector="Formazione / Pubblica Amministrazione",
    project_types=["Automazione social media", "Landing page"],
    platforms=["Facebook", "LinkedIn"],
    features=[
        "Lettura e elaborazione PDF con materiale didattico",
        "Generazione automatica pillole social con AI",
        "Creazione grafiche brandizzate automatiche",
        "Dashboard approvazione post prima della pubblicazione",
        "Pubblicazione automatica su Facebook e LinkedIn",
        "Scheduler per pianificare le pubblicazioni",
        "Landing page con raccolta email",
    ],
    content_source="PDF forniti dal cliente",
    has_brand=True,
    brand_assets=["Logo", "Palette colori"],
    needs_brand_creation=False,
    approval_workflow=True,
    posts_frequency="2-3 post a settimana",
    target_audience="Persone che vogliono superare concorsi pubblici (PA, ASL, Comuni)",
    phase2_goals="Vendita videolezioni quando il brand è consolidato",
    needs_landing_page=True,
    needs_email_marketing=True,
    timeline="4-6 settimane",
    budget_hint="Budget medio",
    special_notes="Il cliente usa uno pseudonimo. È dipendente pubblico ASL. LinkedIn API soggetta ad approvazione.",
    raw_summary="Sistema di automazione social per il brand 'Amministrativi in Sanità'. "
                "Genera pillole formative da PDF del cliente, crea grafiche brandizzate, "
                "le sottopone ad approvazione e le pubblica su Facebook e LinkedIn. "
                "Include landing page con raccolta email per preparare la fase di vendita videolezioni."
)

print("Analisi in corso...\n")
analyzer = FeasibilityAnalyzer(hourly_rate=60)
quote = analyzer.analyze(brief)

print(f"\nPreventivo generato: {len(quote.items)} voci")
print(f"Totale sviluppo: €{quote.total_one_time:,.0f}")
print(f"Totale mensile: €{quote.total_monthly:,.0f}/mese")

print("\nGenerazione documenti...")
generator = DocumentGenerator()
output_dir = generator.generate(brief, quote)
print(f"\nDocumenti salvati in: {output_dir}")
